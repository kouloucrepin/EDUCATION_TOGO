from pyecharts.charts import Line
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from .data import get_bepc_data

ROSE = '#e91e63'
BLEU = '#1976d2'


def bepc_evolution_html(dfs, region='Togo'):
    """Courbes Filles / Garçons avec bande d'écart rose entre les deux
    (style du mockup). La bande est réalisée par un empilement invisible :
    base = min(F, M), hauteur = |M - F|."""
    series = get_bepc_data(dfs, region=region, sexes=['Féminin', 'Masculin'])
    fem = dict(series.get('Féminin', []))
    mas = dict(series.get('Masculin', []))
    annees = sorted(set(fem) | set(mas))

    f_vals = [fem.get(a) for a in annees]
    m_vals = [mas.get(a) for a in annees]
    base = [min(f, m) if f is not None and m is not None else None
            for f, m in zip(f_vals, m_vals)]
    hauteur = [round(abs(m - f), 1) if f is not None and m is not None else None
               for f, m in zip(f_vals, m_vals)]

    invisible = opts.LineStyleOpts(width=0, opacity=0)

    line = (
        Line(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
        .add_xaxis([str(a) for a in annees])
        # Bande d'écart (empilement, exclue de la légende et du tooltip)
        .add_yaxis('_base', base, stack='ecart', symbol='none',
                   linestyle_opts=invisible,
                   areastyle_opts=opts.AreaStyleOpts(opacity=0),
                   label_opts=opts.LabelOpts(is_show=False),
                   is_smooth=True)
        .add_yaxis('_bande', hauteur, stack='ecart', symbol='none',
                   linestyle_opts=invisible,
                   areastyle_opts=opts.AreaStyleOpts(opacity=0.16, color=ROSE),
                   label_opts=opts.LabelOpts(is_show=False),
                   is_smooth=True)
        # Courbes réelles
        .add_yaxis('Filles', f_vals, is_smooth=True, symbol='circle', symbol_size=6,
                   linestyle_opts=opts.LineStyleOpts(width=2.5, color=ROSE),
                   itemstyle_opts=opts.ItemStyleOpts(color=ROSE),
                   label_opts=opts.LabelOpts(is_show=False))
        .add_yaxis('Garçons', m_vals, is_smooth=True, symbol='circle', symbol_size=6,
                   linestyle_opts=opts.LineStyleOpts(width=2.5, color=BLEU),
                   itemstyle_opts=opts.ItemStyleOpts(color=BLEU),
                   label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                name='Année', name_location='middle', name_gap=30,
                axislabel_opts=opts.LabelOpts(rotate=0, font_size=10),
                boundary_gap=False,
            ),
            yaxis_opts=opts.AxisOpts(
                name="Taux d'admission BEPC (%)",
                name_location='middle', name_gap=34,
                min_=40, max_=80,
                axislabel_opts=opts.LabelOpts(font_size=10),
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger='axis',
                formatter=JsCode(
                    """function(params) {
                        var f = null, m = null;
                        var s = '<b>' + params[0].axisValue + '</b><br/>';
                        for (var i = 0; i < params.length; i++) {
                            var nom = params[i].seriesName;
                            if (nom !== 'Filles' && nom !== 'Gar\\u00e7ons') continue;
                            var v = Array.isArray(params[i].value) ? params[i].value[1] : params[i].value;
                            if (v === null || v === undefined) continue;
                            if (nom === 'Filles') f = v; else m = v;
                            s += params[i].marker + ' ' + nom + ' : ' + v + '%<br/>';
                        }
                        if (f !== null && m !== null) {
                            s += '\\u00c9cart : <b>' + (m - f).toFixed(1) + ' pts</b>';
                        }
                        return s;
                    }"""
                ),
            ),
            legend_opts=opts.LegendOpts(pos_bottom=0),
        )
    )
    # Légende limitée aux deux courbes réelles
    line.options['legend'][0]['data'] = ['Filles', 'Garçons']
    line.options['grid'] = {'left': '2%', 'right': '2%', 'top': 16, 'bottom': 72, 'containLabel': True}
    return line.render_embed()
