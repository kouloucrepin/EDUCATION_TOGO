# Dashboard Éducation Togo — Données Ouvertes

**Source :** https://opendata.gouv.tg — Ministère de l'Enseignement Primaire et Secondaire / INSEED / Banque Mondiale / UNESCO  
**Producteur :** Ministère de l'Enseignement Primaire et Secondaire (MEPS) / INSEED  
**Dernière mise à jour :** Variable selon le jeu de données (2024-2026)  
**Licence :** Open Data / Creative Commons Attribution 4.0

---

## Structure du répertoire

```
data/
├── README.md                           ← Ce fichier
├── 01-etablissements-scolaires.csv     (4.2 Mo)
├── 02-toilettes-scolaires.csv          (1.7 Mo)
├── 03-batiments-electrification.csv    (9.9 Mo)
├── 04-bibliotheques.csv                (3.6 Ko)
├── 05-professeurs-schema.csv           (3.0 Ko — schéma uniquement)
├── 06-education-resultats-scolaires.csv (37 Ko)
├── 07-sdg4-data-togo.csv               (260 Ko)
├── 08-taux-promotion-primaire-region.csv (11 Ko)
├── 09-admission-bepc-region-sexe.csv   (22 Ko)
├── 10-transition-primaire-secondaire.csv (16 Ko)
├── 11-adolescents-non-scolarises.csv   (5.3 Ko)
├── 12-statistiques-secondaire.csv      (12 Ko)
├── 13-enseignants-prescolaire-inspection.csv (27 Ko)
├── 14-projet-coso-education.csv        (152 Ko)
├── 15-projet-coso-education.geojson    (798 Ko)
└── 16-education-togo-banque-mondiale.csv (1.6 Mo)
```

---

## 01 — Établissements Scolaires (DES-TG)

**Fichier :** `01-etablissements-scolaires.csv`  
**Taille :** 4.2 Mo  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-etablissements-scolaires-au-togo/  
**Période :** 2022-2030 (collecte 2024)  
**Géométrie :** Point (lon/lat)  
**Lien direct :** [Télécharger](https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-etablissements-scolaires-au-togo/20241218-202046/file-etablissements-scolaires-18-12-2024-20-42-43.csv)

### Colonnes principales (168 au total)

| Champ | Description |
|-------|------------|
| `region_nom_bdd` | Région |
| `prefecture_nom_bdd` | Préfecture |
| `commune_nom_bdd` | Commune |
| `canton_nom_bdd` | Canton |
| `etablissement_nom` | Nom de l'établissement |
| `etablissement_categorie` | Catégorie (primaire, secondaire, etc.) |
| `etablissement_secteur` | Public / Privé |
| `etablissement_creation_date` | Année de création |
| `etablissement_reconnu` | Reconnu par l'État ? |
| `inspection_tutelle` | Inspection de tutelle |
| `classe_nbr` | Nombre total de classes |
| `eleve_nbr` | **Nombre total d'élèves** |
| `fille_nbr` | Nombre de filles |
| `garcon_nbr` | Nombre de garçons |
| `eleve_moinsquatre` à `eleve_dixhuit` | Élèves par âge |
| `etablissement_enseignant_nbr` | **Nombre total d'enseignants** |
| `prof_femme_nbr` | Enseignantes femmes |
| `prof_homme_nbr` | Enseignants hommes |
| `etablissement_enseignant_fct_nbr` | Enseignants fonctionnaires |
| `etablissement_enseignant_vne_nbr` | Enseignants volontaires VNE |
| `etablissement_enseignant_ape_nbr` | Enseignants volontaires APE |
| `personnel_nbr` | Total personnel |
| `personnel_femmme_nbr` | Personnel femmes |
| `elec_acces` | Accès à l'électricité ? |
| `elec_source` | Source (réseau/solaire/générateur) |
| `elec_qualite` | Qualité de l'accès |
| `toilette` | A des toilettes ? |
| `toilettes_nbr` | Nombre d'assises |
| `biblio` | A une bibliothèque ? |
| `salle_info` | A une salle informatique ? |
| `cantine` | A une cantine ? |
| `terrain_sport` | A un terrain de sport ? |
| `internet` | A un accès internet ? |
| `ordinateur_nbr` | Ordinateurs fixes |
| `ordinateurs_fonctionnel` | Ordinateurs fonctionnels |
| `laptop_nbr` | Ordinateurs portables |
| `tablette_nbr` | Tablettes |
| `rampe_handicape` | Rampes handicapés ? |
| `defis` | Problèmes/Difficultés |
| `solutions` | Solutions potentielles |
| `geometry` | Géométrie (Point) |

---

## 02 — Toilettes Scolaires (DEST-TG)

**Fichier :** `02-toilettes-scolaires.csv`  
**Taille :** 1.7 Mo  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-etablissements-scolaires-toilettes-au-togo/  
**Géométrie :** Point  
**Lien direct :** [Télécharger](https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-etablissements-scolaires-toilettes-au-togo/20241218-202710/file-etablissements-scolaires-toilettes-18-12-2024-20-45-49.csv)

### Colonnes (41)

| Champ | Description |
|-------|------------|
| `region_nom_bdd` | Région |
| `prefecture_nom_bdd` | Préfecture |
| `commune_nom_bdd` | Commune |
| `canton_nom_bdd` | Canton |
| `etab_nom` | Nom de l'établissement |
| `toilette_place` | Où se situent les toilettes ? |
| `toilette_type` | Type de sanitaires |
| `wc_nbr` | Nombre de WC |
| `wc_fonc_nbr` | WC fonctionnels |
| `latrine_nbr` | Nombre de latrines à eau |
| `latrine_fonc_nbr` | Latrines à eau fonctionnelles |
| `latrine_seche_nbr` | Nombre de latrines sèches |
| `latrine_seche_fonc_nbr` | Latrines sèches fonctionnelles |
| `douche_nbr` | Nombre de douches |
| `douche_fonc_nbr` | Douches fonctionnelles |
| `pissotiere_nbr` | Nombre de pissotières |
| `pissotiere_fonc_nbr` | Pissotières fonctionnelles |
| `mixite` | Séparation garçons/filles ? |
| `toilette_raccordage` | Type de raccordement |
| `fosse` | Présence d'une fosse ? |
| `toilette_etat` | État général |
| `toilette_utilisateur` | Qui utilise les toilettes ? |
| `geometry` | Point |

---

## 03 — Bâtiments / Statut d'Électrification (DESBSE-TG)

**Fichier :** `03-batiments-electrification.csv`  
**Taille :** 9.9 Mo (le plus volumineux)  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-etablissements-scolaires-batiments-statut-delectrification-au-togo/  
**Géométrie :** MultiPolygon   
**Lien direct :** [Télécharger](https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-etablissements-scolaires-batiments-statut-delectrification-au-togo/20241218-211936/file-etablissements-scolaires-batiments-statut-delectrification-18-12-2024-20-44-15.csv)

### Colonnes principales (71 au total)

| Champ | Description |
|-------|------------|
| `region_nom_bdd` | Région |
| `prefecture_nom_bdd` | Préfecture |
| `commune_nom_bdd` | Commune |
| `canton_nom_bdd` | Canton |
| `batiment_nom` | Nom du bâtiment |
| `batiment_type` | Matériau du bâtiment |
| `batiment_etat` | État du bâtiment |
| `batiment_construction` | En construction ? |
| `batiment_utilise` | Utilisé ? |
| `batiment_fonction` | Fonction du bâtiment |
| `etages_nbr` | Nombre d'étages |
| `salles_nbr` | **Nombre de salles de classe** |
| `salles_fnc` | **Salles fonctionnelles** |
| `bureau_nbr` | Nombre de bureaux |
| `bureau_fnc` | Bureaux fonctionnels |
| `elec_acces` | **Accès à l'électricité ?** |
| `elec_source` | Source (réseau/solaire/générateur) |
| `elec_qualite` | Qualité de l'accès |
| `elec_acces_temps` | Temps d'accès |
| `eau_acces` | Accès à l'eau ? |
| `eau_source` | Source d'eau |
| `eau_qualite` | Qualité de l'eau |
| `toiture_type` | Type de toiture |
| `mur_materiel` | Matériau du mur |
| `lavage_mains` | Dispositifs lavage de mains |
| `lavage_mains_nbr` | Nombre de dispositifs |
| `batiment_hygiene` | Hygiène du bâtiment |
| `geometry` | MultiPolygon |

---

## 04 — Bibliothèques Scolaires (DESB-TG)

**Fichier :** `04-bibliotheques.csv`  
**Taille :** 3.6 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-etablissements-scolaires-bibliotheques-au-togo/  
**Géométrie :** MultiPolygon  
**Lien direct :** [Télécharger](https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-etablissements-scolaires-bibliotheques-au-togo/20241218-211605/file-etablissements-scolaires-bibliotheques-18-12-2024-20-43-45.csv)

### Colonnes principales (62 au total)

| Champ | Description |
|-------|------------|
| `region_nom_bdd` | Région |
| `prefecture_nom_bdd` | Préfecture |
| `etablissement_nom` | Nom de la bibliothèque |
| `biblio_type` | Type de bibliothèque |
| `biblio_visiteur` | Visiteurs par jour |
| `biblio_pret_physique` | Prêts livres physiques/an |
| `biblio_pret_numer` | Prêts livres numériques/an |
| `biblio_abonnes` | Total abonnés |
| `biblio_abonnes_f` | Abonnées femmes |
| `biblio_abonnes_m` | Abonnés hommes |
| `biblio_employe_plein_f` | Employées plein temps |
| `biblio_employe_plein_m` | Employés plein temps |
| `batiment_eau` | Accès à l'eau ? |
| `batiment_electicite` | Accès à l'électricité ? |
| `batiment_telecom` | Accès internet ? |
| `accessibilite` | Rampes handicapés ? |
| `batiment_etat` | État du bâtiment |
| `defis` | Défis |
| `solutions` | Solutions |
| `geometry` | MultiPolygon |

---

## 05 — Professeurs (DESP-TG) — SCHÉMA UNIQUEMENT

**Fichier :** `05-professeurs-schema.csv`  
**Taille :** 3.0 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-etablissements-scolaires-professeurs-au-togo/  
**⚠️ Données privées — contacter le Ministère pour obtenir les données réelles**

### Colonnes du schéma (45)

| Champ | Description |
|-------|------------|
| `region_nom_bdd` | Région |
| `prefecture_nom_bdd` | Préfecture |
| `etablissement_nom` | Nom de l'établissement |
| `prof_genre` | Genre du professeur |
| `prof_presence` | Présent ? |
| `prof_secteur` | Secteur d'enseignement |
| `anciennete_prof` | Année début d'enseignement |
| `employe_position` | Catégorie d'employé |
| `contrat_type` | Type de contrat |
| `diplome_academique` | Diplôme académique |
| `diplome_professionel` | Diplôme professionnel |
| `matiere` | Matière(s) enseignée(s) |
| `prof_titulaire` | Professeur titulaire ? |
| `classes_nbr` | Nombre de classes titulaire |
| `technologie` | Possède outil tech ? |
| `livre` | Livres pédagogiques dispo ? |
| `challenges` | Problèmes rencontrés |

---

## 06 — Éducation et Résultats Scolaires (DERS-TG)

**Fichier :** `06-education-resultats-scolaires.csv`  
**Taille :** 37 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-leducation-et-les-resultats-scolaires-au-togo/  
**Période :** 2013-2022  
**Lien direct :** [Télécharger](https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-leducation-et-les-resultats-scolaires-au-togo/20250108-181843/observationdata-aqbqam.csv)

### Colonnes (6)

| Champ | Description | Exemple |
|-------|------------|---------|
| `indicateurs` | Nom de l'indicateur | `Nombre d'écoles`, `Nombre d'enseignants`, `Taux de scolarisation`, `Taux d'achèvement`, `Résultats examen`, `Dépenses éducation`, `Part du budget` |
| `niveau` | Niveau scolaire | `Total`, `Jardins d'enfants`, `Primaire`, `Collège`, `Lycée` |
| `secteur` | Secteur | `Total`, `Public`, `Autres (Privés, etc.)` |
| `Unit` | Unité | `Number`, `percentage` |
| `Date` | Année | 2013 → 2022 |
| `Value` | Valeur | (numérique) |

### Données clés incluses

- **Nombre d'écoles** par niveau et secteur (2013-2022)
- **Nombre d'enseignants** par niveau et secteur (2013-2022)
- **Dépenses annuelles d'éducation** (2013-2022)
- **Part du budget alloué à l'éducation** (%) (2013-2022)
- **Taux d'achèvement** par niveau (primaire, collège, lycée)
- **Résultats examen de compétence** par niveau
- **Taux de scolarisation** par niveau
- **Taux d'analphabétisme des adultes** (2017)

---

## 07 — Indicateurs d'Éducation UNESCO / SDG 4 (DIE-TG)

**Fichier :** `07-sdg4-data-togo.csv`  
**Taille :** 260 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-indicateurs-deducation-au-togo/  
**Producteur :** Humanitarian Data Exchange (UNESCO)  
**Période :** 1970-2023  
**Licence :** Creative Commons Attribution 4.0

### Colonnes

| Champ | Description |
|-------|------------|
| `#indicator+name` | Nom de l'indicateur ODD4 |
| `#indicator+code` | Code indicateur |
| `#date+year` | Année |
| `#country+name` | Pays |
| `#country+code` | Code pays |
| `#indicator+value+num` | Valeur |

### Autres fichiers du même dataset

| Fichier | Description |
|---------|------------|
| `sdg-metadata-tgo.csv` (787 Ko) | Métadonnées des indicateurs ODD4 |
| `sdg-indicatorlist-tgo.csv` (301 Ko) | Liste des indicateurs ODD4 |
| `qc-sdg-data-tgo.csv` (1.6 Ko) | Données réduites pour graphiques |
| `opri-data-tgo.csv` | Autres indicateurs politiques |
| `opri-indicatorlist-tgo.csv` (92 Ko) | Liste indicateurs politiques |
| `opri-metadata-tgo.csv` (260 Ko) | Métadonnées indicateurs politiques |
| `dse-data-tgo.csv` | Données démographiques et socio-économiques |
| `dse-indicatorlist-tgo.csv` | Liste indicateurs démographiques |
| `dse-metadata-tgo.csv` | Métadonnées démographiques |

---

## 08 — Taux de Promotion au Primaire par Région (DTPPR-TG)

**Fichier :** `08-taux-promotion-primaire-region.csv`  
**Taille :** 11 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-le-taux-de-promotion-au-primaire-par-region-au-togo/  
**Producteur :** INSEED  
**Période :** 2014-2019

### Colonnes (6)

| Champ | Description |
|-------|------------|
| `indicateur` | `Taux de Promotion au primaire par région (%)` |
| `région` | Togo, Lomé-Golfe, Maritime, Plateaux, Centrale, Kara, Savanes |
| `sexe` | Total / Masculin / Féminin |
| `Unit` | `%` |
| `Date` | 2014 → 2019 |
| `Value` | Taux de promotion |

---

## 09 — Admission au BEPC par Région et Sexe (DABEPCRS-TG)

**Fichier :** `09-admission-bepc-region-sexe.csv`  
**Taille :** 22 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-ladmission-au-bepc-par-region-et-par-sexe-au-togo/  
**Producteur :** INSEED  
**Période :** 2011-2022

### Colonnes (6)

| Champ | Description |
|-------|------------|
| `indicateur` | `Admission au BEPC par région et par sexe (%)` |
| `région` | Togo, Lomé-Golfe, Maritime, Plateaux, Centrale, Kara, Savanes (et Plateaux Ouest/Est en 2022) |
| `sexe` | Total / Masculin / Féminin |
| `Unit` | `%` |
| `Date` | 2011 → 2022 |
| `Value` | Taux d'admission |

---

## 10 — Taux de Transition Primaire / Secondaire 1 (DTTPS-TG)

**Fichier :** `10-transition-primaire-secondaire.csv`  
**Taille :** 16 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-le-taux-de-transition-primaire-secondaire-1-au-togo/  
**Producteur :** INSEED  
**Période :** 2014-2022

### Colonnes (6)

| Champ | Description |
|-------|------------|
| `indicateur` | `Taux de transition primaire/secondaire 1` |
| `région` | Togo, Lomé-Golfe, Maritime, Plateaux, Centrale, Kara, Savanes (et Plateaux Ouest/Est en 2022) |
| `sexe` | Total / Masculin / Féminin |
| `Unit` | `%` |
| `Date` | 2014 → 2022 |
| `Value` | Taux de transition |

---

## 11 — Adolescents Non Scolarisés — Banque Mondiale (DANS-TG)

**Fichier :** `11-adolescents-non-scolarises.csv`  
**Taille :** 5.3 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-adolescents-non-scolarises-au-togo/  
**Producteur :** Banque Mondiale  
**Période :** 1960-2023

### Colonnes (8)

| Champ | Description |
|-------|------------|
| `indicator` | `Adolescents out of school (% of lower secondary school age)` |
| `country` | `Togo` |
| `countryiso3code` | `TGO` |
| `date` | 1960 → 2023 |
| `value` | Pourcentage |
| `unit` | (vide) |
| `obs_status` | Statut observation |
| `decimal` | Décimales |

---

## 12 — Statistiques Brutes de l'Enseignement Secondaire (DSBES-TG)

**Fichier :** `12-statistiques-secondaire.csv`  
**Taille :** 12 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-les-statistiques-brutes-de-lenseignement-secondaire-au-togo/  
**Producteur :** INSEED  
**Période :** 2015-2017

### Colonnes (7)

| Champ | Description |
|-------|------------|
| `indicateur` | `Nombre Etablissements`, `Nombre de salles de classe`, `Nombre Elèves`, `Nombre Enseignants` |
| `secteur` | `Collège`, `Lycée` |
| `type-salle` | `Dur`, `Banco`, `Autres`, `Total` (pour salles de classe uniquement) |
| `region` | Togo + 6 régions (Golfe Lomé, Maritime, Plateaux, Centrale, Kara, Savanes) |
| `sexe` | Total / Masculin / Féminin |
| `Date` | 2015 |
| `Value` | Valeur numérique |

---

## 13 — Répartition des Enseignants du Préscolaire par Inspection (DREPIS-TG)

**Fichier :** `13-enseignants-prescolaire-inspection.csv`  
**Taille :** 27 Ko  
**Source :** https://opendata.gouv.tg/fr/datasets/donnee-ouverte-sur-la-repartition-des-enseignants-du-prescolaire-par-inspection-et-le-sexe-2021-2022/  
**Producteur :** INSEED  
**Période :** 2021-2022

### Colonnes (6)

| Champ | Description |
|-------|------------|
| `indicateur` | `Répartition des enseignants du préscolaire par inspection et le sexe, 2021-2022` |
| `inspections` | Nom de l'inspection (50 inspections couvrant tout le Togo : T.Général, T.R.Grand Lomé, Agoenyive, Lomé Centre, Maritime, Plateaux Est/Ouest, Centrale, Kara, Savanes, etc.) |
| `sexe` | Total / Masculin / Féminin |
| `Unit` | `Nombre` |
| `Date` | 2022 |
| `Value` | Nombre d'enseignants |

---

## 14 — Projet COSO — Infrastructures Éducation (PCISE-TG)

**Fichier :** `14-projet-coso-education.csv`  
**Taille :** 152 Ko  
**Fichier GeoJSON :** `15-projet-coso-education.geojson` (798 Ko)  
**Source :** https://opendata.gouv.tg/fr/datasets/projet-coso-infrastructures-du-secteur-de-leducation-au-togo/  
**Producteur :** Ministère du Développement à la Base  
**Période :** 2023-2026  
**Description :** 241 microprojets d'infrastructures scolaires dans les zones frontalières du nord du Togo

### Colonnes principales (70+)

| Champ | Description |
|-------|------------|
| `id` | Identifiant unique |
| `title` | Titre du projet |
| `type` | Type d'infrastructure |
| `subproject_type_designation` | Désignation du sous-projet |
| `sector` | Secteur |
| `works_type` | Type de travaux |
| `status` | Statut |
| `progress_percent` | Pourcentage d'avancement |
| `estimated_cost` | Coût estimé |
| `contract_amount_work_companies` | Montant contrat entreprises |
| `total_contract_amount_paid` | Total payé |
| `number_of_classrooms` | **Nombre de salles de classe** |
| `number_of_infrastructures` | Nombre d'infrastructures |
| `population` | Population |
| `direct_beneficiaries_men` | Bénéficiaires hommes |
| `direct_beneficiaries_women` | Bénéficiaires femmes |
| `location_name` | Nom de la localité |
| `latitude` | Latitude |
| `longitude` | Longitude |
| `hierarchy` | Hiérarchie administrative |
| `has_latrine_blocs` | A des blocs de latrines ? |
| `number_of_latrine_blocks` | Nombre de blocs de latrines |
| `has_fence` | A une clôture ? |
| `geometry` | Géométrie |

---

## 15 — Éducation Togo (DED-TG) — Banque Mondiale / HDX

**Fichier :** `16-education-togo-banque-mondiale.csv`  
**Taille :** 1.6 Mo  
**Source :** https://opendata.gouv.tg/fr/datasets/donnees-ouvertes-sur-leducation-au-togo/  
**Producteur :** Humanitarian Data Exchange / Banque Mondiale  
**Période :** 1960-2023  
**Licence :** Creative Commons Attribution 4.0

### Colonnes (6)

| Champ | Description |
|-------|------------|
| `Country Name` | `Togo` |
| `Country ISO3` | `TGO` |
| `Year` | 1960 → 2023 |
| `Indicator Name` | Nom de l'indicateur |
| `Indicator Code` | Code de l'indicateur |
| `Value` | Valeur |

### Indicateurs inclus (200+)

Barro-Lee (éducation population), dépenses publiques éducation, scolarisation (primaire, secondaire), achèvement, ratios élèves/enseignant, alphabétisation, etc.

---

## Recommandations d'utilisation

| Analyse | Datasets à croiser |
|---------|-------------------|
| **Couverture scolaire prioritaire** | 01 (établissements) + 03 (bâtiments/élec) + 02 (toilettes) |
| **Disparités régionales** | 08 (promotion) + 09 (BEPC) + 10 (transition) |
| **Investissements COSO** | 14 (projets) + 01 (écoles existantes dans le nord) |
| **Tendances long terme** | 06 (résultats 2013-2022) + 16 (BM 1960-2023) |
| **Genre** | 09 (BEPC par sexe) + 13 (enseignantes préscolaire) |
| **Abandon scolaire** | 11 (ados non scolarisés) + 10 (transition) |
| **ODD4** | 07 (indicateurs UNESCO) |
| **Enseignants** | 05 (professeurs — sur demande au Ministère) + 01 |
