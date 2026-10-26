"""Unit tests for the transform step. No database or raw files needed."""
import pandas as pd

from transform import recompute_result, standardize_text


def test_standardize_text_cleans_station_and_empty_defect():
    df = pd.DataFrame(
        {
            "station_id": [" st-01 ", "ST-02"],
            "defect_code": ["", None],
        }
    )
    out = standardize_text(df)
    assert out["station_id"].tolist() == ["ST-01", "ST-02"]
    assert out["defect_code"].isna().all()


def test_standardize_text_does_not_modify_input():
    df = pd.DataFrame({"station_id": [" st-01 "], "defect_code": [""]})
    standardize_text(df)
    assert df["station_id"].tolist() == [" st-01 "]


def test_recompute_result_fixes_contradiction():
    df = pd.DataFrame(
        {
            "gain_db": [25.0, 30.0],
            "noise_db": [20.0, 20.0],
            "distortion_pct": [1.5, 1.5],
            "result": ["PASS", "PASS"],
            "defect_code": [None, None],
        }
    )
    out, corrected = recompute_result(df)
    assert out["result"].tolist() == ["FAIL", "PASS"]
    assert out["defect_code"].iloc[0] == "D01_LOW_GAIN"
    assert corrected == 1
