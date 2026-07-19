import os

from .data import load_onglet1_data, get_kpi_data, get_funnel_data, get_scatter_data
from .kpi import kpi_gauge_html
from .funnel_sankey import sankey_funnel_html
from .evolution import get_evolution_data, evolution_line_html, area_chart_univarie_html
from .scatter_budget import scatter_budget_html
from .table import indicator_table_html, indicator_table

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

DASHBOARD_CSS = '''
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f2f5; color: #333; }
.header {
  background: linear-gradient(135deg, #006A4E 0%, #00885E 50%, #00A86B 100%);
  color: white; padding: 24px 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.header h1 { font-size: 26px; font-weight: 700; }
.header p { font-size: 14px; opacity: 0.85; margin-top: 4px; }
.filters-bar {
  display: flex; gap: 16px; padding: 16px 32px; background: white;
  border-bottom: 1px solid #e0e0e0; align-items: center; flex-wrap: wrap;
}
.filters-bar .badge {
  background: #e8f5e9; color: #006A4E; padding: 6px 14px; border-radius: 20px;
  font-size: 13px; font-weight: 600;
}
.container { max-width: 1400px; margin: 0 auto; padding: 20px 32px; }
.section-title {
  font-size: 18px; font-weight: 700; color: #006A4E; margin-bottom: 16px;
  padding-bottom: 8px; border-bottom: 2px solid #006A4E;
}

/* --- KPI CARDS --- */
.kpi-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px;
}
@media (max-width: 1000px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .kpi-grid { grid-template-columns: 1fr; } }

.kpi-card {
  background: white; border-radius: 14px; padding: 12px 12px 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center;
  transition: transform 0.15s, box-shadow 0.15s;
  display: flex; flex-direction: column;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
.kpi-card .kpi-label {
  font-size: 13px; font-weight: 600; color: #555; margin-bottom: 2px;
  letter-spacing: 0.3px;
}
.kpi-card .kpi-gauge { margin: -10px 0 -5px; }
.kpi-card .kpi-spark { margin: -8px 0 -2px; }
.kpi-card .kpi-evolution {
  font-size: 12px; color: #666; padding: 4px 0 6px;
  border-top: 1px solid #f0f0f0; margin-top: 2px;
}

.negatif { color: #ef4444 !important; }
.positif { color: #22c55e !important; }

/* --- CHARTS --- */
.chart-card {
  background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }

/* --- TABLE --- */
table.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
table.data-table th {
  background: #006A4E; color: white; padding: 10px 12px; text-align: left; font-weight: 600;
}
table.data-table td { padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }
table.data-table tr:hover { background: #f5f5f5; }
table.data-table .up { color: #22c55e; font-weight: 600; }
table.data-table .down { color: #ef4444; font-weight: 600; }
'''

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Éducation Togo - Onglet 1</title>
<script src="https://assets.pyecharts.org/assets/v6/echarts.min.js"></script>
<style>{css}</style>
</head>
<body>

<div class="header">
  <h1>Le Système Éducatif Togolais en Chiffres</h1>
  <p>Dashboard interactif - Données INSEED 2013–2022</p>
</div>

<div class="filters-bar">
  <span class="badge">Année: {annee}</span>
  <span class="badge">Niveau: {niveau}</span>
  <span class="badge">Secteur: Total</span>
  <span style="margin-left:auto;font-size:13px;color:#666;">
    Source: <strong>06-education-resultats-scolaires.csv</strong>
  </span>
</div>

<div class="container">
  <div class="section-title">Indicateurs Clés</div>
  <div class="kpi-grid">{kpi_gauges}</div>

  <div class="two-col">
    <div>
      <div class="section-title">Entonnoir Éducatif</div>
      <div class="chart-card">{funnel}</div>
    </div>
    <div>
      <div class="section-title">Évolution des Taux d'Achèvement</div>
      <div class="chart-card">{evolution}</div>
    </div>
  </div>

  <div class="section-title">Dépenses vs Résultats</div>
  <div class="chart-card">{scatter}</div>

  <div class="section-title">Tableau des Indicateurs</div>
  <div class="chart-card" style="overflow-x:auto;">{table}</div>
</div>

</body>
</html>'''


def generer_dashboard_html(annee=2022, niveau='Tous'):
    dfs = load_onglet1_data()
    df6 = dfs['resultats']

    kpi = get_kpi_data(df6, annee=annee)
    funnel = get_funnel_data(df6, annee=annee)
    evol = get_evolution_data(df6)
    scatter = get_scatter_data(df6)
    table_rows = indicator_table(df6, niveau=niveau)

    return DASHBOARD_HTML.format(
        css=DASHBOARD_CSS,
        annee=annee,
        niveau=niveau,
        kpi_gauges=kpi_gauge_html(kpi),
        funnel=sankey_funnel_html(funnel, annee),
        evolution=evolution_line_html(evol, ""),
        scatter=scatter_budget_html(scatter),
        table=indicator_table_html(table_rows),
    )


def export_dashboard(path=None, annee=2022, niveau='Tous'):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'onglet1_dashboard.html')
    html = generer_dashboard_html(annee=annee, niveau=niveau)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Dashboard exporté: {path}')
    return path
