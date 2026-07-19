import pandas as pd
import folium
from folium import plugins
from .config import (
    COULEURS_CATEGORIE, COULEURS_TOILETTE,
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


def _ecole_color(cat):
    cat = _s(cat)
    for key, color in COULEURS_CATEGORIE.items():
        if key.lower() in cat.lower():
            return color
    return '#9ca3af'


def _toilette_color(t):
    t_clean = _s(t).strip('{}')
    for key, color in COULEURS_TOILETTE.items():
        if key.lower() in t_clean.lower():
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
              '<br>Inspection: ' + row[6]);
  return m;
}
"""

_CALLBACK_BATIMENTS = """
function (row) {
  var f = row[2] || 'N/a';
  var color = '#6b7280';
  if (f.indexOf('Non fonctionnel') !== -1) color = '#ef4444';
  else if (f.indexOf('Salle de classe') !== -1) color = '#0d9488';
  var m = L.circleMarker(new L.LatLng(row[0], row[1]),
    {radius: 4, color: 'white', weight: 1, fillColor: color, fillOpacity: 0.75});
  m.bindPopup('<b>B\\u00e2timent scolaire</b><br>Fonction: ' + f +
              '<br>Ann\\u00e9e: ' + (row[3] || 'N/a') + '<br>R\\u00e9gion: ' + row[4]);
  return m;
}
"""

_CALLBACK_TOILETTES = """
function (row) {
  var t = (row[2] || '').replace(/[{}]/g, '');
  var color = '#9ca3af';
  if (t.indexOf('seches') !== -1) color = '#92400e';
  else if (t.indexOf('eau') !== -1) color = '#2563eb';
  else if (t.indexOf('WC') !== -1) color = '#0ea5e9';
  else if (t.indexOf('Pissoti') !== -1) color = '#a3e635';
  var m = L.circleMarker(new L.LatLng(row[0], row[1]),
    {radius: 4, color: 'white', weight: 1, fillColor: color, fillOpacity: 0.8});
  m.bindPopup('Type: ' + t + '<br>R\\u00e9gion: ' + row[3] +
              '<br>\\u00c9tablissement: ' + row[4]);
  return m;
}
"""


def build_carte_interactive(dfs, regions=None, prefecture=None, commune=None,
                            show_toilettes=True, show_coso=True, show_batiments=True):
    ecoles = get_ecoles_points(dfs, regions, prefecture, commune)
    toilettes = get_toilettes_points(dfs, regions, prefecture, commune) if show_toilettes else []
    coso = get_coso_projets(dfs, regions, prefecture, commune) if show_coso else []

    m = folium.Map(location=CARTE_CENTRE, zoom_start=CARTE_ZOOM,
                   tiles='CartoDB positron', control_scale=True)

    # Zoom automatique sur le territoire sélectionné (préfecture ou commune)
    if (prefecture or commune) and ecoles:
        lats = [p['lat'] for p in ecoles]
        lons = [p['lon'] for p in ecoles]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(24, 24))

    # Layer 1: Écoles (FastMarkerCluster - données embarquées, marqueurs créés côté client)
    ecole_data = [
        [p['lat'], p['lon'], _s(p['nom']), _s(p['categorie']),
         _s(p['region']), _s(p['prefecture']), _s(p['inspection'])]
        for p in ecoles
    ]
    plugins.FastMarkerCluster(
        ecole_data,
        callback=_CALLBACK_ECOLES,
        name='Établissements scolaires',
        overlay=True, control=True, show=True,
        options={
            'maxClusterRadius': 50,
            'spiderfyOnMaxZoom': True,
            'disableClusteringAtZoom': 14,
        },
    ).add_to(m)

    # Layer 2: Toilettes (FastMarkerCluster)
    if show_toilettes:
        toilette_data = [
            [p['lat'], p['lon'], _s(p['type']), _s(p['region']), _s(p['etab'])]
            for p in toilettes
        ]
        plugins.FastMarkerCluster(
            toilette_data,
            callback=_CALLBACK_TOILETTES,
            name='Toilettes',
            overlay=True, control=True, show=False,
            options={
                'maxClusterRadius': 40,
                'disableClusteringAtZoom': 14,
            },
        ).add_to(m)

    # Layer 3: Projets COSO (86 points - rendu serveur classique)
    if show_coso:
        fg_coso = folium.FeatureGroup(name='Projets COSO',
                                      overlay=True,
                                      control=True,
                                      show=True)
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

    # Layer 4 : Bâtiments scolaires (fichier 03 — 28 000 polygones ramenés à
    # des points). Présent dans le contrôle de couches mais DÉCOCHÉ par défaut
    # (show=False) : aucun coût de rendu tant que l'utilisateur ne l'active pas.
    if show_batiments:
        from .data import get_batiments_points
        batiments = get_batiments_points(dfs, regions, prefecture, commune)
        if batiments:
            bati_data = [
                [p['lat'], p['lon'], _s(p['fonction']), _s(p['annee']), _s(p['region'])]
                for p in batiments
            ]
            plugins.FastMarkerCluster(
                bati_data,
                callback=_CALLBACK_BATIMENTS,
                name='Bâtiments scolaires',
                overlay=True, control=True, show=False,
                options={
                    'maxClusterRadius': 40,
                    'disableClusteringAtZoom': 15,
                },
            ).add_to(m)

    # Legend HTML
    legend_html = '''
    <div style="position:fixed;bottom:24px;left:12px;z-index:9999;
                background:white;padding:12px 14px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.15);font-size:12px;
                max-height:260px;overflow-y:auto;width:200px;">
      <b>Légende</b><br>
      <span style="color:#22c55e;">●</span> Primaire<br>
      <span style="color:#f59e0b;">●</span> Collège<br>
      <span style="color:#ef4444;">●</span> Lycée<br>
      <span style="color:#3b82f6;">●</span> Maternelle<br>
      <span style="color:#2563eb;">●</span> Toilette (eau)<br>
      <span style="color:#92400e;">●</span> Toilette (sèche)<br>
      <span style="color:#eab308;">●</span> COSO provisoire<br>
      <span style="color:#22c55e;">●</span> COSO définitif<br>
      <span style="color:#0d9488;">●</span> Bâtiment (salle de classe)<br>
      <span style="color:#6b7280;">●</span> Bâtiment (autre fonction)<br>
      <span style="color:#ef4444;">●</span> Bâtiment non fonctionnel<br>
    </div>'''
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False, position='topright').add_to(m)
    plugins.Fullscreen(position='topleft').add_to(m)

    return m
