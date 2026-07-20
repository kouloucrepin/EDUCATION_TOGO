from .data import (
    load_onglet4_data,
    get_bepc_data,
    get_bepc_by_region_sexe,
    get_bepc_table_data,
    get_ecart_regional,
    get_prescolaire_data,
    get_prescolaire_par_inspection,
    get_prescolaire_par_region,
    get_prescolaire_matrice,
)
from .bepc_lines import bepc_evolution_html
from .bepc_map import bepc_region_map_html
from .ecart_bars import ecart_bar_html
from .ecart_map import ecart_choropleth_html
from .prescolaire import prescolaire_pie_html, top_inspections_bar_html, prescolaire_table_html
from .dashboard_html import generer_dashboard_html, export_dashboard

__all__ = [
    'load_onglet4_data',
    'get_bepc_data', 'get_bepc_by_region_sexe', 'get_bepc_table_data', 'get_ecart_regional',
    'get_prescolaire_data', 'get_prescolaire_par_inspection', 'get_prescolaire_par_region',
    'bepc_evolution_html',
    'bepc_region_map_html',
    'ecart_bar_html',
    'ecart_choropleth_html',
    'prescolaire_pie_html', 'top_inspections_bar_html', 'prescolaire_table_html',
    'get_prescolaire_matrice',
    'generer_dashboard_html', 'export_dashboard',
]
