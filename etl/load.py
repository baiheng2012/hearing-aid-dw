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