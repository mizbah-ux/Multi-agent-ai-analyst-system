import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')  # IMPORTANT: non-GUI backend
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CLEAN_DIR = BASE_DIR / "cleaned"
CHART_DIR = BASE_DIR / "charts"

CHART_DIR.mkdir(exist_ok=True)


def run_visualization(file_id: str):
    file_path = CLEAN_DIR / f"{file_id}_cleaned.csv"

    if not os.path.exists(file_path):
        raise Exception("Cleaned file not found")

    df = pd.read_csv(file_path)
    for col in df.columns:
        try:
            df[col] = pd.to_datetime(df[col], errors="ignore")
        except:
            pass

    if df.empty:
        raise Exception("Dataset is empty")

    charts = []

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = []

    for col in df.columns:
        unique_ratio = df[col].nunique() / len(df)

        # Keep only meaningful categorical columns
        if (
            df[col].dtype == "object" and unique_ratio < 0.5 and
            not pd.api.types.is_datetime64_any_dtype(df[col])
            ):
            categorical_cols.append(col)

    # ---- Numeric charts (histogram) ----
    for col in numeric_cols[:3]:  # limit
        plt.figure()
        df[col].hist()
        plt.title(f"{col} Distribution")

        chart_path = CHART_DIR / f"{file_id}_{col}_hist.png"
        plt.savefig(str(chart_path))
        plt.close()

        charts.append(chart_path)

    # ---- Categorical charts (bar chart) ----
    for col in categorical_cols[:2]:
        plt.figure()
        df[col].value_counts().head(5).plot(kind="bar")
        plt.title(f"{col} Top Categories")

        chart_path = CHART_DIR / f"{file_id}_{col}_bar.png"
        plt.savefig(str(chart_path))
        plt.close()

        charts.append(chart_path)

    return {
        "file_id": file_id,
        "charts": charts
    }