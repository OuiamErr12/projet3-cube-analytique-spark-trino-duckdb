-- KPI mensuels par région et catégorie ; le panier moyen est calculé sur
-- les commandes distinctes ayant contribué à chaque groupe.
SELECT
    d.date_month,
    r.region_name,
    p.category,
    SUM(f.sales_amount) AS revenue,
    COUNT(DISTINCT f.order_id) AS distinct_orders,
    SUM(f.sales_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS average_basket
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_region r ON f.region_id = r.region_id
JOIN dim_product p ON f.product_id = p.product_id
JOIN dim_channel c ON f.channel_id = c.channel_id
WHERE d.full_date >= DATE '2024-01-01'
  AND d.full_date < DATE '2026-01-01'
GROUP BY d.date_month, r.region_name, p.category
ORDER BY d.date_month, r.region_name, p.category
