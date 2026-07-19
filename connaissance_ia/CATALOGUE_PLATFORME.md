# Catalogue plateforme — Dashboard Éducation Togo

Plateforme web de pilotage du système éducatif togolais (2013-2022), construite pour le Défi Togo AI Lab
à destination des décideurs (ministère, partenaires, public). Flask + pyecharts + folium, bilingue FR/EN,
alimentée par 16 jeux de données ouvertes (INSEED, MEPS, Banque Mondiale, UNESCO, projets COSO).

## Rôle

Son rôle : **montrer où agir**. Le Togo a réalisé 10 ans de collecte de données éducatives, mais elles
restent dispersées dans 16 fichiers difficiles à croiser. La plateforme les unifie pour transformer
ces chiffres bruts en décisions : **où** investir en priorité (quelle région, quelle préfecture, quelle
commune), **sur quoi** (infrastructures, rétention au collège, parité, budget) et **avec quelles preuves**
(chaque constat est traçable jusqu'au fichier source). Elle sert trois usages : le pilotage par le
ministère (territoires en décrochage, suivi des investissements COSO), la redevabilité envers les
partenaires (Banque Mondiale, UNESCO) et l'information du public.

## Les quatre vues

Chaque vue part d'un constat chiffré et mène à une action possible :
1. **Vue d'ensemble nationale** — 6 KPI avec tendance 10 ans, entonnoir éducatif (100 élèves au primaire
   → 63 achèvent le collège → 27 le lycée), lien budget ↔ résultats (chute à 14,7 % du budget en 2022).
2. **Cartographie des infrastructures** — 15 454 écoles et 10 228 toilettes en clusters, cartes thématiques
   par région/préfecture/commune, 241 microprojets COSO ciblant le nord.
3. **Disparités régionales** — matrice région × indicateur, comparateur de profils (radar), classement par
   score composite : les Savanes décrochent sur tous les indicateurs.
4. **Parité filles-garçons** — écart au BEPC par région depuis 2011 (5,9 pts en 2022, était 10,6),
   préscolaire féminisé à 91,8 %.

L'assistant IA intégré répond aux questions chiffrées via ces mêmes données (voir CATALOGUE_SCHEMAS.yml).
