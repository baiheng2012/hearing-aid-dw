"""Transform step: clean, validate and split extracted test records."""
import pandas as pd
import numpy as np




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

SPEC = {
    "gain_low": 27.0,
    "gain_high": 33.0,
    "noise_max": 24.0,
    "distortion_max": 2.5,
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

def recompute_result(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Recompute defect_code and result from measurements. Return (df, corrected count)."""
    df = df.copy()
    old_result = df["result"].copy()

    conditions = [
        df["gain_db"] < SPEC["gain_low"],
        df["gain_db"] > SPEC["gain_high"],
        df["noise_db"] > SPEC["noise_max"],
        df["distortion_pct"] > SPEC["distortion_max"],
    ]
    choices = ["D01_LOW_GAIN", "D02_HIGH_GAIN", "D03_HIGH_NOISE", "D04_HIGH_DISTORTION"]

    codes = np.select(conditions, choices, default="")
    df["defect_code"] = pd.Series(codes, index=df.index).replace("", pd.NA)

    df["result"] = np.where(df["defect_code"].isna(), "PASS", "FAIL")
    corrected = (old_result != df["result"]).sum()
    return df, int(corrected)


def transform(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Run all cleaning steps. Return (clean df, quarantine df, quality report)."""
    std = parse_types(standardize_text(raw))
    deduped, n_dup = remove_duplicates(std)
    valid, quarantine = split_invalid(deduped)
    fixed, n_corrected = recompute_result(valid)

    assert len(fixed) + len(quarantine) == len(deduped), "row count mismatch after split"

    report = {
        "rows_extracted": len(raw),
        "duplicates_removed": n_dup,
        "rows_after_dedup": len(deduped),
        "quarantined_total": len(quarantine),
        "quarantined_by_reason": quarantine["reject_reason"].value_counts().to_dict(),
        "results_corrected": n_corrected,
        "rows_clean": len(fixed),
    }
    return fixed, quarantine, report



if __name__ == "__main__":
    import json
    from pathlib import Path

    from extract import extract

    raw = extract(Path("data/raw"))
    fixed, quarantine, report = transform(raw)
    print(json.dumps(report, indent=2))
    print(fixed.dtypes)