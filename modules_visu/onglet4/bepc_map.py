import json
import math
import folium
from .config import TOGO_GEOJSON
from .data import get_bepc_by_region_sexe

ROSE = '#e91e63'
BLEU = '#1976d2'
COULEURS_Q = {1: '#22c55e', 2: '#f59e0b', 3: '#ef4444'}
LABELS_Q = {1: 'Q1 (faible écart)', 2: 'Q2 (écart moyen)', 3: 'Q3 (écart élevé)'}


def _centre_polygone(coords):
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _svg_donut(f_pct, m_pct, taille=56):
    """SVG donut Filles/Garçons avec trou central."""
    f = f_pct / 100
    m = m_pct / 100
    r = taille / 2
    trou = r * 0.45
    cx = cy = r

    def _arc(pct, decal=0):
        angle = 2 * math.pi * pct + decal
        x = cx + r * math.sin(angle)
        y = cy - r * math.cos(angle)
        return x, y

    parts = []
    if f > 0.001:
        x1, y1 = _arc(0)
        x2, y2 = _arc(f)
        large = 1 if f > 0.5 else 0
        parts.append(
            f'<path d="M{cx},{cy} L{x1},{y1} A{r},{r} 0 {large},1 {x2},{y2} Z" '
            f'fill="{ROSE}" stroke="white" stroke-width="0.5"/>')
    if m > 0.001:
        x1, y1 = _arc(0, 2 * math.pi * f)
        x2, y2 = _arc(m, 2 * math.pi * f)
        large = 1 if m > 0.5 else 0
        parts.append(
            f'<path d="M{cx},{cy} L{x1},{y1} A{r},{r} 0 {large},1 {x2},{y2} Z" '
            f'fill="{BLEU}" stroke="white" stroke-width="0.5"/>')

    return (
        f'<svg width="{taille}" height="{taille}" viewBox="0 0 {taille} {taille}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'{" ".join(parts)}'
        f'<circle cx="{cx}" cy="{cy}" r="{trou}" fill="white"/>'
        f'</svg>')


def _tertiles_ecarts(rows):
    """Calcule les seuils Q1/Q2/Q3 à partir des écarts."""
    ecarts = sorted(abs(r.get('Masculin', 0) - r.get('F\u00e9minin', 0))
                    for r in rows if r.get('F\u00e9minin') and r.get('Masculin')
                    and r['region'] not in ('Plateaux Ouest', 'Plateaux Est'))
    if not ecarts:
        return 0, 0
    n = len(ecarts)
    s1 = ecarts[max(0, n // 3 - 1)]
    s2 = ecarts[min(n - 1, 2 * n // 3 - 1)]
    return s1, s2


def _q_ecart(ecart, s1, s2):
    if ecart is None:
        return 0, '#ccc'
    e = abs(ecart)
    if e <= s1:
        return 1, COULEURS_Q[1]
    if e <= s2:
        return 2, COULEURS_Q[2]
    return 3, COULEURS_Q[3]


def _norm(nom):
    return nom.strip().upper().replace(' REGION', '').replace("'", "\\'")


def bepc_region_map_html(dfs, annee=2022):
    rows = get_bepc_by_region_sexe(dfs, annee=annee)
    rows = [r for r in rows if r['region'] not in ('Plateaux Ouest', 'Plateaux Est')]
    data = {}
    for r in rows:
        data[_norm(r['region'])] = r

    s1, s2 = _tertiles_ecarts(rows)

    with open(TOGO_GEOJSON, 'r', encoding='utf-8') as f:
        gj = json.load(f)

    m = folium.Map(location=[8.6, 0.9], zoom_start=7,
                   tiles='CartoDB positron', control_scale=True)

    for ft in gj['features']:
        nom = _norm(ft['properties'].get('shapeName', ''))
        d = data.get(nom)
        p = ft['properties']
        p['nom'] = nom
        if d:
            ecart = round(d.get('Masculin', 0) - d.get('F\u00e9minin', 0), 1) \
                if d.get('F\u00e9minin') and d.get('Masculin') else 0
            q, couleur = _q_ecart(ecart, s1, s2)
            p['_ecart'] = ecart
            p['_q'] = q
            p['_couleur'] = couleur
            p['_f'] = f"{d['F\u00e9minin']:.1f}%"
            p['_g'] = f"{d['Masculin']:.1f}%"
            p['_t'] = f"{d['Total']:.1f}%"
        else:
            p['_ecart'] = None
            p['_q'] = 0
            p['_couleur'] = '#ccc'
            p['_f'] = p['_g'] = p['_t'] = 'N/D'

    folium.GeoJson(
        gj,
        style_function=lambda ft: {
            'fillColor': ft['properties'].get('_couleur', '#ccc'),
            'color': 'white',
            'weight': 1.4,
            'fillOpacity': 0.8 if ft['properties'].get('_ecart') is not None else 0.35,
        },
        highlight_function=lambda ft: {'weight': 3, 'color': '#1A202C', 'fillOpacity': 0.95},
        tooltip=folium.GeoJsonTooltip(
            fields=['nom', '_f', '_g', '_t', '_ecart'],
            aliases=['', 'Filles :', 'Garçons :', 'Total :', 'Écart M-F :'],
            style='font-size:12px;',
        ),
    ).add_to(m)

    # Donut markers at region centers
    for ft in gj['features']:
        nom = _norm(ft['properties'].get('shapeName', ''))
        d = data.get(nom)
        if not d:
            continue
        coords = ft['geometry']['coordinates']
        if ft['geometry']['type'] == 'Polygon':
            ctr_lon, ctr_lat = _centre_polygone(coords[0])
        else:
            ctr_lon, ctr_lat = _centre_polygone(coords[0][0])

        f_v = d['F\u00e9minin'] or 0
        m_v = d['Masculin'] or 0
        total = f_v + m_v
        f_pct = f_v / total * 100 if total else 50
        m_pct = m_v / total * 100 if total else 50

        svg = _svg_donut(f_pct, m_pct, taille=56)
        html = f'<div style="text-align:center;font-size:10px;font-weight:700;color:#333;">' \
               f'{svg}<br><span style="background:rgba(255,255,255,0.85);padding:1px 4px;border-radius:3px;">' \
               f'{nom}</span></div>'

        folium.Marker(
            location=[ctr_lat, ctr_lon],
            icon=folium.DivIcon(html=html, icon_size=(70, 80), icon_anchor=(35, 70)),
        ).add_to(m)

    # Légende Q1/Q2/Q3
    legend_html = f'''
    <div style="position:fixed;bottom:20px;left:20px;background:white;padding:8px 12px;
                border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,0.2);font-size:12px;z-index:9999;">
      <div style="font-weight:700;margin-bottom:4px;">Écart Filles-Garçons — {s1:.1f} / {s2:.1f} pts</div>
      <div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{COULEURS_Q[1]};margin-right:4px;"></span>{LABELS_Q[1]}</div>
      <div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{COULEURS_Q[2]};margin-right:4px;"></span>{LABELS_Q[2]}</div>
      <div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{COULEURS_Q[3]};margin-right:4px;"></span>{LABELS_Q[3]}</div>
    </div>'''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m.get_root().render()
