# Hearing Aid Production Test Data Warehouse

![CI](https://github.com/baiheng2012/hearing-aid-dw/actions/workflows/ci.yml/badge.svg)

An end-to-end data engineering project: simulated production test data from hearing aid
manufacturing is cleaned with Python, loaded into a PostgreSQL star schema, and visualized
in Apache Superset.

All data is simulated. No real product specifications are used.

![Dashboard](docs/dashboard.png)

## Tech stack

Python (pandas, SQLAlchemy), PostgreSQL 16, Apache Superset 6.1, Docker Compose,
pytest, ruff, GitHub Actions.

## Architecture

```
CSV + JSON (dirty)  ->  extract  ->  transform  ->  load  ->  PostgreSQL (star schema)  ->  Superset
                                        |
                                        +-> quarantine table (rejected rows + reason)
```

| Step | File | Responsibility |
|---|---|---|
| Generate | `etl/generate_data.py` | Simulate 5,000 test records with injected data quality problems (seeded, reproducible) |
| Extract | `etl/extract.py` | Read CSV and JSON sources into one table without altering values |
| Transform | `etl/transform.py` | Standardize, parse, deduplicate, validate, recompute results |
| Load | `etl/load.py` | Idempotent load into dimension, fact and quarantine tables |
| Pipeline | `etl/pipeline.py` | Run all steps and print a data quality report |

## Project structure

```
etl/              ETL code (generate, extract, transform, load, pipeline, db helper)
sql/              01_schema.sql (DDL), 02_analysis.sql (queries), 03_views.sql (dashboard view)
tests/            pytest unit tests for the transform step
docker/           Superset image (adds the PostgreSQL driver) and Superset config
superset_export/  Exported dashboard
docs/             Dashboard screenshot
.github/          GitHub Actions workflow (ruff + pytest)
```

## Data model

Star schema in the `dw` schema:

- `fact_test`: one row per test, with measurements (gain, noise, distortion) and the result
- `dim_product`, `dim_station`, `dim_date`, `dim_defect`: descriptive dimensions
- `quarantine_test`: rows rejected during validation, stored with `reject_reason`
- `v_test_detail`: a denormalized view used as the Superset dataset

`serial_number` is kept in the fact table as a degenerate dimension. Foreign key columns
are indexed.

## Data quality handling

Six kinds of problems are injected into the raw data and handled in the transform step:

| Problem | Handling |
|---|---|
| Duplicate records (including overlap between the CSV and JSON sources) | Deduplicate by `test_id` |
| Missing `gain_db` | Quarantine, because the result cannot be judged |
| Out-of-range values (999, -50) | Quarantine, using a plausible-range check |
| Mixed timestamp formats | Parse both formats into one datetime |
| Inconsistent station ids (case, whitespace) | Normalize |
| `result` contradicting the measurements | Recompute from measurements and count corrections |

Report from one pipeline run:

```json
{
  "rows_extracted": 5600,
  "duplicates_removed": 600,
  "rows_after_dedup": 5000,
  "quarantined_total": 130,
  "quarantined_by_reason": {"missing_gain_db": 100, "gain_db_out_of_range": 30},
  "results_corrected": 50,
  "rows_clean": 4870
}
```

Row counts are reconciled at each step: 5,000 rows after deduplication equals
4,870 clean rows plus 130 quarantined rows, and an `assert` enforces it.

## Analysis results

Overall yield is 91.01% (4,432 of 4,870 clean tests). Queries are in `sql/02_analysis.sql`.

| Station | Tests | Yield |
|---|---|---|
| ST-01 | 997 | 91.17% |
| ST-02 | 974 | 91.48% |
| ST-03 | 910 | 89.78% |
| ST-04 | 1,012 | 91.01% |
| ST-05 | 977 | 91.50% |

Stations and defect types do not influence results in the simulation, so differences such
as ST-03 being lower are random variation, not a real effect.

## Design decisions

- **Quarantine instead of imputing.** A missing measurement decides pass or fail, so filling
  it with an average would inflate yield. Uncertain rows are kept aside with a reason.
- **Deduplicate before validating**, so one faulty row is not counted several times.
- **Recompute `result` from measurements** instead of trusting the source label.
- **Idempotent load** (`UNIQUE` constraints plus `ON CONFLICT DO NOTHING`): re-running the
  pipeline does not create duplicates.
- **Reproducible data**: a fixed random seed makes the generated files identical on every run.

## Getting started

Requirements: Docker, Python 3.12.

```bash
# 1. Configuration: copy the template, then set SUPERSET_SECRET_KEY in .env
cp .env.example .env
openssl rand -base64 42        # paste the output as SUPERSET_SECRET_KEY

# 2. Start PostgreSQL first and create Superset's metadata database
docker compose up -d postgres
docker exec -it hearing_dw_postgres psql -U etl_user -d production_dw -c "CREATE DATABASE superset;"

# 3. Build and start Superset, then initialize it (first run only)
docker compose up -d --build
docker exec -it hearing_dw_superset superset db upgrade
docker exec -it hearing_dw_superset superset fab create-admin \
  --username admin --firstname Admin --lastname Admin \
  --email admin@localhost --password admin
docker exec -it hearing_dw_superset superset init

# 4. Python environment
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# 5. Create the schema, generate data, run the pipeline, create the view
docker exec -i hearing_dw_postgres psql -U etl_user -d production_dw < sql/01_schema.sql
python etl/generate_data.py
python etl/pipeline.py
docker exec -i hearing_dw_postgres psql -U etl_user -d production_dw < sql/03_views.sql
```

The admin password above is for local use only.

### Dashboard

Open http://localhost:8088 and log in. Add a database connection with the URI
`postgresql+psycopg2://etl_user:etl_pass@postgres:5432/production_dw`
(the host is the Compose service name `postgres`, not `localhost`), register
`dw.v_test_detail` as a dataset, and build the charts. The dashboard I built is exported in
`superset_export/dashboard_export.zip` and shown in `docs/dashboard.png`.

### Tests and lint

```bash
pytest -v
ruff check . && ruff format --check .
```

## Known limitations

- Records are generated sequentially; a real line has parallel stations.
- Timestamps in the slash format have no seconds, so that information is lost.
- Pass/fail limits and plausible ranges are made up for this simulation.
- Loads are full reloads rather than incremental.
- Unit tests cover the transform step only; the load step is verified by manual runs.
- Only the local setup is covered; there is no scheduling or monitoring.
