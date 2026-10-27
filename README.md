# Projet 3 — Cube analytique sur Parquet

Projet pédagogique reproductible de ventes au format Parquet, analysées avec
Spark SQL, DuckDB et, via Docker, Trino. Le modèle en étoile comprend
`fact_sales`, `dim_date`, `dim_region`, `dim_product` et `dim_channel`.

## Architecture

```text
data/                 Parquet générés (non versionnés)
scripts/              Génération reproductible des données
spark_sql/            SQL Spark et lanceur PySpark
duckdb/               SQL DuckDB et lanceur local
trino/                Catalogue Hive, tables, SQL et scripts Docker
tests/                Contrôles de qualité et parité des moteurs
results/              Résultats CSV générés (non versionnés)
docs/                 Modèle, installation, exploitation et présentation
```

## Démarrage rapide (Windows PowerShell)

Prérequis recommandés : Python 3.11 ou 3.12, Java 17 pour Spark, et Docker
Desktop démarré pour Trino. Créez un environnement et installez les
dépendances :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Produisez les fichiers Parquet et lancez les contrôles :

```powershell
python scripts\generate_data.py --orders 50000 --seed 42
python -m pytest -q
```

Analyses locales :

```powershell
python duckdb\run_analysis.py
python spark_sql\run_analysis.py
```

Trino requiert un service Hive Metastore et un stockage objet S3-compatible.
Le `docker-compose.yml` configure Trino, MinIO et un Hive Metastore ; les
Parquet locaux sont copiés dans MinIO au démarrage. Après génération :

```powershell
docker compose up -d
docker compose exec -T trino trino --server http://localhost:8080 --file /project/trino/setup.sql
docker compose exec -T trino trino --server http://localhost:8080 --catalog hive --schema sales --file /project/trino/analysis.sql
```

Les étapes, les commandes de comparaison et les limites connues sont détaillées
dans [docs/INSTALLATION.md](docs/INSTALLATION.md) et
[docs/MODELE_ET_KPI.md](docs/MODELE_ET_KPI.md).
Les validations réellement lancées sont consignées dans
[docs/VALIDATION.md](docs/VALIDATION.md).

## Principes de calcul

Le grain de `fact_sales` est une ligne de produit d'une commande. Le chiffre
d'affaires est `SUM(sales_amount)`, le nombre de commandes est
`COUNT(DISTINCT order_id)` et le panier moyen d'un groupe est le chiffre
d'affaires du groupe divisé par les commandes distinctes contribuant à ce
groupe. Ce dernier indicateur n'est pas additif : une commande avec plusieurs
catégories contribue à chacune de ces catégories.

Les résultats mesurent les mêmes données et règles, pas les performances dans
des conditions matérielles différentes. Aucun résultat ni temps d'exécution
n'est prérempli : chaque script produit ses propres fichiers localement.
