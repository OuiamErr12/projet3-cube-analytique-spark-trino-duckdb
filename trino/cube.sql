-- CUBE agrège toutes les combinaisons de mois, région et catégorie.
SELECT
    d.date_month,
    r.region_name,
    p.category,
    SUM(f.sales_amount) AS revenue,
    COUNT(DISTINCT f.order_id) AS distinct_orders,
    SUM(f.sales_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS average_basket
FROM hive.sales.fact_sales f
JOIN hive.sales.dim_date d ON f.date_key = d.date_key
JOIN hive.sales.dim_region r ON f.region_id = r.region_id
JOIN hive.sales.dim_product p ON f.product_id = p.product_id
JOIN hive.sales.dim_channel c ON f.channel_id = c.channel_id
GROUP BY CUBE(d.date_month, r.region_name, p.category)
ORDER BY d.date_month, r.region_name, p.category
