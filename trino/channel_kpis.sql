-- Même indicateurs que Spark SQL et DuckDB, lus dans le catalogue Hive
-- sur les Parquet déposés dans MinIO.
SELECT
    d.date_month,
    r.region_name,
    p.category,
    c.channel_name,
    SUM(f.sales_amount) AS revenue,
    COUNT(DISTINCT f.order_id) AS distinct_orders,
    SUM(f.sales_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS average_basket
FROM hive.sales.fact_sales f
JOIN hive.sales.dim_date d ON f.date_key = d.date_key
JOIN hive.sales.dim_region r ON f.region_id = r.region_id
JOIN hive.sales.dim_product p ON f.product_id = p.product_id
JOIN hive.sales.dim_channel c ON f.channel_id = c.channel_id
WHERE d.full_date >= DATE '2024-01-01'
  AND d.full_date < DATE '2026-01-01'
GROUP BY d.date_month, r.region_name, p.category, c.channel_name
ORDER BY d.date_month, r.region_name, p.category, c.channel_name;
