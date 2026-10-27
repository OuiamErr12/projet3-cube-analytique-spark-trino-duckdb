from pathlib import Path

import pytest

from scripts.generate_data import generate


@pytest.fixture
def parquet_data(tmp_path: Path) -> Path:
    output = tmp_path / "data"
    generate(output, order_count=300, seed=31415)
    return output
