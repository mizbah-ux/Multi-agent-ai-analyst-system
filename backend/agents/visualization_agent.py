import pandas as pd
import os
import matplotlib
from fastapi import Header, HTTPException
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

    if df.empty:
        raise Exception("Dataset is empty")

    # Work on a copy so we can detect datetime columns without destroying numeric dtypes.
    df_time = df.copy()
    datetime_cols = []
    for col in df_time.columns:
        if df_time[col].dtype != "object":
            continue
        parsed = pd.to_datetime(df_time[col], errors="coerce", format="mixed")
        valid_ratio = parsed.notna().mean()
        if valid_ratio > 0.7:
            df_time[col] = parsed
            datetime_cols.append(col)

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

    # ---- Numeric distributions (histogram) ----
    for col in numeric_cols[:4]:
        plt.figure()
        df[col].hist()
        plt.title(f"{col} Distribution")
        plt.xlabel(col)
        plt.ylabel("Frequency")

        chart_name = f"{file_id}_{col}_hist.png"
        chart_path = CHART_DIR / chart_name
        plt.savefig(str(chart_path))
        plt.close()

        charts.append(f"charts/{chart_name}")

    # ---- Categorical bar charts ----
    for col in categorical_cols[:3]:
        plt.figure()
        df[col].value_counts().head(5).plot(kind="bar")
        plt.title(f"{col} Top Categories")
        plt.xlabel(col)
        plt.ylabel("Count")

        chart_name = f"{file_id}_{col}_bar.png"
        chart_path = CHART_DIR / chart_name
        plt.savefig(str(chart_path))
        plt.close()

        charts.append(f"charts/{chart_name}")

    # ---- Correlation Heatmap ----

    if len(numeric_cols) >= 2:

        plt.figure(figsize=(8, 6))

        corr_matrix = df[numeric_cols].corr()

        plt.imshow(corr_matrix, cmap="coolwarm")

        plt.colorbar()

        plt.xticks(
            range(len(corr_matrix.columns)),
            corr_matrix.columns,
            rotation=45
        )

        plt.yticks(
            range(len(corr_matrix.columns)),
            corr_matrix.columns
        )

        plt.title("Correlation Heatmap")

        heatmap_name = f"{file_id}_heatmap.png"
        heatmap_path = CHART_DIR / heatmap_name

        plt.tight_layout()

        plt.savefig(str(heatmap_path))

        plt.close()

        charts.append(f"charts/{heatmap_name}")

    # ---- Scatter Plot ----

    if len(numeric_cols) >= 2:

        x_col = numeric_cols[0]
        y_col = numeric_cols[1]

        plt.figure(figsize=(7, 5))

        plt.scatter(df[x_col], df[y_col])

        plt.xlabel(x_col)

        plt.ylabel(y_col)

        plt.title(f"{x_col} vs {y_col}")

        scatter_name = f"{file_id}_scatter.png"
        scatter_path = CHART_DIR / scatter_name

        plt.savefig(str(scatter_path))

        plt.close()

        charts.append(f"charts/{scatter_name}")

    # ---- Box Plot ----

    for col in numeric_cols[:3]:

        plt.figure(figsize=(6, 4))

        plt.boxplot(df[col].dropna())

        plt.title(f"{col} Box Plot")

        boxplot_name = f"{file_id}_{col}_boxplot.png"
        boxplot_path = CHART_DIR / boxplot_name

        plt.savefig(str(boxplot_path))

        plt.close()

        charts.append(f"charts/{boxplot_name}")

    # ---- Pie Chart ----

    for col in categorical_cols[:2]:

        plt.figure(figsize=(6, 6))

        df[col].value_counts().head(5).plot(
            kind="pie",
            autopct="%1.1f%%"
        )

        plt.ylabel("")

        plt.title(f"{col} Distribution")

        pie_name = f"{file_id}_{col}_pie.png"
        pie_path = CHART_DIR / pie_name

        plt.savefig(str(pie_path))

        plt.close()

        charts.append(f"charts/{pie_name}")

    # ---- Line Chart (generic numeric trend) ----

    for col in numeric_cols[:1]:

        plt.figure(figsize=(8, 4))

        plt.plot(df[col])

        plt.title(f"{col} Trend")

        plt.xlabel("Index")

        plt.ylabel(col)

        line_name = f"{file_id}_{col}_line.png"
        line_path = CHART_DIR / line_name

        plt.savefig(str(line_path))

        plt.close()

        charts.append(f"charts/{line_name}")

    # ---- Time-series trend chart when datetime columns exist ----
    if datetime_cols and numeric_cols:
        dt_col = datetime_cols[0]
        value_col = numeric_cols[0]

        trend_df = df_time[[dt_col, value_col]].dropna()
        if not trend_df.empty:
            trend_df["__period"] = trend_df[dt_col].dt.to_period("M").astype(str)
            grouped = trend_df.groupby("__period")[value_col].mean().reset_index()

            if len(grouped) > 1:
                plt.figure(figsize=(9, 4))
                plt.plot(grouped["__period"], grouped[value_col], marker="o")
                plt.xticks(rotation=45, ha="right")
                plt.title(f"{value_col} Monthly Trend ({dt_col})")
                plt.xlabel("Period")
                plt.ylabel(f"Average {value_col}")
                plt.tight_layout()

                time_name = f"{file_id}_{value_col}_time_trend.png"
                time_path = CHART_DIR / time_name
                plt.savefig(str(time_path))
                plt.close()

                charts.append(f"charts/{time_name}")

    return [str(c) for c in charts]

INTERNAL_API_KEY = "internal-secret"


def verify_internal_key(
    x_internal_key: str = Header(None)
):

    if x_internal_key != INTERNAL_API_KEY:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )
