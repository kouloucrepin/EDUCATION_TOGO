import os
import re
from .config import REGIONS_09_SIMPLE
from .data import load_onglet4_data, get_ecart_regional, get_prescolaire_data
from .bepc_lines import bepc_evolution_html
from .ecart_bars import ecart_bar_html
from .ecart_map import ecart_choropleth_html
from .prescolaire import prescolaire_pie_html

DASHBOARD_CSS = '''
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f2f5; color: #333; }
.header {
  background: linear-gradient(135deg, #8B008B 0%, #A020F0 50%, #DA70D6 100%);
  color: white; padding: 20px 28px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.header h1 { font-size: 24px; font-weight: 700; }
.header p { font-size: 14px; opacity: 0.85; margin-top: 4px; }
.filters-bar {
  background: white; padding: 12px 28px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  display: flex; gap: 20px; align-items: center; flex-wrap: wrap;
}
.filters-bar label { font-size: 13px; font-weight: 600; color: #333; }
.filters-bar select {
  padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px;
  font-size: 13px; background: white; min-width: 140px;
}
.filters-bar .filter-group { display: flex; align-items: center; gap: 6px; }
.container { max-width: 1400px; margin: 0 auto; padding: 16px 24px; }
.section-title {
  font-size: 17px; font-weight: 700; color: #8B008B; margin: 20px 0 12px;
  padding-bottom: 6px; border-bottom: 2px solid #8B008B;
}
.chart-card {
  background: white; border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden;
}
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px; }
.kpi-card {
  background: white; border-radius: 12px; padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center;
  border-left: 5px solid #8B008B;
}
.kpi-card.filles { border-left-color: #e91e63; }
.kpi-card.garcons { border-left-color: #1976d2; }
.kpi-card.ecart { border-left-color: #f59e0b; }
.kpi-value { font-size: 32px; font-weight: 800; line-height: 1.2; }
.kpi-label { font-size: 13px; color: #666; margin-top: 4px; }
.kpi-evol { font-size: 12px; margin-top: 6px; padding: 2px 10px; border-radius: 10px; display: inline-block; }
.kpi-evol.up { background: #dcfce7; color: #16a34a; }
.kpi-evol.neutral { background: #fef3c7; color: #d97706; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .two-col, .three-col, .kpi-grid { grid-template-columns: 1fr; } }
'''

RX_EMBED = re.compile(r'<div\s+id="[^"]*"[^>]*>.*?</div>\s*<script>.*?</script>', re.DOTALL)


def _chart_embed(fn, *args, **kwargs):
    html = fn(*args, **kwargs)
    m = RX_EMBED.search(html)
    if m:
        return m.group(0)
    # fallback: extract everything after <body> and before </body>
    body = re.search(r'<body[^>]*>(.*)</body>', html, re.DOTALL)
    if body:
        return body.group(1).strip()
    return html


def _options_html(selected_region, selected_annee):
    annees = [str(a) for a in range(2011, 2023)]
    anne_html = ''.join(
        f'<option value="{a}"{" selected" if a==selected_annee else ""}>{a}</option>'
        for a in annees
    )
    regions_html = ''.join(
        f'<option value="{r}"{" selected" if r==selected_region else ""}>{r}</option>'
        for r in REGIONS_09_SIMPLE
    )
    return f'''<div class="filter-group">
  <label for="filtre_region">R\u00e9gion</label>
  <select id="filtre_region">{regions_html}</select>
</div>
<div class="filter-group">
  <label for="filtre_annee">Ann\u00e9e</label>
  <select id="filtre_annee">{anne_html}</select>
</div>
<div class="filter-group">
  <button onclick="appliquerFiltres()" style="padding:6px 16px;background:#8B008B;color:white;border:none;border-radius:6px;font-size:13px;cursor:pointer;">Appliquer</button>
</div>'''


def _kpi_html(dfs, annee):
    rows = get_ecart_regional(dfs, annee=annee)
    togo = [r for r in rows if r['region'] == 'Togo']
    if not togo:
        return ''
    t = togo[0]
    f = t.get('F\u00e9minin', 0) or 0
    m = t.get('Masculin', 0) or 0
    ecart = t.get('ecart', 0) or 0
    e_accent = '\u00e9'
    up_arrow = '\u2191'
    down_arrow = '\u2193'

    # Valeurs 2011
    rows_2011 = get_ecart_regional(dfs, annee=2011)
    t11 = [r for r in rows_2011 if r['region'] == 'Togo']
    if t11:
        f11 = t11[0].get('F\u00e9minin', 0) or 0
        m11 = t11[0].get('Masculin', 0) or 0
        ecart11 = t11[0].get('ecart', 0) or 0
        evol_f = f - f11
        evol_m = m - m11
        evol_ecart = ecart11 - ecart
    else:
        f11 = m11 = ecart11 = 0
        evol_f = evol_m = evol_ecart = 0

    def evol_html(v, unite='pts'):
        if v > 0:
            return f'<span class="kpi-evol up">{up_arrow} +{v:.1f} {unite}</span>'
        elif v < 0:
            return f'<span class="kpi-evol up">{down_arrow} {v:.1f} {unite}</span>'
        else:
            return f'<span class="kpi-evol neutral">{v:.1f} {unite}</span>'

    return f'''
<div class="kpi-grid">
  <div class="kpi-card filles">
    <div class="kpi-value" style="color:#e91e63;">{f:.1f}%</div>
    <div class="kpi-label">Taux BEPC &mdash; Filles ({annee})</div>
    <div>{evol_html(evol_f)}</div>
    <div class="kpi-label" style="font-size:11px;margin-top:2px;">Niveau {annee} ({e_accent}tait {f11:.1f}% en 2011)</div>
  </div>
  <div class="kpi-card garcons">
    <div class="kpi-value" style="color:#1976d2;">{m:.1f}%</div>
    <div class="kpi-label">Taux BEPC &mdash; Gar\u00e7ons ({annee})</div>
    <div>{evol_html(evol_m)}</div>
    <div class="kpi-label" style="font-size:11px;margin-top:2px;">Niveau {annee} ({e_accent}tait {m11:.1f}% en 2011)</div>
  </div>
  <div class="kpi-card ecart">
    <div class="kpi-value" style="color:#d97706;">{ecart:.1f} pts</div>
    <div class="kpi-label">\u00c9cart Filles &mdash; Gar\u00e7ons</div>
    <div>{evol_html(evol_ecart)}</div>
    <div class="kpi-label" style="font-size:11px;margin-top:2px;">Se r\u00e9duit ({e_accent}tait {ecart11:.1f} pts en 2011)</div>
  </div>
</div>'''


def generer_dashboard_html(region='Togo', annee=2022):
    dfs = load_onglet4_data()

    bepc = _chart_embed(bepc_evolution_html, dfs, region=region)
    ecart_bars = _chart_embed(ecart_bar_html, dfs, annee=annee)
    ecart_map = _chart_embed(ecart_choropleth_html, dfs, annee=annee)
    pie = _chart_embed(prescolaire_pie_html, dfs)
    kpis = _kpi_html(dfs, annee)
    filters = _options_html(region, str(annee))

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>\u00c9cart Filles-Gar\u00e7ons dans l'\u00c9ducation</title>
<script src="https://assets.pyecharts.org/assets/v6/echarts.min.js"></script>
<style>{DASHBOARD_CSS}</style>
<script>
function appliquerFiltres() {{
  var region = document.getElementById('filtre_region').value;
  var annee = document.getElementById('filtre_annee').value;
  var params = new URLSearchParams();
  if (region !== 'Togo') params.set('region', region);
  if (annee !== '2022') params.set('annee', annee);
  var qs = params.toString();
  window.location.search = qs ? '?' + qs : '';
}}
window.addEventListener('DOMContentLoaded', function() {{
  var p = new URLSearchParams(window.location.search);
  if (p.has('region')) document.getElementById('filtre_region').value = p.get('region');
  if (p.has('annee')) document.getElementById('filtre_annee').value = p.get('annee');
}});
</script>
</head>
<body>

<div class="header">
  <h1>\u00c9cart Filles-Gar\u00e7ons dans l'\u00c9ducation</h1>
  <p>Disparit\u00e9s de genre au BEPC et personnel du pr\u00e9scolaire \u2014 Donn\u00e9es INSEED 2011\u20132022</p>
</div>

<div class="filters-bar">{filters}</div>

<div class="container">

  {kpis}

  <div class="section-title">\u00c9volution du Taux d\u2019Admission au BEPC par Sexe</div>
  <div class="chart-card">{bepc}</div>

  <div class="two-col">
    <div>
      <div class="section-title">\u00c9cart F/M par R\u00e9gion ({annee})</div>
      <div class="chart-card">{ecart_bars}</div>
    </div>
    <div>
      <div class="section-title">Carte de l\u2019\u00c9cart F/M ({annee})</div>
      <div class="chart-card">{ecart_map}</div>
    </div>
  </div>

  <div class="section-title">R\u00e9partition R\u00e9gionale des Enseignants du Pr\u00e9scolaire (2021-2022)</div>
  <div class="chart-card">{pie}</div>

</div>

</body>
</html>'''


def export_dashboard(path=None, region='Togo', annee=2022):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'onglet4_dashboard.html')
    html = generer_dashboard_html(region=region, annee=annee)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Dashboard export\u00e9: {path}')
    return path
