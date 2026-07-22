"""
Cleans and feature-engineers the raw steel plant energy data.

Run:
    python src/clean_data.py
"""

import numpy as np
import pandas as pd

INPUT_CSV = "data/raw/Steel_industry_data.csv"
OUTPUT_CSV = "data/processed/cleaned_steel_energy.csv"
REPORT_PATH = "data/processed/data_quality_report.txt"


def main():
    df = pd.read_csv(INPUT_CSV)
    original_rows = len(df)

    # Standardize column names
    df.columns = [
        c.strip().replace(" ", "_").replace(".", "_").replace("(", "").replace(")", "")
        for c in df.columns
    ]

    date_col = [c for c in df.columns if "date" in c.lower()][0]
    df["record_datetime"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=["record_datetime"])

    usage_col = [c for c in df.columns if "usage" in c.lower()][0]
    missing_before = int(df[usage_col].isnull().sum())

    # Remove sensor-glitch negative readings
    bad_readings = int((df[usage_col] < 0).sum())
    df = df[(df[usage_col] >= 0) | (df[usage_col].isnull())]

    # Median-impute remaining missing numeric values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    total_missing_before = int(df[numeric_cols].isnull().sum().sum())
    for col in numeric_cols:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    # Cap outliers at the 99th percentile
    for col in numeric_cols:
        cap = df[col].quantile(0.99)
        df[col] = np.where(df[col] > cap, cap, df[col])

    # Feature engineering
    df["hour_of_day"] = df["record_datetime"].dt.hour

    def assign_shift(hour):
        if 6 <= hour < 14:
            return "Morning"
        elif 14 <= hour < 22:
            return "Afternoon"
        return "Night"

    df["shift"] = df["hour_of_day"].apply(assign_shift)

    final_rows = len(df)
    rows_removed = original_rows - final_rows

    df.to_csv(OUTPUT_CSV, index=False)

    report = f"""DATA QUALITY REPORT
====================
Original rows:               {original_rows:,}
Sensor-glitch rows removed:  {bad_readings:,}
Missing values (before):     {total_missing_before:,}
Missing values (after):      {int(df[numeric_cols].isnull().sum().sum()):,}
Final clean dataset:         {final_rows:,} rows
Data retained:                {final_rows/original_rows*100:.1f}%
"""
    with open(REPORT_PATH, "w") as f:
        f.write(report)

    print(report)
    print(f"Cleaned data -> {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
