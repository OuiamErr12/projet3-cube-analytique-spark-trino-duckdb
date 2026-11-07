# Installation et exécution

## Environnement Windows

1. Installez Python 3.11 ou 3.12 et vérifiez `py --list`.
2. Pour Spark, installez un JDK 17 et vérifiez `java -version` et
   `JAVA_HOME`. Spark 4.0.x requiert Java 17 ou 21 ; PySpark s'exécute en
   local sans installer un cluster.
3. Créez/activez `.venv` et installez `requirements.txt` selon le README.
4. Pour Trino, installez et démarrez Docker Desktop ; `docker compose version`
   doit fonctionner.

## Environnement macOS

Les mêmes étapes, avec les commandes du shell :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/generate_data.py --orders 50000 --seed 42
python -m pytest -q
python duckdb/run_analysis.py
python spark_sql/run_analysis.py
python scripts/compare_results.py
```

Java 17 doit être visible (`java -version`, `JAVA_HOME`). L'interface Trino
est publiée sur le port hôte 8081. Depuis l'intérieur du conteneur, le CLI
continue d'utiliser `http://localhost:8080`.

Les versions Python et Java disponibles sur la machine peuvent différer.
Cette configuration recommande Python 3.11/3.12, Java 17, PySpark 4.0.x,
DuckDB 1.2+ (2.0 testé localement) et Trino 476. Les images du compose sont épinglées ; la disponibilité
des images et leur compatibilité doivent être vérifiées sur la machine au
premier démarrage. Les tests Spark nécessitent un JDK opérationnel.

## Commandes

Depuis la racine du projet :

```powershell
python scripts\generate_data.py --orders 50000 --seed 42
python -m pytest -q
python duckdb\run_analysis.py
python spark_sql\run_analysis.py
python scripts\compare_results.py
```

Le nombre de commandes et la graine sont modifiables. La graine reproduit les
mêmes lignes, pas nécessairement des fichiers identiques octet pour octet
entre différentes versions de PyArrow.

### Trino avec MinIO et Hive Metastore

1. Générez les fichiers Parquet avant de démarrer Compose.
2. Démarrez les services avec `docker compose up -d`.
3. Exécutez `trino/setup.sql` une fois afin d'enregistrer les tables externes
   dans le metastore.
4. Exécutez `trino/analysis.sql` pour les KPI et
   `trino/cube.sql` pour les niveaux du cube :

```powershell
docker compose exec -T trino trino --server http://localhost:8080 --file /project/trino/setup.sql
docker compose exec -T trino trino --server http://localhost:8080 --catalog hive --schema sales --file /project/trino/analysis.sql
docker compose exec -T trino trino --server http://localhost:8080 --catalog hive --schema sales --file /project/trino/cube.sql
docker compose exec -T trino trino --server http://localhost:8080 --catalog hive --schema sales --file /project/trino/channel_kpis.sql
python scripts\export_trino_results.py
python scripts\compare_results.py
```

MinIO fournit le stockage S3-compatible. Le catalogue
`trino/etc/catalog/hive.properties` utilise un metastore fichier dont le
répertoire est `s3://project-data/trino-metastore/`. C'est ce catalogue qui
enregistre les tables créées par `setup.sql`. Le service `hive-metastore` du
Compose démarre un metastore Derby de démonstration ; le catalogue Trino ne
s'y connecte pas. Un conteneur d'initialisation copie les fichiers locaux
dans le bucket `project-data`. Les identifiants MinIO du compose sont des
identifiants de démonstration locaux, à remplacer avant toute exposition hors
du poste. Ni le metastore fichier ni Derby ne sont destinés à la haute
disponibilité.

Pour arrêter les services sans effacer leur volume :

```powershell
docker compose down
```

Pour réinitialiser le catalogue persistant, supprimer le volume nommé est
destructif pour ses métadonnées et doit être volontaire. Les fichiers copiés
dans MinIO ne sont pas automatiquement recopiés si le conteneur d'initialisation
a déjà terminé. Après une nouvelle génération, relancez explicitement la copie :

```powershell
docker compose run --rm --no-deps minio-init
```

## Lecture des résultats et comparaison

DuckDB et Spark écrivent `monthly_kpis.csv`, `cube_kpis.csv`,
`channel_kpis.csv` et `timings.csv`, respectivement sous `results/duckdb/`
et `results/spark/`. `python scripts/compare_results.py` compare ces CSV
ligne à ligne, sur les clés d'analyse. Il n'additionne pas les commandes
distinctes. Trino est inclus seulement si `results/trino/` contient les trois
CSV, produits par `scripts/export_trino_results.py`. Les tests comparent
les agrégats de référence DuckDB et Spark sur un petit jeu synthétique et
valident les clés. Trino est préparé et ses requêtes sont fournies, mais le
test automatisé ne prétend pas lancer Docker ni certifier un service qui
n'aurait pas été démarré. Pour comparer Trino, exécutez les mêmes requêtes et
comparez les CSV/valeurs produits par les autres moteurs.

Séparez les mesures de démarrage (création session Spark/conteneurs), de
chargement des fichiers, et de temps SQL. Comparez les moteurs avec les mêmes
données, filtres, dimensions, ressources et état de cache ; consignez versions,
CPU, mémoire et stockage. Aucun chiffre de performance n'est fourni à l'avance. Les exécutions réellement
effectuées dans cet espace de travail sont consignées dans
[docs/VALIDATION.md](VALIDATION.md).

## Dépannage fréquent

- **`JAVA_HOME` ou Java introuvable** : définissez `JAVA_HOME` vers le JDK 17
  et rouvrez PowerShell.
- **Spark échoue pendant l'initialisation Java** : vérifiez l'architecture
  64 bits du JDK et la compatibilité Java 17/21.
- **Erreur PyArrow/DuckDB manquant** : activez le bon `.venv` puis relancez
  `pip install -r requirements.txt`.
- **Docker daemon inaccessible** : démarrez Docker Desktop et attendez que son
  moteur Linux soit opérationnel.
- **Trino ne voit pas les tables** : vérifiez que les données ont été générées
  avant Compose, que l'initialisation MinIO a terminé et que `setup.sql` a été
  exécuté ; regardez `docker compose logs trino hive-metastore minio-init`.
- **Résultats différents** : vérifiez graine, nombre de commandes, fichiers
  réellement lus, filtres et définition du panier moyen. Les agrégats par
  catégorie ne sont pas additifs.
