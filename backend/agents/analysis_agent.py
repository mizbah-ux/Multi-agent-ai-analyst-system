import pandas as pd
import os

CLEAN_DIR = "cleaned"


def run_analysis(file_id: str):
    file_path = f"{CLEAN_DIR}/{file_id}_cleaned.csv"

    if not os.path.exists(file_path):
        raise Exception("Cleaned file not found")

    df = pd.read_csv(file_path)

    if df.empty:
        raise Exception("Dataset is empty")

    result = {}

    # ---- BASIC STATS ----
    result["row_count"] = len(df)
    result["column_count"] = len(df.columns)

    # ---- NUMERIC ANALYSIS ----
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    numeric_summary = {}

    for col in numeric_cols:
        numeric_summary[col] = {
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": float(df[col].mean()),
            "median": float(df[col].median())
        }

    result["numeric_summary"] = numeric_summary

    # ---- TOP CATEGORIES ----
    categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    categorical_summary = {}

    for col in categorical_cols[:5]:  # limit to avoid overload
        top_values = df[col].value_counts().head(5).to_dict()
        categorical_summary[col] = top_values

    result["categorical_summary"] = categorical_summary

    # ---- CORRELATION ----
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr().to_dict()
        result["correlation"] = corr
    else:
        result["correlation"] = {}

    return result