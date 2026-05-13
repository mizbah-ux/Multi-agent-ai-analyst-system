import pandas as pd
from fastapi import Header, HTTPException
import os
import re

CLEAN_DIR = "cleaned"

STOP_WORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "about",
    "show", "give", "analyze", "analysis", "please", "need", "want", "data",
    "table", "dataset", "report", "summary", "trends", "trend", "focus"
}

def _extract_request_terms(user_request: str):
    if not user_request:
        return []
    words = re.findall(r"[a-zA-Z0-9_]+", user_request.lower())
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


def run_analysis(file_id: str, user_request: str = None):
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
    result["columns"] = df.columns.tolist()

    # ---- NUMERIC ANALYSIS ----
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    numeric_summary = {}

    for col in numeric_cols:
        numeric_summary[col] = {
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": float(df[col].mean()),
            "median": float(df[col].median()),
            "std": float(df[col].std()) if len(df[col].dropna()) > 1 else 0.0
        }

    result["numeric_summary"] = numeric_summary

    # ---- TOP CATEGORIES ----
    categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    categorical_summary = {}

    for col in categorical_cols[:5]:  # limit to avoid overload
        top_values = df[col].value_counts().head(5).to_dict()
        categorical_summary[col] = top_values

    result["categorical_summary"] = categorical_summary

    # ---- DATA QUALITY ----
    missing_values = df.isna().sum()
    missing_pct = ((missing_values / len(df)) * 100).round(2)
    result["data_quality"] = {
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_by_column": {
            col: {
                "count": int(missing_values[col]),
                "percent": float(missing_pct[col])
            }
            for col in df.columns
            if int(missing_values[col]) > 0
        }
    }

    # ---- CORRELATION ----
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr().to_dict()
        result["correlation"] = corr
    else:
        result["correlation"] = {}

    # ---- REQUEST-ALIGNED INSIGHTS ----
    request_terms = _extract_request_terms(user_request or "")
    matched_columns = [
        col for col in df.columns
        if any(term in col.lower() for term in request_terms)
    ]

    request_insights = []
    if user_request:
        request_insights.append(
            f"Request received: {user_request.strip()}"
        )
        if matched_columns:
            request_insights.append(
                "Matched dataset columns for your request: " + ", ".join(matched_columns[:8])
            )
        else:
            request_insights.append(
                "No direct column-name matches were found; analysis used overall dataset patterns."
            )

    # ---- BUSINESS SUMMARY ----
    summary_lines = []
    summary_lines.append(
        f"The dataset contains {result['row_count']} records across {result['column_count']} fields."
    )

    if numeric_cols:
        lead_numeric = numeric_cols[0]
        lead_stats = numeric_summary[lead_numeric]
        summary_lines.append(
            f"Primary numeric signal '{lead_numeric}' has mean {lead_stats['mean']:.2f}, "
            f"median {lead_stats['median']:.2f}, and range {lead_stats['min']:.2f} to {lead_stats['max']:.2f}."
        )

    if categorical_summary:
        lead_cat = next(iter(categorical_summary))
        top_values = categorical_summary[lead_cat]
        if top_values:
            top_key = next(iter(top_values))
            summary_lines.append(
                f"In categorical patterns, '{lead_cat}' is led by '{top_key}' with {top_values[top_key]} records."
            )

    missing_columns = list(result["data_quality"]["missing_by_column"].keys())
    if missing_columns:
        summary_lines.append(
            "Data completeness risk exists in: " + ", ".join(missing_columns[:5]) + "."
        )
    else:
        summary_lines.append("No material missing-value risk was detected after cleaning.")

    if user_request:
        summary_lines.append("The narrative and insights were aligned to the user analysis request.")

    result["request_alignment"] = {
        "request": user_request,
        "terms": request_terms,
        "matched_columns": matched_columns,
        "insights": request_insights
    }
    result["business_summary"] = " ".join(summary_lines)

    return result

INTERNAL_API_KEY = "internal-secret"


def verify_internal_key(
    x_internal_key: str = Header(None)
):

    if x_internal_key != INTERNAL_API_KEY:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )
