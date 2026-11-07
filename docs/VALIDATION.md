# Résultats de validation

Exécution du 7 novembre 2026 sur le poste décrit dans
[COMPARAISON.md](COMPARAISON.md). Une vérification antérieure, le 26 octobre
2026 sous Windows, avait généré les données et fait passer les tests DuckDB,
sans pouvoir lancer Spark ni Trino. Cette exécution couvre les trois moteurs.

| Étape | Résultat |
|---|---|
| Génération `--orders 50000 --seed 42` | 50 000 commandes, 124 923 lignes, 731 jours |
| `python -m pytest -q` | 4 réussites, dont la parité Spark / DuckDB |
| DuckDB | 480 KPI mensuels, 750 lignes de cube, 1 440 lignes canal |
| Spark SQL `local[*]` | Mêmes volumes, valeurs égales à DuckDB à 0,01 près |
| Trino 476 sur MinIO | Mêmes volumes, valeurs égales à DuckDB à 0,01 près |
| `scripts/compare_results.py` | Bilan réussi pour les trois analyses |

Les durées et le total général sont dans [COMPARAISON.md](COMPARAISON.md).
Les CSV de cette exécution sont versionnés dans `results/`.
