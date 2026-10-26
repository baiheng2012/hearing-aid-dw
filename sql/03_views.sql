CREATE OR REPLACE VIEW dw.v_test_detail AS
SELECT
    f.test_id,
    f.serial_number,
    p.product_model,
    s.station_id,
    dt.full_date,
    f.test_time,
    d.defect_code,
    d.description AS defect_description,
    f.gain_db,
    f.noise_db,
    f.distortion_pct,
    f.result,
    (f.result = 'PASS')::int AS is_pass
FROM dw.fact_test f
JOIN dw.dim_product p ON f.product_key = p.product_key
JOIN dw.dim_station s ON f.station_key = s.station_key
JOIN dw.dim_date dt ON f.date_key = dt.date_key
LEFT JOIN dw.dim_defect d ON f.defect_key = d.defect_key;
