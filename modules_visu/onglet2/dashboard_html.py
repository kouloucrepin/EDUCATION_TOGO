import os
from .data import load_onglet2_data, get_counters, get_coso_aggregation
from .map import build_carte_interactive
from .coso_charts import coso_type_bar_html, coso_status_pie_html

DASHBOARD_CSS = '''
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f2f5; color: #333; }
.header {
  background: linear-gradient(135deg, #006A4E 0%, #00885E 50%, #00A86B 100%);
  color: white; padding: 20px 28px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.header h1 { font-size: 24px; font-weight: 700; }
.header p { font-size: 14px; opacity: 0.85; margin-top: 4px; }
.container { max-width: 1500px; margin: 0 auto; padding: 16px 24px; }
.section-title {
  font-size: 17px; font-weight: 700; color: #006A4E; margin: 20px 0 12px;
  padding-bottom: 6px; border-bottom: 2px solid #006A4E;
}
.chart-card {
  background: white; border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

/* COUNTERS */
.counter-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px;
}
@media (max-width: 600px) { .counter-grid { grid-template-columns: repeat(2, 1fr); } }
.counter-card {
  background: white; border-radius: 12px; padding: 16px; text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.counter-card .num { font-size: 28px; font-weight: 700; color: #006A4E; }
.counter-card .num.gold { color: #D4A017; }
.counter-card .label { font-size: 12px; color: #666; margin-top: 2px; }

/* MAP */
.map-container { height: 520px; border-radius: 12px; overflow: hidden; }

/* TWO COL */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }
'''


def generer_carte_interactive_html(dfs, regions=None):
    m = build_carte_interactive(dfs, regions=regions)
    return m.get_root().render()


def generer_dashboard_html(regions=None):
    dfs = load_onglet2_data()
    counters = get_counters(dfs, regions)
    type_rows, status_rows = get_coso_aggregation(dfs, regions)
    carte_html = generer_carte_interactive_html(dfs, regions)

    bar_html = coso_type_bar_html(type_rows) if type_rows else ''
    pie_html = coso_status_pie_html(status_rows) if status_rows else ''

    region_label = ', '.join(regions) if regions else 'Toutes les régions'

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Carte Interactive des Écoles et Infrastructures</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<script src="https://assets.pyecharts.org/assets/v6/echarts.min.js"></script>
<style>{DASHBOARD_CSS}</style>
</head>
<body>

<div class="header">
  <h1>Carte Interactive des Écoles et Infrastructures</h1>
  <p>Carte scolaire du Togo - {region_label}</p>
</div>

<div class="container">

  <div class="section-title">Indicateurs Clés</div>
  <div class="counter-grid">
    <div class="counter-card">
      <div class="num">{counters["total_ecoles"]:,}</div>
      <div class="label">Établissements</div>
    </div>
    <div class="counter-card">
      <div class="num">{counters["toilettes_total"]:,}</div>
      <div class="label">Blocs de toilettes ({counters["toilettes_par_ecole"]}/école)</div>
    </div>
    <div class="counter-card">
      <div class="num">{counters["terrain_sport"]:,}</div>
      <div class="label">Avec terrain sport ({counters["terrain_sport_pct"]}%)</div>
    </div>
  </div>

  <div class="section-title">Carte Interactive</div>
  <div class="chart-card map-container">
    {carte_html}
  </div>

  <div class="section-title">Analyse des Projets COSO</div>
  <div class="two-col">
    <div class="chart-card">{bar_html}</div>
    <div class="chart-card">{pie_html}</div>
  </div>

</div>

</body>
</html>'''


def export_dashboard(path=None, regions=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'onglet2_dashboard.html')
    html = generer_dashboard_html(regions=regions)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Dashboard exporté: {path}')
    return path
