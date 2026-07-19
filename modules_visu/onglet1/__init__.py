from .data import (load_onglet1_data, filter_data, get_kpi_data, get_funnel_data,
                   get_funnel_evolution_data, get_scatter_data)
from .kpi import kpi_gauge_html
from .funnel_sankey import (sankey_funnel_chart, sankey_funnel_html,
                            funnel_evolution_bar_chart, funnel_evolution_bar_html)
from .scatter_budget import (scatter_budget_chart, scatter_budget_html,
                             scatter_budget_evolution_chart, scatter_budget_evolution_html)
from .table import (
    indicator_table, indicator_table_html,
    regional_indicator_table, regional_indicator_table_html,
    get_correlation_data, correlation_table_html,
)
from .evolution import (
    get_evolution_data, evolution_line_chart, evolution_line_html,
    get_evolution_par_secteur, evolution_secteur_chart, evolution_secteur_html,
    area_chart_univarie, area_chart_univarie_html,
)
from .dashboard_html import generer_dashboard_html, export_dashboard

__all__ = [
    'load_onglet1_data', 'filter_data', 'get_kpi_data', 'get_funnel_data',
    'get_funnel_evolution_data', 'get_scatter_data',
    'kpi_gauge_html',
    'sankey_funnel_chart', 'sankey_funnel_html',
    'funnel_evolution_bar_chart', 'funnel_evolution_bar_html',
    'scatter_budget_chart', 'scatter_budget_html',
    'scatter_budget_evolution_chart', 'scatter_budget_evolution_html',
    'indicator_table', 'indicator_table_html',
    'regional_indicator_table', 'regional_indicator_table_html',
    'get_correlation_data', 'correlation_table_html',
    'get_evolution_data', 'evolution_line_chart', 'evolution_line_html',
    'get_evolution_par_secteur', 'evolution_secteur_chart', 'evolution_secteur_html',
    'area_chart_univarie', 'area_chart_univarie_html',
    'generer_dashboard_html', 'export_dashboard',
]
