# Résultats de validation

Compte rendu des commandes réellement lancées dans cet espace de travail le
26 octobre 2026. Il décrit cet environnement uniquement ; ce n'est pas une
certification pour d'autres versions ou machines.

## Environnement observé

- Windows, Python 3.13.3
- DuckDB 2.0.0, PyArrow 26.0.0 et pytest 9.1.1 présents
- PySpark absent ; Java/JDK introuvable dans le `PATH`
- Docker Compose disponible et capable de valider le YAML, mais le moteur
  Docker Desktop n'a pas répondu à `docker info` (erreur HTTP 500 via le pipe
  Linux Engine)

## Exécutions et résultats

| Étape | Résultat réellement observé |
|---|---|
| Génération `--orders 50000 --seed 42` | Réussie : 50 000 commandes, 124 923 lignes de faits et 731 jours |
| Tests `python -m pytest -q` | 3 réussis, 1 ignoré ; le test Spark/DuckDB est ignoré car PySpark et un JDK sont nécessaires |
| Vérification de syntaxe Python (`py_compile`) | Réussie pour les scripts et tests Python |
| Analyses DuckDB | Réussies sur les Parquet générés |
| Résultats DuckDB | `monthly_kpis.csv` : 480 lignes ; `cube_kpis.csv` : 750 lignes (hors en-tête) |
| `docker compose config -q` | Réussi : configuration Compose résolue |
| Démarrage / requêtes Spark SQL | Non exécutés : PySpark et Java/JDK ne sont pas installés |
| Démarrage / requêtes Trino | Non exécutés : le daemon Docker est inaccessible dans cet environnement |

Les fichiers Parquet et CSV sont générés localement et exclus du contrôle de
version. Aucun temps d'exécution ou résultat de performance n'est rapporté.
La parité DuckDB/Spark est définie par un test sur petit jeu synthétique, mais
elle n'a pas été exécutée ici ; le contrôle DuckDB du total et des KPI, ainsi
que les contraintes de clés étrangères et de montants, a été exécuté.

## À faire pour compléter l'intégration

1. Installer un JDK 17 et PySpark selon `requirements.txt`, puis relancer
   `python -m pytest -q` et `python spark_sql\run_analysis.py`.
2. Démarrer Docker Desktop, exécuter les commandes Trino de
   `docs/INSTALLATION.md` et consigner la version des images, les sorties et
   les éventuelles erreurs observées.
3. Pour toute comparaison de performance, documenter séparément démarrage,
   lecture/chargement, exécution SQL, cache, matériel et configuration des
   moteurs.
