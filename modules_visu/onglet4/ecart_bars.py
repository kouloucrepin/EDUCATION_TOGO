from pyecharts.charts import Bar
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from .data import get_ecart_regional

ROSE = '#e91e63'
BLEU = '#1976d2'


def ecart_bar_html(dfs, annee=2022):
    """Barres groupées Filles / Garçons par région, triées par écart décroissant.
    Inclut toutes les régions disponibles pour l'année (Plateaux Ouest / Est en 2022)."""
    rows = get_ecart_regional(dfs, annee=annee)
    rows = [r for r in rows if r['Féminin'] is not None and r['Masculin'] is not None]
    rows.sort(key=lambda r: -(r['ecart'] if r['ecart'] is not None else 0))

    regions = [r['region'] for r in rows]
    filles = [r['Féminin'] for r in rows]
    garcons = [r['Masculin'] for r in rows]

    bar = (
        Bar(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
        .add_xaxis(regions)
        .add_yaxis('Filles', filles, color=ROSE, category_gap='40%',
                   label_opts=opts.LabelOpts(is_show=True, position='top',
                                             font_size=9, color=ROSE,
                                             font_weight='bold'))
        .add_yaxis('Garçons', garcons, color=BLEU,
                   label_opts=opts.LabelOpts(is_show=True, position='top',
                                             font_size=9, color=BLEU,
                                             font_weight='bold'))
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=-25, font_size=9, interval=0)),
            yaxis_opts=opts.AxisOpts(
                min_=0, max_=100,
                axislabel_opts=opts.LabelOpts(font_size=10),
                splitline_opts=opts.SplitLineOpts(is_show=True)),
            tooltip_opts=opts.TooltipOpts(
                trigger='axis',
                formatter=JsCode(
                    """function(params) {
                        var f = null, m = null;
                        var s = '<b>' + params[0].axisValue + '</b><br/>';
                        for (var i = 0; i < params.length; i++) {
                            var v = Array.isArray(params[i].value) ? params[i].value[1] : params[i].value;
                            if (v === null || v === undefined) continue;
                            if (params[i].seriesName === 'Filles') f = v; else m = v;
                            s += params[i].marker + ' ' + params[i].seriesName + ' : ' + v + '%<br/>';
                        }
                        if (f !== null && m !== null) {
                            s += '\\u00c9cart : <b>' + (m - f).toFixed(1) + ' pts</b> en d\\u00e9faveur des filles';
                        }
                        return s;
                    }"""
                ),
            ),
            legend_opts=opts.LegendOpts(pos_bottom=0),
        )
    )
    bar.options['grid'] = {'left': '2%', 'right': '2%', 'top': 16, 'bottom': 64, 'containLabel': True}
    return bar.render_embed()
