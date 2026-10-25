"""Transform step: clean, validate and split extracted test records."""
import pandas as pd


def standardize_text(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize station_id and defect_code. Return a new DataFrame."""
    df = df.copy()
    #  station_id -> strip + upper
    #  defect_code -> "" becomes missing
    df["station_id"] = df["station_id"].str.strip().str.upper()
    df["defect_code"] = df["defect_code"].str.strip().replace("", pd.NA)

    return df


if __name__ == "__main__":
    from extract import extract
    from pathlib import Path

    raw = extract(Path("data/raw"))
    out = standardize_text(raw)
    print(out["station_id"].value_counts())
    print((out["defect_code"] == "").sum(), out["defect_code"].isna().sum())