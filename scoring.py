import pandas as pd
import numpy as np
from datetime import datetime

TODAY = datetime(2025, 4, 14)

SEGMENT_RULES = {
    "Champions":  lambda r: (r.R >= 4) & (r.F >= 4) & (r.M >= 4),
    "Loyal":      lambda r: (r.F >= 3) & (r.M >= 3) & ~((r.R >= 4) & (r.F >= 4) & (r.M >= 4)),
    "Promising":  lambda r: (r.R >= 4) & (r.F <= 2) & (r.M <= 3),
    "At-Risk":    lambda r: (r.R <= 2) & (r.F >= 3) & (r.M >= 3),
    "Lapsed":     lambda r: (r.R == 1) & (r.F >= 2),
    "New":        lambda r: (r.F == 1) & (r.R >= 3),
}

# Default lifespan assumptions (years) — can be overridden at runtime
# via the lifespan_overrides parameter in compute_ltv()
SEGMENT_LTV_LIFESPAN = {
    "Champions": 4.0,
    "Loyal":     3.0,
    "Promising": 2.0,
    "At-Risk":   1.5,
    "Lapsed":    0.5,
    "New":       2.5,
    "Other":     1.0,
}

SEGMENT_COLORS = {
    "Champions": "#1D9E75",
    "Loyal":     "#378ADD",
    "Promising": "#EF9F27",
    "At-Risk":   "#E24B4A",
    "Lapsed":    "#888780",
    "New":       "#7F77DD",
    "Other":     "#B4B2A9",
}


def compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"])
    df["recency_days"] = (TODAY - df["last_purchase_date"]).dt.days.clip(lower=0)
    df["frequency"]    = df["total_orders"].clip(lower=1)
    df["monetary"]     = df["total_spend"].clip(lower=0.01)

    # Quintile scoring — handle duplicate edges gracefully
    def safe_qcut(series, labels):
        try:
            return pd.qcut(series, q=5, labels=labels, duplicates="drop")
        except Exception:
            return pd.cut(series, bins=5, labels=labels[:5], duplicates="drop")

    df["R"] = safe_qcut(df["recency_days"], labels=[5, 4, 3, 2, 1]).astype(int)
    df["F"] = safe_qcut(df["frequency"],    labels=[1, 2, 3, 4, 5]).astype(int)
    df["M"] = safe_qcut(df["monetary"],     labels=[1, 2, 3, 4, 5]).astype(int)

    df["RFM_score"]     = "R" + df["R"].astype(str) + "_F" + df["F"].astype(str) + "_M" + df["M"].astype(str)
    df["RFM_composite"] = df["R"] + df["F"] + df["M"]

    return df


def assign_segments(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["segment"] = "Other"
    # Apply rules in priority order — first match wins
    for seg_name, rule_fn in SEGMENT_RULES.items():
        mask = rule_fn(df) & (df["segment"] == "Other")
        df.loc[mask, "segment"] = seg_name
    return df


def compute_ltv(df: pd.DataFrame, lifespan_overrides: dict = None) -> pd.DataFrame:
    """
    Compute historical and projected LTV for each customer.

    lifespan_overrides: optional dict to override default lifespan assumptions.
    Example:
        compute_ltv(df, lifespan_overrides={
            "Champions": 5.0,
            "Lapsed": 0.3,
        })
    Any segment not in overrides falls back to SEGMENT_LTV_LIFESPAN defaults.
    """
    df = df.copy()

    # Merge defaults with any user-provided overrides
    lifespan = {**SEGMENT_LTV_LIFESPAN}
    if lifespan_overrides:
        for seg, yrs in lifespan_overrides.items():
            if seg in lifespan:
                lifespan[seg] = float(yrs)

    df["historical_ltv"] = df["total_spend"].round(2)
    df["purchase_freq_per_year"] = (df["frequency"] / 2).clip(lower=0.5)
    df["lifespan_years"] = df["segment"].map(lifespan).fillna(1.0)
    df["projected_ltv"] = (
        df["aov"] * df["purchase_freq_per_year"] * df["lifespan_years"]
    ).round(2)
    df["ltv_score_percentile"] = (
        df["projected_ltv"].rank(pct=True) * 100
    ).round(1)
    return df


def build_consolidated(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "customer_id", "email",
        "total_orders", "total_spend", "aov",
        "channels_used", "channel_count",
        "web_orders", "store_orders", "app_sessions",
        "last_purchase_date", "fav_store", "fav_category",
        "recency_days", "frequency", "monetary",
        "R", "F", "M", "RFM_score", "RFM_composite",
        "segment",
        "historical_ltv", "projected_ltv", "ltv_score_percentile",
    ]
    existing = [c for c in cols if c in df.columns]
    return df[existing].sort_values("RFM_composite", ascending=False).reset_index(drop=True)


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("segment").agg(
        customer_count=("customer_id", "count"),
        avg_rfm=("RFM_composite", "mean"),
        avg_recency=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        avg_historical_ltv=("historical_ltv", "mean"),
        avg_projected_ltv=("projected_ltv", "mean"),
        total_revenue=("total_spend", "sum"),
    ).round(2).reset_index()
    grp["pct_customers"] = (grp["customer_count"] / grp["customer_count"].sum() * 100).round(1)
    grp["pct_revenue"]   = (grp["total_revenue"]  / grp["total_revenue"].sum()  * 100).round(1)
    order = list(SEGMENT_RULES.keys()) + ["Other"]
    grp["_order"] = grp["segment"].map({s: i for i, s in enumerate(order)}).fillna(99)
    return grp.sort_values("_order").drop(columns="_order").reset_index(drop=True)
