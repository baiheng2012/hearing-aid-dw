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

def remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows with a repeated test_id (keep first). Return (clean df, removed count)."""
    before = len(df)
    deduped = df.drop_duplicates(subset="test_id", keep="first").reset_index(drop=True)
    return deduped, before - len(deduped)



PLAUSIBLE_RANGES = {
    "gain_db": (0, 60),
    "noise_db": (0, 60),
    "distortion_pct": (0, 20),
}


def split_invalid(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split df into (valid, quarantine). Quarantine rows get a reject_reason."""
    reason = pd.Series(pd.NA, index=df.index, dtype="string")
    reason = reason.mask(df["gain_db"].isna(), "missing_gain_db")

    for col, (low, high) in PLAUSIBLE_RANGES.items():
        out_of_range = (df[col].notna() & ~df[col].between(low, high)).fillna(False)
        reason = reason.mask(out_of_range & reason.isna(), f"{col}_out_of_range")

    valid = df[reason.isna()].reset_index(drop=True)
    quarantine = df[reason.notna()].assign(reject_reason=reason[reason.notna()]).reset_index(drop=True)
    return valid, quarantine







if __name__ == "__main__":
    from pathlib import Path

    from extract import extract

    raw = extract(Path("data/raw"))
    std = parse_types(standardize_text(raw))
    deduped, n_removed = remove_duplicates(std)
    print("dedup removed:", n_removed)

    valid, quarantine = split_invalid(deduped)
    print("valid:", len(valid), "quarantine:", len(quarantine))
    print(quarantine["reject_reason"].value_counts())
    print(valid[["gain_db", "noise_db", "distortion_pct"]].describe())