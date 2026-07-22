"""
Generates a realistic SYNTHETIC sample of the Steel Industry Energy
Consumption dataset so the full pipeline can be demoed/tested immediately.

>>> Replace data/raw/Steel_industry_data.csv with the REAL dataset before
>>> using this for your actual resume project / dashboard. Real dataset:
>>> Kaggle or UCI ML Repository - "Steel Industry Energy Consumption"
>>> (DAEWOO Steel Co. Ltd, South Korea - 35,040 records, 15-min intervals, 2018)

Run:
    python src/generate_sample_data.py
"""

import numpy as np
import pandas as pd

np.random.seed(42)

# 15-minute intervals for one year, matching the real dataset's cadence
start = pd.Timestamp("2018-01-01 00:00:00")
n_periods = 35040  # 365 days * 96 intervals/day
timestamps = pd.date_range(start=start, periods=n_periods, freq="15min")

df = pd.DataFrame({"date": timestamps})
df["hour"] = df["date"].dt.hour
df["day_of_week"] = df["date"].dt.day_name()
df["WeekStatus"] = np.where(df["date"].dt.dayofweek < 5, "Weekday", "Weekend")
df["NSM"] = df["date"].dt.hour * 3600 + df["date"].dt.minute * 60

# Load type depends on hour of day (industrial pattern: heavy load during work shifts)
def load_type(hour):
    if 6 <= hour < 14:
        return np.random.choice(["Maximum_Load", "Medium_Load"], p=[0.6, 0.4])
    elif 14 <= hour < 22:
        return np.random.choice(["Medium_Load", "Maximum_Load", "Light_Load"], p=[0.5, 0.3, 0.2])
    else:
        return np.random.choice(["Light_Load", "Medium_Load"], p=[0.7, 0.3])

df["Load_Type"] = df["hour"].apply(load_type)

load_base = {"Light_Load": 8, "Medium_Load": 25, "Maximum_Load": 55}
df["Usage_kWh"] = df["Load_Type"].map(load_base) + np.random.normal(0, 3, n_periods)
df["Usage_kWh"] = df["Usage_kWh"].clip(lower=0)

# Weekend usage runs lower (plant partially idle)
df.loc[df["WeekStatus"] == "Weekend", "Usage_kWh"] *= np.random.uniform(0.4, 0.6)

df["Lagging_Current_Reactive_Power_kVarh"] = (df["Usage_kWh"] * np.random.uniform(0.2, 0.4, n_periods)).round(3)
df["Leading_Current_Reactive_Power_kVarh"] = (df["Usage_kWh"] * np.random.uniform(0.0, 0.05, n_periods)).round(3)
df["CO2(tCO2)"] = (df["Usage_kWh"] * 0.0005 + np.random.normal(0, 0.0001, n_periods)).clip(lower=0).round(6)
df["Lagging_Current_Power_Factor"] = np.random.uniform(65, 99, n_periods).round(2)
df["Leading_Current_Power_Factor"] = np.random.uniform(90, 100, n_periods).round(2)

# Inject some realistic messiness: missing values + a few sensor error rows
missing_idx = np.random.choice(df.index, size=150, replace=False)
df.loc[missing_idx, "Usage_kWh"] = np.nan

bad_idx = np.random.choice(df.index, size=30, replace=False)
df.loc[bad_idx, "Usage_kWh"] = -999  # sensor glitch, should get filtered in cleaning

df = df.drop(columns=["hour"])
df = df.rename(columns={"date": "date"})

out_path = "data/raw/Steel_industry_data.csv"
df.to_csv(out_path, index=False)
print(f"Synthetic dataset written to {out_path} ({len(df)} rows)")
