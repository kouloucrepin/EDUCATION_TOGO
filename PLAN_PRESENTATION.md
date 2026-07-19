# Plan Stratégique de Présentation — Dashboard Éducation Togo

**Contexte :** Défi Togo AI Lab — Cartographie scolaire et identification des territoires prioritaires d'investissement  
**Auteur :** Analyse statistique et data-scientifique des 16 jeux de données ouverts  
**Période couverte :** 1960-2023 (selon les datasets)  
**Stack recommandé :** Python (pandas, geopandas, scikit-learn, statsmodels) → Streamlit + Plotly + Folium

---

## Architecture de la Présentation

Le récit doit suivre une logique de **pyramide inversée** :
1. **Vision macro** → Où en est l'éducation au Togo ?
2. **Diagnostic territorial** → Où sont les disparités ?
3. **Analyse causale** → Pourquoi ces écarts ?
4. **Prescription** → Où et comment investir ?

---

## PARTIE 1 — VISION MACRO (2013-2022)

### 1.1 Tableau de bord des indicateurs clés (KPI Dashboard)

| Indicateur | 2013 | 2022 | Tendance | Alerte |
|---|---|---|---|---|
| Taux d'achèvement primaire | 77.7% | 88.7% | ↗ | 🟢 |
| Taux d'achèvement collège | 36.6% | 62.7% | ↗ | 🟡 |
| Taux d'achèvement lycée | 16.3% | 27.2% | ↗ | 🔴 |
| Scolarisation préscolaire | 15.8% | 45.5% | ↗ | 🟡 |
| Dépenses éducation (Md FCFA) | 108.2 | 195.5 | ↗ | 🟢 |
| Part budget éducation | 13.8% | 14.7% | ↘ **pic 2021: 19.4%** | 🔴 |

**Visualisation :** Jauge / Bullet chart pour chaque KPI + sparkline tendance 10 ans  
**Interactivité :** Filtre par année (slider 2013-2022), sélecteur d'indicateur

### 1.2 Pyramide du système éducatif (Entonnoir)

```
Primaire: 115% scolarisation → 88.7% achèvement
    ↓
Collège: 77% scolarisation → 62.7% achèvement
    ↓
Lycée: 34.5% scolarisation → 27.2% achèvement
```

**Visualisation :** Sankey diagram (flux d'élèves par niveau) ou funnel chart  
**Insight clé :** Perte massive au passage collège→lycée. Sur 100 élèves au primaire, seulement 27 achèvent le lycée.

### 1.3 Dépenses vs Résultats (Scatter animé)

**Visualisation :** Scatter plot animé (année par année) avec en X la part du budget éducation, en Y le taux d'achèvement collège, taille = dépenses totales  
**Insight :** Corrélation claire entre budget et performance — la chute 2021→2022 (19.4%→14.7%) est un signal d'alarme immédiat

---

## PARTIE 2 — DIAGNOSTIC TERRITORIAL

### 2.1 Carte choroplèthe interactive — Achèvement et transition par région

**Calques superposables :**
- Taux d'achèvement primaire par région
- Taux de transition primaire→secondaire
- Taux d'admission au BEPC
- Taux de promotion au primaire

**Visualisation :** Folium/GeoPandas avec 6 régions + découpage Plateaux Est/Ouest (2022)  
**Interactivité :** Hover → valeur + tendance, clic → popup avec série temporelle

### 2.2 Classement des régions — Score Composite de Vulnérabilité Éducative

**Construction du score :** Moyenne pondérée de :
- Taux d'achèvement collège (poids 30%)
- Taux de transition primaire→secondaire (poids 25%)
- Taux d'admission BEPC (poids 25%)
- Taux de scolarisation (poids 20%)

**Résultats attendus :**

| Rang | Région | Score | Priorité |
|---|---|---|---|
| 1 | Savanes | ⚠️ Faible | **URGENT** |
| 2 | Plateaux | ⚠️ Faible | **Prioritaire** |
| 3 | Centrale | ⚠️ Moyen | À surveiller |
| 4 | Maritime | ✅ Moyen | Renforcement |
| 5 | Kara | ✅ Bon | Maintien |
| 6 | Lomé-Golfe | ✅ Bon | Maintien |

**Visualisation :** Heatmap + Radar chart par région (6 axes = 6 indicateurs)  
**Interactivité :** Clic sur région → affiche le radar détaillé

### 2.3 Carte des établissements scolaires (15 454 points)

**Calques :**
- Points = écoles, colorés par catégorie (primaire, secondaire, jardin)
- Couche chaleur (heatmap) pour densité scolaire
- Clusterisation à faible zoom

**Insight :** Maritime (43% des écoles) concentre la majorité, Savanes (11.7%) et Centrale (11%) sont sous-équipées

**Visualisation :** Folium avec MarkerCluster + HeatMap  
**Interactivité :** Filtre par région, catégorie, inspection tutelle → popup avec détails

### 2.4 Toilettes et bâtiments — Carte des infrastructures

**Calques :**
- Toilettes (10 228 points) → colorés par type (latrine sèche vs WC)
- Bâtiments (28 055 polygones) → colorés par fonction

**Insight :** Ratio toilettes/écoles ~0.66 — 1/3 des écoles sans données toilettes  
**Visualisation :** Dual-layer Folium avec toggle

---

## PARTIE 3 — ANALYSE CAUSALE ET CROISEMENTS

### 3.1 Genre : Écart filles/garçons par région

**Données :** Fichier 09 (BEPC par sexe, 2011-2022) + 08 (promotion primaire par sexe)

**Visualisation :** Grouped bar chart ou connected scatter — chaque région = 2 lignes (F/M)  
**Insight :** L'écart se creuse dans certaines régions. Savanes : BEPC 48.9% (vs 65% moyenne nationale).  
**Interactivité :** Sélecteur d'année + highlight région au clic

### 3.2 Analyse des COSO — 241 microprojets dans le nord

**Données :** Fichier 14 (84 colonnes, 241 lignes)

**KPI Projets :**
- **Total salles de classes construites :** 385
- **Total blocs latrines :** 337
- **Coût estimé total :** 4.44 milliards FCFA
- **Avancement moyen :** 32.3% — 57% des projets en réception provisoire, 33% en réception définitive

**Visualisation :**
- Carte Folium des 241 projets (taille = coût, couleur = statut)
- Bar chart horizontal : type de projet (89 bâtiments primaire, 81 latrines, 27 clôtures...)
- Treemap : coût par type d'infrastructure
- Gauge : % d'avancement global

**Interactivité :** Filtre par type, statut, tranche de coût  
**Insight :** Investissement concentré sur le primaire (89/241 projets). Seulement 5 projets lycées, 1 bibliothèque, 1 bloc administratif.

### 3.3 Distribution des enseignants du préscolaire

**Données :** Fichier 13 (70 inspections, 2021-2022)

**KPI :** 23 406 enseignants dont 91.8% de femmes  
**Concentration :** T. Général (7 802) + T.R. Grand Lomé (1 710) = 40% des effectifs

**Visualisation :**
- Bar chart horizontal (top 20 inspections)
- Carte de chaleur par inspection
- Pie chart genre

### 3.4 Analyse long terme — Banque Mondiale (1960-2023)

**Données :** Fichier 16 (17 224 lignes, 837 indicateurs, 1960-2023)

**Visualisation :**
- Time series interactif avec sélecteur d'indicateur
- Corrélogramme entre indicateurs clés (ex: dépenses éducation vs achèvement)
- Ligne de tendance avec prédiction Prophet pour 2023-2030

**Insight :** 837 indicateurs disponibles — sélectionner les ~20 pertinents pour l'éducation

---

## PARTIE 4 — MODÈLES PRÉDICTIFS ET ML

### 4.1 Prévision des taux d'achèvement (Prophet / ARIMA)

**Objectif :** Projeter 2023-2030 pour chaque niveau (primaire, collège, lycée)  
**Données :** 06 (2013-2022) + 16 (1960-2023)

**Visualisation :**
- Line chart (historique + prédiction avec intervalle de confiance)
- 3 scénarios : tendanciel, optimiste (+20% budget), pessimiste (statu quo)

**Indicateurs à modéliser :**
- Taux d'achèvement primaire, collège, lycée
- Taux de scolarisation par niveau
- Part du budget éducation

### 4.2 Clustering des préfectures (K-Means / HDBSCAN)

**Objectif :** Segmenter les 39 préfectures en clusters homogènes pour cibler les interventions

**Features candidates (à construire à partir des données disponibles) :**
- Ratio établissements/population (par préfecture)
- Densité de toilettes
- Taux d'accès à l'électricité (via bâtiments)
- Proximité des projets COSO
- Résultats BEPC et transition

**Visualisation :**
- Carte colorée par cluster (Folium)
- Radar chart du profil de chaque cluster
- Table des centroïdes

**Résultat attendu :** 3-4 clusters identifiés : "Zones vertes" (tout OK), "Zones sous-équipées" (manque d'infrastructures), "Zones en crise" (faibles résultats + sous-équipement)

### 4.3 Scoring prédictif d'abandon scolaire (Régression logistique / Random Forest)

**Objectif :** Identifier les facteurs prédictifs d'abandon (proxy : faible transition primaire→secondaire)

**Features :** Taux promotion, BEPC, toilettes, type bâtiments, budget régional  
**Target :** Binaire (transition < 70% = risque)

**Livrable :** Carte de risque Togo — chaque préfecture avec probabilité d'abandon

### 4.4 Analyse de l'impact des projets COSO (DiD / avant-après)

**Objectif :** Mesurer si les 241 projets COSO ont amélioré les indicateurs dans les zones nord  
**Méthode :** Différence-de-différences (avant 2023 vs après 2025) si données futures disponibles

---

## PARTIE 5 — RECOMMANDATIONS PRIORITAIRES

### 5.1 Matrice de décision : où investir ?

| Préfecture | Score vulnérabilité | Projets COSO | Ratio écoles/pop | Priorité |
|---|---|---|---|---|
| Tône (Savanes) | Très élevé | Oui (1 projet) | Faible | 🔴 URGENT |
| Kpendjal (Savanes) | Très élevé | Oui (1 projet) | Très faible | 🔴 URGENT |
| Oti (Savanes) | Élevé | Oui | Faible | 🟠 Prioritaire |
| Sotouboua (Centrale) | Élevé | Non | Moyen | 🟠 Prioritaire |
| Haho (Plateaux) | Élevé | Non | Moyen | 🟠 Prioritaire |
| ... | ... | ... | ... | ... |

**Visualisation :** Scatter plot (score vulnérabilité vs ratio écoles/pop) + bulles colorées par région  
**Interactivité :** Clic → fiche préfecture détaillée

### 5.2 Recommandations chiffrées

1. **Rehausser la part du budget éducation** à 20% (vs 14.7% en 2022) — chaque point de % = ~13 Md FCFA supplémentaires
2. **Construire 200+ salles de classe** dans les préfectures les plus sous-équipées (Savanes, Centrale)
3. **Déployer 50 bibliothèques scolaires** (vs 11 actuellement — quasi inexistantes)
4. **Généraliser l'accès à l'eau et aux toilettes** dans les 5 000+ écoles sans données sanitaires
5. **Programme préscolaire** dans les régions à faible scolarisation (<30% : Savanes, Kara rurale)
6. **Bourses filles** dans les préfectures où l'écart F/M au BEPC > 10 points

---

## SPÉCIFICATIONS TECHNIQUES DU DASHBOARD

### Stack
- **Backend :** Python (pandas, numpy, geopandas, scikit-learn, statsmodels, prophet)
- **Frontend :** Streamlit (multi-page)
- **Visualisation :** Plotly (charts interactifs) + Folium (cartes)
- **Déploiement :** Streamlit Cloud / Hugging Face Spaces

### Structure proposée (5 onglets)

```
1. Accueil / Macro
   - KPI Dashboard (6 jauges)
   - Sankey entonnoir éducatif
   - Scatter budget vs résultats

2. Carte interactive
   - Carte choroplèthe (régions)
   - Carte points (écoles, toilettes, bâtiments)
   - Carte COSO (projets)
   - Couches superposables avec légende

3. Disparités régionales
   - Heatmap région × indicateur
   - Radar comparatif (2 régions max)
   - Évolution temporelle par région

4. Analyse genre
   - Time series BEPC F/M par région
   - Écart filles-garçons
   - Enseignantes préscolaire

5. Modèles & Prévisions
   - Prophet (achèvement, scolarisation)
   - Clustering préfectures
   - Matrice de priorité
```

### Fonctionnalités interactives clés

| Fonction | Implémentation |
|---|---|
| Slider année | Plotly animation_frame + Streamlit slider |
| Filtre région | Streamlit multiselect → cascade sur préfectures |
| Filtre niveau | Primaire/Collège/Lycée/Préscolaire |
| Hover données | Plotly hovertemplate avec toutes les métriques |
| Click → détail | streamlit-plotly-events + popup Folium |
| Téléchargement | Export PNG des graphiques + CSV filtré |
| Mode comparaison | Selectbox "Comparer avec" → 2 régions superposées |

### Couleurs et charte

```python
# Palette Togo (drapeau + variantes)
COULEURS = {
    'Togo': '#006A4E',      # vert
    'Maritime': '#006A4E',
    'Plateaux': '#FFCE00',  # jaune
    'Centrale': '#EF3340',  # rouge
    'Kara': '#0033A0',      # bleu
    'Savanes': '#D4A017',   # or
    'Lomé-Golfe': '#00A86B'  # vert clair
}
```

---

## DATASETS UTILISÉS PAR ANALYSE

| Analyse | Datasets | Colonnes clés |
|---|---|---|
| KPI Dashboard | 06, 07, 16 | indicateurs, niveau, Date, Value |
| Cartes scolaires | 01, 02, 03, 04 | geometry, région, catégorie |
| Disparités régionales | 08, 09, 10, 12 | région, sexe, Date, Value |
| Genre | 09, 13 | sexe, région, Value |
| Infrastructures COSO | 14 | type, status, coût, avancement |
| Long terme | 16 | Indicator Name, Year, Value |
| Préscolaire | 13 | inspections, sexe, Value |
| Enseignants | 05 (schéma) + 01 | (données privées pour 05) |

---

## CALENDRIER DE CONSTRUCTION SUGGÉRÉ

| Phase | Durée | Livrable |
|---|---|---|
| 1. Import et nettoyage | 1 jour | Base de données consolidée |
| 2. Analyses univariées | 1 jour | Statistiques descriptives complètes |
| 3. Modèles ML | 2 jours | Prophet + Clustering + Scoring |
| 4. Dashboard core | 3 jours | Streamlit + Plotly + Folium |
| 5. Finalisation | 1 jour | Tests, export, déploiement |
| **Total** | **8 jours** | **Avant deadline 20 juillet 2026** |

---

## POINTS D'ATTENTION

1. **Données manquantes :** Fichier 05 (Professeurs) privé — nécessite une demande au Ministère
2. **Standardisation régions :** `Lomé-Golfe` ≠ `Maritime` dans les datasets régionaux vs fichier 01 (Maritime inclut Lomé)
3. **Bibliothèques :** Seulement 11 enregistrements — quasi inexistantes dans le système
4. **Élèves/enseignants dans 01 :** Colonnes non incluses dans l'export CSV malgré 168 colonnes dans le schéma
5. **Données 2019 pour le primaire :** Dernière année disponible pour le taux de promotion
