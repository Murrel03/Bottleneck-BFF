import streamlit as st
import joblib
import pandas as pd
import numpy as np
import sqlglot
import os
from datetime import datetime

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Bottleneck BFF",
    page_icon="⚡",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Clean professional font */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@400;500;700&display=swap');

    html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

    /* Remove default streamlit padding */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    /* Header */
    .bff-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 0.25rem;
    }
    .bff-title {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .bff-subtitle {
        font-size: 0.9rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }

    /* Status badge */
    .badge-healthy { background:#dcfce7; color:#166534; padding:4px 12px; border-radius:999px; font-size:12px; font-weight:500; display:inline-block; }
    .badge-warn    { background:#fef9c3; color:#854d0e; padding:4px 12px; border-radius:999px; font-size:12px; font-weight:500; display:inline-block; }
    .badge-danger  { background:#fee2e2; color:#991b1b; padding:4px 12px; border-radius:999px; font-size:12px; font-weight:500; display:inline-block; }

    /* Metric cards */
    .metric-row { display:flex; gap:12px; margin-bottom:1.5rem; flex-wrap:wrap; }
    .metric-card {
        background:#f8fafc;
        border:1px solid #e2e8f0;
        border-radius:10px;
        padding:16px 20px;
        min-width:160px;
        flex:1;
    }
    .metric-card .label { font-size:12px; color:#64748b; margin-bottom:4px; }
    .metric-card .value { font-size:26px; font-weight:700; color:#0f172a; line-height:1; }
    .metric-card .sub   { font-size:11px; color:#94a3b8; margin-top:4px; }

    /* Section card */
    .section-card {
        background:#ffffff;
        border:1px solid #e2e8f0;
        border-radius:12px;
        padding:20px 24px;
        margin-bottom:1rem;
    }
    .section-title { font-size:14px; font-weight:600; color:#0f172a; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.05em; }

    /* SQL textarea */
    .stTextArea textarea {
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 13px !important;
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        background: #f8fafc !important;
    }

    /* Tip items */
    .tip-warn  { background:#fef9c3; border-left:3px solid #eab308; padding:10px 14px; border-radius:6px; margin-bottom:8px; font-size:13px; }
    .tip-info  { background:#eff6ff; border-left:3px solid #3b82f6; padding:10px 14px; border-radius:6px; margin-bottom:8px; font-size:13px; }
    .tip-ok    { background:#dcfce7; border-left:3px solid #22c55e; padding:10px 14px; border-radius:6px; margin-bottom:8px; font-size:13px; }
    .tip-danger{ background:#fee2e2; border-left:3px solid #ef4444; padding:10px 14px; border-radius:6px; margin-bottom:8px; font-size:13px; }

    /* Score pill */
    .score-pill {
        display:inline-block;
        font-size:48px;
        font-weight:700;
        line-height:1;
        margin-bottom:4px;
    }
    .score-good  { color:#16a34a; }
    .score-ok    { color:#d97706; }
    .score-bad   { color:#dc2626; }

    /* Code block */
    code { font-family: 'IBM Plex Mono', monospace; }
    .stCodeBlock { border-radius:8px !important; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Load CSV data ─────────────────────────────────────────────
@st.cache_data
def load_data():
    csv_path = "database_metrics.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, parse_dates=["timestamp"])
        return df
    return None

df = load_data()


# ── Load ML model ─────────────────────────────────────────────
@st.cache_resource
def load_model():
    model_path = "bottleneck_predictor.pkl"
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

model = load_model()


# ── Helper functions ──────────────────────────────────────────
def analyze_query(sql: str) -> list[dict]:
    """Return list of suggestions for a SQL query."""
    suggestions = []
    upper = sql.upper()

    if "SELECT *" in upper:
        suggestions.append({
            "type": "warn",
            "title": "Avoid SELECT *",
            "detail": "Specify only the columns you need — reduces I/O and network transfer significantly."
        })

    if "WHERE" not in upper:
        suggestions.append({
            "type": "danger",
            "title": "No WHERE clause — full table scan",
            "detail": "Without a WHERE clause this will scan every row. Add a filter condition."
        })

    if "JOIN" in upper and " ON " not in upper:
        suggestions.append({
            "type": "danger",
            "title": "JOIN without ON clause",
            "detail": "This produces a cartesian product. Extremely expensive on large tables."
        })

    if " OR " in upper:
        suggestions.append({
            "type": "warn",
            "title": "OR in WHERE clause",
            "detail": "OR conditions can prevent index usage. Consider UNION ALL as an alternative."
        })

    if "LIKE" in upper and "'%" in upper:
        suggestions.append({
            "type": "warn",
            "title": "Leading wildcard in LIKE",
            "detail": "LIKE '%value' cannot use an index. Consider full-text search instead."
        })

    if "NOT IN" in upper:
        suggestions.append({
            "type": "info",
            "title": "NOT IN detected",
            "detail": "NOT EXISTS is often more efficient, especially when NULLs may be present."
        })

    if "ORDER BY" in upper and "LIMIT" not in upper:
        suggestions.append({
            "type": "info",
            "title": "ORDER BY without LIMIT",
            "detail": "Sorting the full result set is expensive. Add LIMIT if you don't need all rows."
        })

    if not suggestions:
        suggestions.append({
            "type": "ok",
            "title": "No obvious issues found",
            "detail": "This query looks structurally sound. Run EXPLAIN to review the execution plan."
        })

    return suggestions


def compute_score(sql: str) -> tuple[int, list[dict]]:
    """Return a 0-100 quality score and per-check breakdown."""
    upper = sql.upper()
    checks = [
        {"label": "Column specificity (no SELECT *)", "pass": "SELECT *" not in upper},
        {"label": "Has WHERE clause",                 "pass": "WHERE" in upper},
        {"label": "JOIN integrity (has ON clause)",   "pass": "JOIN" not in upper or " ON " in upper},
        {"label": "No risky OR / NOT IN patterns",    "pass": " OR " not in upper and "NOT IN" not in upper},
        {"label": "Leading wildcard avoided",         "pass": "'%" not in upper},
        {"label": "ORDER BY paired with LIMIT",       "pass": "ORDER BY" not in upper or "LIMIT" in upper},
    ]
    score = round(sum(1 for c in checks if c["pass"]) / len(checks) * 100)
    return score, checks


def extract_index_suggestions(sql: str) -> list[dict]:
    """Extract column names from WHERE for index suggestions."""
    suggestions = []
    upper = sql.upper()
    if "WHERE" in upper:
        where_part = sql.split("WHERE", 1)[-1].split("GROUP")[0].split("ORDER")[0].split("LIMIT")[0]
        parts = where_part.replace("AND", "|").replace("OR", "|").split("|")
        for part in parts:
            import re
            match = re.search(r'([a-zA-Z_]+\.[a-zA-Z_]+|[a-zA-Z_]+)\s*[=<>!]', part)
            if match:
                raw = match.group(1).strip()
                col = raw.split(".")[-1]
                tbl = raw.split(".")[0] if "." in raw else "your_table"
                if col.upper() not in ("AND", "OR", "NOT", "IN", "IS", "NULL"):
                    suggestions.append({"col": col, "table": tbl})
    return suggestions


def optimize_sql(sql: str) -> str:
    """Basic rule-based SQL optimization pass."""
    try:
        optimized = sqlglot.transpile(sql, read="mysql", write="mysql", identify=True)[0]
    except Exception:
        optimized = sql

    upper = optimized.upper()
    if "SELECT *" in upper:
        optimized = optimized.replace("SELECT *", "SELECT id, /* specify columns */", 1)
    if "ORDER BY" in upper and "LIMIT" not in upper:
        optimized = optimized.rstrip(";").rstrip() + "\nLIMIT 1000;"

    return optimized


# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="bff-header">
    <span style="font-size:2rem;">⚡</span>
    <span class="bff-title">Bottleneck BFF</span>
</div>
<p class="bff-subtitle">ML-powered SQL performance optimization &amp; monitoring dashboard</p>
""", unsafe_allow_html=True)


# ── Metrics from CSV ──────────────────────────────────────────
if df is not None:
    avg_qt   = df["query_time"].mean()
    avg_cpu  = df["cpu_usage"].mean()
    avg_lock = df["locks"].mean()
    bn_rate  = df["bottleneck"].mean() * 100

    if bn_rate > 60:
        badge_html = f'<span class="badge-danger">⚠ High bottleneck risk — {bn_rate:.0f}% of queries</span>'
    elif bn_rate > 40:
        badge_html = f'<span class="badge-warn">◑ Moderate risk — {bn_rate:.0f}% bottleneck rate</span>'
    else:
        badge_html = f'<span class="badge-healthy">✓ System healthy — {bn_rate:.0f}% bottleneck rate</span>'

    st.markdown(badge_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Query Time", f"{avg_qt:.2f}s", delta=None)
    with col2:
        st.metric("Avg CPU Usage", f"{avg_cpu:.1f}%", delta=None)
    with col3:
        st.metric("Avg Lock Count", f"{avg_lock:.1f}", delta=None)
    with col4:
        st.metric("Bottleneck Rate", f"{bn_rate:.0f}%", delta=None)

    st.markdown("---")

    # ── Trend Charts ──────────────────────────────────────────
    st.subheader("Performance trends")
    df_sorted = df.sort_values("timestamp").reset_index(drop=True)

    tab_chart1, tab_chart2, tab_chart3 = st.tabs(["Query time", "CPU usage", "Lock contention"])

    with tab_chart1:
        st.line_chart(df_sorted.set_index("timestamp")["query_time"], use_container_width=True)

    with tab_chart2:
        st.line_chart(df_sorted.set_index("timestamp")["cpu_usage"], use_container_width=True)

    with tab_chart3:
        st.line_chart(df_sorted.set_index("timestamp")["locks"], use_container_width=True)

    # ── ML Prediction ─────────────────────────────────────────
    if model is not None:
        st.markdown("---")
        st.subheader("Live bottleneck prediction")
        st.caption("Adjust the sliders to simulate a query scenario and get an ML prediction.")

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            sim_qt = st.slider("Query time (s)", 0.0, 5.0, float(round(avg_qt, 2)), 0.01)
        with col_s2:
            sim_cpu = st.slider("CPU usage (%)", 0, 100, int(avg_cpu))
        with col_s3:
            sim_lock = st.slider("Active locks", 0, 10, int(avg_lock))

        prediction = model.predict([[sim_qt, sim_cpu, sim_lock]])[0]
        prob = None
        if hasattr(model, "predict_proba"):
            prob = model.predict_proba([[sim_qt, sim_cpu, sim_lock]])[0][1]

        if prediction == 1:
            st.error(f"**Bottleneck detected** — confidence: {prob*100:.0f}%" if prob else "**Bottleneck detected**")
            st.markdown("**Recommendations:**")
            if sim_qt > 3:
                st.markdown("- Query time is high — check for missing indexes or N+1 query patterns")
            if sim_cpu > 70:
                st.markdown("- CPU pressure is elevated — consider query parallelism or read replicas")
            if sim_lock > 5:
                st.markdown("- High lock count — review transaction scope and lock ordering")
        else:
            st.success(f"**No bottleneck detected** — confidence: {(1-prob)*100:.0f}%" if prob else "**No bottleneck detected**")

    st.markdown("---")

else:
    st.warning("database_metrics.csv not found. Place it in the same folder as dashboard.py.")


# ── SQL Analyzer ──────────────────────────────────────────────
st.subheader("SQL analyzer")
st.caption("Paste any SQL query to get instant optimization suggestions, a quality score, and index advice.")

raw_sql = st.text_area(
    "SQL query",
    value="SELECT * FROM orders WHERE customer_id = 100 AND status = 'pending'",
    height=120,
    label_visibility="collapsed"
)

btn_col1, btn_col2 = st.columns([1, 5])
with btn_col1:
    run_analysis = st.button("Analyze", type="primary", use_container_width=True)
with btn_col2:
    run_optimize = st.button("Optimize SQL", use_container_width=False)

if run_analysis or run_optimize:
    tab1, tab2, tab3, tab4 = st.tabs(["Suggestions", "Optimized SQL", "Index advice", "Query score"])

    with tab1:
        suggestions = analyze_query(raw_sql)
        for s in suggestions:
            css_cls = f"tip-{s['type']}"
            st.markdown(
                f'<div class="{css_cls}"><strong>{s["title"]}</strong><br><span style="color:#475569">{s["detail"]}</span></div>',
                unsafe_allow_html=True
            )

    with tab2:
        optimized = optimize_sql(raw_sql)
        st.code(optimized, language="sql")
        st.caption("Note: This is a rule-based pass. Always review before running in production.")

    with tab3:
        index_hints = extract_index_suggestions(raw_sql)
        if index_hints:
            for hint in index_hints:
                st.markdown(f"**Index on `{hint['col']}`:**")
                st.code(f"CREATE INDEX idx_{hint['col'].lower()} ON {hint['table']}({hint['col']});", language="sql")
        else:
            st.info("No WHERE clause columns detected for index suggestions.")

    with tab4:
        score, checks = compute_score(raw_sql)
        score_class = "score-good" if score >= 75 else "score-ok" if score >= 50 else "score-bad"
        label = "Excellent" if score >= 75 else "Needs work" if score >= 50 else "Poor"

        col_score, col_checks = st.columns([1, 2])
        with col_score:
            st.markdown(
                f'<div class="score-pill {score_class}">{score}</div><br>'
                f'<span style="font-size:13px;color:#64748b;">{label} query quality</span>',
                unsafe_allow_html=True
            )
        with col_checks:
            for c in checks:
                icon = "✅" if c["pass"] else "❌"
                st.markdown(f"{icon} {c['label']}")


# ── Footer ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="text-align:center;font-size:12px;color:#94a3b8;">Bottleneck BFF · Built with Streamlit · Oracle DBA meets Python</p>',
    unsafe_allow_html=True
)
