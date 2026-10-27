
#!/bin/sh
set -eu

attempt=0

until mc alias set local http://minio:9000 minioadmin minioadmin; do
    attempt=$((attempt + 1))

    if [ "$attempt" -ge 30 ]; then
        echo "MinIO n'est pas disponible après 30 tentatives." >&2
        exit 1
    fi

    sleep 2
done

mc mb --ignore-existing local/project-data

for table in dim_date dim_region dim_product dim_channel fact_sales; do
    mc cp "/project-data/${table}.parquet" \
        "local/project-data/sales/${table}/part-00000.parquet"
done

echo "Initialisation de MinIO terminée."
