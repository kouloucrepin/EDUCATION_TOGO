import pandas as pd
import folium
from folium import plugins
from .config import (
    COULEURS_CATEGORIE,
    COULEURS_COSO_STATUS, CARTE_CENTRE, CARTE_ZOOM,
)
from .data import get_ecoles_points, get_toilettes_points, get_coso_projets


def _s(v):
    """Chaîne sûre pour l'embarquement JS (NaN/None -> '')."""
    if v is None:
        return ''
    try:
        if pd.isna(v):
            return ''
    except (TypeError, ValueError):
        pass
    return str(v)


def _make_ecole_row(p):
    t = p.get('enseignants_total')
    f = p.get('enseignants_femmes')
    return [
        p['lat'], p['lon'], _s(p['nom']), _s(p['categorie']),
        _s(p['region']), _s(p['prefecture']), _s(p['inspection']),
        _s(t) if t else '', _s(f) if f else '',
    ]


def _ecole_color(cat):
    cat = _s(cat)
    for key, color in COULEURS_CATEGORIE.items():
        if key.lower() in cat.lower():
            return color
    return '#9ca3af'


def _coso_color(status):
    status = _s(status)
    for key, color in COULEURS_COSO_STATUS.items():
        if key.lower() in status.lower():
            return color
    return '#9ca3af'


def _make_coso_popup(p):
    cout_m = (p['cout'] or 0) / 1e6
    return f"""
    <b>{_s(p['titre'])[:80]}</b><br>
    Type: {_s(p['type'])}<br>
    Statut: {_s(p['status'])}<br>
    Coût: {cout_m:.0f} M FCFA<br>
    Salles: {p['salles']} · Latrines: {p['latrines']}<br>
    Localité: {_s(p['localite'])}
    """


# Callbacks JS des FastMarkerCluster : les marqueurs sont créés côté client
# à partir d'un tableau compact - indispensable avec 15 000+ points
# (le rendu serveur point par point produisait un HTML de plusieurs dizaines de Mo).
_CALLBACK_TERRAIN_SPORT = """
function (row) {
  var cat = row[3] || '';
  var color = '#D4A017';
  var m = L.circleMarker(new L.LatLng(row[0], row[1]),
    {radius: 6, color: 'white', weight: 1, fillColor: color, fillOpacity: 0.85});
  m.bindPopup('<b>' + row[2] + '</b><br>Cat\\u00e9gorie: ' + row[3] +
              '<br>R\\u00e9gion: ' + row[4] + '<br>Pr\\u00e9fecture: ' + row[5] +
              '<br><span style=\\"color:#D4A017;font-weight:bold\\">\\u2714 Terrain de sport</span>' +
              (row[7] ? '<br><span style=\\"color:#006A4E\\">\\ud83c\\udf93 Ens. pr\\u00e9sc. : ' +
              row[7] + ' (dont ' + row[8] + ' femmes)</span>' : ''));
  return m;
}
"""

_CALLBACK_ECOLES = """
function (row) {
  var cat = row[3] || '';
  var color = '#9ca3af';
  if (cat.indexOf('primaire') !== -1) color = '#22c55e';
  else if (cat.indexOf('College') !== -1 || cat.indexOf('Coll') !== -1) color = '#f59e0b';
  else if (cat.indexOf('Lyc') !== -1) color = '#ef4444';
  else if (cat.indexOf('Jardin') !== -1) color = '#3b82f6';
  var m = L.circleMarker(new L.LatLng(row[0], row[1]),
    {radius: 5, color: 'white', weight: 1, fillColor: color, fillOpacity: 0.85});
  m.bindPopup('<b>' + row[2] + '</b><br>Cat\\u00e9gorie: ' + row[3] +
              '<br>R\\u00e9gion: ' + row[4] + '<br>Pr\\u00e9fecture: ' + row[5] +
              '<br>Inspection: ' + row[6] +
              (row[7] ? '<br><span style=\\"color:#006A4E\\">\\ud83c\\udf93 Ens. pr\\u00e9sc. : ' +
              row[7] + ' (dont ' + row[8] + ' femmes)</span>' : ''));
  return m;
}
"""

_CALLBACK_AVEC_TOILETTES = """
function (row) {
  var cat = row[3] || '';
  var color = '#2563eb';
  var m = L.circleMarker(new L.LatLng(row[0], row[1]),
    {radius: 5, color: 'white', weight: 1, fillColor: color, fillOpacity: 0.85});
  m.bindPopup('<b>' + row[2] + '</b><br>Cat\\u00e9gorie: ' + row[3] +
              '<br>R\\u00e9gion: ' + row[4] + '<br>Pr\\u00e9fecture: ' + row[5] +
              '<br><span style=\\"color:#2563eb;font-weight:bold\\">\\u2714 Toilettes</span>' +
              (row[7] ? '<br><span style=\\"color:#006A4E\\">\\ud83c\\udf93 Ens. pr\\u00e9sc. : ' +
              row[7] + ' (dont ' + row[8] + ' femmes)</span>' : ''));
  return m;
}
"""


def build_carte_interactive(dfs, regions=None, prefecture=None, commune=None,
                            show_coso=True):
    ecoles = get_ecoles_points(dfs, regions, prefecture, commune)
    coso = get_coso_projets(dfs, regions, prefecture, commune) if show_coso else []

    m = folium.Map(location=CARTE_CENTRE, zoom_start=CARTE_ZOOM,
                   tiles='CartoDB positron', control_scale=True)

    # Zoom automatique sur le territoire sélectionné (préfecture ou commune)
    if (prefecture or commune) and ecoles:
        lats = [p['lat'] for p in ecoles]
        lons = [p['lon'] for p in ecoles]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(24, 24))

    # Layer 1: Tous les établissements (décoché par défaut, sert de total)
    ecole_data = [_make_ecole_row(p) for p in ecoles]
    plugins.FastMarkerCluster(
        ecole_data,
        callback=_CALLBACK_ECOLES,
        name='Tous les établissements',
        overlay=True, control=True, show=False,
        options={
            'maxClusterRadius': 50,
            'spiderfyOnMaxZoom': True,
            'disableClusteringAtZoom': 14,
        },
    ).add_to(m)

    # Couches par catégorie (toutes cochées par défaut)
    # On utilise startswith pour gérer les différences d'encodage des accents
    cat_rules = [
        ('Établissements primaires', 'Ecole', '#22c55e'),
        ('Collèges', 'College', '#f59e0b'),
        ('Lycées', 'Lyc', '#ef4444'),
        ('Jardins d\'enfants', 'Jardin', '#3b82f6'),
    ]
    for label, cat_prefix, color in cat_rules:
        filtered = [p for p in ecoles if _s(p.get('categorie', '')).startswith(cat_prefix)]
        if not filtered:
            continue
        _cb = f"""
function (row) {{
  var m = L.circleMarker(new L.LatLng(row[0], row[1]),
    {{radius: 5, color: 'white', weight: 1, fillColor: '{color}', fillOpacity: 0.85}});
  m.bindPopup('<b>' + row[2] + '</b><br>Cat\\u00e9gorie: ' + row[3] +
              '<br>R\\u00e9gion: ' + row[4] + '<br>Pr\\u00e9fecture: ' + row[5] +
              '<br>Inspection: ' + row[6] +
              (row[7] ? '<br><span style=\\"color:#006A4E\\">\\ud83c\\udf93 Ens. pr\\u00e9sc. : ' +
              row[7] + ' (dont ' + row[8] + ' femmes)</span>' : ''));
  return m;
}}
"""
        data = [_make_ecole_row(p) for p in filtered]
        plugins.FastMarkerCluster(
            data,
            callback=_cb,
            name=label,
            overlay=True, control=True, show=True,
            options={
                'maxClusterRadius': 50,
                'spiderfyOnMaxZoom': True,
                'disableClusteringAtZoom': 14,
            },
        ).add_to(m)

    # Layer 1b: Écoles avec terrain de sport (décoché par défaut)
    sport_data = [_make_ecole_row(p) for p in ecoles if p.get('terrain_sport') == 'Oui']
    if sport_data:
        plugins.FastMarkerCluster(
            sport_data,
            callback=_CALLBACK_TERRAIN_SPORT,
            name='Établissements avec terrain de sport',
            overlay=True, control=True, show=False,
            options={
                'maxClusterRadius': 50,
                'spiderfyOnMaxZoom': True,
                'disableClusteringAtZoom': 14,
            },
        ).add_to(m)

    # Layer 2: Établissements avec toilettes (décoché par défaut)
    etab_avec_toilettes = set()
    for p in get_toilettes_points(dfs, regions, prefecture, commune):
        if p.get('etab'):
            etab_avec_toilettes.add(p['etab'])
    toilette_data = [_make_ecole_row(p) for p in ecoles if p['nom'] in etab_avec_toilettes]
    if toilette_data:
        plugins.FastMarkerCluster(
            toilette_data,
            callback=_CALLBACK_AVEC_TOILETTES,
            name='Établissements avec toilettes',
            overlay=True, control=True, show=False,
            options={
                'maxClusterRadius': 50,
                'spiderfyOnMaxZoom': True,
                'disableClusteringAtZoom': 14,
            },
        ).add_to(m)

    # Layer 3: Projets COSO (86 points - rendu serveur classique, décoché par défaut)
    if show_coso:
        fg_coso = folium.FeatureGroup(name='Projets COSO',
                                      overlay=True,
                                      control=True,
                                      show=False)
        for p in coso:
            color = _coso_color(p['status'])
            radius = max(6, min(20, (p['cout'] or 0) / 5e6))
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=radius,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2,
                popup=_make_coso_popup(p),
            ).add_to(fg_coso)
        fg_coso.add_to(m)

    # Legend HTML
    legend_html = '''
    <div style="position:fixed;bottom:24px;left:12px;z-index:9999;
                background:white;padding:12px 14px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.15);font-size:12px;
                max-height:200px;overflow-y:auto;width:180px;">
      <b>Légende</b><br>
      <span style="color:#D4A017;">●</span> Terrain de sport<br>
      <span style="color:#2563eb;">●</span> Avec toilettes<br>
    </div>'''
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False, position='topright').add_to(m)
    plugins.Fullscreen(position='topleft').add_to(m)

    return m
