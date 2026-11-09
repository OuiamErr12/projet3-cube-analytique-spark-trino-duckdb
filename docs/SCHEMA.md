# Schéma du modèle analytique

Schéma en étoile. `fact_sales` est au centre. Les dimensions portent les
libellés utilisés par les KPI. Les contraintes de clés ne sont pas imposées
par Parquet ; elles sont contrôlées par les tests.

```mermaid
erDiagram
    dim_date ||--o{ fact_sales : "date_key"
    dim_region ||--o{ fact_sales : "region_id"
    dim_product ||--o{ fact_sales : "product_id"
    dim_channel ||--o{ fact_sales : "channel_id"

    fact_sales {
        bigint sale_id PK
        bigint order_id
        int date_key FK
        int region_id FK
        int product_id FK
        int channel_id FK
        smallint quantity
        decimal unit_price
        decimal sales_amount
    }
    dim_date {
        int date_key PK
        date full_date
        smallint calendar_year
        smallint quarter
        smallint month
        string month_name
        string date_month
    }
    dim_region {
        int region_id PK
        string region_name
        string country
    }
    dim_product {
        int product_id PK
        string product_name
        string category
        decimal unit_price
    }
    dim_channel {
        int channel_id PK
        string channel_name
    }
```

## Lecture décisionnelle

| Question | Requête | Axes |
|---|---|---|
| CA, commandes et panier moyen du pilotage mensuel | `monthly_kpis.sql` | mois, région, catégorie |
| Sous-totaux et total général | `cube.sql` | les 8 niveaux du `CUBE` |
| Le même pilotage, avec le canal de vente | `channel_kpis.sql` | mois, région, catégorie, canal |

Le grain d'une commande est plus haut que le grain du fait : une commande a
une date, une région et un canal, et une ou plusieurs catégories. C'est pour
cela que `COUNT(DISTINCT order_id)` et le panier moyen ne s'additionnent pas
le long de la catégorie.
