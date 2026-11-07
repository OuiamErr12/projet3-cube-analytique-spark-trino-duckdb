"""Compare les CSV des moteurs sur les clés, sans additionner les KPI non additifs."""

from __future__ import annotations

import csv
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "results"
REQUIRED_ENGINES = ("spark", "duckdb")
OPTIONAL_ENGINES = ("trino",)
ANALYSES = (
    ("monthly", "monthly_kpis.csv", ("date_month", "region_name", "category")),
    ("cube", "cube_kpis.csv", ("date_month", "region_name", "category")),
    ("channel", "channel_kpis.csv", ("date_month", "region_name", "category", "channel_name")),
)
METRICS = ("revenue", "distinct_orders", "average_basket")
TOLERANCE = Decimal("0.01")


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"Fichier vide : {path}")
        return list(reader.fieldnames), list(reader)


def key_of(row: dict[str, str], columns: tuple[str, ...]) -> tuple[str, ...]:
    return tuple((row.get(column) or "").strip() for column in columns)


def decimal_value(value: str | None) -> Decimal | None:
    if value is None or not str(value).strip():
        return None
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return None


def index_rows(rows: list[dict[str, str]], columns: tuple[str, ...], engine: str) -> dict[tuple[str, ...], dict[str, str]]:
    indexed: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = key_of(row, columns)
        if key in indexed:
            raise ValueError(f"Clé dupliquée pour {engine} : {key}")
        indexed[key] = row
    return indexed


def values_match(reference: str | None, other: str | None) -> bool:
    left = decimal_value(reference)
    right = decimal_value(other)
    if left is None or right is None:
        return (reference or "").strip() == (other or "").strip()
    return abs(left - right) <= TOLERANCE


def compare_analysis(
    name: str,
    filename: str,
    key_columns: tuple[str, ...],
    engines: list[str],
) -> bool:
    print(f"\n=== {name} ===")
    indexed = {}
    for engine in engines:
        path = ROOT / engine / filename
        columns, rows = load_csv(path)
        missing = set(key_columns).union(METRICS) - set(columns)
        if missing:
            print(f"{engine} : colonnes absentes : {sorted(missing)}")
            return False
        indexed[engine] = index_rows(rows, key_columns, engine)
        print(f"{engine}: {len(indexed[engine])} lignes")

    reference_name = "duckdb"
    reference = indexed[reference_name]
    ok = True
    for engine in engines:
        if engine == reference_name:
            continue
        other = indexed[engine]
        if set(reference) != set(other):
            only_reference = len(set(reference) - set(other))
            only_other = len(set(other) - set(reference))
            print(
                f"DIFFÉRENCE de clés DuckDB vs {engine} : "
                f"{only_reference} seulement DuckDB, {only_other} seulement {engine}."
            )
            ok = False
        differences = 0
        for key in set(reference) & set(other):
            for metric in METRICS:
                if not values_match(reference[key].get(metric), other[key].get(metric)):
                    differences += 1
        if differences:
            print(f"DIFFÉRENCES DuckDB vs {engine} : {differences} valeurs.")
            ok = False
        elif set(reference) == set(other):
            print(f"OK : DuckDB et {engine} correspondent à 0,01 près.")
    return ok


def available_engines() -> list[str]:
    engines = list(REQUIRED_ENGINES)
    for engine in OPTIONAL_ENGINES:
        paths = [ROOT / engine / filename for _, filename, _ in ANALYSES]
        if all(path.exists() for path in paths):
            engines.append(engine)
        else:
            print(f"{engine} : CSV absents, comparaison omise.")
    missing = [engine for engine in REQUIRED_ENGINES if not (ROOT / engine).is_dir()]
    if missing:
        raise FileNotFoundError(
            "Résultats obligatoires absents pour : " + ", ".join(missing)
        )
    return engines


def main() -> None:
    engines = available_engines()
    ok = True
    for name, filename, key_columns in ANALYSES:
        for engine in engines:
            path = ROOT / engine / filename
            if not path.exists():
                raise FileNotFoundError(f"Fichier manquant : {path}")
        ok = compare_analysis(name, filename, key_columns, engines) and ok

    print("\n" + "=" * 40)
    print("BILAN :", "RÉUSSI" if ok else "À ANALYSER")
    print("=" * 40)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
