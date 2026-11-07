-- Analyse par canal, en plus du cube mois × région × catégorie.
-- Le besoin métier demande aussi le canal de vente. Chaque ligne de fait
-- n'a qu'un canal, donc la somme des chiffres d'affaires de cette requête
-- retrouve le chiffre d'affaires total. Les commandes distinctes et le
-- panier moyen ne s'additionnent pas d'un canal, d'une région ou d'une
-- catégorie à l'autre.
SELECT
    d.date_month,
    r.region_name,
    p.category,
    c.channel_name,
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
GROUP BY d.date_month, r.region_name, p.category, c.channel_name
ORDER BY d.date_month, r.region_name, p.category, c.channel_name
