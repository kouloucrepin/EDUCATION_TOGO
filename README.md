---
title: Education Togo
emoji: 🎓
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# Dashboard Éducation Togo

Tableau de bord de pilotage du système éducatif togolais (2013-2022), construit pour le **Défi Togo AI Lab**.

## Contenu

- **Vue d'ensemble nationale** : 6 KPI avec tendance 10 ans, entonnoir éducatif (100 élèves → 63 collège → 27 lycée), lien budget ↔ résultats.
- **Cartographie des infrastructures** : 15 454 écoles et 10 228 toilettes en clusters, cartes thématiques par région / préfecture / commune, 241 projets COSO.
- **Disparités régionales** : matrice région × indicateur, comparateur de profils (radar), classement par score composite.
- **Parité filles-garçons** : écart au BEPC par région depuis 2011, féminisation du corps enseignant préscolaire.

Interface bilingue FR / EN, mode sombre, export PNG / CSV, note méthodologique en PDF.

## Stack

Flask · pyecharts (ECharts) · folium (Leaflet) · pandas — servi par gunicorn dans un conteneur Docker.

## Sources

INSEED · MEPS · Banque Mondiale · UNESCO · Projets COSO · opendata.gouv.tg
