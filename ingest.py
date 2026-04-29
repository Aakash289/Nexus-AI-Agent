import pandas as pd
import numpy as np
from datetime import datetime

TODAY = datetime(2025, 4, 14)

CHANNEL_SCHEMAS = {
    "web": {
        "id_cols": ["customer_id", "customer_email"],
        "date_col": "order_date",
        "amount_col": "order_total",
        "required": ["order_date", "order_total"],
    },
    "instore": {
        "id_cols": ["loyalty_id", "customer_email"],
        "date_col": "txn_date",
        "amount_col": "amount",
        "required": ["txn_date", "amount"],
    },
    "app": {
        "id_cols": ["app_user_id", "customer_email"],
        "date_col": "event_date",
        "amount_col": None,
        "required": ["event_date", "event_type"],
    },
}


def detect_channel(df: pd.DataFrame) -> str:
    cols = set(df.columns.str.lower())
    if "order_total" in cols:
        return "web"
    if "loyalty_id" in cols or "store_location" in cols:
        return "instore"
    if "event_type" in cols or "app_user_id" in cols:
        return "app"
    return "unknown"


def validate_file(df: pd.DataFrame, channel: str) -> list[str]:
    warnings = []
    schema = CHANNEL_SCHEMAS.get(channel, {})
    for col in schema.get("required", []):
        if col not in df.columns:
            warnings.append(f"Missing required column: `{col}`")
    if df.duplicated().sum() > 0:
        warnings.append(f"{df.duplicated().sum():,} duplicate rows detected")
    return warnings


def resolve_identities(web_df, store_df, app_df) -> pd.DataFrame:
    frames = []

    if web_df is not None:
        w = web_df[["customer_id", "customer_email"]].rename(
            columns={"customer_id": "raw_id", "customer_email": "email"}
        )
        w["channel_source"] = "web"
        frames.append(w)

    if store_df is not None:
        s = store_df[["loyalty_id", "customer_email"]].rename(
            columns={"loyalty_id": "raw_id", "customer_email": "email"}
        )
        s["channel_source"] = "instore"
        frames.append(s)

    if app_df is not None:
        a = app_df[["app_user_id", "customer_email"]].rename(
            columns={"app_user_id": "raw_id", "customer_email": "email"}
        )
        a["channel_source"] = "app"
        frames.append(a)

    combined = pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["raw_id", "email"]
    )
    email_to_cid = (
        combined.dropna(subset=["email"])
        .drop_duplicates(subset=["raw_id"])
        .set_index("raw_id")["email"]
        .to_dict()
    )
    combined["customer_id"] = combined["raw_id"].map(email_to_cid).fillna(
        combined["raw_id"]
    )
    id_map = combined.set_index("raw_id")[["customer_id", "email"]].drop_duplicates()
    return id_map


def build_customer_360(web_df, store_df, app_df, id_map: pd.DataFrame) -> pd.DataFrame:
    profiles = {}

    def get_cid(raw_id):
        if raw_id in id_map.index:
            return id_map.loc[raw_id, "customer_id"]
        return raw_id

    # --- Web transactions ---
    if web_df is not None:
        web = web_df.copy()
        web["customer_id"] = web["customer_id"].apply(get_cid)
        web["order_date"] = pd.to_datetime(web["order_date"])
        for cid, grp in web.groupby("customer_id"):
            profiles.setdefault(cid, {})
            profiles[cid]["email"] = grp["customer_email"].iloc[0]
            profiles[cid]["web_orders"] = len(grp)
            profiles[cid]["web_spend"] = round(grp["order_total"].sum(), 2)
            profiles[cid]["web_last_date"] = grp["order_date"].max()
            profiles[cid]["web_categories"] = grp["product_category"].value_counts().index[0] if "product_category" in grp else None

    # --- In-store transactions ---
    if store_df is not None:
        store = store_df.copy()
        store["customer_id"] = store["loyalty_id"].apply(get_cid)
        store["txn_date"] = pd.to_datetime(store["txn_date"])
        for cid, grp in store.groupby("customer_id"):
            profiles.setdefault(cid, {})
            profiles[cid].setdefault("email", grp["customer_email"].iloc[0])
            profiles[cid]["store_orders"] = len(grp)
            profiles[cid]["store_spend"] = round(grp["amount"].sum(), 2)
            profiles[cid]["store_last_date"] = grp["txn_date"].max()
            profiles[cid]["fav_store"] = grp["store_location"].value_counts().index[0] if "store_location" in grp else None

    # --- App events ---
    if app_df is not None:
        app = app_df.copy()
        app["customer_id"] = app["app_user_id"].apply(get_cid)
        app["event_date"] = pd.to_datetime(app["event_date"])
        purchases = app[app["event_type"] == "purchase"] if "event_type" in app.columns else pd.DataFrame()
        for cid, grp in app.groupby("customer_id"):
            profiles.setdefault(cid, {})
            profiles[cid].setdefault("email", grp["customer_email"].iloc[0])
            profiles[cid]["app_sessions"] = len(grp)
            profiles[cid]["app_last_date"] = grp["event_date"].max()
        for cid, grp in purchases.groupby("customer_id") if not purchases.empty else []:
            profiles.setdefault(cid, {})
            profiles[cid]["app_purchases"] = len(grp)

    # --- Consolidate ---
    rows = []
    for cid, p in profiles.items():
        all_dates = [d for d in [
            p.get("web_last_date"), p.get("store_last_date"), p.get("app_last_date")
        ] if pd.notna(d)] if any(k.endswith("_last_date") for k in p) else []

        total_spend = round(
            p.get("web_spend", 0) + p.get("store_spend", 0), 2
        )
        total_orders = (
            p.get("web_orders", 0) + p.get("store_orders", 0) + p.get("app_purchases", 0)
        )
        last_purchase = max(all_dates) if all_dates else None

        channels = []
        if p.get("web_orders", 0) > 0: channels.append("web")
        if p.get("store_orders", 0) > 0: channels.append("instore")
        if p.get("app_sessions", 0) > 0: channels.append("app")

        aov = round(total_spend / total_orders, 2) if total_orders > 0 else 0

        rows.append({
            "customer_id": cid,
            "email": p.get("email", ""),
            "total_orders": total_orders,
            "total_spend": total_spend,
            "aov": aov,
            "channels_used": "|".join(channels),
            "channel_count": len(channels),
            "web_orders": p.get("web_orders", 0),
            "store_orders": p.get("store_orders", 0),
            "app_sessions": p.get("app_sessions", 0),
            "last_purchase_date": last_purchase,
            "fav_store": p.get("fav_store"),
            "fav_category": p.get("web_categories"),
        })

    df = pd.DataFrame(rows)
    df = df[df["total_orders"] > 0].copy()
    return df
