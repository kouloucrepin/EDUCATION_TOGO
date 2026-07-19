from pyecharts.charts import Line, Scatter
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from .config import COULEURS


def scatter_budget_chart(rows):
    if not rows:
        return None

    niveaux = ['Primaire', 'Collège', 'Lycée']
    colors = {'Primaire': '#22c55e', 'Collège': '#f59e0b', 'Lycée': '#ef4444'}

    scatter = (
        Scatter(init_opts=opts.InitOpts(width='100%', height='400px', bg_color='transparent'))
        .set_global_opts(
            # Pas de titre interne : la card du dashboard porte déjà le titre
            xaxis_opts=opts.AxisOpts(
                name='Part du budget éducation (%)',
                name_location='middle',
                name_gap=30,
                type_='value',
                min_=10,
                max_=22,
                splitline_opts=opts.SplitLineOpts(is_show=True),
                axislabel_opts=opts.LabelOpts(formatter='{value}%'),
            ),
            yaxis_opts=opts.AxisOpts(
                name="Taux d'achèvement (%)",
                type_='value',
                min_=0,
                max_=100,
                splitline_opts=opts.SplitLineOpts(is_show=True),
                axislabel_opts=opts.LabelOpts(formatter='{value}%'),
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger='item',
                formatter=JsCode(
                    """function(p) {
                        var d = p.data;
                        return '<b>' + d[4] + '</b><br/>' +
                               'Année: ' + d[3] + '<br/>' +
                               'Part budget: ' + d[0] + '%<br/>' +
                               'Achèvement: ' + d[1] + '%<br/>' +
                               'Dépenses: ' + (d[2] || 'N/A') + ' Md FCFA';
                    }"""
                ),
            ),
            legend_opts=opts.LegendOpts(pos_top='0'),
        )
    )

    for niv in niveaux:
        pts = sorted([r for r in rows if r['niveau'] == niv], key=lambda x: x['annee'])
        if not pts:
            continue
        x_vals = [r['part_budget'] for r in pts]
        y_vals = [r['achevement'] for r in pts]
        scatter.add_xaxis(x_vals)
        scatter.add_yaxis(
            niv,
            y_vals,
            symbol_size=12,
            color=colors[niv],
            label_opts=opts.LabelOpts(is_show=False),
        )
        # Injecte les dimensions supplémentaires attendues par le tooltip :
        # [part_budget, achèvement, dépenses, année, niveau]
        scatter.options['series'][-1]['data'] = [
            [r['part_budget'], r['achevement'], r['depenses'], r['annee'], r['niveau']]
            for r in pts
        ]

    # Grille étendue sur toute la largeur de la card
    scatter.options['grid'] = {'left': '2%', 'right': '4%', 'top': 36, 'bottom': 48, 'containLabel': True}
    return scatter


def scatter_budget_html(rows):
    chart = scatter_budget_chart(rows)
    if chart is None:
        return '<p style="color:red">Données insuffisantes pour le scatter</p>'
    return f'<div id="scatter_budget">{chart.render_embed()}</div>'


def scatter_budget_evolution_chart(rows):
    """Mêmes axes que le scatter (x = part du budget, y = achèvement), mais
    les points de chaque niveau sont reliés dans l'ordre chronologique
    2013 → 2022 : on suit la trajectoire année après année."""
    if not rows:
        return None

    niveaux = ['Primaire', 'Collège', 'Lycée']
    colors = {'Primaire': '#22c55e', 'Collège': '#f59e0b', 'Lycée': '#ef4444'}

    line = (
        Line(init_opts=opts.InitOpts(width='100%', height='400px', bg_color='transparent'))
        .add_xaxis([])
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                name='Part du budget éducation (%)',
                name_location='middle',
                name_gap=30,
                type_='value',
                min_=10,
                max_=22,
                splitline_opts=opts.SplitLineOpts(is_show=True),
                axislabel_opts=opts.LabelOpts(formatter='{value}%'),
            ),
            yaxis_opts=opts.AxisOpts(
                name="Taux d'achèvement (%)",
                type_='value',
                min_=0,
                max_=100,
                splitline_opts=opts.SplitLineOpts(is_show=True),
                axislabel_opts=opts.LabelOpts(formatter='{value}%'),
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger='item',
                formatter=JsCode(
                    """function(p) {
                        var d = p.data;
                        return '<b>' + d[4] + '</b><br/>' +
                               'Année: ' + d[3] + '<br/>' +
                               'Part budget: ' + d[0] + '%<br/>' +
                               'Achèvement: ' + d[1] + '%<br/>' +
                               'Dépenses: ' + (d[2] || 'N/A') + ' Md FCFA';
                    }"""
                ),
            ),
            legend_opts=opts.LegendOpts(pos_top='0'),
        )
    )

    for niv in niveaux:
        pts = sorted([r for r in rows if r['niveau'] == niv], key=lambda x: x['annee'])
        if not pts:
            continue
        line.add_yaxis(
            niv,
            [],
            color=colors[niv],
            symbol='circle',
            symbol_size=10,
            label_opts=opts.LabelOpts(
                is_show=True,
                position='top',
                font_size=9,
                color=colors[niv],
                formatter=JsCode('function(p){ return p.data[3]; }'),
            ),
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=0.75),
        )
        # Points [x=part_budget, y=achèvement, dépenses, année, niveau], reliés
        # dans l'ordre des années (l'axe x est de type valeur, pas catégorie)
        line.options['series'][-1]['data'] = [
            [r['part_budget'], r['achevement'], r['depenses'], r['annee'], r['niveau']]
            for r in pts
        ]

    line.options['grid'] = {'left': '2%', 'right': '4%', 'top': 36, 'bottom': 48, 'containLabel': True}
    return line


def scatter_budget_evolution_html(rows):
    chart = scatter_budget_evolution_chart(rows)
    if chart is None:
        return "<p style=\"color:red\">Données insuffisantes pour l'évolution</p>"
    return f'<div id="scatter_budget_evo">{chart.render_embed()}</div>'
