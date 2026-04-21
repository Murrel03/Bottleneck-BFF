⚡ Bottleneck BFF — ML-Powered SQL Performance Optimization Dashboard
A production-style database performance monitoring and SQL optimization dashboard built with Python and Streamlit. Designed to simulate real-world DBA tooling for detecting query bottlenecks and providing actionable optimization advice.

Features

Live bottleneck prediction using a trained ML model (Random Forest classifier)
Interactive sliders to simulate query scenarios and get instant predictions
SQL analyzer — paste any query to receive:

Structural issue detection (SELECT *, missing WHERE, cartesian JOINs, etc.)
Query quality score (0–100) with per-check breakdown
Optimized SQL rewrite
Index creation suggestions based on WHERE clause columns


Performance trend charts for query time, CPU usage, and lock contention
Metrics dashboard showing dataset-level averages and bottleneck rate


Tech Stack
LayerTechnologyDashboardStreamlitML ModelScikit-learn (Random Forest)SQL ParsingsqlglotDataPandas, NumPyDatasetCustom simulated Oracle/MySQL metrics (database_metrics.csv)

Project Structure
bottleneck-bff/
├── dashboard.py               # Main Streamlit app
├── database_metrics.csv       # Simulated database metrics dataset
├── bottleneck_predictor.pkl   # Trained ML model
├── train_model.py             # Model training script
├── requirements.txt           # Dependencies
└── README.md

Setup & Run
bash# 1. Clone the repository
git clone https://github.com/Murrel03/bottleneck-bff.git
cd bottleneck-bff

# 2. Install dependencies
pip install -r requirements.txt

# 3. Train the model (if .pkl not present)
python train_model.py

# 4. Run the dashboard
streamlit run dashboard.py

Model Details
The ML model is a Random Forest Classifier trained on simulated database metrics:
FeatureDescriptionquery_timeQuery execution time in secondscpu_usageCPU usage percentage at query timelocksNumber of active database locks
Target variable: bottleneck (1 = bottleneck detected, 0 = normal)
Training accuracy: ~85% on the simulated dataset.

Dataset
database_metrics.csv contains 500 simulated rows of database performance metrics, modeled after real Oracle 19c RAC production patterns observed in banking environments. Each row represents a single query execution event.

SQL Analyzer — Checks Performed
CheckWhat it catchesSELECT * usageUnnecessary data transferMissing WHEREFull table scansJOIN without ONCartesian productsOR in WHEREPotential index bypassLeading wildcard LIKENon-sargable predicatesNOT INNULL-unsafe patternsORDER BY without LIMITUnbounded sort operations

Background
Built as a portfolio project to demonstrate practical data engineering and DBA skills. The patterns in the SQL analyzer and recommendations are based on real-world Oracle and MySQL performance tuning experience, including work on Oracle 19c RAC environments supporting mission-critical banking applications.

Author <br>
Murrel Miranda <br>
Entry-Level Data Engineer | Oracle DBA <br>
LinkedIn · Portfolio
