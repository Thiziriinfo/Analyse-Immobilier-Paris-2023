# 🏠 Analyse du Marché Immobilier Parisien — DVF 2023

**Dashboard interactif sur les transactions immobilières à Paris en 2023 — données réelles, 30 000+ transactions**

👉 **[Voir le dashboard en live](https://analyse-immobilier-paris-2023-q8bg29uahcojkerqbstyxu.streamlit.app/)**

---

## Pourquoi ce projet ?

L'immobilier parisien est l'un des marchés les plus scrutés de France — et pourtant, la plupart des analyses disponibles se limitent à des prix moyens par arrondissement. Ce projet va plus loin : exploiter les données brutes DVF (Demandes de Valeurs Foncières) publiées par l'État pour répondre aux vraies questions que se posent acheteurs, investisseurs et vendeurs en 2023.

Avec une correction de -3 à -5 % après le pic de 2022, le marché parisien traversait une période charnière. Ce dashboard permet de la comprendre, la mesurer, et en tirer des décisions concrètes.

---

## Ce que le dashboard permet de faire

**6 pages, chacune avec un objectif précis :**

- **Vue du Marché** — KPIs globaux, évolution mensuelle des prix, saisonnalité, répartition appartements / maisons
- **Carte & Arrondissements** — Carte interactive des 30 000+ transactions colorées par prix/m², comparatif arrondissements, analyse volume vs prix
- **Profil des Biens** — Impact de la surface et du nombre de pièces sur le prix/m², tableau pivot par segment de marché
- **Simulation Investissement** — Le cœur du projet pour un investisseur : simuler un rendement locatif selon son budget, visualiser le coût réel d'acquisition (frais notaire, agence, travaux), projeter la valeur de son bien sur 10 ans
- **Explorateur SQL** — Interroger les données en direct avec du SQL (CTEs, window functions, NTILE, RANK, pivots conditionnels) sur un échantillon de 15 000 transactions chargé en mémoire
- **Tendances & Prévisions** — Historique des prix 2014–2023, projections 2024–2026, radar comparatif 5 arrondissements, positionnement de Paris parmi les grandes métropoles européennes

---

## Stack technique

| Outil | Usage |
|-------|-------|
| Python / Pandas | Chargement et nettoyage des données DVF |
| Streamlit | Interface web interactive multi-pages |
| Plotly | Visualisations (line, bar, scatter, mapbox, violin, waterfall, radar) |
| SQLite (in-memory) | Base de données pour l'explorateur SQL |
| data.gouv.fr | Source de données brutes DVF en temps réel |
| GitHub + Streamlit Cloud | Déploiement continu |

---

## Les données

Les données proviennent directement du **registre officiel des transactions immobilières françaises** (DVF — Demandes de Valeurs Foncières), publié par la DGFiP via data.gouv.fr.

- **Source :** [data.gouv.fr — DVF 2023](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)
- **Périmètre :** Paris — département 75, année 2023
- **Volume brut → nettoyé :** ~37 000 lignes → **30 741 transactions** après suppression des valeurs aberrantes (prix < 1 500 €/m² ou > 50 000 €/m², surfaces < 9 m²)
- **Types retenus :** Appartements et maisons uniquement

Les données de loyers de référence (simulation investissement) sont issues de l'**Observatoire des Loyers de Paris 2023**.

---

## Requêtes SQL incluses

Le dashboard embarque 9 requêtes analytiques dans l'explorateur SQL :

- `GROUP BY` — Prix médian et amplitude par arrondissement
- `LAG` — Variation mensuelle des prix (YoY)
- `RANK` + `DENSE_RANK` — Double classement prix / volume
- `CTE` imbriquée — Arrondissements au-dessus de la moyenne parisienne
- Rolling moyenne 3 mois — Window function `ROWS BETWEEN`
- `NTILE` — Quartiles locaux et parisiens par arrondissement
- Pivot conditionnel — Prix Appartement vs Maison par arrondissement (`CASE WHEN`)
- Score composite normalisé — Min-max sur accessibilité + liquidité

---

## Résultats clés

- **-3,2 %** de baisse du prix médian vs 2022 — correction post-pic confirmée
- **Écart de 73 %** entre le 6e arrondissement (~15 000 €/m²) et le 19e (~8 700 €/m²)
- **Studios < 30 m²** : prix/m² systématiquement plus élevés que les grands appartements (prime de liquidité)
- **Meilleur rendement locatif brut** : 19e, 20e, 18e (autour de 2,8–3,0 %)
- **Paris vs Europe** : 2e marché le plus cher après Londres, mais rendements parmi les plus bas (2,5 %)

---

## Structure du projet

```
├── app.py              # Application Streamlit principale (6 pages)
├── requirements.txt    # Dépendances Python
└── README.md           # Ce fichier
```

Les données DVF sont chargées dynamiquement depuis data.gouv.fr au démarrage — aucun fichier CSV à embarquer dans le repo.

---

## Lancer le projet en local

```bash
git clone https://github.com/Thiziriinfo/Analyse-Immobilier-Paris-2023
cd Analyse-Immobilier-Paris-2023
pip install -r requirements.txt
streamlit run app.py
```

Le premier chargement prend 15–20 secondes (téléchargement et nettoyage du fichier DVF compressé).

---

## Ce que j'ai appris

Ce projet m'a montré qu'un jeu de données brutes comme le DVF peut raconter des histoires très différentes selon l'angle d'analyse. Partir du prix médian seul, c'est passer à côté de l'essentiel — la distribution asymétrique, l'effet taille sur le prix/m², les dynamiques de volume qui signalent les marchés en mouvement.

La page simulation investissement a été la plus intéressante à construire : pas juste afficher un rendement, mais recréer le raisonnement complet d'un investisseur — du budget brut au coût réel d'acquisition, jusqu'à la projection patrimoniale.

---

