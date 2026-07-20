from pyecharts.charts import Bar
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from .config import REGIONS_09_SIMPLE, COULEURS_SEXE
from .data import get_ecart_regional


def ecart_choropleth_html(dfs, annee=2022):
    rows = get_ecart_regional(dfs, annee=annee)
    rows = [r for r in rows if r['region'] in REGIONS_09_SIMPLE]

    regions = [r['region'] for r in rows]
    ecarts = [r['ecart'] or 0 for r in rows]

    bar = (
        Bar(init_opts=opts.InitOpts(width='100%', height='360px',
                                     bg_color='transparent'))
        .add_xaxis(regions)
        .add_yaxis(
            '\u00c9cart M-F (pts)', ecarts,
            color='#f59e0b',
            label_opts=opts.LabelOpts(
                is_show=True, position='top',
                font_size=11, font_weight='bold',
                formatter=JsCode(
                    "function(p){var v=p.data;return v>0?'+'+v:v+' pts';}"),
            ),
            itemstyle_opts=opts.ItemStyleOpts(
                color=JsCode(
                    "function(p){var v=p.data;return v>5?'#ef4444':v>2?'#eab308':'#22c55e';}"),
            ),
        )
        .set_global_opts(
            # Pas de titre interne : la card du dashboard porte d\u00e9j\u00e0 le titre
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=-25, font_size=9)),
            yaxis_opts=opts.AxisOpts(
                name='\u00e9cart (pts)',
                axislabel_opts=opts.LabelOpts(font_size=10)),
            tooltip_opts=opts.TooltipOpts(
                trigger='item',
                formatter=JsCode(
                    """function(p) {
                        var v = p.data;
                        var sens = v > 0 ? 'en d\\u00e9faveur des filles' : 'en faveur des filles';
                        var couleur = v > 5 ? '#ef4444' : v > 2 ? '#eab308' : '#22c55e';
                        return '<b>' + p.name + '</b><br/>' +
                               '\\u00c9cart M-F : <b style=\"color:' + couleur + '\">' + (v > 0 ? '+' : '') + v + ' pts</b><br/>' +
                               '<span style=\"color:#718096;font-size:11px\">' + sens + '</span>';
                    }"""
                ),
            ),
            legend_opts=opts.LegendOpts(pos_bottom=0),
        )
    )
    # Grille étendue en largeur (légende en bas)
    bar.options['grid'] = {'left': '2%', 'right': '2%', 'top': 16, 'bottom': 58, 'containLabel': True}
    return bar.render_embed()
