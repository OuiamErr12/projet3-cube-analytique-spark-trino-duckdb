"""Exécute les requêtes Spark SQL sur les Parquet locaux et exporte des CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from pyspark.sql import SparkSession


ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = ("dim_date", "dim_region", "dim_product", "dim_channel")


def write_csv(frame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(frame.columns)
        for row in frame.toLocalIterator():
            writer.writerow([value.isoformat() if hasattr(value, "isoformat") else value for value in row])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "spark")
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()

    spark = (
        SparkSession.builder.appName("Projet3CubeAnalytique")
        .master("local[*]")
        .getOrCreate()
    )
    try:
        for table in ("fact_sales", *DIMENSIONS):
            spark.read.parquet(str(data_dir / f"{table}.parquet")).createOrReplaceTempView(table)
        for name in ("monthly_kpis", "cube"):
            output_name = "cube_kpis" if name == "cube" else name
            query_path = Path(__file__).resolve().parent / f"{name}.sql"
            write_csv(
                spark.sql(query_path.read_text(encoding="utf-8")),
                args.output_dir / f"{output_name}.csv",
            )
    finally:
        spark.stop()
    print(f"Résultats Spark écrits dans {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
