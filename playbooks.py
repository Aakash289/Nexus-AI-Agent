import anthropic
import pandas as pd
import json

PLAYBOOK_SYSTEM = """You are a senior CRM strategist with expertise in retail, D2C, and omnichannel brands.
You receive a customer segment summary from Nexus and generate a precise, actionable 5-point playbook.
Return ONLY valid JSON with no preamble and no markdown fences.
Do not use em dashes anywhere in your response. Use commas, colons, or plain sentences instead."""

PLAYBOOK_PROMPT = """Segment: {segment}
Customers: {count:,} ({pct:.1f}% of base)
Avg RFM composite score: {avg_rfm:.1f} / 15
Avg recency: {avg_recency:.0f} days since last purchase
Avg order frequency: {avg_freq:.1f} orders
Avg order value: ${avg_monetary:.2f}
Avg historical LTV: ${avg_hist_ltv:.2f}
Avg projected 12-month LTV: ${avg_proj_ltv:.2f}
Revenue contribution: {pct_revenue:.1f}% of total revenue
Channel mix: {channels}

Generate a 5-point action playbook. Return this exact JSON structure:
{{
  "headline": "One-sentence strategic priority for this segment",
  "email_strategy": "Specific email/CRM approach covering cadence, tone, and content type",
  "offer_type": "What incentive or offer works best and why",
  "channel_priority": "Which channel to prioritize and how to activate it",
  "reengagement_trigger": "The specific behavioral or time-based trigger to act on",
  "success_metric": "The one KPI to track progress for this segment",
  "risk": "The biggest risk if you ignore this segment"
}}"""


def generate_playbooks(summary_df: pd.DataFrame, consolidated_df: pd.DataFrame) -> pd.DataFrame:
    client = anthropic.Anthropic()
    results = []

    # Build channel mix per segment from consolidated
    channel_mix = {}
    for seg, grp in consolidated_df.groupby("segment"):
        total = len(grp)
        web_pct   = round(grp["web_orders"].gt(0).sum() / total * 100)
        store_pct = round(grp["store_orders"].gt(0).sum() / total * 100)
        app_pct   = round(grp["app_sessions"].gt(0).sum() / total * 100)
        channel_mix[seg] = f"Web {web_pct}% · Store {store_pct}% · App {app_pct}%"

    total_customers = summary_df["customer_count"].sum()

    for _, row in summary_df.iterrows():
        seg = row["segment"]
        prompt = PLAYBOOK_PROMPT.format(
            segment=seg,
            count=int(row["customer_count"]),
            pct=row["customer_count"] / total_customers * 100,
            avg_rfm=row["avg_rfm"],
            avg_recency=row["avg_recency"],
            avg_freq=row["avg_frequency"],
            avg_monetary=row["avg_monetary"],
            avg_hist_ltv=row["avg_historical_ltv"],
            avg_proj_ltv=row["avg_projected_ltv"],
            pct_revenue=row["pct_revenue"],
            channels=channel_mix.get(seg, "N/A"),
        )

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=PLAYBOOK_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            # Strip any accidental fences
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:])
            if raw.endswith("```"):
                raw = "\n".join(raw.split("\n")[:-1])
            # Remove em dashes from output
            raw = raw.replace("\u2014", ",").replace("\u2013", ",")
            data = json.loads(raw)
        except Exception as e:
            data = {
                "headline": f"Error generating playbook: {e}",
                "email_strategy": "",
                "offer_type": "",
                "channel_priority": "",
                "reengagement_trigger": "",
                "success_metric": "",
                "risk": "",
            }

        results.append({
            "segment": seg,
            "customer_count": int(row["customer_count"]),
            "pct_customers": row["pct_customers"],
            "avg_rfm_composite": row["avg_rfm"],
            "avg_historical_ltv": row["avg_historical_ltv"],
            "avg_projected_ltv": row["avg_projected_ltv"],
            "total_revenue": row["total_revenue"],
            **data,
        })

    return pd.DataFrame(results)
