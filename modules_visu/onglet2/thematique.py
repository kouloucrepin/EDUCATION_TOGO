"""Carte thématique de l'onglet 2 : un indicateur agrégé par région,
préfecture ou commune (fichiers 01 + 02).

Rendu :
 - région / préfecture : choroplèthe (polygones geoBoundaries, data_togo/) ;
 - commune : bulles aux centroïdes (pas de polygones ADM3 disponibles).
"""
import json
import math
import os
import re
import unicodedata

import folium
import pandas as pd
from branca.colormap import LinearColormap
from pyecharts.charts import Bar
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode

DATA_TOGO = os.path.join(os.path.dirname(__file__), '..', '..', 'data_togo')

NIVEAU_COLS = {
    'region': 'region_nom_bdd',
    'prefecture': 'prefecture_nom_bdd',
    'commune': 'commune_nom_bdd',
}
NIVEAU_LABELS = {'region': 'Région', 'prefecture': 'Préfecture', 'commune': 'Commune'}

INDICATEURS = {
    'ecoles': "Nombre d'établissements",
    'primaire': 'Établissements primaires',
    'college': 'Collèges',
    'lycee': 'Lycées',
    'maternelle': 'Jardins d\'enfants',
    'toilettes': 'Établissements avec toilettes',
    'terrain_sport': 'Établissements avec terrain de sport',
    'batiments': 'Bâtiments électrifiés',
    'bibliotheques': 'Établissements avec bibliothèque',
    'coso': 'Nombre de projets COSO',
    'enseignants_total': 'Effectif enseignant (préscolaire)',
    'enseignants_femmes': 'Enseignantes (femmes)',
    'enseignants_hommes': 'Enseignants (hommes)',
}

GEOJSON_NIVEAUX = {
    'region': 'togo_regions.geojson',
    'prefecture': 'togo_prefectures.geojson',
}

# Le découpage geoBoundaries (37 préfectures) est antérieur aux créations récentes :
# on rattache les nouvelles préfectures au polygone d'origine.
ALIAS_PREFECTURES = {
    'MO': 'PLAINE DE MO',
    'TANDJOARE': 'TANDJOUARE',
    'KPENDJAL OUEST': 'KPENDJAL',
    'OTI SUD': 'OTI',
    'AGOE NYIVE': 'GOLFE',
}

COULEUR_SANS_DONNEE = '#CBD5E0'

# Quintiles Q1-Q5 : du plus prioritaire (rouge) au plus performant (vert)
COULEURS_QUINTILES = [
    '#DC2626',  # Q1 – Très prioritaire
    '#F97316',  # Q2 – Prioritaire
    '#FBBF24',  # Q3 – Modéré
    '#22C55E',  # Q4 – Performant
    '#16A34A',  # Q5 – Très performant
]
LABELS_QUINTILES = ['Très prioritaire', 'Prioritaire', 'Modéré', 'Performant', 'Très performant']


def _quintiles(valeurs):
    """Calcule les 4 seuils (20/40/60/80 percentiles) et retourne (seuils, labels)."""
    tri = sorted(valeurs)
    n = len(tri)
    if n < 5:
        return [float('inf')] * 4, LABELS_QUINTILES
    seuils = [
        tri[max(0, n * 20 // 100 - 1)],
        tri[max(0, n * 40 // 100 - 1)],
        tri[max(0, n * 60 // 100 - 1)],
        tri[max(0, n * 80 // 100 - 1)],
    ]
    return seuils, LABELS_QUINTILES


def _indice_quintile(v, seuils):
    for i, s in enumerate(seuils):
        if v <= s:
            return i
    return 4


def _couleur_quintile(v, seuils):
    return COULEURS_QUINTILES[_indice_quintile(v, seuils)]


_RX_POINT = re.compile(r'POINT\s*\(([\d\.\-]+)\s+([\d\.\-]+)\)')
_geo_cache: dict = {}


def _norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', str(s))
                if unicodedata.category(c) != 'Mn')
    return ' '.join(s.upper().replace('-', ' ').split())


def _load_geojson(niveau):
    if niveau not in _geo_cache:
        path = os.path.join(DATA_TOGO, GEOJSON_NIVEAUX[niveau])
        with open(path, encoding='utf-8') as f:
            _geo_cache[niveau] = json.load(f)
    return _geo_cache[niveau]


def get_agregats(dfs, niveau='region', regions=None, prefecture=None, commune=None):
    """Agrège écoles + toilettes + COSO par unité administrative, avec centroïde."""
    col = NIVEAU_COLS[niveau]
    ecoles = dfs['etablissements']
    toilettes = dfs['toilettes']
    coso = dfs['coso']
    if regions:
        ecoles = ecoles[ecoles['region_nom_bdd'].isin(regions)]
        toilettes = toilettes[toilettes['region_nom_bdd'].isin(regions)]
    if prefecture:
        ecoles = ecoles[ecoles['prefecture_nom_bdd'] == prefecture]
        toilettes = toilettes[toilettes['prefecture_nom_bdd'] == prefecture]
    if commune:
        ecoles = ecoles[ecoles['commune_nom_bdd'] == commune]
        toilettes = toilettes[toilettes['commune_nom_bdd'] == commune]

    coords = ecoles['geometry'].astype(str).str.extract(_RX_POINT)
    e = ecoles[[col]].copy()
    e['_lon'] = pd.to_numeric(coords[0], errors='coerce')
    e['_lat'] = pd.to_numeric(coords[1], errors='coerce')

    ts = ecoles[[col, 'terrain_sport']].copy() if 'terrain_sport' in ecoles.columns else None
    if ts is not None:
        ts['_sport'] = (ts['terrain_sport'] == 'Oui').astype(int)

    cat_col = 'etablissement_categorie'
    if cat_col in ecoles.columns:
        cat_map = {
            'Ecole primaire': 'primaire',
            'College': 'college',
            'Lycée': 'lycee',
            'Jardin (maternelle)': 'maternelle',
        }
        e[cat_col] = ecoles[cat_col].map(cat_map).fillna('autre')
        cats = pd.get_dummies(e[[col, cat_col]], columns=[cat_col])
        for c in ['primaire', 'college', 'lycee', 'maternelle']:
            col_c = f'{cat_col}_{c}'
            if col_c in cats.columns:
                e[c] = cats[col_c]
            else:
                e[c] = 0

    agg = e.groupby(col).agg(
        ecoles=(col, 'size'),
        lat=('_lat', 'mean'),
        lon=('_lon', 'mean'),
        **{c: (c, 'sum') for c in ['primaire', 'college', 'lycee', 'maternelle'] if c in e.columns},
    ).reset_index()

    t = toilettes.groupby(col)['etab_nom'].nunique().rename('toilettes').reset_index()
    agg = agg.merge(t, on=col, how='left')
    agg['toilettes'] = agg['toilettes'].fillna(0).astype(int)
    if ts is not None:
        ts_agg = ts.groupby(col)['_sport'].sum().rename('terrain_sport').reset_index()
        agg = agg.merge(ts_agg, on=col, how='left')
        agg['terrain_sport'] = agg['terrain_sport'].fillna(0).astype(int)
    else:
        agg['terrain_sport'] = 0

    from .data import get_teacher_region_agg, get_teacher_by_inspection
    _teacher_region = get_teacher_region_agg(dfs)
    _teacher_by_insp = get_teacher_by_inspection(dfs)

    coso_niveau = NIVEAU_COLS.get({'region': 'region', 'prefecture': 'prefecture'}.get(niveau, ''))
    if coso_niveau and 'hierarchy' in coso.columns:
        idx = {'region': -1, 'prefecture': -2}.get(niveau)
        coso_unites = coso['hierarchy'].dropna().str.split('>').str.get(idx).str.strip().str.upper()
        coso_unites = coso_unites[coso_unites.notna()]
        c_agg = coso_unites.value_counts().rename('coso').reset_index()
        c_agg.columns = ['_unite_norm', 'coso']
        c_agg['_unite_norm'] = c_agg['_unite_norm'].str.replace(' REGION', '', regex=False)
        if niveau == 'region':
            agg['_unite_norm'] = agg[col].str.upper()
        else:
            from .data import _norm_txt
            agg['_unite_norm'] = agg[col].apply(_norm_txt)
        from collections import defaultdict
        alias_map = defaultdict(str, {_norm(v): k for k, v in ALIAS_PREFECTURES.items()})
        c_agg['_unite_norm'] = c_agg['_unite_norm'].apply(lambda x: alias_map.get(_norm(x), _norm(x)))
        agg = agg.merge(c_agg, on='_unite_norm', how='left')
        agg['coso'] = agg['coso'].fillna(0).astype(int)
        agg = agg.drop(columns=['_unite_norm'])
    else:
        agg['coso'] = 0

    if niveau == 'region' and _teacher_region:
        tr_df = pd.DataFrame([
            {'_region': k, 'ens_t': v['total'],
             'ens_f': v['F\u00e9minin'], 'ens_m': v['Masculin']}
            for k, v in _teacher_region.items()
        ])
        agg = agg.merge(tr_df, left_on=col, right_on='_region', how='left')
        agg['enseignants_total'] = agg['ens_t'].fillna(0).astype(int)
        agg['enseignants_femmes'] = agg['ens_f'].fillna(0).astype(int)
        agg['enseignants_hommes'] = agg['ens_m'].fillna(0).astype(int)
        agg = agg.drop(columns=['_region', 'ens_t', 'ens_f', 'ens_m'])
    elif niveau != 'region' and _teacher_by_insp:
        ecoles_t = dfs['etablissements']
        if regions:
            ecoles_t = ecoles_t[ecoles_t['region_nom_bdd'].isin(regions)]
        if prefecture:
            ecoles_t = ecoles_t[ecoles_t['prefecture_nom_bdd'] == prefecture]
        if commune:
            ecoles_t = ecoles_t[ecoles_t['commune_nom_bdd'] == commune]
        ecoles_t = ecoles_t[[col, 'inspection_tutelle']].drop_duplicates(subset=[col, 'inspection_tutelle'])
        ecoles_t['_t_total'] = ecoles_t['inspection_tutelle'].map(
            lambda x: _teacher_by_insp.get(x, {}).get('total', 0))
        ecoles_t['_t_f'] = ecoles_t['inspection_tutelle'].map(
            lambda x: _teacher_by_insp.get(x, {}).get('F\u00e9minin', 0))
        ecoles_t['_t_m'] = ecoles_t['inspection_tutelle'].map(
            lambda x: _teacher_by_insp.get(x, {}).get('Masculin', 0))
        t_agg = ecoles_t.groupby(col).agg(
            enseignants_total=('_t_total', 'sum'),
            enseignants_femmes=('_t_f', 'sum'),
            enseignants_hommes=('_t_m', 'sum'),
        ).reset_index()
        agg = agg.merge(t_agg, on=col, how='left')
        for c in ['enseignants_total', 'enseignants_femmes', 'enseignants_hommes']:
            agg[c] = agg[c].fillna(0).astype(int)
    else:
        for c in ['enseignants_total', 'enseignants_femmes', 'enseignants_hommes']:
            agg[c] = 0

    batiments = dfs.get('batiments')
    if batiments is not None and col in batiments.columns:
        b_agg = batiments.groupby(col).size().rename('batiments').reset_index()
        agg = agg.merge(b_agg, on=col, how='left')
        agg['batiments'] = agg['batiments'].fillna(0).astype(int)
    else:
        agg['batiments'] = 0

    biblios = dfs.get('bibliotheques')
    if biblios is not None and col in biblios.columns:
        l_agg = biblios.groupby(col)['etablissement_nom'].nunique().rename('bibliotheques').reset_index()
        agg = agg.merge(l_agg, on=col, how='left')
        agg['bibliotheques'] = agg['bibliotheques'].fillna(0).astype(int)
    else:
        agg['bibliotheques'] = 0

    agg = agg.dropna(subset=['lat', 'lon'])

    return [
        {
            'unite': str(r[col]),
            'lat': float(r['lat']),
            'lon': float(r['lon']),
            'ecoles': int(r['ecoles']),
            'primaire': int(r.get('primaire', 0)),
            'college': int(r.get('college', 0)),
            'lycee': int(r.get('lycee', 0)),
            'maternelle': int(r.get('maternelle', 0)),
            'toilettes': int(r['toilettes']),
            'terrain_sport': int(r['terrain_sport']),
            'coso': int(r['coso']),
            'batiments': int(r['batiments']),
            'bibliotheques': int(r['bibliotheques']),
            'enseignants_total': int(r.get('enseignants_total', 0)),
            'enseignants_femmes': int(r.get('enseignants_femmes', 0)),
            'enseignants_hommes': int(r.get('enseignants_hommes', 0)),
        }
        for _, r in agg.iterrows()
    ]


def _valeurs_par_polygone(rows, niveau):
    """Regroupe les agrégats par nom de polygone (avec alias préfectures)."""
    acc = {}
    for r in rows:
        cle = _norm(r['unite'])
        if niveau == 'prefecture':
            cle = ALIAS_PREFECTURES.get(cle, cle)
        d = acc.setdefault(cle, {'ecoles': 0, 'primaire': 0, 'college': 0, 'lycee': 0, 'maternelle': 0, 'toilettes': 0, 'terrain_sport': 0, 'coso': 0, 'batiments': 0, 'bibliotheques': 0, 'enseignants_total': 0, 'enseignants_femmes': 0, 'enseignants_hommes': 0, 'unites': []})
        d['ecoles'] += r['ecoles']
        d['primaire'] += r.get('primaire', 0)
        d['college'] += r.get('college', 0)
        d['lycee'] += r.get('lycee', 0)
        d['maternelle'] += r.get('maternelle', 0)
        d['toilettes'] += r['toilettes']
        d['terrain_sport'] += r['terrain_sport']
        d['coso'] += r['coso']
        d['batiments'] += r.get('batiments', 0)
        d['bibliotheques'] += r.get('bibliotheques', 0)
        d['enseignants_total'] += r.get('enseignants_total', 0)
        d['enseignants_femmes'] += r.get('enseignants_femmes', 0)
        d['enseignants_hommes'] += r.get('enseignants_hommes', 0)
        d['unites'].append(r['unite'])
    # Le polygone « Lomé Commune » est enclavé dans Golfe : même valeur (Grand Lomé)
    if niveau == 'prefecture' and 'GOLFE' in acc and 'LOME COMMUNE' not in acc:
        acc['LOME COMMUNE'] = dict(acc['GOLFE'])
    return acc


def _bbox_features(features):
    """Emprise [lat_min, lon_min, lat_max, lon_max] d'une liste de features."""
    lats, lons = [], []

    def _walk(coords):
        if isinstance(coords[0], (int, float)):
            lons.append(coords[0])
            lats.append(coords[1])
        else:
            for c in coords:
                _walk(c)

    for ft in features:
        _walk(ft['geometry']['coordinates'])
    return min(lats), min(lons), max(lats), max(lons)


def _legende_quintile_html(indicateur, niveau):
    items = ''.join(
        f'<span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:{c};margin-right:4px;vertical-align:middle"></span>{l}<br>'
        for c, l in zip(COULEURS_QUINTILES, LABELS_QUINTILES)
    )
    return f'''
    <div style="position:fixed;bottom:24px;left:12px;z-index:9999;
                background:white;padding:10px 12px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.15);font-size:12px;
                max-height:220px;overflow-y:auto;width:170px;">
      <b>{INDICATEURS[indicateur]}</b><br><small>par {NIVEAU_LABELS[niveau].lower()}</small><br>
      {items}
    </div>'''


def _carte_choroplethe(rows, indicateur, niveau, restreindre=False):
    """Choroplèthe par polygones (région / préfecture) avec quintiles Q1-Q5.
    restreindre=True : n'affiche que les polygones couverts par les données
    (drill-down sur une région) et zoome sur leur emprise."""
    acc = _valeurs_par_polygone(rows, niveau)
    valeurs = [d[indicateur] for d in acc.values()] or [0]
    seuils, labels_q = _quintiles(valeurs)

    # Copie du geojson pour y injecter les valeurs sans toucher au cache
    gj = json.loads(json.dumps(_load_geojson(niveau)))
    if restreindre:
        gj['features'] = [
            ft for ft in gj['features']
            if _norm(str(ft['properties'].get('shapeName', ''))).replace(' REGION', '') in acc
        ]
    for ft in gj['features']:
        nom = str(ft['properties'].get('shapeName', ''))
        cle = _norm(nom).replace(' REGION', '')
        d = acc.get(cle)
        p = ft['properties']
        p['nom'] = nom.replace(' Region', '')
        if d:
            couleur = _couleur_quintile(d[indicateur], seuils) if max(valeurs) != min(valeurs) else COULEURS_QUINTILES[2]
            p['_couleur'] = couleur
            p['_q'] = _indice_quintile(d[indicateur], seuils) if max(valeurs) != min(valeurs) else 2
            p['_avec_donnee'] = True
            p['Écoles'] = f"{d['ecoles']:,}".replace(',', ' ')
            p['Primaire'] = f"{d['primaire']:,}".replace(',', ' ')
            p['Collège'] = f"{d['college']:,}".replace(',', ' ')
            p['Lycée'] = f"{d['lycee']:,}".replace(',', ' ')
            p['Maternelle'] = f"{d['maternelle']:,}".replace(',', ' ')
            p['Toilettes'] = f"{d['toilettes']:,}".replace(',', ' ')
            p['Terrain sport'] = f"{d['terrain_sport']:,}".replace(',', ' ')
            p['Projets COSO'] = str(d['coso'])
            p['Bâtiments'] = f"{d['batiments']:,}".replace(',', ' ')
            p['Bibliothèques'] = f"{d['bibliotheques']:,}".replace(',', ' ')
            p['Enseign. présc.'] = f"{d['enseignants_total']:,}".replace(',', ' ')
            p['dont hommes'] = f"{d['enseignants_hommes']:,}".replace(',', ' ')
        else:
            p['_couleur'] = COULEUR_SANS_DONNEE
            p['_q'] = -1
            p['_avec_donnee'] = False
            p['Écoles'] = 'N/D'
            p['Primaire'] = 'N/D'
            p['Collège'] = 'N/D'
            p['Lycée'] = 'N/D'
            p['Maternelle'] = 'N/D'
            p['Toilettes'] = 'N/D'
            p['Terrain sport'] = 'N/D'
            p['Projets COSO'] = 'N/D'
            p['Bâtiments'] = 'N/D'
            p['Bibliothèques'] = 'N/D'
            p['Enseign. présc.'] = 'N/D'
            p['dont hommes'] = 'N/D'

    m = folium.Map(location=[8.6, 0.9], zoom_start=7,
                   tiles='CartoDB positron', control_scale=True)

    folium.GeoJson(
            gj,
            style_function=lambda ft: {
                'fillColor': ft['properties']['_couleur'],
                'color': 'white',
                'weight': 1.4,
                'fillOpacity': 0.85 if ft['properties']['_avec_donnee'] else 0.35,
            },
            highlight_function=lambda ft: {'weight': 3, 'color': '#1A202C', 'fillOpacity': 0.95},
            tooltip=folium.GeoJsonTooltip(
                fields=['nom', 'Écoles', 'Toilettes', 'Terrain sport', 'Projets COSO', 'Bâtiments', 'Bibliothèques', 'Enseign. présc.', 'dont hommes'],
                aliases=['', 'Écoles :', 'Toilettes :', 'Terrain sport :', 'Projets COSO :', 'Bâtiments :', 'Bibliothèques :', 'Enseign. présc. :', 'dont hommes :'],
                style='font-size:12px;',
            ),
    ).add_to(m)

    # Légende quintile custom
    legend_q = _legende_quintile_html(indicateur, niveau)
    m.get_root().html.add_child(folium.Element(legend_q))

    # Zoom sur l'emprise des polygones affichés (drill-down régional)
    if restreindre and gj['features']:
        lat_min, lon_min, lat_max, lon_max = _bbox_features(gj['features'])
        m.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]], padding=(16, 16))

    return m


def _carte_bulles(rows, indicateur, niveau, regions=None):
    """Bulles proportionnelles avec quintiles (niveau commune : pas de polygones ADM3)."""
    valeurs = [r[indicateur] for r in rows] or [0]
    seuils, labels_q = _quintiles(valeurs)
    vmax = max(valeurs) or 1

    m = folium.Map(location=[8.6, 0.9], zoom_start=8 if regions else 7,
                   tiles='CartoDB positron', control_scale=True)

    for r in rows:
        v = r[indicateur]
        rayon = 6 + 30 * math.sqrt(v / vmax)
        couleur = _couleur_quintile(v, seuils) if max(valeurs) != min(valeurs) else COULEURS_QUINTILES[2]
        ens_t = r.get('enseignants_total', 0)
        ens_h = r.get('enseignants_hommes', 0)
        ens_str = f"<br>Enseign. présc. : {ens_t:,}<br>dont hommes : {ens_h:,}" if ens_t else ""
        popup = (f"<b>{r['unite']}</b><br>"
                 f"Écoles : {r['ecoles']}<br>"
                 f"Primaire : {r['primaire']}<br>"
                 f"Collège : {r['college']}<br>"
                 f"Lycée : {r['lycee']}<br>"
                 f"Maternelle : {r['maternelle']}<br>"
                 f"Toilettes : {r['toilettes']}<br>"
                 f"Terrain sport : {r['terrain_sport']}<br>"
                 f"Bâtiments : {r.get('batiments', 0)}<br>"
                 f"Bibliothèques : {r.get('bibliotheques', 0)}<br>"
                 f"Projets COSO : {r['coso']}"
                 f"{ens_str}")
        folium.CircleMarker(
            location=[r['lat'], r['lon']],
            radius=rayon,
            color='white', weight=1.5,
            fill=True, fill_color=couleur, fill_opacity=0.85,
            popup=folium.Popup(popup, max_width=240),
            tooltip=f"{r['unite']} - {v}",
        ).add_to(m)

    m.get_root().html.add_child(folium.Element(_legende_quintile_html(indicateur, niveau)))
    return m


def carte_thematique(dfs, indicateur='ecoles', niveau='region', regions=None,
                     prefecture=None, commune=None):
    """Carte thématique dont la maille s'adapte au drill-down :
     - pays entier          : maille choisie par l'utilisateur ;
     - une région précise   : détail de SES préfectures (choroplèthe restreint,
                              zoomé sur la région) — jamais l'agrégat régional ;
     - une préfecture       : détail de TOUTES ses communes (bulles zoomées) ;
     - une commune          : la commune seule.
    L'utilisateur peut toujours choisir une maille plus fine que celle induite."""
    ordre = {'region': 0, 'prefecture': 1, 'commune': 2}
    niveau_eff = niveau
    if prefecture or commune:
        niveau_eff = 'commune'
    elif regions and ordre[niveau_eff] < ordre['prefecture']:
        niveau_eff = 'prefecture'

    rows = get_agregats(dfs, niveau=niveau_eff, regions=regions,
                        prefecture=prefecture, commune=commune)

    if niveau_eff in GEOJSON_NIVEAUX and not prefecture and not commune:
        return _carte_choroplethe(rows, indicateur, niveau_eff,
                                  restreindre=bool(regions))

    m = _carte_bulles(rows, indicateur, niveau_eff, regions=regions)
    # Zoom automatique sur le territoire sélectionné
    if (regions or prefecture or commune) and rows:
        lats = [r['lat'] for r in rows]
        lons = [r['lon'] for r in rows]
        marge = 0.05
        m.fit_bounds([[min(lats) - marge, min(lons) - marge],
                      [max(lats) + marge, max(lons) + marge]])
    return m


def bar_thematique_html(rows, indicateur='ecoles', top=25):
    """Classement en barres verticales des unités, trié décroissant."""
    tri = sorted(rows, key=lambda r: -r[indicateur])
    tronque = len(tri) > top
    tri = tri[:top]

    valeurs = [r[indicateur] for r in tri]
    seuils_b, _ = _quintiles(valeurs)
    couleurs_js = ', '.join(f"'{c}'" for c in COULEURS_QUINTILES)
    bar = (
        Bar(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
        .add_xaxis([r['unite'] for r in tri])
        .add_yaxis(
            INDICATEURS[indicateur],
            valeurs,
            category_gap='35%',
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color=JsCode(
                f"function(p){{var c=[{couleurs_js}];var v=p.data;"
                f"var s=[{','.join(str(s) for s in seuils_b)}];"
                f"for(var i=0;i<s.length;i++){{if(v<=s[i]){{return c[i];}}}}return c[4];}}"
            )),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=45, font_size=9, interval=0)),
            yaxis_opts=opts.AxisOpts(
                splitline_opts=opts.SplitLineOpts(is_show=True)),
            tooltip_opts=opts.TooltipOpts(trigger='axis'),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    bar.options['grid'] = {'left': '2%', 'right': '2%', 'top': 20, 'bottom': 6, 'containLabel': True}

    note = ''
    if tronque:
        note = (f'<div style="font-size:11px;color:#A0AEC0;margin-top:4px">'
                f'Top {top} affiché sur {len(rows)} unités - affinez avec le filtre Région.</div>')
    return bar.render_embed() + note
