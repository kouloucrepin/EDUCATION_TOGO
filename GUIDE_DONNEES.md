# Guide des Données — Quel fichier pour quel élément du Dashboard ?

> **Objectif :** savoir exactement quel fichier de `data/` alimente chaque KPI, tableau, graphique et carte du dashboard, avec les colonnes et filtres à appliquer, et pourquoi cet élément est utile.
>
> **Dashboard :** `dashboard-mockup.html` · **Pipeline :** `data-pipeline.py` → `dashboard-data.json`

---

## 1. Vue d'ensemble des fichiers

| Fichier | Contenu | Lignes | Utilisé dans |
|---|---|---|---|
| `01-etablissements-scolaires.csv` | 15 454 écoles géolocalisées (Point) | 15 455 | Onglet 2 (carte) |
| `02-toilettes-scolaires.csv` | 10 228 toilettes géolocalisées (Point) | 10 229 | Onglet 2 (carte) |
| `03-batiments-electrification.csv` | 28 055 bâtiments (MultiPolygon) | 28 056 | Onglet 2 (carte, optionnel) |
| `04-bibliotheques.csv` | 11 bibliothèques seulement | 12 | Onglet 5 (recommandation n°3) |
| `05-professeurs-schema.csv` | ⚠️ Schéma seul — données privées | 46 | Non utilisable en l'état |
| `06-education-resultats-scolaires.csv` | Indicateurs nationaux 2013-2022 | 482 | Onglets 1 et 5 (cœur du dashboard) |
| `07-sdg4-data-togo.csv` | Indicateurs ODD4 UNESCO 1970-2023 | 6 102 | Complément (cibles ODD4) |
| `08-taux-promotion-primaire-region.csv` | Promotion primaire par région 2014-2019 | 127 | Onglet 3 |
| `09-admission-bepc-region-sexe.csv` | BEPC par région ET par sexe 2011-2022 | 256 | Onglets 3 et 4 |
| `10-transition-primaire-secondaire.csv` | Transition P→S par région 2014-2022 | 193 | Onglets 3 et 5 |
| `11-adolescents-non-scolarises.csv` | % ados hors école 1960-2023 (BM) | 65 | Complément (abandon scolaire) |
| `12-statistiques-secondaire.csv` | Effectifs bruts secondaire 2015 | 155 | Complément (ratios) |
| `13-enseignants-prescolaire-inspection.csv` | Enseignants préscolaire par inspection | 211 | Onglet 4 |
| `14-projet-coso-education.csv` | 241 microprojets COSO (tabulaire) | 244 | Onglets 2 et 5 |
| `15-projet-coso-education.geojson` | Les mêmes 241 projets, géolocalisés | 241 features | Onglet 2 (carte) |
| `16-education-togo-banque-mondiale.csv` | 200+ indicateurs BM 1960-2023 | 17 225 | Onglet 5 (prévisions longues) |

--- 

## 2. ONGLET 1 — « En chiffres » (vision macro)

Tout cet onglet repose sur **un seul fichier : `06-education-resultats-scolaires.csv`**.

Ses 6 colonnes : `indicateurs`, `niveau`, `secteur`, `Unit`, `Date`, `Value`. On filtre toujours `secteur = "Total"`.

### 2.1 Les 6 cartes KPI (+ sparklines)

| KPI | Filtre dans le fichier 06 | Utilité |
|---|---|---|
| Achèvement primaire (88,7 %) | `indicateurs = "Taux d'achèvement ou de diplomation"` + `niveau = "Primaire"` | Mesure si les enfants **finissent** le cycle (≠ y être inscrits) |
| Achèvement collège (62,7 %) | idem + `niveau = "Collège"` | Le niveau qui progresse le plus vite (+26 pts) — à surveiller |
| Achèvement lycée (27,2 %) | idem + `niveau = "Lycée"` | **Le point noir du système** — justifie l'alerte rouge |
| Scolarisation préscolaire (45,5 %) | `indicateurs = "Taux de scolarisation"` + `niveau = "Jardins d'enfants"` | Le préscolaire conditionne la réussite future ; ×3 en 10 ans |
| Dépenses éducation (195,5 Md) | `indicateurs = "Dépenses annuelles d'éducation"` | Montre l'effort financier en valeur absolue |
| Part du budget (14,7 %) | `indicateurs = "Part du Budget alloué à l'éducation (%)"` | **L'alerte politique** : chute de 19,4 % → 14,7 % en un an |

Les **sparklines** utilisent la série complète 2013-2022 de chaque indicateur (`Date` de 2013 à 2022).

> ⚠️ Préscolaire et Dépenses ne sont disponibles que pour certaines années — le dashboard interpole entre 2013 / 2018 / 2022 (valeurs préfixées « ≈ »).

### 2.2 Entonnoir éducatif (100 → 63 → 27 élèves)

- **Fichier :** `06` — les 3 taux d'achèvement (primaire, collège, lycée) de l'année sélectionnée.
- **Utilité :** le visuel le plus parlant pour un décideur — sur 100 enfants au primaire, seuls 27 finissent le lycée. Il désigne l'endroit où le système « perd » ses élèves.

### 2.3 Scatter « Budget vs Résultats » (trajectoire 2013→2022)

- **Fichier :** `06` — croisement de deux indicateurs par année : `Part du Budget…` (axe X) × `Taux d'achèvement collège` (axe Y).
- **Utilité :** démontre la **corrélation budget/performance** et met en évidence le recul budgétaire de 2022 (point rouge). C'est l'argument central pour la recommandation « budget à 20 % ».

### 2.4 Tableau « Indicateurs détaillés »

- **Fichier :** `06` — toutes les lignes, colonnes pivotées en 2013 / 2018 / 2022.
- **Utilité :** la vue de référence pour vérifier chaque chiffre du dashboard ; exportable en CSV.

---

## 3. ONGLET 2 — « Carte interactive »

### 3.1 Carte principale (Leaflet)

| Couche | Fichier | Colonnes à utiliser | Utilité |
|---|---|---|---|
| Établissements | `01-etablissements-scolaires.csv` | `geometry` (Point), `region_nom_bdd`, `prefecture_nom_bdd`, `etablissement_categorie`, `inspection_tutelle` | Visualiser la **couverture scolaire réelle** : Maritime concentre 43 % des écoles, Savanes 11,7 % |
| Toilettes | `02-toilettes-scolaires.csv` | `geometry`, `toilette_type`, `region_nom_bdd`, `etab_nom` | Révéler le déficit sanitaire : ratio toilettes/écoles ≈ 0,66 |
| Bâtiments (option) | `03-batiments-electrification.csv` | `geometry` (MultiPolygon), `batiment_fonction`, `batiment_annee` | État du bâti scolaire (fichier lourd : 9,9 Mo — à charger à la demande) |
| Projets COSO | `15-projet-coso-education.geojson` | `geometry`, `type`, `current_status_of_the_site`, `estimated_cost`, `number_of_classrooms`, `number_of_latrine_blocks`, `hierarchy` | Voir **où l'État investit déjà** pour éviter les doublons et cibler les zones oubliées |

> ⚠️ **Pièges connus :**
> - L'export réel du fichier 01 ne contient que **15 colonnes** (pas de `eleve_nbr` ni `etablissement_enseignant_nbr` malgré le schéma du README). Les effectifs élèves/enseignants ne sont donc PAS disponibles par école.
> - Dans le GeoJSON 15, seuls **86 projets sur 241** ont de vraies coordonnées (68 sont à [0,0], 87 sans géométrie). Toujours filtrer les coordonnées nulles.
> - Le mockup actuel affiche des cercles agrégés par région : c'est le backend qui devra servir les 15 454 points individuels (avec clustering type MarkerCluster).

### 3.2 Les 4 KPI compacts (à droite de la carte)

| KPI | Fichier | Calcul |
|---|---|---|
| 15 454 établissements | `01` | Nombre de lignes |
| 10 228 toilettes | `02` | Nombre de lignes |
| 86 / 241 projets géolocalisés | `15` | Features avec coordonnées valides / total |
| 385 salles construites | `14` | Somme de `number_of_classrooms` |

### 3.3 Graphiques COSO (types et statuts)

- **Fichier :** `14-projet-coso-education.csv`
- **Bar chart types :** comptage par `type` (89 bâtiments primaire, 81 latrines, 27 clôtures, 23 préscolaire, 13 CEG, 5 lycées, 1 bibliothèque…).
- **Donut statuts :** comptage par `status` (123 réception provisoire, 57 définitive, 33 remise communauté, 15 technique, 11 achevés, 2 signés).
- **Utilité :** montre que l'investissement COSO porte sur l'infrastructure de base du primaire, et que **seulement 11 % des projets sont réellement achevés** — un signal sur la vitesse d'exécution.

---

## 4. ONGLET 3 — « Comparateur régional »

Trois fichiers régionaux au même format (`indicateur`, `région`, `sexe`, `Unit`, `Date`, `Value`) — on filtre `sexe = "Total"` :

| Élément | Fichier(s) | Filtres | Utilité |
|---|---|---|---|
| **Heatmap Région × Indicateur** | `08` (promotion), `10` (transition), `09` (BEPC) + `06` (scolarisation collège, nationale) | Dernière année dispo par fichier : promotion = **2019**, transition/BEPC = 2022 | Une seule vue pour repérer la région en difficulté sur tous les fronts → **Savanes** |
| **Radar comparateur (2 régions)** | `08` + `09` + `10` (+ estimations pour achèvement/préscolaire régionaux) | `région ∈ {Togo, Lomé-Golfe, Maritime, Plateaux, Centrale, Kara, Savanes}` | Comparer le **profil complet** de 2 régions (ex. Savanes vs Kara) pour argumenter un arbitrage |
| **Courbes de transition P→S** | `10-transition-primaire-secondaire.csv` | Série 2014-2022 par région | La transition est le **prédicteur d'abandon scolaire** : Savanes s'effondre de 86 % (2015) à 66,9 % (2022) |
| **Classement score composite** | `08` + `09` + `10` + `06` | Score = transition 25 % + BEPC 25 % + promotion 20 % + scolarisation 15 % + achèvement 15 % | Un chiffre unique par région pour **prioriser** : Kara 81,1 · Savanes 65,8 |

> ⚠️ **Pièges connus :**
> - Le fichier 08 s'arrête en **2019** — ne pas présenter la promotion comme une donnée 2022.
> - En 2022, la région Plateaux est scindée en **Plateaux Ouest / Plateaux Est** dans les fichiers 09 et 10 — harmoniser avant de comparer aux années antérieures.
> - « Lomé-Golfe » (fichiers régionaux) ≠ « Maritime » (fichier 01, qui inclut Lomé) — attention aux jointures.

---

## 5. ONGLET 4 — « Filles vs Garçons »

| Élément | Fichier | Filtres / colonnes | Utilité |
|---|---|---|---|
| **KPI Filles 61,1 % / Garçons 67,0 % / Écart 5,9 pts** | `09-admission-bepc-region-sexe.csv` | `région = "Togo"`, `sexe = "Féminin"` puis `"Masculin"`, `Date = 2022` (référence 2011 pour l'évolution) | Quantifier l'inégalité de genre à l'examen clé du secondaire |
| **Courbes F/M 2011-2022 (avec bande d'écart)** | `09` | `région = "Togo"`, séries par `sexe` | Montrer que l'écart se **réduit** (10,6 → 5,9 pts) mais ne se ferme pas — argument pour poursuivre les politiques d'inclusion |
| **Barres écart par région (2022)** | `09` | `Date = 2022`, groupé par `région` × `sexe` | Cibler géographiquement : **Plateaux Ouest (-9,8) et Savanes (-9,7)** justifient les bourses filles |
| **Donut enseignants préscolaire (91,8 % femmes)** | `13-enseignants-prescolaire-inspection.csv` | Ligne `inspections = "T.Général"` par `sexe` | Révèle la féminisation extrême du secteur (**7 802** enseignants : 7 164 F / 638 H) |
| **Top 10 inspections** | `13` | Tri décroissant de `Value` avec `sexe = "Total"`, **en excluant `T.Général` et `T.R.*`** | Voir la concentration des effectifs locaux (Agoè-Nyivé, Lomé) pour rééquilibrer les affectations |

> ⚠️ **Piège majeur du fichier 13 — triple comptage :** le fichier est hiérarchique à 3 niveaux. `T.Général` (7 802) = somme des totaux régionaux `T.R.*` (7 802) = somme des inspections locales (7 802). **Additionner toutes les lignes donne 23 406, soit exactement 3× le vrai total.** Pour un total national : prendre la ligne `T.Général`. Pour un classement d'inspections : exclure `T.Général` et `T.R.*`. (Le `data-pipeline.py` actuel fait cette erreur — champ `enseignants_prescolaire.total` à corriger.)

---

## 6. ONGLET 5 — « Investir demain »

| Élément | Fichier(s) | Usage | Utilité |
|---|---|---|---|
| **Prévisions 2023-2030 (Prophet + IC 80 %)** | `06` (achèvement collège 2013-2022) + `16` (séries longues 1960-2023 pour caler la tendance) | Entraîner Prophet/ARIMA sur l'historique, générer 3 scénarios (tendanciel / +20 % budget / -10 %) | Passer du constat à la **projection** : au rythme actuel on atteint 69 % en 2030, loin de la cible ODD4 |
| **Carte des clusters (39 préfectures)** | `01` (densité d'écoles/préfecture) + `02` (toilettes) + `03` (électricité) + `09`/`10` (résultats) + `14` (présence COSO) | K-Means/HDBSCAN sur des features par préfecture → 3 clusters (prioritaire / sous-équipé / équipé) | Transformer 5 fichiers en **une décision géographique** : où construire en premier |
| **Simulateur budgétaire** | `06` (relation budget↔achèvement) + `14` (coûts réels : ~30-40 M FCFA par bâtiment scolaire) | Calibrer le modèle linéaire du frontend avec la régression budget/résultats | Donner au décideur un outil « et si ? » avec des ordres de grandeur crédibles |
| **Top 10 préfectures prioritaires** | Résultat du clustering + `09` + `10` + `14` | Score de vulnérabilité par préfecture, nombre de projets COSO existants | La **matrice de décision finale** : Tône, Kpendjal, Oti en tête |
| **Recommandation « 50 bibliothèques »** | `04-bibliotheques.csv` | 11 lignes seulement dans tout le pays | La donnée choc : les bibliothèques sont quasi inexistantes |

---

## 7. Fichiers complémentaires (pas encore dans le dashboard)

| Fichier | Ce qu'il apporte | Où l'utiliser |
|---|---|---|
| `07-sdg4-data-togo.csv` | Indicateurs ODD4 officiels UNESCO (colonnes réelles : `indicator_id`, `year`, `value`) | Ajouter les **cibles ODD4** en ligne de référence sur les graphiques d'achèvement |
| `11-adolescents-non-scolarises.csv` | % d'ados hors école (Banque Mondiale, série longue) | Renforcer l'onglet 5 : un KPI « adolescents exclus » du système |
| `12-statistiques-secondaire.csv` | Effectifs élèves/enseignants/salles du secondaire (2015) | Calculer des **ratios élèves/enseignant** et élèves/salle par région |
| `05-professeurs-schema.csv` | Schéma seul — données à demander au Ministère | Si obtenu : carte de la qualité d'encadrement (diplômes, contrats) |

---

## 8. Récapitulatif express

```
Onglet 1 (macro)        →  06                    (+ 16 en renfort)
Onglet 2 (carte)        →  01 + 02 + 15          (+ 03 optionnel, 14 pour les graphiques)
Onglet 3 (régions)      →  08 + 09 + 10          (+ 06 pour le score)
Onglet 4 (genre)        →  09 + 13
Onglet 5 (prévisions)   →  06 + 16 + 14 + clustering(01,02,03,09,10)  + 04 (bibliothèques)
```

**Règle d'or :** pour tout indicateur régional, vérifier d'abord (1) la dernière année réellement disponible, (2) le découpage Plateaux Ouest/Est en 2022, (3) la distinction Lomé-Golfe vs Maritime, et (4) l'existence réelle des colonnes dans l'export CSV (le README de `data/` décrit parfois des colonnes absentes de l'export).
