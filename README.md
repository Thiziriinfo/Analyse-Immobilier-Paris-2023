# 🏠 Analyse du marché immobilier parisien — DVF 2023

## Objectif
Analyser les transactions immobilières à Paris en 2023 à partir des données publiques DVF (Demandes de Valeurs Foncières) publiées par data.gouv.fr.

## Questions auxquelles répond ce projet
- Comment ont évolué les prix au m² sur l'année 2023 ?
- Quels arrondissements sont les plus chers / les plus accessibles ?
- Comment les prix varient-ils selon le nombre de pièces ?
- Quelle est la distribution géographique des transactions ?

## Stack technique
`Python` · `pandas` · `Plotly` · `Google Colab`

## Données
- **Source :** [data.gouv.fr — Demandes de Valeurs Foncières](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)
- **Périmètre :** Paris (département 75), année 2023
- **Volume final :** 30 741 transactions après nettoyage

## Résultats clés
- Baisse de **6.9%** du prix médian sur l'année (10 746€ → 10 000€/m²)
- Écart de **72%** entre le 6e arrondissement (15 250€/m²) et le 19e (8 838€/m²)
- Distribution asymétrique : médiane (10 377€/m²) plus représentative que la moyenne (11 526€/m²)

## Auteure
**Thiziri Abchiche** — [GitHub](https://github.com/Thiziriinfo)
