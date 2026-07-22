"""
EDA + KPI tables + a classification model predicting Load_Type from
electrical readings. Saves chart images (for README/Power BI reference)
and KPI CSVs (for direct import into Power BI / Tableau).

Run:
    python src/eda_and_model.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import json

sns.set_style("whitegrid")
DATA = "data/processed/cleaned_steel_energy.csv"

df = pd.read_csv(DATA, parse_dates=["record_datetime"])

# ---------- KPI TABLES (import these directly into Power BI / Tableau) ----------
kpi_by_load = df.groupby("Load_Type")["Usage_kWh"].agg(["mean", "sum", "count"]).round(2)
kpi_by_load.to_csv("data/processed/kpi_by_load_type.csv")

kpi_by_day = df.groupby("day_of_week")[["Usage_kWh", "CO2tCO2"]].sum().round(3)
kpi_by_day.to_csv("data/processed/kpi_by_day_of_week.csv")

kpi_weekday_weekend = df.groupby("WeekStatus")["Usage_kWh"].mean().round(2)
kpi_weekday_weekend.to_csv("data/processed/kpi_weekday_vs_weekend.csv")

kpi_by_shift = df.groupby("shift")[["Usage_kWh", "Lagging_Current_Power_Factor"]].mean().round(2)
kpi_by_shift.to_csv("data/processed/kpi_by_shift.csv")

print("KPI tables written to data/processed/")

# ---------- VISUALS ----------
# 1. Usage by load type
plt.figure(figsize=(7, 4))
sns.barplot(x=kpi_by_load.index, y=kpi_by_load["mean"])
plt.title("Average Energy Usage (kWh) by Load Type")
plt.ylabel("Avg Usage (kWh)")
plt.tight_layout()
plt.savefig("visuals/usage_by_load_type.png", dpi=150)
plt.close()

# 2. Daily usage trend (first 30 days for readability)
daily = df.set_index("record_datetime").resample("D")["Usage_kWh"].sum().head(60)
plt.figure(figsize=(10, 4))
daily.plot()
plt.title("Daily Total Energy Usage (kWh) - First 60 Days")
plt.ylabel("kWh")
plt.tight_layout()
plt.savefig("visuals/daily_usage_trend.png", dpi=150)
plt.close()

# 3. Weekday vs weekend
plt.figure(figsize=(5, 4))
sns.barplot(x=kpi_weekday_weekend.index, y=kpi_weekday_weekend.values)
plt.title("Avg Usage: Weekday vs Weekend")
plt.ylabel("Avg Usage (kWh)")
plt.tight_layout()
plt.savefig("visuals/weekday_vs_weekend.png", dpi=150)
plt.close()

# 4. Correlation heatmap
numeric_cols = ["Usage_kWh", "Lagging_Current_Reactive_Power_kVarh",
                 "Leading_Current_Reactive_Power_kVarh", "CO2tCO2",
                 "Lagging_Current_Power_Factor", "Leading_Current_Power_Factor"]
plt.figure(figsize=(7, 5))
sns.heatmap(df[numeric_cols].corr(), annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation Between Electrical Readings")
plt.tight_layout()
plt.savefig("visuals/correlation_heatmap.png", dpi=150)
plt.close()

print("Charts written to visuals/")

# ---------- ML MODEL: predict Load_Type from electrical readings ----------
features = ["Usage_kWh", "Lagging_Current_Reactive_Power_kVarh",
            "Leading_Current_Reactive_Power_kVarh", "CO2tCO2",
            "Lagging_Current_Power_Factor", "Leading_Current_Power_Factor"]
X = df[features]
le = LabelEncoder()
y = le.fit_transform(df["Load_Type"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)
preds = model.predict(X_test)

acc = accuracy_score(y_test, preds)
report = classification_report(y_test, preds, target_names=le.classes_)

with open("models/model_metrics.txt", "w") as f:
    f.write(f"Accuracy: {acc:.4f}\n\n")
    f.write(report)

print(f"\nModel accuracy: {acc:.4f}")
print(report)

# Feature importance chart
importances = pd.Series(model.feature_importances_, index=features).sort_values()
plt.figure(figsize=(7, 4))
importances.plot(kind="barh")
plt.title("Feature Importance - Load Type Prediction")
plt.tight_layout()
plt.savefig("visuals/feature_importance.png", dpi=150)
plt.close()

# Confusion matrix
cm = confusion_matrix(y_test, preds)
plt.figure(figsize=(5, 4))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.title("Confusion Matrix - Load Type Prediction")
plt.ylabel("Actual")
plt.xlabel("Predicted")
plt.tight_layout()
plt.savefig("visuals/confusion_matrix.png", dpi=150)
plt.close()

summary = {
    "model": "RandomForestClassifier",
    "accuracy": round(acc, 4),
    "rows_used": len(df),
    "features": features,
}
with open("models/model_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\nModel + charts saved to models/ and visuals/")
