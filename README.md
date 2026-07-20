---
title: Education Togo
emoji: 🎓
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# 🎓 Dashboard Éducation Togo

Tableau de bord de pilotage du système éducatif togolais (2013–2022), avec **assistant IA** et **indice de vulnérabilité des infrastructures**. Construit pour le **Défi Togo AI Lab**.

> Données ouvertes • Interface bilingue FR/EN • Mode clair/sombre • Déployé avec Docker sur Railway.

---

## ✨ Fonctionnalités

**4 onglets d'analyse**

| # | Onglet | Contenu |
|---|--------|---------|
| 1 | **Vue d'ensemble nationale** | 6 KPI sur 10 ans (jauges), entonnoir éducatif (100 → 63 → 27), lien budget ↔ résultats |
| 2 | **Cartographie des infrastructures** | Carte thématique (région/préfecture/commune), carte des points, **tableau filtrable + export CSV**, projets COSO |
| 3 | **Performances & Parité** | Matrice région × indicateur, courbes d'évolution, parité filles-garçons au BEPC, carte de l'écart |
| 4 | **Recommandations** | 6 recommandations chiffrées (constat · actions · indicateur de suivi) |

**En plus**
- 🤖 **Assistant IA** conversationnel (Google Gemini) : répond en langage naturel, **calcule sur les données en streaming**.
- 🛡️ **Indice de vulnérabilité infrastructures** (composite, validé par ACP) — affiché par défaut sur la carte et le tableau, du niveau commune à la région.
- 📄 3 documents PDF téléchargeables (note méthodologique, rapport d'analyse, note sur l'indice) + aperçu intégré.
- 🔄 Bouton « Actualiser les données » (retélécharge depuis opendata.gouv.tg).

---

## 📁 Structure du projet

```
.
├── app.py                  # Application Flask (routes, contexte, i18n FR/EN)
├── Dockerfile              # Image de déploiement (gunicorn, port 7860)
├── requirements.txt        # Dépendances Python
│
├── modules_visu/           # Logique métier + visualisations, par onglet
│   ├── onglet1/            #   vue d'ensemble (KPI, entonnoir, scatter)
│   ├── onglet2/            #   cartographie (carte, thématique, tableau, indice, COSO)
│   ├── onglet3/            #   performances & parité (heatmap, score composite, BEPC)
│   └── onglet4/            #   parité / préscolaire (fusionné dans l'onglet 3)
│
├── agent_ia/               # Assistant IA (routage → outils pandas → réponse)
├── connaissance_ia/        # Base de connaissances de l'agent (glossaire, schémas, règles)
│
├── templates/              # Gabarits Jinja (accueil.html, dashboard.html)
├── static/                 # CSS, images, PDF téléchargeables
│
├── data/                   # 16 jeux de données sources (CSV)
├── data_togo/              # Frontières GeoJSON (régions, préfectures, communes)
├── scripts/                # Utilitaires (update_data.py : rafraîchissement des données)
│
├── notebooks/              # Exploration (indice de vulnérabilité — ACP)  ⚠️ non déployé
├── docs/                   # Documentation projet (guide données, spec, relations)
└── archive/                # Anciens scripts / mockups (conservés, non utilisés)
```

---

## 🚀 Lancer en local

```bash
pip install -r requirements.txt

# Clé de l'assistant IA (optionnelle mais requise pour le chat)
echo "GEMMA_API_KEY=votre_cle_google_gemini" > .env

python app.py         # http://127.0.0.1:7860
```

> Sans `GEMMA_API_KEY`, tout fonctionne sauf l'assistant IA (qui bascule sur des réponses locales).

### Déploiement (Docker / Railway)

```bash
docker build -t education-togo .
docker run -p 7860:7860 -e GEMMA_API_KEY=... education-togo
```

Sur **Railway**, définir `GEMMA_API_KEY` dans les variables d'environnement du service.

---

## 📊 Données (16 sources)

Registre géolocalisé (établissements, toilettes, bâtiments, bibliothèques — extraction **18/12/2024**), résultats scolaires 2013–2022 (INSEED/MEPS), admission au BEPC 2011–2022, projets COSO, indicateurs Banque mondiale (séries longues jusqu'à 1960) et UNESCO (ODD4).

Sources : `opendata.gouv.tg` · `geodata.gouv.tg` · INSEED · MEPS · Banque mondiale · UNESCO · Projet COSO.

Détail des fichiers et de leur schéma : [`docs/GUIDE_DONNEES.md`](docs/GUIDE_DONNEES.md) et [`connaissance_ia/CATALOGUE_SCHEMAS.yml`](connaissance_ia/CATALOGUE_SCHEMAS.yml).

---

## 🧱 Stack technique

Flask · pandas · geopandas · pyecharts (ECharts) · folium (Leaflet) · Google Gemini (assistant) — servi par gunicorn dans un conteneur Docker.

---

## 📄 Documents

- **Note méthodologique** — `static/pdf/Methodologie_Dashboard_Education_Togo.pdf`
- **Rapport d'analyse** — `static/pdf/Rapport_Analyse_Education_Togo.pdf`
- **Note sur l'indice de vulnérabilité** — `static/pdf/Indice_Vulnerabilite_Infrastructures.pdf`
- **Notebook d'exploration** de l'indice — `notebooks/indice_vulnerabilite_infrastructures.ipynb`
