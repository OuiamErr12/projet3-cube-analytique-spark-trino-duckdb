"""Exécute les requêtes Spark SQL sur les Parquet locaux et exporte des CSV."""

from __future__ import annotations

import argparse
import csv
import time
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

    timings = ["query,seconds"]
    started = time.perf_counter()
    spark = (
        SparkSession.builder.appName("Projet3CubeAnalytique")
        .master("local[*]")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    timings.append(f"startup,{time.perf_counter() - started:.3f}")
    try:
        for table in ("fact_sales", *DIMENSIONS):
            spark.read.parquet(str(data_dir / f"{table}.parquet")).createOrReplaceTempView(table)
        for name in ("monthly_kpis", "cube", "channel_kpis"):
            output_name = "cube_kpis" if name == "cube" else name
            query_path = Path(__file__).resolve().parent / f"{name}.sql"
            query_started = time.perf_counter()
            write_csv(
                spark.sql(query_path.read_text(encoding="utf-8")),
                args.output_dir / f"{output_name}.csv",
            )
            timings.append(f"{name},{time.perf_counter() - query_started:.3f}")
    finally:
        spark.stop()
    (args.output_dir / "timings.csv").write_text("\n".join(timings) + "\n", encoding="utf-8")
    print(f"Résultats Spark écrits dans {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
