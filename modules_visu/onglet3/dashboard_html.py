import os
from .config import REGIONS
from .data import load_onglet3_data, get_heatmap_matrix
from .heatmap import heatmap_html
from .radar import radar_comparison_html
from .evolution import evolution_line_html
from .ranking import ranking_table_html

DASHBOARD_CSS = '''
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f2f5; color: #333; }
.header {
  background: linear-gradient(135deg, #006A4E 0%, #00885E 50%, #00A86B 100%);
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
  font-size: 17px; font-weight: 700; color: #006A4E; margin: 20px 0 12px;
  padding-bottom: 6px; border-bottom: 2px solid #006A4E;
}
.chart-card {
  background: white; border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }

.rank-table { width:100%; border-collapse:collapse; font-size:13px; }
.rank-table th { background:#006A4E; color:white; padding:10px 12px; text-align:left; font-weight:600; }
.rank-table td { padding:8px 12px; border-bottom:1px solid #e0e0e0; }
.rank-table tr:hover { background:#f5f5f5; }
.rank-num { font-weight:700; color:#666; width:40px; }
.rank-up { color:#22c55e; font-weight:700; }
.rank-mid { color:#eab308; font-weight:700; }
.rank-down { color:#ef4444; font-weight:700; }
'''


def _options_html(selected_annee, selected_sexe, selected_region_a, selected_region_b):
    annees = ['2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']

    opt = ''
    annee_html = ''.join(f'<option value="{a}"{" selected" if a==selected_annee else ""}>{a}</option>'
                         for a in annees)
    opt += f'''<div class="filter-group">
  <label for="filtre_annee">Ann&eacute;e</label>
  <select id="filtre_annee">
    <option value="">Derni&egrave;re dispo</option>
    {annee_html}
  </select>
</div>'''

    sexes = ['Total', 'Féminin', 'Masculin']
    sexe_html = ''.join(f'<option value="{s}"{" selected" if s==selected_sexe else ""}>{s}</option>'
                        for s in sexes)
    opt += f'''<div class="filter-group">
  <label for="filtre_sexe">Sexe</label>
  <select id="filtre_sexe">{sexe_html}</select>
</div>'''

    regions_html = ''.join(f'<option value="{r}"{" selected" if r==selected_region_a else ""}>{r}</option>'
                           for r in REGIONS)
    opt += f'''<div class="filter-group">
  <label for="filtre_ra">R&eacute;gion A</label>
  <select id="filtre_ra">{regions_html}</select>
</div>'''

    regions_html_b = ''.join(f'<option value="{r}"{" selected" if r==selected_region_b else ""}>{r}</option>'
                             for r in REGIONS)
    opt += f'''<div class="filter-group">
  <label for="filtre_rb">R&eacute;gion B</label>
  <select id="filtre_rb">{regions_html_b}</select>
</div>'''

    opt += '''<div class="filter-group">
  <button onclick="appliquerFiltres()" style="padding:6px 16px;background:#006A4E;color:white;border:none;border-radius:6px;font-size:13px;cursor:pointer;">Appliquer</button>
</div>'''

    return opt


def generer_dashboard_html(annee=None, sexe='Total',
                           region_a='Kara', region_b='Savanes'):
    dfs = load_onglet3_data()
    matrix = get_heatmap_matrix(dfs, annee=annee, sexe=sexe)

    heat = heatmap_html(matrix)
    radar = radar_comparison_html(dfs, region_a=region_a, region_b=region_b,
                                  annee=annee, sexe=sexe)
    evol_transition = evolution_line_html(dfs, indicateur='transition', sexe=sexe)
    evol_bepc = evolution_line_html(dfs, indicateur='bepc', sexe=sexe)
    table = ranking_table_html(dfs, annee=annee, sexe=sexe)

    filters = _options_html(
        str(annee) if annee else '',
        sexe, region_a, region_b
    )

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Comparateur R\u00e9gional des Performances Scolaires</title>
<script src="https://assets.pyecharts.org/assets/v6/echarts.min.js"></script>
<style>{DASHBOARD_CSS}</style>
<script>
function appliquerFiltres() {{
  var annee = document.getElementById('filtre_annee').value;
  var sexe = document.getElementById('filtre_sexe').value;
  var ra = document.getElementById('filtre_ra').value;
  var rb = document.getElementById('filtre_rb').value;
  var params = new URLSearchParams();
  if (annee) params.set('annee', annee);
  if (sexe !== 'Total') params.set('sexe', sexe);
  if (ra !== 'Kara') params.set('ra', ra);
  if (rb !== 'Savanes') params.set('rb', rb);
  var qs = params.toString();
  window.location.search = qs ? '?' + qs : '';
}}
window.addEventListener('DOMContentLoaded', function() {{
  var p = new URLSearchParams(window.location.search);
  if (p.has('annee')) document.getElementById('filtre_annee').value = p.get('annee');
  if (p.has('sexe')) document.getElementById('filtre_sexe').value = p.get('sexe');
  if (p.has('ra')) document.getElementById('filtre_ra').value = p.get('ra');
  if (p.has('rb')) document.getElementById('filtre_rb').value = p.get('rb');
}});
</script>
</head>
<body>

<div class="header">
  <h1>Comparateur R\u00e9gional des Performances Scolaires</h1>
  <p>Analyse par r\u00e9gion \u2014 Donn\u00e9es INSEED 2014\u20132022</p>
</div>

<div class="filters-bar">{filters}</div>

<div class="container">

  <div class="section-title">Matrice R\u00e9gion \u00d7 Indicateur</div>
  <div class="chart-card">{heat}</div>

  <div class="two-col">
    <div>
      <div class="section-title">Comparaison Radar</div>
      <div class="chart-card">{radar}</div>
    </div>
    <div>
      <div class="section-title">Classement des R\u00e9gions</div>
      <div class="chart-card" style="overflow-x:auto;">{table}</div>
    </div>
  </div>

  <div class="section-title">\u00c9volution de la Transition Primaire \u2192 Secondaire</div>
  <div class="chart-card">{evol_transition}</div>

  <div class="section-title">\u00c9volution du Taux d\u2019Admission au BEPC</div>
  <div class="chart-card">{evol_bepc}</div>

</div>

</body>
</html>'''


def export_dashboard(path=None, annee=None, sexe='Total',
                     region_a='Kara', region_b='Savanes'):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'onglet3_dashboard.html')
    html = generer_dashboard_html(annee=annee, sexe=sexe,
                                  region_a=region_a, region_b=region_b)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Dashboard export\u00e9: {path}')
    return path
