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
    'toilettes': 'Nombre de toilettes scolaires',
    'ratio': 'Toilettes par établissement',
    'batiments': 'Nombre de bâtiments scolaires',
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
    """Agrège écoles + toilettes par unité administrative, avec centroïde."""
    col = NIVEAU_COLS[niveau]
    ecoles = dfs['etablissements']
    toilettes = dfs['toilettes']
    batiments = dfs['batiments']
    if regions:
        ecoles = ecoles[ecoles['region_nom_bdd'].isin(regions)]
        toilettes = toilettes[toilettes['region_nom_bdd'].isin(regions)]
        batiments = batiments[batiments['region_nom_bdd'].isin(regions)]
    if prefecture:
        ecoles = ecoles[ecoles['prefecture_nom_bdd'] == prefecture]
        toilettes = toilettes[toilettes['prefecture_nom_bdd'] == prefecture]
        batiments = batiments[batiments['prefecture_nom_bdd'] == prefecture]
    if commune:
        ecoles = ecoles[ecoles['commune_nom_bdd'] == commune]
        toilettes = toilettes[toilettes['commune_nom_bdd'] == commune]
        batiments = batiments[batiments['commune_nom_bdd'] == commune]

    coords = ecoles['geometry'].astype(str).str.extract(_RX_POINT)
    e = ecoles[[col]].copy()
    e['_lon'] = pd.to_numeric(coords[0], errors='coerce')
    e['_lat'] = pd.to_numeric(coords[1], errors='coerce')

    agg = e.groupby(col).agg(
        ecoles=(col, 'size'),
        lat=('_lat', 'mean'),
        lon=('_lon', 'mean'),
    ).reset_index()

    t = toilettes.groupby(col).size().rename('toilettes').reset_index()
    agg = agg.merge(t, on=col, how='left')
    agg['toilettes'] = agg['toilettes'].fillna(0).astype(int)
    b = batiments.groupby(col).size().rename('batiments').reset_index()
    agg = agg.merge(b, on=col, how='left')
    agg['batiments'] = agg['batiments'].fillna(0).astype(int)
    agg['ratio'] = (agg['toilettes'] / agg['ecoles']).round(2)
    agg = agg.dropna(subset=['lat', 'lon'])

    return [
        {
            'unite': str(r[col]),
            'lat': float(r['lat']),
            'lon': float(r['lon']),
            'ecoles': int(r['ecoles']),
            'toilettes': int(r['toilettes']),
            'batiments': int(r['batiments']),
            'ratio': float(r['ratio']),
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
        d = acc.setdefault(cle, {'ecoles': 0, 'toilettes': 0, 'batiments': 0, 'unites': []})
        d['ecoles'] += r['ecoles']
        d['toilettes'] += r['toilettes']
        d['batiments'] += r['batiments']
        d['unites'].append(r['unite'])
    for d in acc.values():
        d['ratio'] = round(d['toilettes'] / d['ecoles'], 2) if d['ecoles'] else 0.0
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


def _carte_choroplethe(rows, indicateur, niveau, restreindre=False):
    """Choroplèthe par polygones (région / préfecture).
    restreindre=True : n'affiche que les polygones couverts par les données
    (drill-down sur une région) et zoome sur leur emprise."""
    acc = _valeurs_par_polygone(rows, niveau)
    valeurs = [d[indicateur] for d in acc.values()] or [0]
    vmin, vmax = min(valeurs), max(valeurs)
    if vmin == vmax:
        vmax = vmin + 1

    cmap = LinearColormap(['#FDE68A', '#4AA97C', '#00543D'], vmin=vmin, vmax=vmax)
    cmap.caption = f"{INDICATEURS[indicateur]} - par {NIVEAU_LABELS[niveau].lower()}"

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
            p['_couleur'] = cmap(d[indicateur])
            p['_avec_donnee'] = True
            p['Écoles'] = f"{d['ecoles']:,}".replace(',', ' ')
            p['Toilettes'] = f"{d['toilettes']:,}".replace(',', ' ')
            p['Bâtiments'] = f"{d['batiments']:,}".replace(',', ' ')
            p['Ratio'] = str(d['ratio'])
        else:
            p['_couleur'] = COULEUR_SANS_DONNEE
            p['_avec_donnee'] = False
            p['Écoles'] = 'N/D'
            p['Toilettes'] = 'N/D'
            p['Bâtiments'] = 'N/D'
            p['Ratio'] = 'N/D'

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
            fields=['nom', 'Écoles', 'Toilettes', 'Bâtiments', 'Ratio'],
            aliases=['', 'Écoles :', 'Toilettes :', 'Bâtiments :', 'Ratio :'],
            style='font-size:12px;',
        ),
    ).add_to(m)

    cmap.add_to(m)

    # Zoom sur l'emprise des polygones affichés (drill-down régional)
    if restreindre and gj['features']:
        lat_min, lon_min, lat_max, lon_max = _bbox_features(gj['features'])
        m.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]], padding=(16, 16))

    return m


def _carte_bulles(rows, indicateur, niveau, regions=None):
    """Bulles proportionnelles (niveau commune : pas de polygones ADM3)."""
    valeurs = [r[indicateur] for r in rows] or [0]
    vmin, vmax = min(valeurs), max(valeurs)
    if vmin == vmax:
        vmax = vmin + 1

    cmap = LinearColormap(['#FDE68A', '#4AA97C', '#00543D'], vmin=vmin, vmax=vmax)
    cmap.caption = f"{INDICATEURS[indicateur]} - par {NIVEAU_LABELS[niveau].lower()}"

    m = folium.Map(location=[8.6, 0.9], zoom_start=8 if regions else 7,
                   tiles='CartoDB positron', control_scale=True)

    for r in rows:
        v = r[indicateur]
        if indicateur == 'ratio':
            rayon = 8 + min(v, 2.5) * 12
        else:
            rayon = 6 + 30 * math.sqrt(v / vmax)
        popup = (f"<b>{r['unite']}</b><br>"
                 f"Écoles : {r['ecoles']}<br>"
                 f"Toilettes : {r['toilettes']}<br>"
                 f"Bâtiments : {r['batiments']}<br>"
                 f"Ratio toilettes/école : {r['ratio']}")
        folium.CircleMarker(
            location=[r['lat'], r['lon']],
            radius=rayon,
            color='white', weight=1.5,
            fill=True, fill_color=cmap(v), fill_opacity=0.85,
            popup=folium.Popup(popup, max_width=240),
            tooltip=f"{r['unite']} - {v}",
        ).add_to(m)

    cmap.add_to(m)
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

    bar = (
        Bar(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
        .add_xaxis([r['unite'] for r in tri])
        .add_yaxis(
            INDICATEURS[indicateur],
            [r[indicateur] for r in tri],
            category_gap='35%',
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color=JsCode(
                "function(p){var c=['#00543D','#006A4E','#22865F','#4AA97C','#7CC29B'];"
                "return c[Math.min(Math.floor(p.dataIndex/5), c.length-1)];}"
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
