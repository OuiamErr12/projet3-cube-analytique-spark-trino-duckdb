-- Les fichiers sont copiés dans MinIO par le service minio-init.
CREATE SCHEMA IF NOT EXISTS hive.sales;

CREATE TABLE IF NOT EXISTS hive.sales.dim_date (
    date_key INTEGER,
    full_date DATE,
    calendar_year SMALLINT,
    quarter SMALLINT,
    month SMALLINT,
    month_name VARCHAR,
    date_month VARCHAR
)
WITH (
    format = 'PARQUET',
    external_location = 's3://project-data/sales/dim_date/'
);

CREATE TABLE IF NOT EXISTS hive.sales.dim_region (
    region_id INTEGER,
    region_name VARCHAR,
    country VARCHAR
)
WITH (
    format = 'PARQUET',
    external_location = 's3://project-data/sales/dim_region/'
);

CREATE TABLE IF NOT EXISTS hive.sales.dim_product (
    product_id INTEGER,
    product_name VARCHAR,
    category VARCHAR,
    unit_price DECIMAL(10, 2)
)
WITH (
    format = 'PARQUET',
    external_location = 's3://project-data/sales/dim_product/'
);

CREATE TABLE IF NOT EXISTS hive.sales.dim_channel (
    channel_id INTEGER,
    channel_name VARCHAR
)
WITH (
    format = 'PARQUET',
    external_location = 's3://project-data/sales/dim_channel/'
);

CREATE TABLE IF NOT EXISTS hive.sales.fact_sales (
    sale_id BIGINT,
    order_id BIGINT,
    date_key INTEGER,
    region_id INTEGER,
    product_id INTEGER,
    channel_id INTEGER,
    quantity SMALLINT,
    unit_price DECIMAL(10, 2),
    sales_amount DECIMAL(12, 2)
)
WITH (
    format = 'PARQUET',
    external_location = 's3://project-data/sales/fact_sales/'
);
