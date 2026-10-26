"""Generate simulated hearing-aid production test data with injected dirty records."""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_RECORDS = 5000
RAW_DIR = Path("data/raw")


def generate_clean_records(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Return n clean records; result/defect_code must be consistent with the values.

    test_id	测试记录唯一 ID	T000123
    serial_number	设备序列号	SN20261024-0042
    product_model	产品型号	BTE-100、RIC-200、ITE-300
    station_id	测试工位	ST-01 ~ ST-05
    test_time	测试时间	2026-10-20 08:15:30
    gain_db	增益（dB）	正常约 30±3
    noise_db	内部噪声（dB）	正常约 20±2
    distortion_pct	失真率（%）	正常约 1.5±0.5
    result	判定结果	PASS / FAIL
    defect_code	不良代码（仅 FAIL 时有）	D01_LOW_GAIN 等



    """
    # TODO: 生成各字段，再用 np.select 判定

    gain = rng.normal(30, 1.5, size=n).round(2)
    noise = rng.normal(20, 2.0, size=n).round(2)
    distortion = np.clip(rng.normal(1.5, 0.5, size=n), 0.1, None).round(3)

    product_model = rng.choice(["BTE-100", "RIC-200", "ITE-300"], size=n)
    station_id = rng.choice([f"ST-{i:02d}" for i in range(1, 6)], size=n)

    start = pd.Timestamp("2026-10-20 08:00:00")
    gaps = rng.integers(10, 60, size=n)  # 每台设备间隔 10~59 秒
    test_time = start + pd.to_timedelta(np.cumsum(gaps), unit="s")

    test_id = [f"T{i:06d}" for i in range(1, n + 1)]
    serial_number = [f"SN{t.strftime('%Y%m%d')}-{i:04d}" for i, t in enumerate(test_time, start=1)]

    conditions = [
        gain < 27,
        gain > 33,
        noise > 24,
        distortion > 2.5,
    ]
    choices = ["D01_LOW_GAIN", "D02_HIGH_GAIN", "D03_HIGH_NOISE", "D04_HIGH_DISTORTION"]
    defect_code = np.select(conditions, choices, default="")
    result = np.where(defect_code == "", "PASS", "FAIL")

    return pd.DataFrame(
        {
            "test_id": test_id,
            "serial_number": serial_number,
            "product_model": product_model,
            "station_id": station_id,
            "test_time": test_time,
            "gain_db": gain,
            "noise_db": noise,
            "distortion_pct": distortion,
            "result": result,
            "defect_code": defect_code,
        }
    )


def inject_dirty_data(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Return a dirty copy of df (do not modify the input)."""
    # TODO: 按"脏数据类型"表逐项注入，每项写成独立的小步骤
    df = df.copy()
    n = len(df)
    fail_idx = df.index[df["result"] == "FAIL"].to_numpy()
    idx_contra = rng.choice(fail_idx, size=int(n * 0.01), replace=False)
    df.loc[idx_contra, "result"] = "PASS"
    rest = df.index.difference(idx_contra).to_numpy()
    pool = rng.permutation(rest)
    n_outlier = int(n * 0.006)
    n_missing = int(n * 0.02)  # 2%，约 100 条
    n_lower = int(n * 0.02)  # station 小写
    n_space = int(n * 0.02)  # station 前后有空格
    n_time = int(n * 0.05)  # 时间格式不同，5%
    cuts = np.cumsum([n_outlier, n_missing, n_lower, n_space, n_time])
    idx_outlier, idx_missing, idx_lower, idx_space, idx_time = np.split(pool[: cuts[-1]], cuts[:-1])
    df.loc[idx_outlier, "gain_db"] = rng.choice([999.0, -50.0], size=len(idx_outlier))
    df.loc[idx_missing, "gain_db"] = np.nan
    df.loc[idx_lower, "station_id"] = df.loc[idx_lower, "station_id"].str.lower()
    df.loc[idx_space, "station_id"] = " " + df.loc[idx_space, "station_id"] + " "
    original_time = df["test_time"]
    df["test_time"] = original_time.dt.strftime("%Y-%m-%d %H:%M:%S")
    df.loc[idx_time, "test_time"] = original_time.loc[idx_time].dt.strftime("%Y/%m/%d %H:%M")
    dup_pos = rng.choice(n, size=int(n * 0.02), replace=False)
    df = pd.concat([df, df.iloc[dup_pos]], ignore_index=True)
    return df


def main() -> None:
    rng = np.random.default_rng(SEED)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    # TODO: 生成 -> 注入 -> 输出 CSV 与 JSON
    rng = np.random.default_rng(SEED)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    clean = generate_clean_records(N_RECORDS, rng)
    dirty = inject_dirty_data(clean, rng)

    dirty.to_csv(RAW_DIR / "test_records.csv", index=False)
    dirty.sample(500, random_state=1).to_json(
        RAW_DIR / "test_records.json", orient="records", indent=2
    )
    print(f"Wrote {len(dirty)} rows")


if __name__ == "__main__":
    main()
