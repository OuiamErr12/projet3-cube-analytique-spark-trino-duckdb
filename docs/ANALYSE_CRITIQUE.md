# Analyse critique

## Ce que le projet démontre

Les trois moteurs appliquent la même définition sur les mêmes Parquet :
jointures vers les quatre dimensions, filtre de période, agrégations, et un
cube à huit niveaux. Le chiffre d'affaires est additif. Le nombre de
commandes et le panier moyen ne le sont pas, parce que le grain de la commande
est plus haut que le grain de la ligne produit.

La comparaison retenue est une comparaison de valeurs, ligne à ligne, avec
une tolérance de 0,01 sur les montants. Elle ne classe pas les moteurs.

## SQL distribué, sans conclusion de cluster

Spark SQL et Trino planifient une requête en étapes qui peuvent s'exécuter
sur plusieurs threads ou plusieurs nœuds, puis échangent des résultats
intermédiaires. DuckDB exécute le plan dans un processus embarqué.

Cette répartition ne suffit pas à dire qu'un moteur distribué est plus
rapide. Ici, les trois exécutions tiennent sur un seul poste :

- DuckDB lit les fichiers locaux ;
- Spark est lancé en `local[*]`, donc le démarrage de la JVM pèse plus que
  la requête sur 125 000 lignes ;
- Trino passe par un coordinateur, MinIO et un catalogue, toujours sur la
  même machine.

Les durées mesurées sont dans [COMPARAISON.md](COMPARAISON.md). Elles
séparent le démarrage du temps de requête. Elles décrivent cet environnement
seulement. Un cluster changerait le réseau, le nombre de fichiers, la
mémoire et le cache : rien dans ces durées ne permet de prédire ce résultat.

## Limites du jeu et du modèle

Le générateur tire les dates, les régions, les produits et les canaux de
façon uniforme. Les KPI seront proches d'une répartition au hasard. Ils ne
montrent pas de saison, de région forte, ni de canal dominant. C'est voulu
pour la reproductibilité, et cela limite l'interprétation métier.

Les prix sont constants, il n'y a ni remise, ni taxe, ni stock. `dim_region`
ne contient que la France. Le pays n'est donc pas un axe d'analyse.

Parquet ne porte pas les clés primaires ni les clés étrangères. Les tests
vérifient l'unicité de `sale_id`, la présence des clés dans les dimensions
et l'égalité `sales_amount = quantity × unit_price`. Un fichier produit hors
de ce générateur pourrait casser ces hypothèses sans erreur au moment de
l'écriture.

Le cube laisse le canal de côté. L'ajouter multiplierait les niveaux
d'agrégation et mélangerait deux questions. Le canal a sa requête dédiée.
Comme chaque ligne n'a qu'un canal, la somme des chiffres d'affaires de
cette requête retrouve le total. La somme des commandes distinctes, non.

## Limites d'exploitation

Les identifiants MinIO du fichier Compose sont des identifiants de
démonstration. Le métastore fichier et le métastore Derby du conteneur Hive
ne sont pas une installation haute disponibilité. Le conteneur Hive est
présent dans Compose ; le catalogue Trino utilisé pointe vers le métastore
fichier sur MinIO, qui suffit à enregistrer les tables externes.

Les CSV de `results/` ne sont pas versionnés. La preuve reproductible est la
procédure, les tests, et le compte rendu de l'exécution réellement lancée.

## Suite utile

Partitionner `fact_sales` par mois, relancer la copie MinIO après chaque
génération, et ne comparer les temps que lorsque les trois moteurs lisent
le même stockage, avec le cache froid puis le cache chaud annoncés
séparément.
