"""
train_model.py
Run this once to generate bottleneck_predictor.pkl
Usage: python train_model.py
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

df = pd.read_csv("database_metrics.csv")

FEATURES = ["query_time", "cpu_usage", "locks"]
TARGET   = "bottleneck"

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("Classification Report:")
print(classification_report(y_test, model.predict(X_test)))

joblib.dump(model, "bottleneck_predictor.pkl")
print("Model saved to bottleneck_predictor.pkl")
