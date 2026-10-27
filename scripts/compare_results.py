
import csv
from pathlib import Path
from decimal import Decimal, InvalidOperation
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent / "results"
ENGINES = ["spark", "duckdb", "trino"]

NUMERIC_COLUMNS = [
    "revenue",
    "distinct_orders",
    "average_basket",
]

TOLERANCE = Decimal("0.01")


def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"Fichier vide : {path}")
        return reader.fieldnames, list(reader)


def decimal_value(value):
    try:
        if value is None or not value.strip():
            return None
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        return None


def aggregate_monthly(rows, columns):
    """Agrège par mois pour comparer les KPI mensuels."""
    result = defaultdict(lambda: {
        "revenue": Decimal("0"),
        "distinct_orders": Decimal("0"),
    })

    for row in rows:
        month = (row.get("date_month") or "").strip()
        revenue = decimal_value(row.get("revenue"))
        orders = decimal_value(row.get("distinct_orders"))

        if revenue is not None:
            result[month]["revenue"] += revenue
        if orders is not None:
            result[month]["distinct_orders"] += orders

    return dict(result)


def compare_monthly(datasets):
    print("\n=== Comparaison des KPI mensuels ===")

    aggregated = {}
    for engine, (columns, rows) in datasets.items():
        aggregated[engine] = aggregate_monthly(rows, columns)
        print(f"{engine}: {len(aggregated[engine])} mois")

    reference = aggregated["spark"]
    ok = True

    for engine in ["duckdb", "trino"]:
        other = aggregated[engine]

        if set(reference) != set(other):
            print(f"DIFFÉRENCE : les mois ne correspondent pas pour {engine}.")
            ok = False
            continue

        differences = 0
        for month in reference:
            for metric in ["revenue", "distinct_orders"]:
                if abs(reference[month][metric] - other[month][metric]) > TOLERANCE:
                    differences += 1

        if differences:
            print(f"DIFFÉRENCES Spark vs {engine} : {differences} valeurs.")
            ok = False
        else:
            print(f"OK : Spark et {engine} correspondent.")

    return ok


def compare_cube(datasets):
    print("\n=== Comparaison du cube analytique ===")

    keys = ["date_month", "region_name", "category"]
    data = {}

    for engine, (columns, rows) in datasets.items():
        missing = set(keys) - set(columns)
        if missing:
            print(f"{engine} : colonnes de clé absentes : {missing}")
            return False

        mapped = {}
        for row in rows:
            key = tuple((row.get(k) or "").strip() for k in keys)
            if key in mapped:
                raise ValueError(f"Clé dupliquée dans le cube {engine}: {key}")
            mapped[key] = row

        data[engine] = mapped
        print(f"{engine}: {len(mapped)} lignes")

    ok = True
    reference = data["spark"]

    for engine in ["duckdb", "trino"]:
        other = data[engine]

        if set(reference) != set(other):
            print(f"DIFFÉRENCE de lignes Spark vs {engine}.")
            ok = False

        common_keys = set(reference) & set(other)
        differences = 0

        for key in common_keys:
            for metric in NUMERIC_COLUMNS:
                a = decimal_value(reference[key].get(metric))
                b = decimal_value(other[key].get(metric))

                if a is None or b is None:
                    if reference[key].get(metric) != other[key].get(metric):
                        differences += 1
                elif abs(a - b) > TOLERANCE:
                    differences += 1

        if differences:
            print(f"DIFFÉRENCES Spark vs {engine} : {differences} valeurs.")
            ok = False
        else:
            print(f"OK : Spark et {engine} correspondent.")

    return ok


def main():
    datasets_monthly = {}
    datasets_cube = {}

    for engine in ENGINES:
        monthly_path = ROOT / engine / "monthly_kpis.csv"
        cube_path = ROOT / engine / "cube_kpis.csv"

        for path in [monthly_path, cube_path]:
            if not path.exists():
                raise FileNotFoundError(f"Fichier manquant : {path}")

        datasets_monthly[engine] = load_csv(monthly_path)
        datasets_cube[engine] = load_csv(cube_path)

    monthly_ok = compare_monthly(datasets_monthly)
    cube_ok = compare_cube(datasets_cube)

    print("\n" + "=" * 40)
    print("BILAN :", "RÉUSSI" if monthly_ok and cube_ok else "À ANALYSER")
    print("=" * 40)


if __name__ == "__main__":
    main()
