# Trame de présentation orale

1. **Besoin métier** — analyser les ventes par période, région, catégorie et
   canal ; préciser les KPI demandés.
2. **Modèle** — présenter le grain ligne de vente, la table de faits, les
   dimensions, les PK/FK et les règles de qualité.
3. **Données** — expliquer la génération synthétique sans API, la graine,
   l'échelle choisie et le stockage colonne Parquet.
4. **Requêtes** — montrer les jointures, filtres, agrégations et le `CUBE` ;
   clarifier le sens du panier moyen et les agrégats non additifs.
5. **Moteurs** — comparer Spark SQL (exécution distribuée, ici mode local),
   Trino (SQL distribué/fédéré avec metastore et stockage) et DuckDB (analyse
   locale embarquée).
6. **Résultats** — exécuter les tests et présenter les mesures réellement
   obtenues, avec versions, matériel, démarrage séparé du SQL et protocole
   équitable. Ne pas extrapoler un test local en résultat de cluster.
7. **Limites / suite** — volumes synthétiques, schéma simplifié, absence
   d'authentification de production et possibilité d'ajouter partitionnement,
   catalogue pérenne et mesures sur cluster.
