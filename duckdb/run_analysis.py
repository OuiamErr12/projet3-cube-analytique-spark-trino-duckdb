"""Exécute les analyses DuckDB directement depuis les fichiers Parquet."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
TABLES = ("fact_sales", "dim_date", "dim_region", "dim_product", "dim_channel")


def parquet_literal(path: Path) -> str:
    """Protège les apostrophes dans un chemin SQL DuckDB."""
    return "'" + str(path.resolve()).replace("'", "''") + "'"


def write_csv(connection: duckdb.DuckDBPyConnection, sql_path: Path, output: Path) -> None:
    cursor = connection.execute(sql_path.read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([column[0] for column in cursor.description])
        writer.writerows(cursor.fetchall())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "duckdb")
    args = parser.parse_args()

    timings = ["query,seconds"]
    started = time.perf_counter()
    connection = duckdb.connect()
    timings.append(f"startup,{time.perf_counter() - started:.3f}")
    try:
        for table in TABLES:
            path = args.data_dir / f"{table}.parquet"
            connection.execute(
                f"CREATE VIEW {table} AS SELECT * FROM read_parquet({parquet_literal(path)})"
            )
        for name in ("monthly_kpis", "cube", "channel_kpis"):
            output_name = "cube_kpis" if name == "cube" else name
            query_started = time.perf_counter()
            write_csv(
                connection,
                Path(__file__).resolve().parent / f"{name}.sql",
                args.output_dir / f"{output_name}.csv",
            )
            timings.append(f"{name},{time.perf_counter() - query_started:.3f}")
    finally:
        connection.close()
    (args.output_dir / "timings.csv").write_text("\n".join(timings) + "\n", encoding="utf-8")
    print(f"Résultats DuckDB écrits dans {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
