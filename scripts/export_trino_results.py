"""Exporte les requêtes Trino en CSV sous results/trino/."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERIES = (
    ("monthly_kpis", "analysis.sql", "monthly_kpis.csv"),
    ("cube", "cube.sql", "cube_kpis.csv"),
    ("channel_kpis", "channel_kpis.sql", "channel_kpis.csv"),
)


def export_query(sql_name: str, output_name: str, output_dir: Path) -> float:
    destination = output_dir / output_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "trino",
        "trino",
        "--server",
        "http://localhost:8080",
        "--catalog",
        "hive",
        "--schema",
        "sales",
        "--output-format",
        "CSV_HEADER",
        "--file",
        f"/project/trino/{sql_name}",
    ]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    elapsed = time.perf_counter() - started
    destination.write_bytes(completed.stdout)
    return elapsed


def main() -> None:
    output_dir = ROOT / "results" / "trino"
    timings = ["query,seconds"]
    for timing_name, sql_name, output_name in QUERIES:
        elapsed = export_query(sql_name, output_name, output_dir)
        timings.append(f"{timing_name},{elapsed:.3f}")
        print(f"{timing_name}: {elapsed:.3f} s")
    (output_dir / "timings.csv").write_text("\n".join(timings) + "\n", encoding="utf-8")
    print(f"Résultats Trino écrits dans {output_dir.resolve()}")


if __name__ == "__main__":
    main()
