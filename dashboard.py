import streamlit as st
import joblib
import pandas as pd
import mysql.connector
import sqlglot
from datetime import datetime

# 🌸 Page Configuration
st.set_page_config(page_title="Bottleneck BFF 💖", page_icon="🌸")

# 🌟 Title Section
st.markdown("""
    <h1 style='text-align: center; color: hotpink;'>💖 Bottleneck BFF 🌸</h1>
    <h3 style='text-align: center; color: mediumvioletred;'>Your stylish SQL optimizer & advisor 👑</h3>
    <hr style='border: 1px solid pink;'>
""", unsafe_allow_html=True)

# 🌼 Function to fetch live metrics
def fetch_live_metrics():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="Sunflower@098",
            database="mysql"
        )
        cursor = conn.cursor()

        cursor.execute("SHOW GLOBAL STATUS LIKE 'Threads_connected'")
        active_threads = int(cursor.fetchone()[1])

        cursor.execute("SHOW GLOBAL STATUS LIKE 'Slow_queries'")
        slow_queries = int(cursor.fetchone()[1])

        cursor.execute("SHOW OPEN TABLES WHERE In_use > 0")
        locks = len(cursor.fetchall())

        return {
            "active_threads": active_threads,
            "slow_queries": slow_queries,
            "locks": locks
        }

    except Exception as e:
        return {"error": str(e)}

# --- Sidebar: Show Live Metrics ---
st.sidebar.header("🌸 Live MySQL Metrics 🌸")
metrics = fetch_live_metrics()

model = None
try:
    model = joblib.load('bottleneck_predictor.pkl')
except FileNotFoundError:
    st.sidebar.error("❌ Model file not found! Please place 'bottleneck_predictor.pkl' in the folder.")

if "error" in metrics:
    st.sidebar.error(f"Oops! Couldn't connect: {metrics['error']}")
elif model:
    st.sidebar.metric("🧵 Active Threads", metrics["active_threads"])
    st.sidebar.metric("🐒 Slow Queries", metrics["slow_queries"])
    st.sidebar.metric("🔒 Locks", metrics["locks"])

    prediction = model.predict([[metrics["slow_queries"], metrics["active_threads"], metrics["locks"]]])[0]

    if st.sidebar.button("🔄 Refresh Metrics"):
        st.experimental_rerun()

    def get_recommendation(prediction, slow_queries, cpu_usage):
        if prediction == 1:
            advice = []
            if slow_queries > 100:
                advice.append("💡 **Tip**: Optimize slow queries – check indexes or rewrite logic 🌷")
            if cpu_usage > 80:
                advice.append("⚡ **Scale Up**: Upgrade CPU or improve parallelism 💻")
            return "🌸 **Recommendations:** 🌸\n\n" + "\n\n".join(advice)
        else:
            return "🎉 **Everything's fabulous!** No major bottlenecks 💃✨"

    st.markdown("---")
    st.markdown("### 💅 Results")
    st.success(f"**Prediction:** {'🚨 Bottleneck detected!' if prediction == 1 else '✅ All Clear!'}")

    st.markdown("### 💖 Metrics Trendline")
    chart_data = pd.DataFrame({
        'Metric': ['Slow Queries', 'Active Threads', 'Locks'],
        'Value': [metrics["slow_queries"], metrics["active_threads"], metrics["locks"]]
    })
    st.bar_chart(chart_data.set_index("Metric"))

    st.markdown("---")
    st.markdown("### 📖 Recommendations")
    st.info(get_recommendation(prediction, metrics["slow_queries"], metrics["active_threads"]))

st.markdown("---")
st.markdown("<center>💗 Made with love & Python 🐍 💗</center>", unsafe_allow_html=True)

# --- SQL Optimizer ---
def optimize_query(sql):
    try:
        optimized = sqlglot.transpile(sql, read="mysql", write="mysql", identify=True)[0]
        return optimized
    except:
        return "Unable to optimize this query."

# --- Query Analysis ---
def analyze_query(sql):
    suggestions = []
    sql_upper = sql.upper()

    if "SELECT *" in sql_upper:
        suggestions.append("🌸 **Avoid SELECT ***: Specify columns to reduce data transfer")

    if "WHERE" in sql_upper:
        where_clause = sql_upper.split("WHERE")[1].split("GROUP")[0].split("ORDER")[0]
        columns = [col.strip().split("=")[0].strip() for col in where_clause.split("AND")]
        for col in columns:
            clean_col = col.replace("`", "").split(".")[-1]
            suggestions.append(f"💎 **Index Suggestion**: Create index on `{clean_col}`")

    if "JOIN" in sql_upper and "ON" not in sql_upper:
        suggestions.append("💔 **Missing JOIN Condition**: Add proper ON clause")

    return suggestions

# --- Index Creation Helper ---
def generate_index_suggestions(raw_sql):
    suggestions = []
    if "WHERE" in raw_sql.upper():
        where_clause = raw_sql.upper().split("WHERE")[1].strip()
        columns = [col.strip().split("=")[0].strip() for col in where_clause.split("AND")]
        for col in columns:
            clean_col = col.replace("`", "").split(".")[-1]
            table_name = col.split(".")[0] if "." in col else "your_table"
            suggestions.append((clean_col, table_name))
    return suggestions

# --- Execution Plan Function ---
def get_execution_plan(sql):
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="Sunflower@098",
            database="mysql"
        )
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN {sql}")
        plan = cursor.fetchall()
        columns = [i[0] for i in cursor.description]
        return pd.DataFrame(plan, columns=columns)
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})

# --- Query Tools UI ---
st.subheader("🔮 SQL Fairy Godmother")
raw_sql = st.text_area("Paste your SQL spell here:", "SELECT * FROM orders WHERE customer_id = 100")

col1, col2 = st.columns(2)

with col1:
    st.subheader("✨ Optimized Magic")
    optimized_sql = optimize_query(raw_sql)
    st.code(optimized_sql, language="sql")

with col2:
    st.subheader("💌 Pro Tips")
    suggestions = analyze_query(raw_sql)
    if suggestions:
        for tip in suggestions:
            st.markdown(f"- {tip}")
    else:
        st.markdown("🌈 **Perfect Query!** No suggestions needed!")

# --- Index Wizard ---
index_suggestions = generate_index_suggestions(raw_sql)
if index_suggestions:
    st.subheader("🌟 Index Wizard")
    for clean_col, table_name in index_suggestions:
        st.markdown(f"**Index Spell for `{clean_col}`:**")
        st.code(f"CREATE INDEX idx_{clean_col} ON {table_name}({clean_col});", language="sql")

# --- Execution Plan Viewer ---
st.subheader("🔍 Execution Plan Breakdown")
if st.button("🪄 Show Execution Plan"):
    plan_df = get_execution_plan(raw_sql)
    st.dataframe(plan_df.style.highlight_max(axis=0, color="#FFB6C1"))
