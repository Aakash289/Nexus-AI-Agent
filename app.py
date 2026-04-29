import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from engine.ingest  import detect_channel, validate_file, resolve_identities, build_customer_360
from engine.scoring import compute_rfm, assign_segments, compute_ltv, build_consolidated, segment_summary, SEGMENT_COLORS

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 2rem 2.5rem 4rem 2.5rem;
    max-width: 1400px;
}

/* ── Wordmark ── */
.nexus-wordmark {
    font-family: 'DM Sans', sans-serif;
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: -0.03em;
    color: #0f0f0f;
    display: flex;
    align-items: center;
    gap: 8px;
}
.nexus-wordmark .hex { color: #1D9E75; font-size: 1.2rem; }
.nexus-tagline {
    font-size: 0.78rem;
    color: #888;
    font-weight: 400;
    letter-spacing: 0.02em;
    margin-top: 2px;
}

/* ── Upload zone ── */
.upload-card {
    border: 1.5px dashed #d4d4d4;
    border-radius: 14px;
    padding: 1.6rem 1.4rem;
    background: #fafafa;
    transition: border-color 0.2s;
    height: 100%;
}
.upload-card:hover { border-color: #1D9E75; }
.upload-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 6px;
}
.upload-title {
    font-size: 1rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 4px;
}
.upload-hint {
    font-size: 0.78rem;
    color: #aaa;
    margin-bottom: 12px;
}

/* ── Status pills ── */
.pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.02em;
}
.pill-green  { background: #e1f5ee; color: #0f6e56; }
.pill-yellow { background: #fef3cd; color: #856404; }
.pill-gray   { background: #f1efef; color: #888; }
.pill-red    { background: #fce8e8; color: #a32d2d; }

/* ── Metric cards ── */
.metric-card {
    background: white;
    border: 1px solid #efefef;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    height: 100%;
}
.metric-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 1.9rem;
    font-weight: 600;
    color: #0f0f0f;
    letter-spacing: -0.03em;
    line-height: 1;
}
.metric-sub {
    font-size: 0.78rem;
    color: #aaa;
    margin-top: 4px;
}

/* ── Segment badge ── */
.seg-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    font-family: 'DM Mono', monospace;
}

/* ── Section divider ── */
.section-heading {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #aaa;
    padding-bottom: 10px;
    border-bottom: 1px solid #efefef;
    margin-bottom: 1.2rem;
}

/* ── Playbook card ── */
.playbook-card {
    background: white;
    border: 1px solid #efefef;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.playbook-headline {
    font-size: 1rem;
    font-weight: 600;
    color: #0f0f0f;
    margin-bottom: 1rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid #f4f4f4;
}
.playbook-row {
    display: flex;
    gap: 12px;
    margin-bottom: 0.7rem;
    align-items: flex-start;
}
.playbook-key {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #bbb;
    min-width: 130px;
    padding-top: 1px;
}
.playbook-val {
    font-size: 0.88rem;
    color: #333;
    line-height: 1.5;
}
.playbook-risk {
    margin-top: 0.8rem;
    padding: 0.7rem 1rem;
    background: #fff8f8;
    border-left: 3px solid #e24b4a;
    border-radius: 0 6px 6px 0;
    font-size: 0.82rem;
    color: #a32d2d;
}

/* ── Run button ── */
.stButton > button {
    background: #0f0f0f !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.7rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    width: 100%;
    transition: background 0.2s !important;
}
.stButton > button:hover { background: #1D9E75 !important; }

/* ── Tab strip ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #efefef;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    color: #aaa;
    border-radius: 0;
    padding: 0.6rem 1.2rem;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #0f0f0f !important;
    border-bottom: 2px solid #1D9E75 !important;
    background: transparent !important;
}

/* ── Dataframe tweaks ── */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* ── Warning / info ── */
.warn-box {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    font-size: 0.82rem;
    color: #92400e;
    margin-bottom: 0.6rem;
}
.info-box {
    background: #f0fdf9;
    border: 1px solid #6ee7b7;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    font-size: 0.82rem;
    color: #065f46;
    margin-bottom: 0.6rem;
}

/* Tight columns */
div[data-testid="column"] { padding: 0 6px; }
div[data-testid="column"]:first-child { padding-left: 0; }
div[data-testid="column"]:last-child  { padding-right: 0; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
for key in ["web_df", "store_df", "app_df", "consolidated", "summary", "playbooks", "ran"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "ran" not in st.session_state:
    st.session_state.ran = False


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_num(n, prefix="", decimals=0):
    if n is None: return "—"
    if decimals:
        return f"{prefix}{n:,.{decimals}f}"
    return f"{prefix}{int(n):,}"

def seg_dot(seg):
    c = SEGMENT_COLORS.get(seg, "#888")
    return f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{c};margin-right:5px;"></span>'


# ── HEADER ─────────────────────────────────────────────────────────────────────
col_logo, col_desc = st.columns([1, 3])
with col_logo:
    st.markdown("""
    <div class="nexus-wordmark">
        <span class="hex">✦</span> Nexus
    </div>
    <div class="nexus-tagline">Omnichannel Customer Intelligence</div>
    """, unsafe_allow_html=True)
with col_desc:
    st.markdown("""
    <div style="font-size:0.85rem; color:#888; padding-top:6px; line-height:1.6;">
    Nexus connects your web, in-store, and app data into a single customer view. It scores every customer on recency, frequency, and spend, then segments them into lifecycle tiers and generates AI-powered action playbooks for each group. Upload your CSVs, run the analysis, download your results.
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:2rem;border-bottom:1px solid #efefef;padding-bottom:1.5rem;'></div>", unsafe_allow_html=True)


# ── UPLOAD SECTION ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-heading">01 — Upload data sources</div>', unsafe_allow_html=True)

CHANNEL_LABELS = {
    "web":     ("Web orders",          "order_id · customer_id · order_total · order_date"),
    "instore": ("In-store transactions","txn_id · loyalty_id · amount · txn_date"),
    "app":     ("App events",           "session_id · app_user_id · event_type · event_date"),
    "unknown": ("Unknown format",       "Could not detect channel type"),
}

uploaded_files = st.file_uploader(
    "",
    type=["csv"],
    accept_multiple_files=True,
    key="multi_upload",
    label_visibility="collapsed",
    help="Upload one or more CSV files — web orders, in-store transactions, app events",
)

# ── Parse all uploaded files ───────────────────────────────────────────────────
warnings_all = []
detected = {}   # channel -> (df, filename, rows, uniq)

# Reset channel DFs so removing a file clears it
st.session_state.web_df   = None
st.session_state.store_df = None
st.session_state.app_df   = None

for f in (uploaded_files or []):
    df = pd.read_csv(f)
    ch = detect_channel(df)
    w  = validate_file(df, ch)
    label = CHANNEL_LABELS.get(ch, CHANNEL_LABELS["unknown"])[0]
    warnings_all.extend([f"[{label}] {x}" for x in w])

    if ch == "web":
        st.session_state.web_df = df
        uniq = df["customer_id"].nunique() if "customer_id" in df.columns else "?"
    elif ch == "instore":
        st.session_state.store_df = df
        uniq = df["loyalty_id"].nunique() if "loyalty_id" in df.columns else "?"
    elif ch == "app":
        st.session_state.app_df = df
        uniq = df["app_user_id"].nunique() if "app_user_id" in df.columns else "?"
    else:
        uniq = "?"

    detected[ch] = (df, f.name, len(df), uniq)

# ── File status list ───────────────────────────────────────────────────────────
if detected:
    st.markdown("<div style='margin-top:10px;display:flex;flex-direction:column;gap:6px;'>", unsafe_allow_html=True)
    channel_colors = {"web": "#1D9E75", "instore": "#378ADD", "app": "#7F77DD", "unknown": "#E24B4A"}
    for ch, (df, fname, rows, uniq) in detected.items():
        label, hint = CHANNEL_LABELS.get(ch, CHANNEL_LABELS["unknown"])
        color = channel_colors.get(ch, "#888")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:9px 14px;
                    background:#fafafa;border:1px solid #efefef;border-radius:10px;">
            <div style="width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0;"></div>
            <div style="flex:1;">
                <span style="font-size:0.85rem;font-weight:600;color:#1a1a1a;">{label}</span>
                <span style="font-size:0.78rem;color:#bbb;margin-left:8px;">{fname}</span>
            </div>
            <div style="font-size:0.78rem;color:#888;">{rows:,} rows</div>
            <div style="font-size:0.78rem;color:#888;">{uniq} customers</div>
            <span class="pill pill-green">✓ detected</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if len(detected) > 1:
        channels_found = [CHANNEL_LABELS.get(c, ("?",))[0] for c in detected]
        st.markdown(f'<div class="info-box" style="margin-top:10px;">✦ {len(detected)} files loaded — {" · ".join(channels_found)} — identities will be merged on customer email</div>', unsafe_allow_html=True)

# Warnings
for w in warnings_all:
    st.markdown(f'<div class="warn-box">⚠ {w}</div>', unsafe_allow_html=True)

st.markdown("<div style='margin: 1.8rem 0 0.5rem 0;border-top:1px solid #efefef;padding-top:1.5rem;'></div>", unsafe_allow_html=True)


# ── CONFIGURE + RUN ────────────────────────────────────────────────────────────
st.markdown('<div class="section-heading">02 — Configure & run</div>', unsafe_allow_html=True)

cfg1, cfg2, cfg3, cfg4 = st.columns([2, 2, 1, 1])
with cfg1:
    st.markdown('<div class="upload-label">Brand / company name (optional)</div>', unsafe_allow_html=True)
    brand_name = st.text_input("", placeholder="e.g. Acme Co.", key="brand", label_visibility="collapsed")
with cfg2:
    st.markdown('<div class="upload-label">Analysis window</div>', unsafe_allow_html=True)
    date_window = st.selectbox("", ["Last 24 months", "Last 12 months", "Last 6 months", "All time"], label_visibility="collapsed")
with cfg3:
    st.markdown('<div class="upload-label">Generate AI playbooks</div>', unsafe_allow_html=True)
    gen_playbooks = st.checkbox("", value=True, key="gen_pb", label_visibility="collapsed")
    st.markdown('<div style="font-size:0.78rem;color:#888;margin-top:-8px;">Uses Claude API</div>', unsafe_allow_html=True)
with cfg4:
    st.markdown('<div class="upload-label" style="color:transparent;">run</div>', unsafe_allow_html=True)
    run_btn = st.button("✦  Run analysis", key="run")

# ── Lifespan assumptions expander ─────────────────────────────────────────────
with st.expander("Advanced — LTV lifespan assumptions (years)"):
    st.markdown(
        '<div style="font-size:0.78rem;color:#888;margin-bottom:12px;">'
        'How many years each segment is expected to remain active. '
        'Projected LTV = AOV x purchase frequency per year x lifespan. '
        'Adjust these to match your brand\'s actual retention data.'
        '</div>',
        unsafe_allow_html=True,
    )
    ls_col1, ls_col2, ls_col3, ls_col4 = st.columns(4)
    ls_col5, ls_col6, ls_col7, _ = st.columns(4)
    with ls_col1:
        ls_champions = st.number_input("Champions", min_value=0.1, max_value=10.0, value=4.0, step=0.5, key="ls_champ")
    with ls_col2:
        ls_loyal = st.number_input("Loyal", min_value=0.1, max_value=10.0, value=3.0, step=0.5, key="ls_loyal")
    with ls_col3:
        ls_promising = st.number_input("Promising", min_value=0.1, max_value=10.0, value=2.0, step=0.5, key="ls_promising")
    with ls_col4:
        ls_atrisk = st.number_input("At-Risk", min_value=0.1, max_value=10.0, value=1.5, step=0.5, key="ls_atrisk")
    with ls_col5:
        ls_lapsed = st.number_input("Lapsed", min_value=0.1, max_value=10.0, value=0.5, step=0.1, key="ls_lapsed")
    with ls_col6:
        ls_new = st.number_input("New", min_value=0.1, max_value=10.0, value=2.5, step=0.5, key="ls_new")
    with ls_col7:
        ls_other = st.number_input("Other", min_value=0.1, max_value=10.0, value=1.0, step=0.5, key="ls_other")

lifespan_overrides = {
    "Champions": ls_champions,
    "Loyal":     ls_loyal,
    "Promising": ls_promising,
    "At-Risk":   ls_atrisk,
    "Lapsed":    ls_lapsed,
    "New":       ls_new,
    "Other":     ls_other,
}

files_present = any([
    st.session_state.web_df is not None,
    st.session_state.store_df is not None,
    st.session_state.app_df is not None,
])

if run_btn:
    if not files_present:
        st.error("Upload at least one CSV to run the analysis.")
    else:
        prog = st.progress(0, text="Starting pipeline…")

        # Step 1: identity resolution
        prog.progress(10, text="Resolving customer identities…")
        id_map = resolve_identities(
            st.session_state.web_df,
            st.session_state.store_df,
            st.session_state.app_df,
        )

        # Step 2: Customer 360
        prog.progress(25, text="Building Customer 360 profiles…")
        c360 = build_customer_360(
            st.session_state.web_df,
            st.session_state.store_df,
            st.session_state.app_df,
            id_map,
        )

        # Step 3: RFM
        prog.progress(45, text="Computing RFM scores…")
        c360 = compute_rfm(c360)

        # Step 4: Lifecycle tiers
        prog.progress(60, text="Assigning lifecycle segments…")
        c360 = assign_segments(c360)

        # Step 5: LTV
        prog.progress(72, text="Scoring customer LTV…")
        c360 = compute_ltv(c360, lifespan_overrides=lifespan_overrides)

        # Step 6: Consolidated CSV
        prog.progress(82, text="Building consolidated output…")
        consolidated = build_consolidated(c360)
        summary = segment_summary(consolidated)
        st.session_state.consolidated = consolidated
        st.session_state.summary = summary

        # Step 7: Playbooks
        if gen_playbooks:
            prog.progress(88, text="Generating AI playbooks via Claude…")
            try:
                from ai.playbooks import generate_playbooks
                pb = generate_playbooks(summary, consolidated)
                st.session_state.playbooks = pb
            except Exception as e:
                st.session_state.playbooks = None
                st.warning(f"Playbook generation skipped: {e}")

        prog.progress(100, text="Done.")
        st.session_state.ran = True
        prog.empty()
        st.rerun()


# ── RESULTS ────────────────────────────────────────────────────────────────────
if st.session_state.ran and st.session_state.consolidated is not None:
    consolidated = st.session_state.consolidated
    summary      = st.session_state.summary
    playbooks    = st.session_state.playbooks

    st.markdown("<div style='border-top:1px solid #efefef;padding-top:2rem;margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-heading">03 — Results</div>', unsafe_allow_html=True)

    # ── Top metrics ──
    total_customers = len(consolidated)
    total_revenue   = consolidated["total_spend"].sum()
    avg_ltv         = consolidated["projected_ltv"].mean()
    total_segments  = consolidated["segment"].nunique()
    cross_channel   = (consolidated["channel_count"] > 1).sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    def metric_html(label, value, sub=""):
        return f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {'<div class="metric-sub">' + sub + '</div>' if sub else ''}
        </div>"""

    with m1: st.markdown(metric_html("Total customers", f"{total_customers:,}"), unsafe_allow_html=True)
    with m2: st.markdown(metric_html("Total revenue", f"${total_revenue:,.0f}"), unsafe_allow_html=True)
    with m3: st.markdown(metric_html("Avg projected LTV", f"${avg_ltv:,.0f}"), unsafe_allow_html=True)
    with m4: st.markdown(metric_html("Segments identified", str(total_segments)), unsafe_allow_html=True)
    with m5: st.markdown(metric_html("Cross-channel buyers", f"{cross_channel:,}", f"{cross_channel/total_customers*100:.0f}% of base"), unsafe_allow_html=True)

    st.markdown("<div style='margin:1.5rem 0;'></div>", unsafe_allow_html=True)

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["  Segments  ", "  Customer table  ", "  Playbooks  ", "  Download  "])

    # ── TAB 1: Segments ───────────────────────────────────────────────────────
    with tab1:
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        c_left, c_right = st.columns([1.1, 1.9])

        with c_left:
            # Donut chart
            fig_donut = go.Figure(go.Pie(
                labels=summary["segment"],
                values=summary["customer_count"],
                hole=0.62,
                marker_colors=[SEGMENT_COLORS.get(s, "#888") for s in summary["segment"]],
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>%{value:,} customers<br>%{percent}<extra></extra>",
            ))
            fig_donut.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(
                    font=dict(family="DM Sans", size=12, color="#555"),
                    orientation="v",
                    x=0.82, y=0.5,
                ),
                height=280,
                annotations=[dict(
                    text=f"<b>{total_customers:,}</b><br><span style='font-size:11px;color:#aaa'>customers</span>",
                    x=0.38, y=0.5,
                    font_size=18,
                    font_family="DM Sans",
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

        with c_right:
            # Segment table
            for _, row in summary.iterrows():
                seg = row["segment"]
                color = SEGMENT_COLORS.get(seg, "#888")
                st.markdown(f"""
                <div style="display:flex;align-items:center;padding:10px 14px;border-radius:10px;
                            border:1px solid #f0f0f0;margin-bottom:8px;background:white;gap:12px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0;"></div>
                    <div style="flex:1;font-weight:600;font-size:0.88rem;color:#1a1a1a;">{seg}</div>
                    <div style="text-align:right;min-width:70px;">
                        <div style="font-size:0.88rem;font-weight:600;color:#1a1a1a;">{int(row['customer_count']):,}</div>
                        <div style="font-size:0.72rem;color:#aaa;">{row['pct_customers']}%</div>
                    </div>
                    <div style="text-align:right;min-width:80px;">
                        <div style="font-size:0.88rem;font-weight:600;color:#1a1a1a;">${row['avg_projected_ltv']:,.0f}</div>
                        <div style="font-size:0.72rem;color:#aaa;">avg proj LTV</div>
                    </div>
                    <div style="text-align:right;min-width:70px;">
                        <div style="font-size:0.88rem;font-weight:600;color:#1a1a1a;">{row['pct_revenue']}%</div>
                        <div style="font-size:0.72rem;color:#aaa;">revenue</div>
                    </div>
                    <div style="text-align:right;min-width:60px;">
                        <div style="font-size:0.88rem;font-weight:600;color:#1a1a1a;">{row['avg_rfm']:.1f}</div>
                        <div style="font-size:0.72rem;color:#aaa;">avg RFM</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

        # RFM scatter + LTV bar row
        ch1, ch2 = st.columns(2)

        with ch1:
            fig_rfm = px.scatter(
                consolidated.sample(min(800, len(consolidated)), random_state=42),
                x="recency_days", y="monetary",
                color="segment",
                color_discrete_map=SEGMENT_COLORS,
                size="frequency",
                size_max=14,
                opacity=0.7,
                hover_data={"customer_id": True, "RFM_score": True, "recency_days": True, "monetary": ":.0f"},
                labels={"recency_days": "Recency (days)", "monetary": "Total spend ($)", "segment": ""},
                title="RFM distribution",
            )
            fig_rfm.update_layout(
                font_family="DM Sans", font_size=12,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#fafafa",
                title_font_size=13, title_font_color="#555",
                margin=dict(l=10, r=10, t=40, b=10),
                height=300,
                legend=dict(font_size=11, orientation="h", y=-0.2),
            )
            fig_rfm.update_xaxes(showgrid=False, zeroline=False)
            fig_rfm.update_yaxes(gridcolor="#efefef", zeroline=False)
            st.plotly_chart(fig_rfm, use_container_width=True, config={"displayModeBar": False})

        with ch2:
            ltv_seg = consolidated.groupby("segment")["projected_ltv"].mean().reset_index()
            ltv_seg = ltv_seg.sort_values("projected_ltv", ascending=True)
            fig_ltv = go.Figure(go.Bar(
                x=ltv_seg["projected_ltv"],
                y=ltv_seg["segment"],
                orientation="h",
                marker_color=[SEGMENT_COLORS.get(s, "#888") for s in ltv_seg["segment"]],
                text=[f"${v:,.0f}" for v in ltv_seg["projected_ltv"]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Avg projected LTV: $%{x:,.0f}<extra></extra>",
            ))
            fig_ltv.update_layout(
                title="Avg projected LTV by segment",
                font_family="DM Sans", font_size=12,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#fafafa",
                title_font_size=13, title_font_color="#555",
                margin=dict(l=10, r=60, t=40, b=10),
                height=300,
                xaxis=dict(showgrid=False, visible=False),
                yaxis=dict(showgrid=False),
                bargap=0.35,
            )
            st.plotly_chart(fig_ltv, use_container_width=True, config={"displayModeBar": False})

    # ── TAB 2: Customer table ─────────────────────────────────────────────────
    with tab2:
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

        f1, f2, f3 = st.columns([2, 1.5, 1])
        with f1:
            search = st.text_input("", placeholder="Search by email or customer ID…", label_visibility="collapsed")
        with f2:
            seg_filter = st.multiselect("", options=["All"] + list(consolidated["segment"].unique()), default=[], placeholder="Filter by segment", label_visibility="collapsed")
        with f3:
            sort_by = st.selectbox("", ["RFM composite ↓", "LTV ↓", "Spend ↓", "Recency ↑"], label_visibility="collapsed")

        view = consolidated.copy()
        if search:
            view = view[view["email"].str.contains(search, case=False, na=False) |
                        view["customer_id"].str.contains(search, case=False, na=False)]
        if seg_filter:
            view = view[view["segment"].isin(seg_filter)]

        sort_map = {
            "RFM composite ↓": ("RFM_composite", False),
            "LTV ↓":            ("projected_ltv", False),
            "Spend ↓":          ("total_spend", False),
            "Recency ↑":        ("recency_days", True),
        }
        sc, asc = sort_map[sort_by]
        view = view.sort_values(sc, ascending=asc)

        display_cols = ["customer_id", "email", "segment", "total_orders", "total_spend",
                        "aov", "recency_days", "R", "F", "M", "RFM_composite",
                        "projected_ltv", "ltv_score_percentile", "channels_used"]
        display_cols = [c for c in display_cols if c in view.columns]

        st.markdown(f'<div style="font-size:0.78rem;color:#aaa;margin-bottom:8px;">{len(view):,} customers shown</div>', unsafe_allow_html=True)
        st.dataframe(
            view[display_cols].head(500),
            use_container_width=True,
            height=420,
            column_config={
                "customer_id":         st.column_config.TextColumn("Customer ID", width="medium"),
                "email":               st.column_config.TextColumn("Email", width="large"),
                "segment":             st.column_config.TextColumn("Segment", width="medium"),
                "total_orders":        st.column_config.NumberColumn("Orders", format="%d"),
                "total_spend":         st.column_config.NumberColumn("Total spend", format="$%.2f"),
                "aov":                 st.column_config.NumberColumn("AOV", format="$%.2f"),
                "recency_days":        st.column_config.NumberColumn("Recency (d)", format="%d"),
                "R":                   st.column_config.NumberColumn("R", width="small"),
                "F":                   st.column_config.NumberColumn("F", width="small"),
                "M":                   st.column_config.NumberColumn("M", width="small"),
                "RFM_composite":       st.column_config.ProgressColumn("RFM", min_value=3, max_value=15, format="%d"),
                "projected_ltv":       st.column_config.NumberColumn("Proj LTV", format="$%.0f"),
                "ltv_score_percentile":st.column_config.ProgressColumn("LTV %ile", min_value=0, max_value=100, format="%.0f"),
                "channels_used":       st.column_config.TextColumn("Channels"),
            },
            hide_index=True,
        )

    # ── TAB 3: Playbooks ──────────────────────────────────────────────────────
    with tab3:
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

        if playbooks is None:
            st.markdown('<div class="info-box">Playbooks were not generated. Enable "Generate AI playbooks" and re-run the analysis.</div>', unsafe_allow_html=True)
        else:
            pb_fields = [
                ("email_strategy",       "Email strategy"),
                ("offer_type",           "Offer type"),
                ("channel_priority",     "Channel priority"),
                ("reengagement_trigger", "Re-engagement trigger"),
                ("success_metric",       "Success metric"),
            ]
            for _, row in playbooks.iterrows():
                seg   = row["segment"]
                color = SEGMENT_COLORS.get(seg, "#888")
                rows_html = "".join(
                    f'<div class="playbook-row"><div class="playbook-key">{label}</div><div class="playbook-val">{row.get(key,"")}</div></div>'
                    for key, label in pb_fields if row.get(key)
                )
                risk_html = f'<div class="playbook-risk"><b>Risk:</b> {row["risk"]}</div>' if row.get("risk") else ""
                stats_html = f"""
                <div style="display:flex;gap:20px;margin-bottom:1rem;flex-wrap:wrap;">
                    <span style="font-size:0.78rem;color:#aaa;">{int(row['customer_count']):,} customers · {row['pct_customers']:.1f}%</span>
                    <span style="font-size:0.78rem;color:#aaa;">Avg RFM {row['avg_rfm_composite']:.1f}/15</span>
                    <span style="font-size:0.78rem;color:#aaa;">Avg proj LTV ${row['avg_projected_ltv']:,.0f}</span>
                    <span style="font-size:0.78rem;color:#aaa;">Revenue ${row['total_revenue']:,.0f}</span>
                </div>"""
                st.markdown(f"""
                <div class="playbook-card">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.6rem;">
                        <div style="width:12px;height:12px;border-radius:50%;background:{color};"></div>
                        <div style="font-size:1rem;font-weight:600;color:#0f0f0f;">{seg}</div>
                    </div>
                    {stats_html}
                    <div class="playbook-headline">{row.get('headline','')}</div>
                    {rows_html}
                    {risk_html}
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 4: Download ───────────────────────────────────────────────────────
    with tab4:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        d1, d2 = st.columns(2)

        with d1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Customer 360 scores</div>
                <div style="font-size:0.85rem;color:#555;margin:8px 0 14px;">
                One row per customer — RFM scores, LTV, segment, channel breakdown.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            csv_360 = consolidated.to_csv(index=False).encode()
            st.download_button(
                "↓  Download customer_360_scores.csv",
                data=csv_360,
                file_name="customer_360_scores.csv",
                mime="text/csv",
            )

        with d2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">AI playbook report</div>
                <div style="font-size:0.85rem;color:#555;margin:8px 0 14px;">
                One row per segment — Claude-generated playbooks with strategy, offers, triggers.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            if playbooks is not None:
                csv_pb = playbooks.to_csv(index=False).encode()
                st.download_button(
                    "↓  Download playbooks_report.csv",
                    data=csv_pb,
                    file_name="playbooks_report.csv",
                    mime="text/csv",
                )
            else:
                st.markdown('<div class="pill pill-gray">Playbooks not generated</div>', unsafe_allow_html=True)

# ── EMPTY STATE ────────────────────────────────────────────────────────────────
if not st.session_state.ran and not files_present:
    st.markdown("""
    <div style="text-align:center;padding:3rem 0 2rem;color:#ccc;">
        <div style="font-size:2.5rem;margin-bottom:12px;">✦</div>
        <div style="font-size:0.9rem;font-weight:500;color:#bbb;">Upload your CSV files above to get started</div>
        <div style="font-size:0.78rem;color:#ccc;margin-top:6px;">Nexus · Omnichannel Customer Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
