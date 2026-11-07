# Comparaison des moteurs

Compte rendu de l'exécution du 7 novembre 2026. Les trois moteurs ont lu le
même jeu, graine 42, 50 000 commandes, 124 923 lignes de faits, 731 jours.
La comparaison porte sur les valeurs. Les durées décrivent ce poste, avec
des périmètres différents : elles ne classent pas les moteurs pour un
cluster.

## Environnement

- macOS 26.5, Apple M2, 8 cœurs, 16 Go de mémoire
- Python 3.13, DuckDB 2.0.0, PyArrow 26.0.0, PySpark 4.0.5, pytest 9.2.0
- OpenJDK 17.0.21
- Trino 476, coordinateur déjà démarré, MinIO et métastore fichier sur S3
- Spark en `local[*]` sur la même machine

## Valeurs

`python scripts/compare_results.py` compare chaque ligne sur ses clés, avec
une tolérance de 0,01 sur les montants. Les commandes distinctes ne sont pas
additionnées entre catégories.

| Analyse | Lignes | DuckDB vs Spark | DuckDB vs Trino |
|---|---:|---|---|
| KPI mois × région × catégorie | 480 | identiques | identiques |
| Cube, 8 niveaux | 750 | identiques | identiques |
| KPI avec canal | 1 440 | identiques | identiques |

Le total général du cube est le même des deux côtés, et du troisième :

- chiffre d'affaires : 9 684 550,80
- commandes distinctes : 50 000
- panier moyen : 193,691016 (9 684 550,80 / 50 000)

Les 1 440 lignes canal correspondent aux 480 groupes mois × région ×
catégorie, chacun présent sur les 3 canaux. La somme des chiffres d'affaires
de cette requête retrouve le total, parce qu'une ligne de fait n'a qu'un
canal.

Les tests `python -m pytest -q` ont donné 4 réussites, y compris la parité
Spark / DuckDB sur un jeu de 300 commandes.

## Durées mesurées

Secondes relevées par les lanceurs. Pour DuckDB et Spark, `startup` est
l'ouverture de session. Le temps de requête inclut le calcul et l'écriture
du CSV. Pour Trino, le temps inclut `docker compose exec`, le démarrage du
CLI et le transfert du résultat. Le serveur Trino était déjà chaud. Le cache
disque n'a pas été vidé entre les moteurs.

| Étape | DuckDB | Spark `local[*]` | Trino 476 |
|---|---:|---:|---:|
| Démarrage de session | 0,013 | 2,528 | serveur déjà lancé |
| KPI mensuels | 0,019 | 2,101 | 3,519 |
| Cube | 0,063 | 1,753 | 2,657 |
| KPI avec canal | 0,024 | 0,787 | 1,528 |

Lecture permise par ces chiffres : sur 125 000 lignes déjà locales, le coût
visible de Spark est surtout celui de la JVM et de la première requête. Le
coût visible de Trino inclut le passage par le CLI et par MinIO. Rien ici ne
dit lequel des trois serait le plus rapide sur un cluster, avec des fichiers
partitionnés, un cache froid identique et le même stockage.
