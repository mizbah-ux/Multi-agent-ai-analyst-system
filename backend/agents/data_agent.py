import pandas as pd
from fastapi import Header, HTTPException
import os

UPLOAD_DIR = "uploads"
CLEAN_DIR = "cleaned"

os.makedirs(CLEAN_DIR, exist_ok=True)


def run_data_cleaning(file_id: str):
    # find file
    file_path = None
    for ext in ["csv", "xlsx", "json"]:
        path = f"{UPLOAD_DIR}/{file_id}.{ext}"
        if os.path.exists(path):
            file_path = path
            break

    if not file_path:
        raise Exception("File not found")

    # load data
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_json(file_path)

    if df.empty:
        raise Exception("Dataset is empty")

    original_rows = len(df)

    # ---- CLEANING ----

    # normalize column names
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

    # drop duplicates
    df = df.drop_duplicates()

    # handle missing values
    for col in df.columns:
        if df[col].dtype in ["int64", "float64"]:
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = df[col].fillna("unknown")

    cleaned_rows = len(df)

    # save cleaned file
    clean_path = f"{CLEAN_DIR}/{file_id}_cleaned.csv"
    df.to_csv(clean_path, index=False)

    return {
        "file_id": file_id,
        "original_rows": original_rows,
        "cleaned_rows": cleaned_rows,
        "columns": list(df.columns),
        "cleaned_file_path": clean_path
    }

INTERNAL_API_KEY = "internal-secret"


def verify_internal_key(
    x_internal_key: str = Header(None)
):

    if x_internal_key != INTERNAL_API_KEY:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )