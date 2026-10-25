-- Q1: yield rate by product model
SELECT
    p.product_model,
    count(*) AS total,
    count(*) FILTER (WHERE f.result = 'PASS') AS pass_count,
    round(100.0 * count(*) FILTER (WHERE f.result = 'PASS') / count(*), 2) AS yield_pct
FROM dw.fact_test f
JOIN dw.dim_product p ON f.product_key = p.product_key
GROUP BY p.product_model
ORDER BY yield_pct DESC;


-- Q2: yield rate by station
SELECT
    s.station_id,
    count(*) AS total,
    count(*) FILTER (WHERE f.result = 'PASS') AS pass_count,
    round(100.0 * count(*) FILTER (WHERE f.result = 'PASS') / count(*), 2) AS yield_pct
FROM dw.fact_test f
JOIN dw.dim_station s ON f.station_key = s.station_key
GROUP BY s.station_id
ORDER BY yield_pct DESC;




-- Q3: defect distribution
SELECT
    d.defect_code,
    d.description,
    count(*) AS defect_count,
    round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS pct_of_defects
FROM dw.fact_test f
JOIN dw.dim_defect d ON f.defect_key = d.defect_key
GROUP BY d.defect_code, d.description
ORDER BY defect_count DESC;


-- Q4: daily yield trend
SELECT
    dt.full_date,
    count(*) AS total,
    round(100.0 * count(*) FILTER (WHERE f.result = 'PASS') / count(*), 2) AS yield_pct
FROM dw.fact_test f
JOIN dw.dim_date dt ON f.date_key = dt.date_key
GROUP BY dt.full_date
ORDER BY dt.full_date;


