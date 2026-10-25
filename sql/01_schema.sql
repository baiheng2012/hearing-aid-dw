CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.dim_product (
    product_key   SERIAL PRIMARY KEY,
    product_model VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dw.dim_station (
    station_key SERIAL PRIMARY KEY,
    station_id  VARCHAR(10) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dw.dim_defect (
    defect_key  SERIAL PRIMARY KEY,
    defect_code VARCHAR(30) NOT NULL UNIQUE,
    description VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dw.dim_date (
    date_key     INTEGER PRIMARY KEY,   -- 形如 20261020
    full_date    DATE NOT NULL UNIQUE,
    year         SMALLINT NOT NULL,
    month        SMALLINT NOT NULL,
    day          SMALLINT NOT NULL,
    day_of_week  SMALLINT NOT NULL      -- 1=周一 ... 7=周日
);

CREATE TABLE IF NOT EXISTS dw.fact_test (
    test_key       BIGSERIAL PRIMARY KEY,
    test_id        VARCHAR(20) NOT NULL UNIQUE,
    serial_number  VARCHAR(30) NOT NULL,
    product_key    INTEGER NOT NULL REFERENCES dw.dim_product (product_key),
    station_key    INTEGER NOT NULL REFERENCES dw.dim_station (station_key),
    date_key       INTEGER NOT NULL REFERENCES dw.dim_date (date_key),
    defect_key     INTEGER REFERENCES dw.dim_defect (defect_key),
    test_time      TIMESTAMP NOT NULL,
    gain_db        NUMERIC(6,2),
    noise_db       NUMERIC(6,2),
    distortion_pct NUMERIC(6,3),
    result         VARCHAR(4) NOT NULL CHECK (result IN ('PASS', 'FAIL'))
);

CREATE INDEX IF NOT EXISTS idx_fact_test_product ON dw.fact_test (product_key);
CREATE INDEX IF NOT EXISTS idx_fact_test_station ON dw.fact_test (station_key);
CREATE INDEX IF NOT EXISTS idx_fact_test_date    ON dw.fact_test (date_key);

INSERT INTO dw.dim_defect (defect_code, description) VALUES
    ('D01_LOW_GAIN', 'Gain below lower limit'),
    ('D02_HIGH_GAIN', 'Gain above upper limit'),
    ('D03_HIGH_NOISE', 'Internal noise above limit'),
    ('D04_HIGH_DISTORTION', 'Distortion above limit')
ON CONFLICT (defect_code) DO NOTHING;



CREATE TABLE IF NOT EXISTS dw.quarantine_test (
    quarantine_key BIGSERIAL PRIMARY KEY,
    test_id        VARCHAR(20) NOT NULL,
    serial_number  VARCHAR(30),
    product_model  VARCHAR(20),
    station_id     VARCHAR(10),
    test_time      TIMESTAMP,
    gain_db        NUMERIC(8,2),
    noise_db       NUMERIC(6,2),
    distortion_pct NUMERIC(6,3),
    reject_reason  VARCHAR(50) NOT NULL,
    loaded_at      TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (test_id, reject_reason)
);


