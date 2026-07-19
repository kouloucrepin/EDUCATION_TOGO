from .data import (
    load_onglet3_data, get_heatmap_matrix,
    get_heatmap_data, get_national_indicators,
    get_evolution_data, get_ranking_data,
)
from .heatmap import heatmap_html, heatmap_table_html
from .radar import radar_comparison_html
from .evolution import evolution_line_html
from .ranking import ranking_table_html, ranking_bar_html, ranking_matrix, ranking_matrix_html
from .dashboard_html import generer_dashboard_html, export_dashboard

__all__ = [
    'load_onglet3_data',
    'get_heatmap_data', 'get_heatmap_matrix', 'get_national_indicators',
    'get_evolution_data', 'get_ranking_data',
    'heatmap_html', 'heatmap_table_html',
    'radar_comparison_html',
    'evolution_line_html',
    'ranking_table_html', 'ranking_bar_html',
    'ranking_matrix', 'ranking_matrix_html',
    'generer_dashboard_html', 'export_dashboard',
]
