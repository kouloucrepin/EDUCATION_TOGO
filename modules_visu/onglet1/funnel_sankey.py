from pyecharts.charts import Bar, Sankey
from pyecharts import options as opts

# Couleurs de l'entonnoir : un ton par niveau (palette Togo)
COULEURS_NIVEAUX = {
    'Primaire': '#006A4E',
    'Collège': '#D4A017',
    'Lycée': '#EF3340',
}


def sankey_funnel_chart(data, annee):
    if not data or len(data) < 2:
        return None

    nodes = []
    links = []
    for d in data:
        nodes.append({'name': f"{d['niveau']}\n{d['taux']:.1f}%"})
    for i in range(len(data) - 1):
        val_amont = data[i]['taux']
        val_aval = data[i + 1]['taux']
        perte = val_amont - val_aval
        links.append({
            'source': f"{data[i]['niveau']}\n{data[i]['taux']:.1f}%",
            'target': f"{data[i + 1]['niveau']}\n{data[i + 1]['taux']:.1f}%",
            'value': round(val_aval, 1),
        })
        links.append({
            'source': f"{data[i]['niveau']}\n{data[i]['taux']:.1f}%",
            'target': f"Perte\n{perte:.1f}%",
            'value': round(perte, 1),
        })
        nodes.append({'name': f"Perte\n{perte:.1f}%"})

    sankey = (
        Sankey(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
        .add(
            'Flux',
            nodes,
            links,
            linestyle_opt=opts.LineStyleOpts(opacity=0.4, curve=0.5, color='source'),
            label_opts=opts.LabelOpts(font_size=12, position='right'),
            node_width=20,
            node_gap=12,
            pos_top='3%',
            pos_bottom='3%',
            pos_left='5%',
            pos_right='15%',
        )
        .set_global_opts(
            # Pas de titre interne : la card du dashboard porte déjà le titre
            tooltip_opts=opts.TooltipOpts(
                trigger='item',
                formatter='{b}: {c}%',
            ),
        )
    )
    return sankey


def sankey_funnel_html(data, annee):
    chart = sankey_funnel_chart(data, annee)
    if chart is None:
        return '<p style="color:red">Données insuffisantes pour l\'entonnoir</p>'
    return f'<div id="sankey_funnel">{chart.render_embed()}</div>'


def funnel_evolution_bar_chart(evo):
    """Barres groupées : taux d'achèvement des 3 niveaux de l'entonnoir par année."""
    if not evo or not evo.get('annees'):
        return None

    bar = Bar(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
    bar.add_xaxis([str(a) for a in evo['annees']])
    for niveau, valeurs in evo['series'].items():
        bar.add_yaxis(
            niveau, valeurs,
            itemstyle_opts=opts.ItemStyleOpts(color=COULEURS_NIVEAUX.get(niveau)),
            label_opts=opts.LabelOpts(is_show=False),
        )
    bar.set_global_opts(
        legend_opts=opts.LegendOpts(pos_top=0),
        xaxis_opts=opts.AxisOpts(
            axislabel_opts=opts.LabelOpts(font_size=11),
        ),
        yaxis_opts=opts.AxisOpts(
            name='%', name_location='end',
            axislabel_opts=opts.LabelOpts(font_size=11),
        ),
        tooltip_opts=opts.TooltipOpts(trigger='axis', axis_pointer_type='shadow'),
    )
    bar.options['grid'] = {'left': '2%', 'right': '2%', 'top': 36, 'bottom': 8, 'containLabel': True}
    return bar


def funnel_evolution_bar_html(evo):
    chart = funnel_evolution_bar_chart(evo)
    if chart is None:
        return '<p style="color:red">Données insuffisantes pour l\'évolution de l\'entonnoir</p>'
    return f'<div id="funnel_evolution">{chart.render_embed()}</div>'
