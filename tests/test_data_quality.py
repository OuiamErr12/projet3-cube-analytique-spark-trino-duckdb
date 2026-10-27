from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq

from scripts.generate_data import generate


def test_generation_is_repeatable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate(first, order_count=40, seed=17)
    generate(second, order_count=40, seed=17)

    for table in (
        "fact_sales",
        "dim_date",
        "dim_region",
        "dim_product",
        "dim_channel",
    ):
        assert pq.read_table(first / f"{table}.parquet").equals(
            pq.read_table(second / f"{table}.parquet")
        )


def test_fact_keys_and_amounts_are_valid(parquet_data: Path) -> None:
    facts = pq.read_table(parquet_data / "fact_sales.parquet").to_pylist()
    dimension_keys = {
        "date_key": set(pq.read_table(parquet_data / "dim_date.parquet")["date_key"].to_pylist()),
        "region_id": set(pq.read_table(parquet_data / "dim_region.parquet")["region_id"].to_pylist()),
        "product_id": set(pq.read_table(parquet_data / "dim_product.parquet")["product_id"].to_pylist()),
        "channel_id": set(pq.read_table(parquet_data / "dim_channel.parquet")["channel_id"].to_pylist()),
    }

    assert len({row["sale_id"] for row in facts}) == len(facts)
    assert {row["order_id"] for row in facts} == set(range(1, 301))
    for row in facts:
        assert row["date_key"] in dimension_keys["date_key"]
        assert row["region_id"] in dimension_keys["region_id"]
        assert row["product_id"] in dimension_keys["product_id"]
        assert row["channel_id"] in dimension_keys["channel_id"]
        assert row["quantity"] > 0
        assert row["sales_amount"] == row["unit_price"] * row["quantity"]
        assert isinstance(row["sales_amount"], Decimal)
