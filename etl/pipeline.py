"""Run the full ETL pipeline: extract -> transform -> load."""
import json
from pathlib import Path

from db import get_engine
from extract import extract
from load import load_dim_date, load_dim_product, load_dim_station, load_fact_test, load_quarantine
from transform import transform

RAW_DIR = Path("data/raw")


def run() -> dict:
    """Execute the pipeline and return the quality report."""
    raw = extract(RAW_DIR)
    fixed, quarantine, report = transform(raw)

    engine = get_engine()
    load_dim_product(engine, fixed)
    load_dim_station(engine, fixed)
    load_dim_date(engine, fixed)
    report["fact_rows_sent"] = load_fact_test(engine, fixed)
    report["quarantine_rows_sent"] = load_quarantine(engine, quarantine)
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))