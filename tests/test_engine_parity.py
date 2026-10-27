from __future__ import annotations

import importlib.util
import math
import shutil
from pathlib import Path

import duckdb
import pytest


ROOT = Path(__file__).resolve().parents[1]
TABLES = ("fact_sales", "dim_date", "dim_region", "dim_product", "dim_channel")
QUERIES = ("monthly_kpis", "cube")


def _sql_rows(connection, sql_path: Path):
    return connection.execute(sql_path.read_text(encoding="utf-8")).fetchall()


def _register_duckdb(connection, data_dir: Path) -> None:
    for table in TABLES:
        path = str(data_dir / f"{table}.parquet").replace("'", "''")
        connection.execute(
            f"CREATE VIEW {table} AS SELECT * FROM read_parquet('{path}')"
        )


def _assert_same_results(expected, actual) -> None:
    assert len(expected) == len(actual)
    expected_by_dimensions = {row[:3]: row[3:] for row in expected}
    actual_by_dimensions = {row[:3]: row[3:] for row in actual}
    assert expected_by_dimensions.keys() == actual_by_dimensions.keys()
    for dimensions, expected_metrics in expected_by_dimensions.items():
        actual_metrics = actual_by_dimensions[dimensions]
        assert float(expected_metrics[0]) == pytest.approx(float(actual_metrics[0]), abs=1e-8)
        assert expected_metrics[1] == actual_metrics[1]
        assert math.isclose(
            float(expected_metrics[2]),
            float(actual_metrics[2]),
            rel_tol=1e-9,
            abs_tol=1e-7,
        )


def test_duckdb_kpis_match_independent_total(parquet_data: Path) -> None:
    connection = duckdb.connect()
    try:
        _register_duckdb(connection, parquet_data)
        monthly = _sql_rows(connection, ROOT / "duckdb" / "monthly_kpis.sql")
        cube = _sql_rows(connection, ROOT / "duckdb" / "cube.sql")
        total = connection.execute(
            "SELECT SUM(sales_amount), COUNT(DISTINCT order_id) FROM fact_sales"
        ).fetchone()
    finally:
        connection.close()

    cube_total = next(row for row in cube if row[:3] == (None, None, None))
    assert float(cube_total[3]) == pytest.approx(float(total[0]), abs=1e-8)
    assert cube_total[4] == total[1] == 300
    assert float(cube_total[5]) == pytest.approx(float(total[0]) / 300, abs=1e-7)
    assert monthly


@pytest.mark.skipif(
    importlib.util.find_spec("pyspark") is None or shutil.which("java") is None,
    reason="La parité Spark nécessite PySpark et un JDK installé.",
)
def test_spark_and_duckdb_return_same_kpis(parquet_data: Path) -> None:
    from pyspark.sql import SparkSession

    duck = duckdb.connect()
    _register_duckdb(duck, parquet_data)
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("Projet3ParityTest")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    try:
        for table in TABLES:
            spark.read.parquet(str(parquet_data / f"{table}.parquet")).createOrReplaceTempView(table)
        for query_name in QUERIES:
            duck_rows = _sql_rows(
                duck, ROOT / "duckdb" / f"{query_name}.sql"
            )
            spark_rows = spark.sql(
                (ROOT / "spark_sql" / f"{query_name}.sql").read_text(encoding="utf-8")
            ).collect()
            _assert_same_results(duck_rows, [tuple(row) for row in spark_rows])
    finally:
        spark.stop()
        duck.close()
