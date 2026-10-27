"""Génère un jeu de ventes synthétique et ses fichiers Parquet."""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


START_DATE = date(2024, 1, 1)
END_DATE = date(2025, 12, 31)
REGIONS = [
    (1, "Nord", "France"),
    (2, "Sud", "France"),
    (3, "Est", "France"),
    (4, "Ouest", "France"),
    (5, "Centre", "France"),
]
PRODUCTS = [
    (1, "Cafe moulu", "Epicerie", 650),
    (2, "The vert", "Epicerie", 480),
    (3, "Pates", "Epicerie", 220),
    (4, "Huile olive", "Epicerie", 890),
    (5, "T-shirt", "Mode", 1490),
    (6, "Jean", "Mode", 3990),
    (7, "Veste", "Mode", 6990),
    (8, "Chaussures", "Mode", 5490),
    (9, "Lampe", "Maison", 2590),
    (10, "Coussin", "Maison", 1290),
    (11, "Poele", "Maison", 3290),
    (12, "Ecouteurs", "Electronique", 2990),
    (13, "Clavier", "Electronique", 4490),
    (14, "Chargeur", "Electronique", 1590),
    (15, "Souris", "Electronique", 2190),
]
CHANNELS = [(1, "Magasin"), (2, "Web"), (3, "Application")]
MONTH_NAMES = (
    "janvier",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "decembre",
)


def _schema(fields: list[tuple[str, pa.DataType]]) -> pa.Schema:
    return pa.schema(fields)


def _write_parquet(path: Path, rows: list[dict], schema: pa.Schema) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, path, compression="snappy")


def generate(output_dir: Path, order_count: int, seed: int) -> tuple[int, int]:
    """Écrit les cinq tables ; retourne le nombre de jours et de lignes de faits."""
    if order_count < 1:
        raise ValueError("Le nombre de commandes doit être supérieur ou égal à 1.")

    output_dir.mkdir(parents=True, exist_ok=True)
    date_rows = []
    current = START_DATE
    while current <= END_DATE:
        date_rows.append(
            {
                "date_key": current.year * 10000 + current.month * 100 + current.day,
                "full_date": current,
                "calendar_year": current.year,
                "quarter": (current.month - 1) // 3 + 1,
                "month": current.month,
                "month_name": MONTH_NAMES[current.month - 1],
                "date_month": current.strftime("%Y-%m"),
            }
        )
        current += timedelta(days=1)

    _write_parquet(
        output_dir / "dim_date.parquet",
        date_rows,
        _schema(
            [
                ("date_key", pa.int32()),
                ("full_date", pa.date32()),
                ("calendar_year", pa.int16()),
                ("quarter", pa.int16()),
                ("month", pa.int16()),
                ("month_name", pa.string()),
                ("date_month", pa.string()),
            ]
        ),
    )
    _write_parquet(
        output_dir / "dim_region.parquet",
        [
            {"region_id": key, "region_name": name, "country": country}
            for key, name, country in REGIONS
        ],
        _schema(
            [
                ("region_id", pa.int32()),
                ("region_name", pa.string()),
                ("country", pa.string()),
            ]
        ),
    )
    _write_parquet(
        output_dir / "dim_product.parquet",
        [
            {
                "product_id": key,
                "product_name": name,
                "category": category,
                "unit_price": Decimal(price_cents) / Decimal(100),
            }
            for key, name, category, price_cents in PRODUCTS
        ],
        _schema(
            [
                ("product_id", pa.int32()),
                ("product_name", pa.string()),
                ("category", pa.string()),
                ("unit_price", pa.decimal128(10, 2)),
            ]
        ),
    )
    _write_parquet(
        output_dir / "dim_channel.parquet",
        [
            {"channel_id": key, "channel_name": name}
            for key, name in CHANNELS
        ],
        _schema(
            [
                ("channel_id", pa.int32()),
                ("channel_name", pa.string()),
            ]
        ),
    )

    rng = random.Random(seed)
    fact_rows = []
    date_count = len(date_rows)
    for order_id in range(1, order_count + 1):
        order_date = date_rows[rng.randrange(date_count)]
        line_count = rng.randint(1, 4)
        product_sample = rng.sample(PRODUCTS, line_count)
        region_id = rng.choice(REGIONS)[0]
        channel_id = rng.choice(CHANNELS)[0]
        for product_id, _, _, price_cents in product_sample:
            quantity = rng.randint(1, 5)
            fact_rows.append(
                {
                    "sale_id": len(fact_rows) + 1,
                    "order_id": order_id,
                    "date_key": order_date["date_key"],
                    "region_id": region_id,
                    "product_id": product_id,
                    "channel_id": channel_id,
                    "quantity": quantity,
                    "unit_price": Decimal(price_cents) / Decimal(100),
                    "sales_amount": Decimal(price_cents * quantity) / Decimal(100),
                }
            )

    _write_parquet(
        output_dir / "fact_sales.parquet",
        fact_rows,
        _schema(
            [
                ("sale_id", pa.int64()),
                ("order_id", pa.int64()),
                ("date_key", pa.int32()),
                ("region_id", pa.int32()),
                ("product_id", pa.int32()),
                ("channel_id", pa.int32()),
                ("quantity", pa.int16()),
                ("unit_price", pa.decimal128(10, 2)),
                ("sales_amount", pa.decimal128(12, 2)),
            ]
        ),
    )
    return len(date_rows), len(fact_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=50_000, help="Nombre de commandes.")
    parser.add_argument("--seed", type=int, default=42, help="Graine du générateur.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
        help="Répertoire de sortie (défaut : data/).",
    )
    args = parser.parse_args()
    day_count, line_count = generate(args.output_dir, args.orders, args.seed)
    print(
        f"Données écrites dans {args.output_dir.resolve()} : "
        f"{args.orders} commandes, {line_count} lignes, {day_count} dates."
    )


if __name__ == "__main__":
    main()
