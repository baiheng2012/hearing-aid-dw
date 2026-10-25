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

def parse_types(df: pd.DataFrame) -> pd.DataFrame:
    """Parse test_time to datetime and measurement columns to numeric."""
    df = df.copy()

    fmt_standard = pd.to_datetime(df["test_time"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    fmt_slash = pd.to_datetime(df["test_time"], format="%Y/%m/%d %H:%M", errors="coerce")
    df["test_time"] = fmt_standard.fillna(fmt_slash)

    for col in ["gain_db", "noise_db", "distortion_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df





if __name__ == "__main__":
    from pathlib import Path

    from extract import extract

    raw = extract(Path("data/raw"))
    out = parse_types(standardize_text(raw))
    print(out.dtypes)
    print("NaT in test_time:", out["test_time"].isna().sum())
    print(out[["gain_db", "noise_db", "distortion_pct"]].describe())