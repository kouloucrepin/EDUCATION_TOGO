# Spécification Détaillée du Dashboard — 5 Onglets

---

## ONGLET 1 — Le Système Éducatif Togolais en Chiffres

**Objectif :** Donner au décideur une photographie instantanée de l'état du système

### Section A : KPI Dashboard (6 indicateurs vitaux)

Disposition : 2 rangées × 3 colonnes, chaque KPI dans une carte colorée

| KPI | Valeur 2022 | Évolution 2013→2022 | Format visuel |
|---|---|---|---|
| Achèvement Primaire | 88.7% | ↗ +11 pts | Jauge (0-100%) + sparkline |
| Achèvement Collège | 62.7% | ↗ +26 pts | Jauge + sparkline |
| Achèvement Lycée | 27.2% | ↗ +11 pts | Jauge **rouge** + sparkline |
| Scolarisation Préscolaire | 45.5% | ↗ +30 pts | Jauge + sparkline |
| Dépenses Annuelles Éducation | 195.5 Md FCFA | ↗ +81% | Barre de progression + sparkline |
| Part du Budget Éducation | 14.7% | **↘** −4.7 pts (vs pic 2021) | Jauge **rouge** + alerte |

### Section B : Entonnoir Éducatif (Sankey / Funnel)

Flux : `Primaire (100) → Collège (62.7) → Lycée (27.2)`

Affichage : Diagramme Sankey interactif avec :
- Largeur des flux proportionnelle aux effectifs
- Survole → "X% des élèves passent au niveau suivant"
- Couleur dégradée : vert (primaire) → orange (collège) → rouge (lycée)

Données : fichier 06 (`Taux d'achèvement ou de diplomation`)

### Section C : Dépenses vs Résultats (Scatter Plot Animé)

- Axe X : Part du budget alloué à l'éducation (%)
- Axe Y : Taux d'achèvement au collège (%)
- Animation : slider année (2013→2022)
- Taille des points : Dépenses totales
- Couleur : 3 scénarios (Primaire/Collège/Lycée)

Insight à faire ressortir : corrélation visible, et surtout le point 2022 où la part du budget chute sévèrement.

### Section D : Tableau des indicateurs (data table pliable)

Colonnes : Indicateur | Niveau | 2013 | 2015 | 2018 | 2022 | Tendance | Variation

Filtres : Niveau (Tous/Primaire/Collège/Lycée), Période (selector date range)

---

## ONGLET 2 — Carte Interactive des Écoles et Infrastructures

**Objectif :** Visualiser la couverture scolaire réelle sur le territoire

### Section A : Carte principale (Folium, plein écran)

**Couche 1 — Établissements scolaires (15 454 points)**
- Chaque point = une école
- Couleur par catégorie : Primaire (vert), Collège (orange), Lycée (rouge), Jardin maternelle (bleu)
- Clusterisation automatique (MarkerCluster) : points individuels à zoom>12, clusters sinon
- Popup au clic : Nom, Région, Préfecture, Catégorie, Inspection

**Couche 2 — Toilettes (10 228 points)**
- Icône spécifique (font awesome toilet)
- Couleur par type : Latrine sèche (marron), WC (bleu), Mixte (vert)
- Opacité réglable

**Couche 3 — Bâtiments (28 055 polygones)**
- Si geometry MultiPolygon disponible
- Couleur par fonction (salle de classe, bureau, etc.)

**Couche 4 — Projets COSO (241 points)**
- Taille du marqueur = coût estimé
- Couleur par statut : Réception provisoire (jaune), Réception définitive (vert), Contrat signé (bleu)
- Popup : Titre projet, type, nombre salles classes, latrines, avancement %

### Section B : Légende interactive

Toggle checkboxes pour activer/désactiver chaque couche. Slider transparence.

### Section C : Filtres latéraux

- Région (multiselect) → cascade Préfecture
- Catégorie d'établissement (primaire/secondaire/maternelle)
- Présence de terrain sport, cantine, etc. (si données disponibles dans geometry)
- Type de projet COSO (bâtiment primaire, latrines, clôture...)

### Section D : Compteurs dynamiques

Mise à jour en temps réel quand on applique un filtre :
- "XX écoles affichées sur 15 454"
- "XX projets COSO visibles"
- Ratio toilettes/écoles dans la zone filtrée

Données : fichiers 01, 02, 03, 04, 14

---

## ONGLET 3 — Comparateur Régional des Performances Scolaires

**Objectif :** Identifier les régions et préfectures en retard

### Section A : Heatmap (Région × Indicateur)

Matrice avec :
- Lignes : 6 régions (+ Togo national)
- Colonnes : Taux promotion primaire | Transition P→S | Admission BEPC | Scolarisation collège | Achèvement collège
- Cellules colorées : vert (bon) → jaune (moyen) → rouge (faible)
- Valeur affichée dans chaque cellule

Interactive : clic sur cellule → graphique d'évolution temporelle pour cette région + indicateur

### Section B : Radar Chart Comparatif

Selectbox "Région A" et "Région B" pour superposer 2 radars
Axes (6) : Scolarisation collège, Achèvement collège, Transition primaire/secondaire, Taux BEPC, Promotion primaire, Part des filles

### Section C : Graphiques d'Évolution par Région

Graphique en lignes multiples (6 régions + nationale)
Selecteur d'indicateur : Taux de transition / Taux BEPC / Taux de promotion
Slider année : 2014→2022
Highlight au survol d'une région

### Section D : Tableau de Classement des Régions

Colonnes : Rang | Région | Score composite | Transition P→S | BEPC | Tendance | Alerte

Score composite = moyenne pondérée :
- Transition 25%
- BEPC 25%
- Promotion primaire 20%
- Scolarisation collège 15%
- Achèvement collège 15%

Données : fichiers 06, 08, 09, 10

---

## ONGLET 4 — L'Écart Filles-Garçons dans l'Éducation

**Objectif :** Révéler les disparités de genre

### Section A : Évolution du Taux d'Admission BEPC par Sexe (2011-2022)

Graphique en lignes : 3 lignes (Total, Féminin, Masculin) + bande d'écart colorée entre F et M
Sélecteur région (dropdown). Par défaut : Togo entier.
Insight : L'écart se réduit-il ? Dans quelles régions les filles performent-elles mieux ?

### Section B : Écart F/M par Région (Bar Chart)

Barres groupées : chaque région = 2 barres (F/M) pour l'année sélectionnée
Slider année : 2011→2022
Barre d'écart en superposition (différence F-M en points de pourcentage)

### Section C : Carte Choroplèthe de l'Écart F/M

Fond de carte du Togo en 6 régions
Couleur = écart F/M au BEPC (année sélectionnée)
Rouge si écart > 5 points en défaveur des filles, vert si < 2 points

### Section D : Tableau de Bord Enseignantes du Préscolaire

- Carte des 70 inspections (taille = nombre d'enseignants)
- Pie chart : 91.8% femmes vs 8.2% hommes
- Top 10 inspections les plus féminisées
- Bar chart horizontal : répartition par grande région (T.Général, T.R.Grand Lomé, T.R.Centrale...)

Données : fichiers 09, 13

---

## ONGLET 5 — Où Investir Demain ? Prévisions et Priorités

**Objectif :** Guider la décision d'investissement avec des modèles

### Section A : Prévisions d'Achèvement 2023-2030 (Prophet)

3 graphiques en ligne (primaire, collège, lycée) :
- Points = historique réel (2013-2022)
- Ligne = prédiction Prophet
- Zone ombrée = intervalle de confiance à 80%
- 3 scénarios : tendanciel (bleu), budget+20% (vert), budget-10% (rouge)

Insight : Au rythme actuel, l'achèvement collège atteindrait ~75% en 2030 (loin de la cible ODD4 de 100%)

### Section B : Carte des Clusters de Préfectures

Carte Folium avec 39 préfectures colorées par cluster :
- Cluster vert : "Équipé" (bonnes performances, bonnes infrastructures)
- Cluster orange : "Sous-équipé" (manque d'écoles/infrastructures mais bon potentiel)
- Cluster rouge : "Prioritaire" (faibles résultats + sous-équipement)

Clique sur préfecture → popup avec profil : score, indicateurs clés, nombre d'écoles, distance au projet COSO le plus proche

### Section C : Matrice de Décision — Top 10 Préfectures Prioritaires

Tableau classé par score de vulnérabilité :

| Rang | Préfecture | Région | Score | Transition | BEPC | Projets COSO | Recommandation |
|---|---|---|---|---|---|---|---|
| 1 | Tône | Savanes | 62.1 | 66.9% | 48.9% | 1 | Construire 3 écoles + latrines |
| 2 | Kpendjal | Savanes | 64.3 | 70.2% | 51.3% | 1 | Programme alimentation scolaire |
| 3 | Oti | Savanes | 65.8 | 68.1% | 55.0% | 2 | Bourses filles + cantines |
| 4 | Tchamba | Centrale | 67.2 | 65.4% | 58.7% | 0 | Infrastructures + recrutement |
| 5 | Haho | Plateaux | 68.9 | 67.3% | 62.1% | 0 | Électrification + cantines |
| ... | ... | ... | ... | ... | ... | ... | ... |

### Section D : Scénarios Budgétaires (What-If Simulator)

Sliders interactifs :
- "Budget éducation 2025 : __% du budget national" (12-25%)
- "Nouvelles salles de classe construites : __" (0-500)
- "Projets latrines : __" (0-200)

Résultat simulé en temps réel :
- "Achèvement collège estimé 2030 : XX%"
- "Élèves supplémentaires scolarisés : XX"
- "Investissement nécessaire : XX milliards FCFA"

Données : fichiers 06, 07, 14, 16 + modèles Prophet + clustering

---

## Récapitulatif des Filtres Globaux

Applicables à tout le dashboard (sidebar) :

| Filtre | Type | Valeurs |
|---|---|---|
| Année | Slider | 2013-2022 (ou 1960-2023 pour onglet 5) |
| Région | Multiselect | 6 régions + nationale |
| Niveau scolaire | Dropdown | Primaire / Collège / Lycée / Préscolaire / Tous |
| Sexe | Dropdown | Total / Féminin / Masculin |
| Source de données | Checkbox | INSEED / Banque Mondiale / UNESCO |

---

## Références Croisées des Fichiers

| Onglet | Fichiers utilisés |
|---|---|
| 1. Le Système Éducatif en Chiffres | 06, 07, 16 |
| 2. Carte Interactive | 01, 02, 03, 04, 14 (geometry) |
| 3. Comparateur Régional | 06, 08, 09, 10, 12 |
| 4. Écart Filles-Garçons | 09, 13 |
| 5. Où Investir Demain ? | 06, 07, 14, 16 + modèles |
