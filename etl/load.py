"""Load step: write clean data into the star schema."""

import pandas as pd
from sqlalchemy import Engine, text


def load_dim_product(engine: Engine, df: pd.DataFrame) -> None:
    """Insert distinct product models into dw.dim_product (idempotent)."""
    rows = [{"model": m} for m in df["product_model"].drop_duplicates()]
    sql = text(
        "INSERT INTO dw.dim_product (product_model) VALUES (:model) "
        "ON CONFLICT (product_model) DO NOTHING"
    )
    with engine.begin() as conn:
        conn.execute(sql, rows)


def load_dim_station(engine: Engine, df: pd.DataFrame) -> None:
    """Insert distinct station ids into dw.dim_station (idempotent)."""
    rows = [{"station": s} for s in df["station_id"].drop_duplicates()]
    sql = text(
        "INSERT INTO dw.dim_station (station_id) VALUES (:station) "
        "ON CONFLICT (station_id) DO NOTHING"
    )
    with engine.begin() as conn:
        conn.execute(sql, rows)


def load_dim_date(engine: Engine, df: pd.DataFrame) -> None:
    """Insert distinct test dates into dw.dim_date (idempotent)."""
    dates = df["test_time"].dt.normalize().drop_duplicates()
    rows = [
        {
            "date_key": int(d.strftime("%Y%m%d")),
            "full_date": d.date(),
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "dow": d.isoweekday(),
        }
        for d in dates
    ]
    sql = text(
        "INSERT INTO dw.dim_date (date_key, full_date, year, month, day, day_of_week) "
        "VALUES (:date_key, :full_date, :year, :month, :day, :dow) "
        "ON CONFLICT (date_key) DO NOTHING"
    )
    with engine.begin() as conn:
        conn.execute(sql, rows)


def fetch_key_map(engine: Engine, table: str, key_col: str, value_col: str) -> dict:
    """Return {business value: surrogate key} for a dimension table."""
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT {value_col}, {key_col} FROM dw.{table}")).all()
    return {value: key for value, key in rows}


def load_fact_test(engine: Engine, df: pd.DataFrame) -> int:
    """Insert clean rows into dw.fact_test (idempotent). Return rows sent."""
    out = pd.DataFrame(index=df.index)
    out["test_id"] = df["test_id"]
    out["serial_number"] = df["serial_number"]
    out["product_key"] = df["product_model"].map(
        fetch_key_map(engine, "dim_product", "product_key", "product_model")
    )
    out["station_key"] = df["station_id"].map(
        fetch_key_map(engine, "dim_station", "station_key", "station_id")
    )
    out["date_key"] = df["test_time"].dt.strftime("%Y%m%d").astype(int)
    out["defect_key"] = df["defect_code"].map(
        fetch_key_map(engine, "dim_defect", "defect_key", "defect_code")
    )
    out["test_time"] = df["test_time"]
    out["gain_db"] = df["gain_db"]
    out["noise_db"] = df["noise_db"]
    out["distortion_pct"] = df["distortion_pct"]
    out["result"] = df["result"]

    assert out["product_key"].notna().all(), "unmapped product_model"
    assert out["station_key"].notna().all(), "unmapped station_id"

    records = out.astype(object).where(out.notna(), None).to_dict("records")
    sql = text(
        "INSERT INTO dw.fact_test (test_id, serial_number, product_key, station_key, "
        "date_key, defect_key, test_time, gain_db, noise_db, distortion_pct, result) "
        "VALUES (:test_id, :serial_number, :product_key, :station_key, "
        ":date_key, :defect_key, :test_time, :gain_db, :noise_db, :distortion_pct, :result) "
        "ON CONFLICT (test_id) DO NOTHING"
    )
    with engine.begin() as conn:
        conn.execute(sql, records)
    return len(records)


def load_quarantine(engine: Engine, df: pd.DataFrame) -> int:
    """Insert quarantined rows into dw.quarantine_test (idempotent)."""
    cols = [
        "test_id",
        "serial_number",
        "product_model",
        "station_id",
        "test_time",
        "gain_db",
        "noise_db",
        "distortion_pct",
        "reject_reason",
    ]
    records = df[cols].astype(object).where(df[cols].notna(), None).to_dict("records")
    sql = text(
        "INSERT INTO dw.quarantine_test (test_id, serial_number, product_model, station_id, "
        "test_time, gain_db, noise_db, distortion_pct, reject_reason) "
        "VALUES (:test_id, :serial_number, :product_model, :station_id, "
        ":test_time, :gain_db, :noise_db, :distortion_pct, :reject_reason) "
        "ON CONFLICT (test_id, reject_reason) DO NOTHING"
    )
    with engine.begin() as conn:
        conn.execute(sql, records)
    return len(records)


if __name__ == "__main__":
    from pathlib import Path

    from db import get_engine
    from extract import extract
    from transform import transform

    fixed, _, _ = transform(extract(Path("data/raw")))
    engine = get_engine()
    load_dim_product(engine, fixed)
    load_dim_station(engine, fixed)
    load_dim_date(engine, fixed)
    print("dimensions loaded")

    n = load_fact_test(engine, fixed)
    print("fact rows sent:", n)
