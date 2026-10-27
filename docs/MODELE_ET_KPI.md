# Modèle analytique et règles de calcul

## SQL distribué et moteurs

Une requête SQL distribuée est planifiée puis exécutée sur des partitions de
données, potentiellement sur plusieurs processus ou machines. Le moteur
optimise le plan (projection, filtres, jointures, agrégations) et échange des
résultats intermédiaires. La distribution ne garantit pas à elle seule un
gain : taille des données, stockage, réseau, partitionnement, mémoire et coût
de démarrage comptent.

- **Spark SQL** exécute des plans SQL/DataFrame sur le moteur Spark. Il convient
  aux transformations et traitements distribués, notamment avec un cluster
  configuré. La commande fournie démarre Spark en mode local pour faciliter
  l'apprentissage ; elle ne constitue pas un benchmark distribué.
- **Trino** est un moteur SQL distribué conçu pour interroger des sources
  fédérées. Son connecteur Hive s'appuie sur un metastore pour les métadonnées
  et sur un système de fichiers/stockage objet pour les fichiers. Trino ne
  découvre pas arbitrairement les Parquet d'un disque local.
- **DuckDB** est un moteur analytique embarqué, sans serveur à administrer. Il
  peut lire directement des Parquet locaux et est particulièrement pratique
  pour l'exploration et les analyses sur poste de travail. Il peut traiter de
  grands volumes, mais une exécution locale ne devient pas un cluster Spark
  ou Trino.

## Schéma en étoile

`fact_sales` est au centre, avec une clé primaire de ligne et quatre clés
étrangères vers des dimensions. Les clés des dimensions sont des identifiants
entiers stables dans un jeu généré. Les fichiers générés sont en Parquet ; les
types logiques et contraintes sont définis ci-dessous.

| Table | Grain / clé primaire | Colonnes principales |
|---|---|---|
| `fact_sales` | Une ligne de produit ; `sale_id BIGINT` | `order_id BIGINT`, `date_key INT`, `region_id INT`, `product_id INT`, `channel_id INT`, `quantity SMALLINT`, `unit_price DECIMAL(10,2)`, `sales_amount DECIMAL(12,2)` |
| `dim_date` | Un jour ; `date_key INT` (AAAAMMJJ) | `full_date DATE`, `calendar_year SMALLINT`, `quarter SMALLINT`, `month SMALLINT`, `month_name STRING`, `date_month STRING` (AAAA-MM) |
| `dim_region` | Une région ; `region_id INT` | `region_name STRING`, `country STRING` |
| `dim_product` | Un produit ; `product_id INT` | `product_name STRING`, `category STRING`, `unit_price DECIMAL(10,2)` |
| `dim_channel` | Un canal ; `channel_id INT` | `channel_name STRING` |

Les formats Parquet n'imposent pas les contraintes PK/FK. Elles sont validées
par les tests. `sales_amount = quantity * unit_price`, sans taxe ni remise.
Chaque commande appartient à une date, une région et un canal ; elle peut
contenir plusieurs produits.

## KPI et cube

- **Chiffre d'affaires** : somme de `sales_amount`, en unités monétaires
  synthétiques.
- **Commandes distinctes** : nombre de `order_id` distincts dans chaque groupe.
- **Panier moyen** : chiffre d'affaires du groupe / commandes distinctes du
  groupe ; NULL si le dénominateur est nul.
- **Analyse principale** : mois, région et catégorie, avec jointures des quatre
  dimensions.
- **Cube** : agrégations à toutes les combinaisons de mois, région et
  catégorie, y compris le total général. Une dimension à NULL dans une ligne
  du cube est omise par ce niveau d'agrégation. Les commandes et paniers
  moyens ne s'additionnent pas entre catégories : une commande peut contenir
  plusieurs catégories.

Les scripts Spark, DuckDB et Trino utilisent cette même définition. Les
comparaisons portent sur les valeurs, avec tolérance uniquement pour la
représentation décimale lors de la comparaison des sorties.
