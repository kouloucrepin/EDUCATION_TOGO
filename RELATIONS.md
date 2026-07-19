# Relations entre les Fichiers — Vers une Base de Données Unifiée

## Problème : 16 fichiers, 16 schémas différents, pas de clé commune

Chaque fichier a été exporté depuis une vue différente. Il n'existe **aucune clé étrangère explicite** entre eux. Les seuls ponts possibles sont :
1. **Hiérarchie administrative** (région → préfecture → canton)
2. **Année** (Date/Year)
3. **Nom d'établissement** (approximatif)
4. **Géométrie** (spatial join)

---

## Analyse Granularité par Fichier

| Fichier | Nb lignes | Grain | Clé primaire candidate |
|---|---|---|---|
| 01 Établissements | 15 454 | **Établissement** (point) | FID |
| 02 Toilettes | 10 228 | **Équipement toilette** (point) | FID |
| 03 Bâtiments | 28 055 | **Bâtiment** (point/polygone) | FID |
| 04 Bibliothèques | 11 | **Bibliothèque** (point) | FID |
| 06 Résultats | 481 | **Région × Année × Indicateur × Niveau × Secteur** | composite |
| 07 SDG4 | 6 101 | **Pays × Année × Indicateur ODD4** | composite |
| 08 Promotion primaire | 126 | **Région × Année × Sexe** | composite |
| 09 BEPC | 255 | **Région × Année × Sexe** | composite |
| 10 Transition | 192 | **Région × Année × Sexe** | composite |
| 11 Ados non scolarisés | 64 | **Pays × Année** | composite |
| 12 Secondaire stats | 154 | **Région × Secteur × Indicateur** (2015) | composite |
| 13 Préscolaire | 210 | **Inspection × Sexe** (2022) | composite |
| 14 COSO | 241 | **Projet d'infrastructure** | `id` |
| 16 BM Éducation | 17 224 | **Pays × Année × Indicateur** | composite |

---

## Relations Identifiées

### Relation A — Spatiale : Établissements ↔ Toilettes ↔ Bâtiments ↔ Bibliothèques

```
[01 Établissements] ---[commune_nom_bdd, canton_nom_bdd]--- [02 Toilettes]
        |                                                         |
        +---[commune_nom_bdd, canton_nom_bdd]--- [03 Bâtiments] -+
        |
        +---[commune_nom_bdd, canton_nom_bdd]--- [04 Bibliothèques]
```

**Problème :** Pas d'ID établissement commun. 01 a `etablissement_nom`, 02 a `etab_nom`, 04 a `etablissement_nom`. Les noms sont souvent différents ou ambigus.

**Solution possible :**
```sql
-- Jointure approximative par le nom (risque d'erreur)
SELECT e.*, t.toilette_type
FROM etablissements e
LEFT JOIN toilettes t 
  ON e.region_nom_bdd = t.region_nom_bdd 
  AND e.prefecture_nom_bdd = t.prefecture_nom_bdd
  AND e.nom_localite = t.etab_nom  -- approché

-- Meilleure solution : jointure spatiale
SELECT e.*, t.toilette_type
FROM etablissements e
LEFT JOIN toilettes t 
  ON ST_DWithin(e.geometry, t.geometry, 50)  -- 50 mètres
```

### Relation B — Temporelle : Résultats × Promotion × BEPC × Transition

Tous partagent la dimension **Région × Année × Sexe** :

```
[06 Résultats]          [08 Promotion]
    | région, Date,         | région, Date, sexe
    | indicateur niveau     |
    ↓                       ↓
[09 BEPC]               [10 Transition]
    | région, Date, sexe     | région, Date, sexe
```

**Jointure possible :**
```sql
-- Vue consolidée région × année
SELECT 
  r.région, r.Date, r.sexe,
  r.Value AS taux_promotion_primaire,
  b.Value AS taux_admission_bepc,
  t.Value AS taux_transition
FROM promotion r
JOIN bepc b ON r.région = b.région AND r.Date = b.Date AND r.sexe = b.sexe
JOIN transition t ON r.région = t.région AND r.Date = t.Date AND r.sexe = t.sexe
```

### Relation C — Hiérarchique : Fichiers 01/06/08/09/10 ↔ Fichier 16 (BM)

**Problème de granularité :**
- 01 utilise 5 régions (`Maritime`, `Plateaux`, `Centrale`, `Kara`, `Savanes`)
- 08/09/10 utilisent 7 régions (`Togo`, `Lomé-Golfe`, `Maritime`, `Plateaux`, `Centrale`, `Kara`, `Savanes`)
- 16 est au niveau **pays** (Togo uniquement)

**Table de passage des régions nécessaire :**
```sql
dim_region = {
  'Maritime (01)': ['Lomé-Golfe', 'Maritime'],  -- split !
  'Plateaux (01)': ['Plateaux'],
  'Centrale (01)': ['Centrale'],
  'Kara (01)': ['Kara'],
  'Savanes (01)': ['Savanes']
}
```

### Relation D — Spatiale : COSO (14) ↔ Établissements (01)

Les 241 projets COSO ont `latitude`/`longitude` + `location_name` + `hierarchy`.

```sql
-- Association projet ↔ école existante dans la même localité
SELECT c.*, COUNT(e.FID) AS ecoles_proximite
FROM coso c
LEFT JOIN etablissements e
  ON ST_DWithin(
    ST_SetSRID(ST_MakePoint(c.longitude, c.latitude), 4326),
    e.geometry,
    2000  -- 2 km
  )
GROUP BY c.id
```

---

## Schéma en Étoile (Star Schema) Proposé

```
┌─────────────────────────────────────────────────────┐
│                 DIM_TIME                             │
│  year (PK)                                           │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────┐
│                      │                               │
│  ┌───────────────────┴───┐     ┌───────────────────┐ │
│  │   FACT_RESULTS         │     │  FACT_LONG_TERM   │ │
│  │  region (FK)           │     │  year (FK)         │ │
│  │  year (FK)             │     │  indicator (FK)    │ │
│  │  niveau (FK)           │     │  value              │ │
│  │  sexe (FK)             │     └───────────────────┘ │
│  │  indicateur_code (FK)  │                           │
│  │  value                 │     ┌───────────────────┐ │
│  └────────────────────────┘     │  FACT_COSO         │ │
│                                 │  project_id (PK)   │ │
│  ┌────────────────────────┐     │  region (FK)        │ │
│  │  FACT_INFRASTRUCTURE   │     │  classrooms         │ │
│  │  etab_id (PK)          │     │  latrines           │ │
│  │  region (FK)           │     │  status             │ │
│  │  has_toilet            │     │  cost               │ │
│  │  toilet_type           │     └───────────────────┘ │
│  │  has_library           │                           │
│  │  building_count        │     ┌───────────────────┐ │
│  │  geometry              │     │  FACT_TEACHERS     │ │
│  └────────────────────────┘     │  inspection (FK)   │ │
│                                 │  sexe (FK)         │ │
│  ┌────────────────────────┐     │  count              │ │
│  │  DIM_REGION             │     └───────────────────┘ │
│  │  region_id (PK)         │                           │
│  │  region_name            │     ┌───────────────────┐ │
│  │  prefecture             │     │  DIM_SEXE          │ │
│  │  commune                │     │  sexe_id (PK)      │ │
│  │  canton                 │     │  sexe_label        │ │
│  └────────────────────────┘     └───────────────────┘ │
│                                                       │
│  ┌────────────────────────┐     ┌───────────────────┐ │
│  │  DIM_LEVEL              │     │  DIM_INDICATOR     │ │
│  │  niveau_id (PK)         │     │  indicator_code(PK)│ │
│  │  niveau_label           │     │  indicator_name    │ │
│  │  secteur                │     │  source            │ │
│  └────────────────────────┘     │  unit              │ │
│                                 └───────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## Code de Construction (Python)

```python
import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path('data')

# 1. Charger les fichiers de base
etabs = pd.read_csv(DATA / '01-etablissements-scolaires.csv')
toilettes = pd.read_csv(DATA / '02-toilettes-scolaires.csv')
batiments = pd.read_csv(DATA / '03-batiments-electrification.csv')
biblio = pd.read_csv(DATA / '04-bibliotheques.csv')

# 2. Créer dim_region depuis les noms uniques des établissements
dim_region = (
    etabs[['region_nom_bdd', 'prefecture_nom_bdd', 'commune_nom_bdd', 'canton_nom_bdd']]
    .drop_duplicates()
    .reset_index(drop=True)
    .rename(columns={
        'region_nom_bdd': 'region',
        'prefecture_nom_bdd': 'prefecture',
        'commune_nom_bdd': 'commune',
        'canton_nom_bdd': 'canton'
    })
)
dim_region.index.name = 'region_id'

# 3. Créer fact_infrastructure
# Regroupement spatial via (region, prefecture, commune)
fact_infra = etabs[['FID', 'region_nom_bdd', 'prefecture_nom_bdd',
                    'commune_nom_bdd', 'etablissement_nom', 'geometry',
                    'etablissement_categorie']].copy()

# Compter les toilettes par zone
toilet_count = toilettes.groupby(
    ['region_nom_bdd', 'prefecture_nom_bdd', 'commune_nom_bdd']
).agg(
    toilette_count=('FID', 'count'),
    toilette_types=('toilette_type', lambda x: x.mode().iloc[0] if not x.mode().empty else None)
).reset_index()

# Compter les bâtiments par zone
bati_count = batiments.groupby(
    ['region_nom_bdd', 'prefecture_nom_bdd', 'commune_nom_bdd']
).size().reset_index(name='batiment_count')

# 4. Consolider les indicateurs temporels
resultats = pd.read_csv(DATA / '06-education-resultats-scolaires.csv')
promotion = pd.read_csv(DATA / '08-taux-promotion-primaire-region.csv')
bepc = pd.read_csv(DATA / '09-admission-bepc-region-sexe.csv')
transition = pd.read_csv(DATA / '10-transition-primaire-secondaire.csv')

# Standardiser les noms de régions
MAPPING_REGIONS = {
    'Lomé-Golfe': 'Maritime',
    'Togo': 'Togo',
}

# Pivoter en format large pour chaque indicateur
fact_results = promotion.merge(
    bepc, on=['région', 'Date', 'sexe'],
    suffixes=('_promotion', '_bepc')
).merge(
    transition, on=['région', 'Date', 'sexe']
)
```

---

## Contraintes et Limitations

| Relation | Problème | Solution |
|---|---|---|
| 01 ↔ 02 ↔ 03 ↔ 04 | Pas d'ID commun entre établissement et ses équipements | **Spatial join** (ST_DWithin) ou clé composite (region + préfecture + commune) |
| 01 vs 08/09/10 | Maritime (01) inclut Lomé, alors que 08/09/10 les séparent | Table de mapping manuelle ou regroupement |
| 05 (Professeurs) | Données privées, schéma uniquement | Impossible à intégrer sans demande ministère |
| 06 vs 08/09/10 | 06 utilise des niveaux (`Primaire`, `Collège`...), 08 utilise des indicateurs spécifiques | Union via `indicateur` normalisé |
| 07 (SDG4) vs 16 (BM) | Les deux sont long-format pays×année×indicateur | Peuvent être fusionnés par `year` + normalisation des noms d'indicateurs |
| 13 (Préscolaire) | Grain "inspection", pas de lien direct aux régions | Mapping manuel inspection→région (70 inspections connues) |
