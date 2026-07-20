"""Dashboard Éducation Togo - Application Flask.

Reproduit le dashboard mockup (4 premiers onglets) en s'appuyant sur les
packages de visualisation `modules_visu` (pyecharts / ECharts + folium).

Lancement :  python app.py  →  http://127.0.0.1:5000
"""
from pyecharts.globals import CurrentConfig

# assets.pyecharts.org a un certificat SSL expiré → on utilise jsdelivr
CurrentConfig.ONLINE_HOST = 'https://cdn.jsdelivr.net/npm/echarts@5/dist/'

import gzip
import html as html_std
import json
import os
import queue
import re
import threading
import time
from functools import lru_cache

from flask import Flask, Response, jsonify, render_template, request

import agent_ia
from modules_visu.embed import chart_fragment
from modules_visu import onglet1 as o1
from modules_visu import onglet2 as o2
from modules_visu import onglet3 as o3
from modules_visu import onglet4 as o4
from modules_visu.onglet3.config import REGIONS as REGIONS_O3
from modules_visu.onglet4.config import REGIONS_09_SIMPLE

app = Flask(__name__)

# Cache navigateur : 7 jours pour les fichiers statiques (css, images, js) —
# le CSS est versionné par mtime (voir _version_assets) donc jamais périmé.
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 60 * 60 * 24 * 7


@app.context_processor
def _version_assets():
    """Version du style.css basée sur sa date de modification : le navigateur
    peut cacher longtemps, toute mise à jour du fichier change l'URL."""
    try:
        v = int(os.path.getmtime(os.path.join(app.static_folder, 'css', 'style.css')))
    except OSError:
        v = 0
    return {'css_v': v}


@app.after_request
def _compression_gzip(reponse):
    """Compresse les réponses texte : les pages du dashboard embarquent leurs
    graphiques ECharts (jusqu'à ~200 Ko de HTML) et les cartes folium sont
    encore plus lourdes — le gzip divise le transfert par ~6."""
    compressible = (reponse.mimetype or '').startswith('text/') or \
        reponse.mimetype in ('application/json', 'application/javascript')
    if (not compressible
            or reponse.mimetype == 'text/event-stream'   # SSE : ne JAMAIS bufferiser
            or reponse.is_streamed                        # réponse générée en flux
            or reponse.direct_passthrough
            or reponse.status_code != 200
            or 'Content-Encoding' in reponse.headers
            or 'gzip' not in request.headers.get('Accept-Encoding', '').lower()):
        return reponse
    corps = reponse.get_data()
    if len(corps) < 1000:          # trop petit pour que ça vaille le coût CPU
        return reponse
    reponse.set_data(gzip.compress(corps, 6))
    reponse.headers['Content-Encoding'] = 'gzip'
    reponse.headers['Content-Length'] = str(len(reponse.get_data()))
    reponse.headers.setdefault('Vary', 'Accept-Encoding')
    return reponse

# ---------------------------------------------------------------------------
# Internationalisation FR / EN de l'habillage (les libellés internes des
# graphiques — légendes, axes — restent en français : ils viennent des données)
# ---------------------------------------------------------------------------
TRADUCTIONS = {
    'fr': {
        'nav1': "Vue d'ensemble nationale", 'nav2': 'Cartographie des infrastructures',
        'nav3': 'Performances & Parité',
        'nav5': 'Recommandations',
        'desc5': 'Ce que les données commandent de faire : six recommandations tirées des trois vues',
        'prio1': 'Priorité 1 · agir maintenant', 'prio2': 'Priorité 2 · structurer',
        'prio3': 'Priorité 3 · consolider',
        'reco_constat': 'Constat', 'reco_actions': 'Actions recommandées',
        'reco_suivi': 'Indicateur de suivi',
        'reco_side_note': 'Synthèse des enseignements des 3 vues — aucune donnée à filtrer ici.',
        'desc1': "État du système éducatif togolais : indicateurs clés, flux d'élèves et financement",
        'desc2': 'Couverture scolaire du territoire et investissements COSO',
        'desc3': 'Performances régionales, parité et personnel enseignant : vue complète',

        'filtres': "Filtres d'analyse", 'filtres_sub': "Affinez les données de l'onglet actif",
        'periode': 'Période', 'territoire': 'Territoire (drill-down)',
        'periode_pop': 'Période et population', 'terr_periode': 'Territoire et période',
        'annee_ref': 'Année de référence', 'annee': 'Année', 'region': 'Région',
        'prefecture': 'Préfecture', 'commune': 'Commune', 'sexe': 'Sexe',
        'region_bepc': 'Région (courbes BEPC)',
        'toutes_regions': 'Toutes les régions', 'toutes_prefs': 'Toutes les préfectures',
        'toutes_communes': 'Toutes les communes', 'derniere': 'Dernière disponible',
        'choisir_pref': "Choisissez d'abord une préfecture",
        'appliquer': 'Appliquer', 'sources': 'Sources', 'accueil': 'Accueil',
        'pdf_btn': 'Note méthodologique (PDF)',
        'rapport_btn': "Rapport d'analyse (PDF)", 'indice_btn': 'Indice de vulnérabilité (PDF)',
        'voir_pdf': 'Aperçu', 'telecharger': 'Télécharger', 'nouvel_onglet': 'Ouvrir dans un onglet', 'fermer': 'Fermer',
        'donnees_src': 'Données INSEED / MEPS', 'chargement': 'Chargement des données...',
        'tt_theme': 'Mode sombre / clair', 'tt_menu': 'Plier / déplier le menu',
        'tt_dl': 'Exporter (PNG ou CSV)', 'tt_dl_carte': 'Télécharger la carte en PNG',
        'tt_grandir': 'Agrandir', 'tt_lecture': 'Lecture',
        'c_entonnoir': "Le parcours scolaire : du primaire au lycée",
        'seg_entonnoir': 'Parcours', 'seg_evo_flux': 'Évolution 2013-2022',
        'seg_bud_lien': 'Lien', 'seg_bud_evo': 'Évolution',
        'c_budget': 'Budget et résultats scolaires',
        'c_evolution': 'Évolution 2013-2022 -',
        'evo_niveau': "Réussite par niveau", 'evo_secteur': "Écoles par secteur",
        'seg_niveau': 'Niveau', 'seg_secteur': 'Secteur',
        'c_tableau': 'Tous les chiffres clés',
        'tbl_paren': '(national 2013-2022 · régional 2014-2022)',
        'vue': 'Vue', 'national': 'National', 'par_region': 'Par région',
        'correlations': 'Corrélations',
        'c_carte_pts': 'Carte des écoles et des projets',
        'c_carte_thema': 'Carte thématique -', 'par': 'par',
        'carte_points': 'Points', 'carte_thema': 'Thématique', 'carte_tableau': 'Tableau',
        'c_tableau': 'Indicateurs par commune',
        'tab_variable': 'Variable', 'tab_priorite': 'Niveau de priorité', 'tab_toutes': 'Toutes', 'tab_afficher': 'Afficher', 'tab_telecharger': 'Télécharger (CSV)',
        'col_region': 'Région', 'col_prefecture': 'Préfecture', 'col_commune': 'Commune', 'col_annee': 'Année',
        'q1': 'Très prioritaire', 'q2': 'Prioritaire', 'q3': 'Modéré', 'q4': 'Performant', 'q5': 'Très performant',
        'i_tableau_indic': "Tableau des indicateurs d'infrastructure par commune (registre 2024). Choisissez une variable et un niveau de priorité : les communes sont classées et colorées par quintile (rouge = prioritaire, vert = performant ; inversé pour l'ancienneté).",
        'etablissements': 'Établissements', 'toilettes_lbl': 'Toilettes', 'terrain_sport': 'Terrain sport',
        'primaire_lbl': 'Primaire', 'college_lbl': 'Secondaire', 'lycee_lbl': 'Lycée',
        'biblio_lbl': 'Bibliothèque', 'electrifies_lbl': 'Bâtiments', 'par_ecole': '/école',
        'anciennete_lbl': 'Ancienneté moy.', 'ans': 'ans',
        'enseignants_lbl': 'Enseignants préscolaire', 'femmes_lbl': 'Femmes', 'hommes_lbl': 'Hommes',
        'coso_geo': 'Projets COSO géolocalisés', 'salles': 'Salles de classe (projets géolocalisés)',
        'coso_regions_lbl': 'Régions', 'coso_prefectures_lbl': 'Préfectures',
        'c_types_coso': 'Types de projets réalisés', 'geo_paren': 'projets géolocalisés',
        'c_statut': "Où en sont les projets ?",
        'type_projet': 'Type de projet', 'tous_types': 'Tous les types',
        'c_matrice': 'Comparatif des régions', 'derniere_annee': 'dernière année disponible',
        'tout_comparer': '- Tout comparer -',
        'toutes_label': 'toutes les régions', 'derniere_courte': 'dernière année',
        'c_transition': 'Évolution des résultats par région',

        'graphique': 'Graphique', 'tableau_ar': 'Tableau années × régions',
        'graphique_lbl': 'graphique', 'tableau_lbl': 'tableau',
        'c_bepc': 'Résultats BEPC : filles vs garçons',
        'c_ecart': 'Écart filles-garçons au BEPC',

        'k_filles': 'Filles au BEPC', 'k_garcons': 'Garçons au BEPC',
        'k_moyenne': 'Moyenne BEPC',
        'pts_depuis': 'pts depuis 2011',
        'etait': 'Était', 'en_2011': 'en 2011',

        'i_entonnoir': "L'entonnoir éducatif se resserre au fil des cycles : sur 100 élèves du primaire, seulement 63 atteignent le collège et 27 le lycée. Recommandation : investir massivement dans l'accès et le maintien au collège, principal point de fuite du système.",
        'i_budget': "La part du budget allouée à l'éducation a culminé à 19,4 % en 2021 avant de chuter à 14,7 % en 2022. Recommandation : sanctuariser au moins 18 % du budget pour préserver les acquis et atteindre les cibles ODD4.",
        'i_evolution': "Le taux d'achèvement du primaire plafonne à 88 % (2022), le collège progresse (+26 pts entre 2013 et 2022) mais reste sous 70 %, le lycée stagne sous 30 %. Recommandation : cibler les interventions sur le secondaire inférieur, maillon faible de la chaîne éducative.",
        'i_tableau': "Tableau de bord multi-indicateurs : choisissez entre vue nationale, vue régionale ou matrice de corrélation. Recommandation : utilisez la matrice pour identifier les leviers les plus corrélés à la réussite scolaire.",
        'i_carte_pts': "Carte interactive des 15 454 établissements avec couches superposables. Recommandation : activez la couche toilettes pour repérer les zones prioritaires d'investissement sanitaire.",
        'i_carte_thema': "Carte thématique des indicateurs agrégés par région ou préfecture, niveau commune en bulles. Recommandation : comparez la couverture en infrastructures entre régions pour guider l'allocation budgétaire.",
        'i_types_coso': "86 projets COSO géolocalisés sur 241, concentrés sur les bâtiments primaires et latrines. Recommandation : prioriser les régions les moins dotées, notamment les Savanes qui cumulent les retards.",
        'i_statut': "Seulement 9 projets sur 241 ont atteint la réception définitive. Recommandation : accélérer le bouclage administratif des projets en phase de réception provisoire.",
        'i_matrice': "Les Savanes décrochent sur tous les indicateurs : 48,9 % au BEPC contre 80,8 % à Kara. Recommandation : un programme régional d'urgence est nécessaire pour les Savanes, loin derrière les autres régions.",

        'i_transition': "Le taux de transition primaire-collège atteint 82,7 % à Lomé-Golfe mais chute à 63,1 % dans les Savanes. Recommandation : construire des collèges de proximité dans les zones rurales pour réduire l'abandon après le primaire.",

        'i_bepc': "L'écart filles-garçons au BEPC se réduit lentement : de -5,3 pts en 2011 à -4,3 pts en 2022 au national. Recommandation : déployer des programmes de soutien ciblés pour les filles dans les régions les plus inégalitaires (Savanes, Plateaux Ouest).",
        'i_ecart': "Carte de l'écart filles-garçons par région : plus la teinte est rouge, plus l'inégalité est forte. Recommandation : concentrer les actions de rattrapage sur les Savanes (-9,7 pts) et Plateaux Ouest (-9,8 pts).",

        'chat_nom': 'Assistant Éducation Togo', 'chat_statut': 'En ligne · Données 2013-2022',
        'chat_bienvenue': 'Bonjour ! Je suis votre assistant pour les données éducatives du Togo. Posez votre question ou choisissez un sujet :',
        'chat_placeholder': 'Exprimez votre question...',
        'chat_q1': '📊 Taux lycée', 'chat_q2': '📍 Région prioritaire', 'chat_q3': '💰 Budget',
        'chat_q4': '🏗️ Projet COSO', 'chat_q5': '👩‍🎓 Parité',
        'chat_tq1': "Quel est le taux d'achèvement au lycée ?",
        'chat_tq2': 'Quelle région est la plus prioritaire ?',
        'chat_tq3': 'Comment évolue le budget éducation ?',
        'chat_tq4': "C'est quoi le projet COSO ?",
        'chat_tq5': "Quel est l'écart filles-garçons ?",
        'chat_q6': '🏫 Écoles', 'chat_q7': '🧮 Score composite', 'chat_q8': '🔁 Transition',
        'chat_q9': '🎓 BEPC 2022', 'chat_q10': '🧮 Score composite',
        'chat_tq6': "Combien d'écoles compte le Togo et comment se répartissent-elles par région ?",
        'chat_tq7': 'Quelle région a le score composite le plus faible et pourquoi ?',
        'chat_tq8': "C'est quoi le taux de transition primaire-secondaire ?",
        'chat_tq9': "Où se concentrent les enseignants du préscolaire ?",
        'chat_tq10': 'Quel est le score composite de chaque région ?',
        'a_ouvrir': 'Ouvrir le dashboard',
        'a_kicker': 'Défi Togo AI Lab · Éducation',
        'a_h1': "Dix ans de données pour <em>piloter</em> l'école togolaise",
        'a_p': "De 2013 à 2022 : sur 100 élèves entrés au primaire, <strong>seuls 27 achèvent le lycée</strong>. Ce tableau de bord croise 16 jeux de données ouvertes - 15 454 écoles, 241 projets COSO, résultats régionaux et parité filles-garçons - pour montrer où agir.",
        'a_cta1': 'Explorer le dashboard', 'a_cta2': 'Voir la carte',
        'a_st1': 'Établissements cartographiés', 'a_st2': 'Projets COSO suivis',
        'a_st3': 'Jeux de données ouverts', 'a_st4': 'Part du budget éducation - en chute',
        'a_exp_kicker': 'Quatre vues, une décision', 'a_exp_h2': 'Explorez le tableau de bord',
        'a_vue': 'Vue',
        'a_d1': "6 indicateurs vitaux avec tendance 10 ans, entonnoir éducatif et lien budget ↔ résultats.",
        'a_d2': "15 454 écoles et 10 228 toilettes cartographiées, cartes thématiques par région et préfecture, projets COSO.",
        'a_d3': "Matrice région × indicateur, classement par score de vulnérabilité, parité filles-garçons au BEPC et carte de l'écart régional depuis 2011.",
        'a_d4': "Écart au BEPC par région depuis 2011 et féminisation du corps enseignant préscolaire (91,8 %).",
        'a_go1': 'Ouvrir la vue', 'a_go2': 'Ouvrir la carte',
        'a_go3': 'Comparer les régions', 'a_go4': 'Analyser la parité',
        'a_d5': "Six recommandations chiffrées tirées des trois vues : où agir, comment, et avec quel indicateur de suivi.",
        'a_go5': 'Lire les recommandations',
    },
    'en': {
        'nav1': 'National overview', 'nav2': 'Infrastructure mapping',
        'nav3': 'Performance & Parity',
        'nav5': 'Recommendations',
        'desc5': 'What the data demands: six recommendations drawn from the three views',
        'prio1': 'Priority 1 · act now', 'prio2': 'Priority 2 · structure',
        'prio3': 'Priority 3 · consolidate',
        'reco_constat': 'Finding', 'reco_actions': 'Recommended actions',
        'reco_suivi': 'Tracking indicator',
        'reco_side_note': 'Synthesis of the lessons from the 3 views — nothing to filter here.',
        'desc1': 'State of the Togolese education system: key indicators, student flows and funding',
        'desc2': 'School coverage of the territory and COSO investments',
        'desc3': 'Regional performance, gender parity and teaching staff: complete view',

        'filtres': 'Analysis filters', 'filtres_sub': 'Refine the data of the active tab',
        'periode': 'Period', 'territoire': 'Territory (drill-down)',
        'periode_pop': 'Period and population', 'terr_periode': 'Territory and period',
        'annee_ref': 'Reference year', 'annee': 'Year', 'region': 'Region',
        'prefecture': 'Prefecture', 'commune': 'Municipality', 'sexe': 'Gender',
        'region_bepc': 'Region (BEPC curves)',
        'toutes_regions': 'All regions', 'toutes_prefs': 'All prefectures',
        'toutes_communes': 'All municipalities', 'derniere': 'Latest available',
        'choisir_pref': 'Choose a prefecture first',
        'appliquer': 'Apply', 'sources': 'Sources', 'accueil': 'Home',
        'pdf_btn': 'Methodology note (PDF)',
        'rapport_btn': 'Analysis report (PDF)', 'indice_btn': 'Vulnerability index (PDF)',
        'voir_pdf': 'Preview', 'telecharger': 'Download', 'nouvel_onglet': 'Open in a tab', 'fermer': 'Close',
        'donnees_src': 'INSEED / MEPS data', 'chargement': 'Loading data...',
        'tt_theme': 'Dark / light mode', 'tt_menu': 'Collapse / expand menu',
        'tt_dl': 'Export (PNG or CSV)', 'tt_dl_carte': 'Download map as PNG',
        'tt_grandir': 'Expand', 'tt_lecture': 'Insight',
        'c_entonnoir': 'From primary to high school: the student journey',
        'seg_entonnoir': 'Journey', 'seg_evo_flux': 'Trend 2013-2022',
        'seg_bud_lien': 'Link', 'seg_bud_evo': 'Trend',
        'c_budget': 'Budget and school results',
        'c_evolution': 'Trend 2013-2022 -',
        'evo_niveau': 'Success rate by level', 'evo_secteur': 'Schools by sector',
        'seg_niveau': 'Level', 'seg_secteur': 'Sector',
        'c_tableau': 'All key figures',
        'tbl_paren': '(national 2013-2022 · regional 2014-2022)',
        'vue': 'View', 'national': 'National', 'par_region': 'By region',
        'correlations': 'Correlations',
        'c_carte_pts': 'Map of schools and projects',
        'c_carte_thema': 'Thematic map -', 'par': 'by',
        'carte_points': 'Points', 'carte_thema': 'Thematic', 'carte_tableau': 'Table',
        'c_tableau': 'Indicators by municipality',
        'tab_variable': 'Variable', 'tab_priorite': 'Priority level', 'tab_toutes': 'All', 'tab_afficher': 'Apply', 'tab_telecharger': 'Download (CSV)',
        'col_region': 'Region', 'col_prefecture': 'Prefecture', 'col_commune': 'Municipality', 'col_annee': 'Year',
        'q1': 'Very high priority', 'q2': 'High priority', 'q3': 'Moderate', 'q4': 'Good', 'q5': 'Very good',
        'i_tableau_indic': 'Infrastructure indicators by municipality (2024 registry). Pick a variable and a priority level: municipalities are ranked and colored by quintile (red = priority, green = good; inverted for building age).',
        'etablissements': 'Schools', 'toilettes_lbl': 'Toilets', 'terrain_sport': 'Sports field',
        'primaire_lbl': 'Primary', 'college_lbl': 'Secondary', 'lycee_lbl': 'High school',
        'biblio_lbl': 'Library', 'electrifies_lbl': 'Buildings', 'par_ecole': '/school',
        'anciennete_lbl': 'Avg. age', 'ans': 'yrs',
        'enseignants_lbl': 'Preschool teachers', 'femmes_lbl': 'Women', 'hommes_lbl': 'Men',
        'coso_geo': 'Geolocated COSO projects', 'salles': 'Classrooms (geolocated projects)',
        'coso_regions_lbl': 'Regions', 'coso_prefectures_lbl': 'Prefectures',
        'c_types_coso': 'Project types built', 'geo_paren': 'geolocated projects',
        'c_statut': 'What is the project status?',
        'type_projet': 'Project type', 'tous_types': 'All types',
        'c_matrice': 'Region comparison', 'derniere_annee': 'latest available year',
        'tout_comparer': '- Compare all -',
        'toutes_label': 'all regions', 'derniere_courte': 'latest year',
        'c_transition': 'Results trend by region',

        'graphique': 'Chart', 'tableau_ar': 'Years × regions table',
        'graphique_lbl': 'chart', 'tableau_lbl': 'table',
        'c_bepc': 'BEPC results: girls vs boys',
        'c_ecart': 'Girl-boy gap at BEPC',

        'k_filles': 'Girls at BEPC', 'k_garcons': 'Boys at BEPC',
        'k_moyenne': 'BEPC average',
        'pts_depuis': 'pts since 2011',
        'etait': 'Was', 'en_2011': 'in 2011',

        'i_entonnoir': 'The educational funnel narrows at each cycle: out of 100 primary pupils, only 63 reach middle school and 27 reach high school. Recommendation: invest massively in middle-school access and retention, the system\'s main leak point.',
        'i_budget': 'The share of the education budget peaked at 19.4% in 2021 then fell to 14.7% in 2022. Recommendation: lock in at least 18% of the budget to preserve gains and meet SDG4 targets.',
        'i_evolution': 'Primary completion plateaus at 88% (2022), middle school progresses (+26 pts between 2013 and 2022) but remains under 70%, high school stagnates below 30%. Recommendation: target interventions on lower secondary, the weakest link in the chain.',
        'i_tableau': 'Multi-indicator dashboard: choose between national view, regional view, or correlation matrix. Recommendation: use the matrix to identify the levers most correlated with academic success.',
        'i_carte_pts': 'Interactive map of 15,454 schools with toggleable layers. Recommendation: turn on the toilet layer to locate priority areas for sanitation investment.',
        'i_carte_thema': 'Thematic map of aggregated indicators by region or prefecture, municipality level as bubbles. Recommendation: compare infrastructure coverage between regions to guide budget allocation.',
        'i_types_coso': '86 geolocated COSO projects out of 241, focused on primary buildings and latrines. Recommendation: prioritise the least equipped regions, especially Savanes which lags across the board.',
        'i_statut': 'Only 9 out of 241 projects have reached final acceptance. Recommendation: fast-track administrative closure of projects at provisional acceptance stage.',
        'i_matrice': 'Savanes lags on every indicator: 48.9% at BEPC versus 80.8% in Kara. Recommendation: an emergency regional programme is needed for Savanes, far behind all other regions.',

        'i_transition': 'The primary-to-middle transition reaches 82.7% in Lomé-Golfe but drops to 63.1% in Savanes. Recommendation: build local middle schools in rural areas to reduce dropout after primary.',

        'i_bepc': 'The girls-boys gap at BEPC narrows slowly: from -5.3 pts in 2011 to -4.3 pts in 2022 nationally. Recommendation: deploy targeted support programmes for girls in the most unequal regions (Savanes, Plateaux Ouest).',
        'i_ecart': 'Map of the girls-boys gap by region: the redder the shade, the stronger the inequality. Recommendation: focus catch-up actions on Savanes (-9.7 pts) and Plateaux Ouest (-9.8 pts).',

        'chat_nom': 'Togo Education Assistant', 'chat_statut': 'Online · 2013-2022 data',
        'chat_bienvenue': 'Hello! I am your assistant for Togo education data. Ask a question or pick a topic:',
        'chat_placeholder': 'Type your question...',
        'chat_q1': '📊 High school rate', 'chat_q2': '📍 Priority region', 'chat_q3': '💰 Budget',
        'chat_q4': '🏗️ COSO project', 'chat_q5': '👩‍🎓 Parity',
        'chat_tq1': 'What is the high school completion rate?',
        'chat_tq2': 'Which region is the highest priority?',
        'chat_tq3': 'How is the education budget evolving?',
        'chat_tq4': 'What is the COSO project?',
        'chat_tq5': 'What is the girl-boy gap?',
        'chat_q6': '🏫 Schools', 'chat_q7': '🧮 Composite score', 'chat_q8': '🔁 Transition',
        'chat_q9': '🎓 BEPC 2022', 'chat_q10': '🧮 Composite score',
        'chat_tq6': 'How many schools does Togo have and how are they distributed by region?',
        'chat_tq7': 'Which region has the lowest composite score and why?',
        'chat_tq8': 'What is the primary-to-secondary transition rate?',
        'chat_tq9': 'Where are preschool teachers concentrated?',
        'chat_tq10': 'What is the composite score of each region?',
        'a_ouvrir': 'Open the dashboard',
        'a_kicker': 'Défi Togo AI Lab · Education',
        'a_h1': 'Ten years of data to <em>steer</em> Togolese schools',
        'a_p': 'From 2013 to 2022: out of 100 pupils entering primary school, <strong>only 27 complete high school</strong>. This dashboard combines 16 open datasets - 15,454 schools, 241 COSO projects, regional results and girl-boy parity - to show where to act.',
        'a_cta1': 'Explore the dashboard', 'a_cta2': 'View the map',
        'a_st1': 'Schools mapped', 'a_st2': 'COSO projects tracked',
        'a_st3': 'Open datasets', 'a_st4': 'Education budget share - falling',
        'a_exp_kicker': 'Four views, one decision', 'a_exp_h2': 'Explore the dashboard',
        'a_vue': 'View',
        'a_d1': '6 vital indicators with 10-year trends, the education funnel and the budget ↔ results link.',
        'a_d2': '15,454 schools and 10,228 toilets mapped, thematic maps by region and prefecture, COSO projects.',
        'a_d3': 'Region × indicator matrix, composite vulnerability ranking, girl-boy BEPC parity and a regional gap map since 2011.',
        'a_d4': 'BEPC gap by region since 2011 and feminization of preschool teaching staff (91.8%).',
        'a_go1': 'Open the view', 'a_go2': 'Open the map',
        'a_go3': 'Compare regions', 'a_go4': 'Analyze parity',
        'a_d5': 'Six evidence-based recommendations drawn from the three views: where to act, how, and with which tracking indicator.',
        'a_go5': 'Read the recommendations',
    },
}

# ---------------------------------------------------------------------------
# Onglet 5 : recommandations tirées des enseignements des 4 vues
# ---------------------------------------------------------------------------
RECOMMANDATIONS = {
    'fr': [
        {'prio': 1, 'icone': 'fa-filter', 'titre': 'Faire du collège la priorité nationale',
         'constat': "Sur 100 élèves entrés au primaire, 63 achèvent le collège et 27 seulement le lycée ; l'achèvement lycée stagne sous 30 % depuis 10 ans (Vue d'ensemble).",
         'actions': ["Cibler la transition primaire → secondaire dans les préfectures sous 70 %",
                     "Réduire les coûts d'accès au collège en zone rurale : kits scolaires, cantines, transport",
                     "Ouvrir des collèges de proximité dans les cantons qui n'en ont aucun (voir Cartographie)"],
         'suivi': "Taux d'achèvement collège ≥ 75 % et lycée ≥ 40 % d'ici 2030"},
        {'prio': 1, 'icone': 'fa-coins', 'titre': "Garantir le budget de l'éducation",
         'constat': "La part du budget est retombée à 14,7 % en 2022 après le pic de 19,4 % en 2021, alors que les résultats progressent avec la dépense (corrélations, Vue d'ensemble).",
         'actions': ["Fixer un plancher de 15 à 20 % du budget de l'État (référence Éducation 2030)",
                     "Flécher les moyens supplémentaires vers le secondaire, maillon faible de l'entonnoir",
                     "Publier chaque année l'exécution budgétaire par région pour la redevabilité"],
         'suivi': 'Part du budget ≥ 15 % chaque année, retour vers 19 % d\'ici 2027'},
        {'prio': 1, 'icone': 'fa-map-marked-alt', 'titre': "Un plan d'urgence pour les Savanes",
         'constat': "Dernière au score composite, BEPC à 48,9 % contre 80,8 % à Kara, transition en chute depuis 2016 (Disparités régionales).",
         'actions': ["Allocation péréquée : bonus par élève pour les régions sous la moyenne du score composite",
                     "Accélérer la remise des ouvrages COSO : 91 remis sur 241 (programme 2022-2026)",
                     "Primes d'affectation et logements pour stabiliser les enseignants dans le nord"],
         'suivi': "Écart de score composite Savanes / moyenne nationale divisé par 2 d'ici 2028"},
        {'prio': 2, 'icone': 'fa-venus-mars', 'titre': "Fermer l'écart filles-garçons au BEPC",
         'constat': "-5,9 points pour les filles en 2022 (61,1 % vs 67,0 %), jusqu'à -9,8 aux Plateaux Ouest ; l'écart se réduit depuis 2011 (10,6 pts) mais ne se ferme pas (Parité).",
         'actions': ["Bourses et tutorat pour les filles au collège dans les 3 régions les plus inégalitaires",
                     "Sensibilisation communautaire contre mariages et grossesses précoces",
                     "Rééquilibrer les corps enseignants : 91,8 % de femmes au préscolaire, modèles mixtes au secondaire"],
         'suivi': 'Écart BEPC national ≤ 2 pts en 2030, aucun écart régional > 5 pts'},
        {'prio': 2, 'icone': 'fa-school', 'titre': "Cibler les infrastructures via l'indice de vulnérabilité",
         'constat': "L'indice de vulnérabilité infrastructures (carte par défaut, Cartographie) classe les communes : les plus sous-équipées sont Golfe et Wawa (indice > 80/100), les préfectures Danyi, Wawa, Kloto en tête. À l'échelle du pays, 0,66 bloc de toilettes par école et 11 bibliothèques seulement.",
         'actions': ["Programme WASH ciblé sur le quintile 'Très prioritaire' de l'indice (communes des Plateaux et grand Lomé sous-équipées)",
                     "Étendre le modèle COSO (bâtiment + latrines) aux préfectures à indice élevé du sud, en complément de l'effort au nord",
                     "Rénover en priorité le parc vétuste (composante ancienneté de l'indice) et un point lecture par inspection"],
         'suivi': "Réduire de moitié le nombre de communes du quintile 'Très prioritaire' et ratio toilettes / école ≥ 1 d'ici 2028"},
        {'prio': 3, 'icone': 'fa-database', 'titre': 'Publier des données à jour',
         'constat': "Le taux de promotion s'arrête en 2019, les statistiques du secondaire datent de 2015, le préscolaire n'a qu'une année de données (sources du dashboard).",
         'actions': ["Reprendre la publication annuelle des séries interrompues (promotion, secondaire)",
                     "Harmoniser les noms de régions entre jeux de données (Lomé-Golfe / Golfe Lomé…)",
                     "Publier en open data avec un délai maximal d'un an"],
         'suivi': '100 % des séries clés à jour à N-1 dès 2027'},
    ],
    'en': [
        {'prio': 1, 'icone': 'fa-filter', 'titre': 'Make middle school the national priority',
         'constat': 'Out of 100 pupils entering primary school, 63 complete middle school and only 27 high school; high-school completion has stagnated below 30% for 10 years (Overview).',
         'actions': ['Target the primary → secondary transition in prefectures below 70%',
                     'Cut the cost of attending middle school in rural areas: school kits, canteens, transport',
                     'Open local middle schools in cantons that have none (see Mapping)'],
         'suivi': 'Middle-school completion ≥ 75% and high school ≥ 40% by 2030'},
        {'prio': 1, 'icone': 'fa-coins', 'titre': 'Guarantee education funding',
         'constat': 'The budget share fell back to 14.7% in 2022 after the 19.4% peak of 2021, while results move with spending (correlations, Overview).',
         'actions': ['Set a floor of 15-20% of the state budget (Education 2030 benchmark)',
                     'Direct additional resources to secondary education, the weak link of the funnel',
                     'Publish budget execution by region every year for accountability'],
         'suivi': 'Budget share ≥ 15% every year, back towards 19% by 2027'},
        {'prio': 1, 'icone': 'fa-map-marked-alt', 'titre': 'An emergency plan for Savanes',
         'constat': 'Last on the composite score, BEPC at 48.9% versus 80.8% in Kara, transition falling since 2016 (Regional disparities).',
         'actions': ['Equalised funding: a per-pupil bonus for regions below the average composite score',
                     'Speed up COSO handovers: 91 delivered out of 241 (2022-2026 programme)',
                     'Posting bonuses and housing to retain teachers in the north'],
         'suivi': 'Savanes composite-score gap to the national average halved by 2028'},
        {'prio': 2, 'icone': 'fa-venus-mars', 'titre': 'Reduce the girl-boy gap at the BEPC',
         'constat': '-5.9 points for girls in 2022 (61.1% vs 67.0%), down to -9.8 in Plateaux Ouest; the gap has narrowed since 2011 (10.6 pts) but never closes (Parity).',
         'actions': ['Scholarships and tutoring for girls in middle school in the 3 most unequal regions',
                     'Community campaigns against early marriage and pregnancy',
                     'Rebalance teaching staff: 91.8% women in preschool, mixed role models in secondary'],
         'suivi': 'National BEPC gap ≤ 2 pts by 2030, no regional gap > 5 pts'},
        {'prio': 2, 'icone': 'fa-school', 'titre': 'Target infrastructure using the vulnerability index',
         'constat': "The infrastructure vulnerability index (default map, Mapping) ranks municipalities: the most under-equipped are Golfe and Wawa (index > 80/100), with prefectures Danyi, Wawa, Kloto on top. Nationally, 0.66 toilet block per school and only 11 libraries.",
         'actions': ["WASH programme focused on the index's 'very high priority' quintile (under-equipped Plateaux and greater Lomé municipalities)",
                     'Extend the COSO model (building + latrines) to high-index southern prefectures, complementing the northern effort',
                     'Renovate the ageing stock first (age component of the index) and add a reading point per inspectorate'],
         'suivi': "Halve the number of municipalities in the 'very high priority' quintile and reach a toilet/school ratio ≥ 1 by 2028"},
        {'prio': 3, 'icone': 'fa-database', 'titre': 'Publish up-to-date data',
         'constat': 'The promotion rate stops in 2019, secondary statistics date from 2015, preschool has a single year of data (dashboard sources).',
         'actions': ['Resume yearly publication of the interrupted series (promotion, secondary)',
                     'Harmonise region names across datasets (Lomé-Golfe / Golfe Lomé…)',
                     'Publish open data with a maximum one-year lag'],
         'suivi': '100% of key series updated to N-1 from 2027'},
    ],
}

REGIONS_CARTE = ['Maritime', 'Plateaux', 'Centrale', 'Kara', 'Savanes']
ANNEES_O1 = list(range(2013, 2023))
ANNEES_O3 = list(range(2014, 2023))
ANNEES_O4 = list(range(2011, 2023))
SEXES = ['Total', 'Féminin', 'Masculin']

# ---------------------------------------------------------------------------
# Chargement paresseux et unique des données (les CSV ne bougent pas)
# ---------------------------------------------------------------------------
_lock = threading.Lock()
_data: dict = {}

_LOADERS = {
    'o1': o1.load_onglet1_data,
    'o2': o2.load_onglet2_data,
    'o3': o3.load_onglet3_data,
    'o4': o4.load_onglet4_data,
}


def _dfs(key):
    with _lock:
        if key not in _data:
            _data[key] = _LOADERS[key]()
        return _data[key]


# ---------------------------------------------------------------------------
# Construction des contenus par onglet (fragments ECharts mis en cache)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=32)
def _tab1_context(annee: int) -> dict:
    df6 = _dfs('o1')['resultats']
    dfs3 = _dfs('o3')
    kpi_rows = o1.get_kpi_data(df6, annee=annee)

    return {
        'kpi_html': o1.kpi_gauge_html(kpi_rows),
        'funnel': chart_fragment(o1.sankey_funnel_html(o1.get_funnel_data(df6, annee=annee), annee)),
        'funnel_evolution': chart_fragment(
            o1.funnel_evolution_bar_html(o1.get_funnel_evolution_data(df6))),
        'scatter': chart_fragment(o1.scatter_budget_html(o1.get_scatter_data(df6))),
        'scatter_evolution': chart_fragment(
            o1.scatter_budget_evolution_html(o1.get_scatter_data(df6))),
        # Évolution, deux lectures du fichier 06 :
        #  - par niveau  : taux d'achèvement (Primaire/Collège/Lycée/Préscolaire)
        #  - par secteur : nombre d'écoles (Total/Public/Privé), seul détail sectoriel du fichier
        'evolution_niveau': chart_fragment(o1.evolution_line_html(o1.get_evolution_data(df6), titre='')),
        'evolution_secteur': chart_fragment(o1.evolution_secteur_html(
            o1.get_evolution_par_secteur(df6, indicateur="Nombre d'écoles", niveau='Total'))),
        # Vues du tableau des indicateurs : national + régional (fichiers 08/09/10)
        'table_total': o1.indicator_table_html(o1.indicator_table(df6, secteur='Total'), root_id='tbl_nat'),
        'table_correlation': o1.correlation_table_html(df6),
        'table_regional': o1.regional_indicator_table_html(
            o1.regional_indicator_table(dfs3['promotion'], dfs3['bepc'], dfs3['transition'])),
    }


@lru_cache(maxsize=1)
def _territoires() -> dict:
    """Arbre Région → Préfecture → [Communes] (fichier 01), calculé une fois."""
    return o2.get_territoires(_dfs('o2'))


def _valider_territoire(region, pref, commune):
    """Valide la cascade : une préfecture doit appartenir à la région choisie,
    une commune à la préfecture choisie. Retourne (region, pref, commune) sûrs."""
    arbre = _territoires()
    if region not in arbre:
        region = 'Toutes'
    prefs_valides = arbre.get(region, {}) if region != 'Toutes' else {
        p: c for prefs in arbre.values() for p, c in prefs.items()
    }
    if pref not in prefs_valides:
        pref = 'Toutes'
    communes_valides = prefs_valides.get(pref, []) if pref != 'Toutes' else []
    if commune not in communes_valides:
        commune = 'Toutes'
    return region, pref, commune


def _args_territoire(region, pref, commune):
    """Convertit les valeurs de filtre en arguments pour modules_visu."""
    return {
        'regions': [region] if region != 'Toutes' else None,
        'prefecture': pref if pref != 'Toutes' else None,
        'commune': commune if commune != 'Toutes' else None,
    }


@lru_cache(maxsize=48)
def _tab2_context(region: str, pref: str, commune: str) -> dict:
    dfs = _dfs('o2')
    t = _args_territoire(region, pref, commune)
    counters = o2.get_counters(dfs, **t)
    type_rows, status_rows = o2.get_coso_aggregation(dfs, **t)
    return {
        'counters': counters,
        'coso_croise': o2.get_coso_croise(dfs, **t),
        'coso_bar': chart_fragment(o2.coso_type_bar_html(type_rows)) if type_rows else '<p style="padding:20px;color:#A0AEC0">Aucun projet COSO géolocalisé sur ce territoire.</p>',
        'coso_pie': chart_fragment(o2.coso_status_pie_html(status_rows)) if status_rows else '<p style="padding:20px;color:#A0AEC0">Aucun projet COSO géolocalisé sur ce territoire.</p>',
        # Tableau complet des indicateurs par commune (indépendant du filtre —
        # le filtrage se fait dans le tableau via variable + niveau de priorité).
        'tableau_rows': o2.get_tableau_data(dfs),
        'tableau_vars': o2.TABLEAU_VARIABLES,
    }


# Fonction d'export PNG injectée dans les pages carte, appelée depuis le bouton
# de la card parente (iframe même origine). Capture html2canvas : attente du
# chargement complet des tuiles, puis capture du document recadrée sur la carte
# (évite les décalages liés aux transforms Leaflet).
_PNG_EXPORT_SNIPPET = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script>
function _attendreTuiles(maxMs){
  return new Promise(function(resolve){
    var debut = Date.now();
    (function verifier(){
      var enCours = document.querySelectorAll('img.leaflet-tile:not(.leaflet-tile-loaded)').length;
      if (enCours === 0 || Date.now() - debut > maxMs) return resolve();
      setTimeout(verifier, 200);
    })();
  });
}

/* html2canvas gère mal les transform CSS de Leaflet : on convertit temporairement
   chaque TRANSLATION pure en position left/top équivalente, sur TOUTE la hiérarchie
   (conteneur principal — décalé après un fit_bounds —, conteneurs de tuiles, tuiles,
   calques vectoriels, marqueurs), puis on restaure après la capture.
   Les transformations d'échelle (zoom en cours) ne sont pas touchées. */
function _neutraliserTransforms(){
  var cibles = document.querySelectorAll(
    '.leaflet-map-pane, .leaflet-tile-container, img.leaflet-tile, ' +
    '.leaflet-overlay-pane svg, .leaflet-overlay-pane canvas, ' +
    '.leaflet-marker-pane .leaflet-marker-icon, .leaflet-shadow-pane img'
  );
  var etats = [];
  cibles.forEach(function(el){
    var cs = getComputedStyle(el);
    var m = (cs.transform || '').match(/matrix\\(([^)]+)\\)/);
    if (!m) return;
    var p = m[1].split(',').map(parseFloat);
    /* Translation pure uniquement : matrix(1, 0, 0, 1, tx, ty) */
    if (Math.abs(p[0] - 1) > 0.001 || Math.abs(p[1]) > 0.001 ||
        Math.abs(p[2]) > 0.001 || Math.abs(p[3] - 1) > 0.001) return;
    var tx = p[4] || 0, ty = p[5] || 0;
    etats.push({el: el, transform: el.style.transform, left: el.style.left, top: el.style.top});
    el.style.transform = 'none';
    el.style.left = ((parseFloat(cs.left) || 0) + tx) + 'px';
    el.style.top = ((parseFloat(cs.top) || 0) + ty) + 'px';
  });
  return etats;
}
function _restaurerTransforms(etats){
  etats.forEach(function(e){
    e.el.style.transform = e.transform;
    e.el.style.left = e.left;
    e.el.style.top = e.top;
  });
}

function telechargerCartePng(){
  var el = document.querySelector('.folium-map') || document.body;
  var etats = [];
  return _attendreTuiles(4000).then(function(){
    etats = _neutraliserTransforms();
    var rect = el.getBoundingClientRect();
    return html2canvas(document.body, {
      useCORS: true,
      scale: 2,
      backgroundColor: '#ffffff',
      imageTimeout: 15000,
      x: rect.left + window.scrollX,
      y: rect.top + window.scrollY,
      width: rect.width,
      height: rect.height,
      windowWidth: document.documentElement.clientWidth,
      windowHeight: document.documentElement.clientHeight
    });
  }).then(function(canvas){
    _restaurerTransforms(etats);
    var a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = 'carte-togo.png';
    a.click();
  }).catch(function(e){
    _restaurerTransforms(etats);
    alert('Export impossible : ' + e);
  });
}
</script>
"""


def _avec_export_png(html: str) -> str:
    return html.replace('</body>', _PNG_EXPORT_SNIPPET + '</body>')


@lru_cache(maxsize=24)
def _carte_html(region: str, pref: str, commune: str) -> str:
    dfs = _dfs('o2')
    m = o2.build_carte_interactive(dfs, **_args_territoire(region, pref, commune))
    return _avec_export_png(m.get_root().render())


IND_THEMA = list(o2.INDICATEURS_THEMA.keys())      # ecoles / toilettes / ratio
NIV_THEMA = list(o2.NIVEAUX_THEMA.keys())          # region / prefecture / commune


@lru_cache(maxsize=64)
def _carte_thema_html(region: str, pref: str, commune: str, ind: str, niv: str) -> str:
    dfs = _dfs('o2')
    m = o2.carte_thematique(dfs, indicateur=ind, niveau=niv,
                            **_args_territoire(region, pref, commune))
    return _avec_export_png(m.get_root().render())


@lru_cache(maxsize=32)
def _carte_bepc_html(annee: int) -> str:
    dfs = _dfs('o4')
    return o4.bepc_region_map_html(dfs, annee=annee)




def _bepc_table_html(dfs):
    rows = o4.get_bepc_table_data(dfs)
    rows = [r for r in rows if r['region'] not in ('Plateaux Ouest', 'Plateaux Est')]
    annees = list(range(2011, 2023))
    SEXE_LABEL = {'F\u00e9minin': 'Filles', 'Masculin': 'Gar\u00e7ons', 'Total': 'Total'}
    regions_list = sorted({r['region'] for r in rows}, key=lambda x: (x != 'Togo', x))
    trs = []
    for r in rows:
        trend = r['trend']
        if trend is not None:
            arrow = '\u2191' if trend > 0 else '\u2193'
            trend_cell = f'{arrow} {abs(trend):+.1f}'
        else:
            trend_cell = 'N/D'
        cells = ''.join(
            f'<td>{r["annees"].get(a, "")}</td>' for a in annees
        )
        trs.append(f'''<tr data-region="{r['region']}" data-sexe="{SEXE_LABEL[r['sexe']]}">
  <td>{r['region']}</td>
  <td>{SEXE_LABEL[r['sexe']]}</td>
  {cells}
  <td class="{"up" if trend and trend > 0 else "down" if trend and trend < 0 else ""}">{trend_cell}</td>
</tr>''')
    thead = ''.join(f'<th>{a}</th>' for a in annees)
    opts_region = ''.join(f'<option value="{r}">{r}</option>' for r in regions_list)
    opts_sexe = '<option value="Tous">Tous</option><option value="Filles">Filles</option><option value="Gar\u00e7ons">Gar\u00e7ons</option><option value="Total">Total</option>'
    return f'''<div class="bepc-filters" style="display:flex;gap:8px;margin-bottom:8px">
  <select id="bepc-filter-region" class="mini-select" onchange="filterBepcTable()">
    <option value="Toutes">R\u00e9gion : Toutes</option>
    {opts_region}
  </select>
  <select id="bepc-filter-sexe" class="mini-select" onchange="filterBepcTable()">
    {opts_sexe}
  </select>
</div>
<div class="table-scroll hscroll">
<table id="bepc-data-table">
<thead><tr><th>R\u00e9gion</th><th>Sexe</th>{thead}<th>Tendance</th></tr></thead>
<tbody>{"".join(trs)}</tbody>
</table></div>'''


@lru_cache(maxsize=64)
def _tab3_context(annee, sexe: str, region_bepc: str, indicateur: str = 'transition') -> dict:
    dfs_o3 = _dfs('o3')
    dfs_o4 = _dfs('o4')
    rows = o4.get_ecart_regional(dfs_o4, annee=annee)
    rows_2011 = o4.get_ecart_regional(dfs_o4, annee=2011)
    def _find_row(rows, region):
        return next((r for r in rows if r['region'] == region), {})
    row_sel = _find_row(rows, region_bepc)
    row_sel_2011 = _find_row(rows_2011, region_bepc)

    def _delta(a, b):
        if a is None or b is None:
            return None
        return round(a - b, 1)

    kpis = {
        'filles': row_sel.get('Féminin'),
        'garcons': row_sel.get('Masculin'),
        'filles_2011': row_sel_2011.get('Féminin'),
        'garcons_2011': row_sel_2011.get('Masculin'),
        'evol_filles': _delta(row_sel.get('Féminin'), row_sel_2011.get('Féminin')),
        'evol_garcons': _delta(row_sel.get('Masculin'), row_sel_2011.get('Masculin')),
    }
    kpis['moyenne'] = round((kpis['filles'] + kpis['garcons']) / 2, 1) if kpis['filles'] is not None and kpis['garcons'] is not None else None
    kpis['region'] = region_bepc

    return {
        'heatmap': o3.heatmap_table_html(dfs_o3, annee=annee, sexe=sexe),
        'evol_charts': {
            'transition': chart_fragment(o3.evolution_line_html(dfs_o3, indicateur='transition', sexe=sexe)),
            'bepc': chart_fragment(o3.evolution_line_html(dfs_o3, indicateur='bepc', sexe=sexe)),
            'promotion': chart_fragment(o3.evolution_line_html(dfs_o3, indicateur='promotion', sexe=sexe)),
        },
        'evol_indicateur': indicateur,
        'kpis': kpis,
        'bepc_lines': chart_fragment(o4.bepc_evolution_html(dfs_o4, region=region_bepc)),
        'ecart_bars': chart_fragment(o4.ecart_bar_html(dfs_o4, annee=annee)),
        'bepc_table': _bepc_table_html(dfs_o4),
    }





# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Assistant IA (package agent_ia) : un agent par session de navigateur
# ---------------------------------------------------------------------------
_agents = {}
_agents_verrou = threading.Lock()
_AGENTS_MAX = 30


def _agent_pour(session_id):
    with _agents_verrou:
        if session_id not in _agents:
            if len(_agents) >= _AGENTS_MAX:
                _agents.pop(next(iter(_agents)))   # éviction du plus ancien
            _agents[session_id] = agent_ia.AgentEducation()
        return _agents[session_id]


def _md_inline(ligne):
    """Gras / italique / code sur une ligne déjà échappée HTML."""
    ligne = html_std.escape(ligne, quote=False)
    ligne = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', ligne)
    ligne = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', ligne)
    ligne = re.sub(r'`([^`]+)`', r'<code>\1</code>', ligne)
    return ligne


def _md_table(bloc):
    rangees = []
    for ligne in bloc:
        cellules = [c.strip() for c in ligne.strip().strip('|').split('|')]
        if cellules and all(re.fullmatch(r':?-{2,}:?', c) for c in cellules if c):
            continue   # ligne de séparation |---|---|
        rangees.append(cellules)
    if not rangees:
        return ''
    corps = ['<table class="chat-table"><thead><tr>'
             + ''.join(f'<th>{_md_inline(c)}</th>' for c in rangees[0])
             + '</tr></thead><tbody>']
    for r in rangees[1:]:
        corps.append('<tr>' + ''.join(f'<td>{_md_inline(c)}</td>' for c in r) + '</tr>')
    corps.append('</tbody></table>')
    return ''.join(corps)


def _md_en_html(texte):
    """Convertit le markdown de l'agent (tableaux, gras, listes) en HTML sûr."""
    lignes = str(texte).split('\n')
    sortie, i, en_liste = [], 0, False
    while i < len(lignes):
        ligne = lignes[i]
        if ligne.strip().startswith('|') and ligne.count('|') >= 2:
            if en_liste:
                sortie.append('</ul>')
                en_liste = False
            bloc = []
            while i < len(lignes) and lignes[i].strip().startswith('|'):
                bloc.append(lignes[i])
                i += 1
            sortie.append(_md_table(bloc))
            continue
        if re.match(r'^\s*[-•*]\s+', ligne):
            if not en_liste:
                sortie.append('<ul>')
                en_liste = True
            sortie.append('<li>' + _md_inline(re.sub(r'^\s*[-•*]\s+', '', ligne)) + '</li>')
            i += 1
            continue
        if en_liste:
            sortie.append('</ul>')
            en_liste = False
        if ligne.strip():
            sortie.append('<p>' + _md_inline(ligne) + '</p>')
        i += 1
    if en_liste:
        sortie.append('</ul>')
    return ''.join(sortie)


def _vider_caches():
    """Purge les caches en mémoire après un rafraîchissement des données,
    pour que le rechargement de page serve bien les nouveaux CSV."""
    with _lock:
        _data.clear()
    for fn in (_tab1_context, _territoires, _tab2_context, _tab3_context,
               _carte_html, _carte_thema_html, _carte_bepc_html):
        try:
            fn.cache_clear()
        except Exception:  # noqa: BLE001 — purge best-effort
            pass


@app.route('/api/refresh-data')
def api_refresh_data():
    from scripts import update_data
    def stream():
        yield 'data: {"type":"start","total":' + str(len(update_data.FILES)) + '}\n\n'
        for evt in update_data.run_stream():
            yield 'data: ' + json.dumps(evt, ensure_ascii=False) + '\n\n'
        # Données réécrites sur disque : on vide les caches pour que le
        # rechargement côté client reconstruise tout à partir des nouveaux CSV.
        _vider_caches()
    return Response(stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/chat', methods=['POST'])
def api_chat():
    donnees = request.get_json(silent=True) or {}
    question = str(donnees.get('question', '')).strip()[:500]
    if not question:
        return jsonify({'erreur': 'question vide'}), 400
    session_id = str(donnees.get('session', 'defaut'))[:64]
    try:
        resultat = _agent_pour(session_id).repondre(question)
    except Exception as e:  # noqa: BLE001 — le client bascule sur les réponses locales
        return jsonify({'erreur': f'{type(e).__name__}: {str(e)[:200]}'}), 500
    return jsonify({'html': _rendu_html(resultat), 'route': resultat['route'],
                    'iterations': resultat['iterations']})


def _rendu_html(resultat):
    """Réponse markdown de l'agent → HTML sûr, marqueurs [GRAPHIQUE_n]
    remplacés par les vrais fragments ECharts."""
    contenu = _md_en_html(resultat['reponse'])
    for cle, fragment in (resultat.get('graphiques') or {}).items():
        contenu = contenu.replace(f'[{cle}]', fragment)
    return contenu


def _apercu_flux(texte):
    """Texte simple pour l'effet « machine à écrire » : sans marqueurs de
    graphique ni symboles markdown (le rendu HTML complet arrive à la fin)."""
    t = re.sub(r'\[GRAPHIQUE_\d+\]', '', str(texte))
    t = re.sub(r'[*`]', '', t)
    return re.sub(r'\n{3,}', '\n\n', t).strip()


def _chunks_flux(texte, taille=3):
    """Découpe le texte en petits groupes de mots (espaces conservés)."""
    mots = re.findall(r'\S+\s*', texte)
    for i in range(0, len(mots), taille):
        yield ''.join(mots[i:i + taille])


@app.route('/api/chat-stream', methods=['POST'])
def api_chat_stream():
    donnees = request.get_json(silent=True) or {}
    question = str(donnees.get('question', '')).strip()[:500]
    if not question:
        return jsonify({'erreur': 'question vide'}), 400
    session_id = str(donnees.get('session', 'defaut'))[:64]

    def stream():
        evts = queue.Queue()
        resultat = {}

        def worker():
            try:
                resultat['ok'] = _agent_pour(session_id).repondre(
                    question, progression=evts.put)
            except Exception as e:  # noqa: BLE001
                resultat['err'] = f'{type(e).__name__}: {str(e)[:200]}'
            finally:
                evts.put({'type': '__fin__'})

        threading.Thread(target=worker, daemon=True).start()
        # 1) statuts en direct pendant que l'agent travaille (routage, outils…)
        while True:
            evt = evts.get()
            if evt.get('type') == '__fin__':
                break
            yield 'data: ' + json.dumps(evt, ensure_ascii=False) + '\n\n'
        # 2) échec éventuel de l'agent
        if 'err' in resultat:
            yield 'data: ' + json.dumps({'type': 'error', 'erreur': resultat['err']}, ensure_ascii=False) + '\n\n'
            return
        r = resultat['ok']
        # 3) révélation progressive du texte (effet machine à écrire)
        for chunk in _chunks_flux(_apercu_flux(r['reponse'])):
            yield 'data: ' + json.dumps({'type': 'delta', 'text': chunk}, ensure_ascii=False) + '\n\n'
            time.sleep(0.03)
        # 4) rendu final complet (markdown converti + graphiques ECharts)
        yield 'data: ' + json.dumps({'type': 'done', 'html': _rendu_html(r), 'route': r['route']}, ensure_ascii=False) + '\n\n'

    return Response(stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


def _langue():
    v = request.args.get('lang', 'fr')
    return v if v in TRADUCTIONS else 'fr'


@app.route('/')
def accueil():
    lang = _langue()
    return render_template('accueil.html', lang=lang, t=TRADUCTIONS[lang])


@app.route('/dashboard')
def dashboard():
    try:
        tab = int(request.args.get('tab', 1))
    except ValueError:
        tab = 1
    if tab not in (1, 2, 3, 4, 5):
        tab = 1

    def _int_arg(name, default, allowed):
        try:
            v = int(request.args.get(name, default))
        except (TypeError, ValueError):
            return default
        return v if v in allowed else default

    def _str_arg(name, default, allowed):
        v = request.args.get(name, default)
        return v if v in allowed else default

    lang = _langue()

    ts_path = os.path.join(app.root_path, 'data', '.last_update')
    if os.path.isfile(ts_path):
        try:
            with open(ts_path) as f:
                ts = int(f.read().strip())
                derniere_maj = time.strftime('%d/%m/%Y %H:%M', time.gmtime(ts))
        except (ValueError, OSError):
            derniere_maj = None
    else:
        derniere_maj = None

    ctx = {
        'tab': tab,
        'lang': lang,
        't': TRADUCTIONS[lang],
        'derniere_maj': derniere_maj,
        'annees_o1': ANNEES_O1,
        'annees_o3': ANNEES_O3,
        'annees_o4': ANNEES_O4,
        'sexes': SEXES,
        'regions_carte': REGIONS_CARTE,
        'regions_o3': REGIONS_O3,
        'regions_o4': REGIONS_09_SIMPLE,
    }

    if tab == 1:
        annee = _int_arg('annee', 2022, ANNEES_O1)
        ctx.update(annee=annee, **_tab1_context(annee))
    elif tab == 2:
        region, pref, commune = _valider_territoire(
            request.args.get('region', 'Toutes'),
            request.args.get('pref', 'Toutes'),
            request.args.get('commune', 'Toutes'))
        vue = _str_arg('vue', 'thema', ['thema', 'points', 'tableau'])
        ind = _str_arg('ind', 'indice_vuln_infra', IND_THEMA)
        niv = _str_arg('niv', 'region', NIV_THEMA)

        arbre = _territoires()
        prefectures = sorted(arbre.get(region, {}).keys()) if region != 'Toutes' else \
            sorted({p for prefs in arbre.values() for p in prefs})
        communes = sorted(arbre.get(region, {}).get(pref, [])) if pref != 'Toutes' and region != 'Toutes' else \
            (sorted(next((prefs[pref] for prefs in arbre.values() if pref in prefs), [])) if pref != 'Toutes' else [])

        morceaux = [v for v in (region, pref, commune) if v != 'Toutes']
        territoire_label = ' › '.join(morceaux) if morceaux else 'toutes les régions'

        t2c = _tab2_context(region, pref, commune)
        ctx.update(region=region, pref=pref, commune=commune,
                   prefectures=prefectures, communes=communes,
                   territoire_label=territoire_label,
                   vue=vue, ind=ind, niv=niv,
                   ind_labels=o2.INDICATEURS_THEMA, niv_labels=o2.NIVEAUX_THEMA,
                    **t2c)
    elif tab == 3:
        annee_raw = request.args.get('annee', '')
        annee = int(annee_raw) if annee_raw.isdigit() and int(annee_raw) in ANNEES_O3 else 2022
        sexe = _str_arg('sexe', 'Total', SEXES)
        region_bepc = _str_arg('region_bepc', 'Togo', REGIONS_09_SIMPLE)
        indicateur = _str_arg('indicateur', 'transition', ['transition', 'bepc', 'promotion'])
        ctx.update(annee=annee, sexe=sexe, region_bepc=region_bepc, indicateur=indicateur,
                   **_tab3_context(annee, sexe, region_bepc, indicateur))
    elif tab == 5:
        ctx.update(recos=RECOMMANDATIONS[lang])

    return render_template('dashboard.html', **ctx)


@app.route('/carte')
def carte():
    region, pref, commune = _valider_territoire(
        request.args.get('region', 'Toutes'),
        request.args.get('pref', 'Toutes'),
        request.args.get('commune', 'Toutes'))
    return Response(_carte_html(region, pref, commune), mimetype='text/html')


@app.route('/carte-thematique')
def carte_thematique():
    region, pref, commune = _valider_territoire(
        request.args.get('region', 'Toutes'),
        request.args.get('pref', 'Toutes'),
        request.args.get('commune', 'Toutes'))
    ind = request.args.get('ind', 'indice_vuln_infra')
    if ind not in IND_THEMA:
        ind = 'indice_vuln_infra'
    niv = request.args.get('niv', 'region')
    if niv not in NIV_THEMA:
        niv = 'region'
    return Response(_carte_thema_html(region, pref, commune, ind, niv), mimetype='text/html')


@app.route('/carte-bepc')
def carte_bepc():
    annee = request.args.get('annee', '2022', type=int)
    return Response(_carte_bepc_html(annee), mimetype='text/html')


# ---------------------------------------------------------------------------
# Préchauffage : les vues par défaut de chaque onglet sont construites en
# arrière-plan dès le démarrage, pour que le premier visiteur ne paie pas la
# génération (la carte folium seule prend plusieurs secondes).
# ---------------------------------------------------------------------------
def _prechauffer_caches():
    etapes = (
        lambda: _tab1_context(2022),
        lambda: _tab3_context(None, 'Total', 'Togo'),
        _territoires,
        lambda: _tab2_context('Toutes', 'Toutes', 'Toutes'),
        lambda: _carte_html('Toutes', 'Toutes', 'Toutes'),
    )
    for etape in etapes:
        try:
            etape()
        except Exception as e:  # noqa: BLE001 — le préchauffage ne doit jamais tuer l'app
            print(f'Préchauffage : étape ignorée ({type(e).__name__}: {e})')


threading.Thread(target=_prechauffer_caches, daemon=True).start()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
