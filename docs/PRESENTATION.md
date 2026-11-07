# Support de présentation

Durée indicative : 12 à 15 minutes. Les chiffres cités à l'oral doivent être
ceux de [COMPARAISON.md](COMPARAISON.md), mesurés sur la machine du groupe.

## 1. Besoin métier

Une distribution veut lire ses ventes par période, région, catégorie et canal.
Trois indicateurs : le chiffre d'affaires, le nombre de commandes distinctes
et le panier moyen. Les fichiers sources sont en Parquet. La solution doit
produire ces indicateurs sur un modèle analytique, pas sur les tables
opérationnelles.

## 2. Modèle

Montrer [SCHEMA.md](SCHEMA.md).

- Le grain de `fact_sales` est une ligne produit d'une commande.
- Une commande a une seule date, une seule région et un seul canal, et une à
  quatre lignes produit.
- `sales_amount = quantity × unit_price`, sans taxe ni remise.
- Les clés sont contrôlées par les tests, pas par le format Parquet.

## 3. Données

Jeu synthétique, sans API : 50 000 commandes, graine 42, du 1er janvier 2024
au 31 décembre 2025. Cinq régions, quinze produits, quatre catégories, trois
canaux. Le tirage est uniforme : il sert à comparer les moteurs, pas à
découvrir une saisonnalité.

## 4. Requêtes

Trois requêtes, la même définition sur Spark SQL, DuckDB et Trino.

- `monthly_kpis.sql` : jointures, filtre de dates, agrégation par mois,
  région et catégorie.
- `cube.sql` : `GROUP BY CUBE` sur ces trois axes, donc huit niveaux, du
  détail jusqu'au total général. Une dimension NULL est un axe omis.
- `channel_kpis.sql` : les mêmes indicateurs avec le canal.

Insister sur le panier moyen : CA du groupe / commandes distinctes du groupe.
Une commande présente dans deux catégories compte dans chacune. Additionner
les paniers ou les commandes le long de la catégorie double-compte.

## 5. Moteurs

- DuckDB lit les Parquet du disque. Pas de serveur.
- Spark SQL exécute le même SQL. Ici le master est `local[*]` : le plan est
  distribué entre threads, pas entre machines.
- Trino interroge un catalogue Hive dont les fichiers sont dans MinIO. Le
  métastore de démonstration est un métastore fichier sur S3. Ce n'est pas un
  cluster Trino.

## 6. Résultats

Enchaîner : `pytest`, les deux lanceurs, `compare_results.py`, et Trino si
Docker a démarré. Montrer que les clés et les trois indicateurs coincident
à 0,01 près. Séparer le temps de démarrage du temps de requête. Ne pas
conclure qu'un moteur est plus rapide en production : les conditions ne sont
pas celles d'un cluster, et le volume tient en mémoire.

## 7. Analyse critique

S'appuyer sur [ANALYSE_CRITIQUE.md](ANALYSE_CRITIQUE.md).

- Volume synthétique, prix fixes, pas de saisonnalité.
- Indicateurs non additifs : un tableau croisé dynamique mal configuré
  afficherait un faux panier.
- Spark local et Trino mono-nœud n'estiment pas un passage à l'échelle.
- Le canal est analysé à part pour ne pas gonfler le cube au-delà de la
  question principale.
- Suite possible : partitionner les Parquet par mois, figer un catalogue, et
  ne mesurer les performances que sur un cluster avec le même matériel.
