from pyecharts.charts import Line
from pyecharts import options as opts
from .config import COULEURS_REGIONS_DISTINCTES, REGIONS
from .data import get_evolution_data


def evolution_line_html(dfs, indicateur='transition', sexe='Total',
                        regions_filter=None):
    series = get_evolution_data(dfs, indicateur=indicateur, sexe=sexe,
                                regions_filter=regions_filter)
    regions = regions_filter if regions_filter else REGIONS

    nom_indicateur = {
        'transition': 'Taux de transition Primaire \u2192 Secondaire',
        'bepc': "Taux d'admission au BEPC",
        'promotion': 'Taux de promotion au Primaire',
    }.get(indicateur, indicateur)

    if sexe != 'Total':
        nom_indicateur += f' ({sexe})'

    all_years = sorted(set(d for pts in series.values() for d, _ in pts))

    line = (
        Line(init_opts=opts.InitOpts(width='100%', height='430px',
                                      bg_color='transparent'))
        .add_xaxis([str(y) for y in all_years])
    )

    for r in regions:
        pts = series.get(r, [])
        d = dict(pts)
        def _r(v):
            return round(v, 1) if v is not None else None
        values = [_r(d.get(y)) for y in all_years]
        couleur = COULEURS_REGIONS_DISTINCTES.get(r, '#666')
        line.add_yaxis(
            r, values,
            is_smooth=True,
            symbol='circle',
            symbol_size=6,
            linestyle_opts=opts.LineStyleOpts(width=2, color=couleur),
            # Points et légende dans la même couleur que la ligne
            itemstyle_opts=opts.ItemStyleOpts(color=couleur),
            label_opts=opts.LabelOpts(is_show=False),
            areastyle_opts=opts.AreaStyleOpts(opacity=0),
        )

    line.set_global_opts(
        # Pas de titre interne : la card du dashboard porte déjà le titre
        xaxis_opts=opts.AxisOpts(
            name='Ann\u00e9e',
            name_location='middle',
            name_gap=30,
            axislabel_opts=opts.LabelOpts(rotate=0, font_size=10),
        ),
        yaxis_opts=opts.AxisOpts(
            name='%',
            min_=40, max_=100,
            axislabel_opts=opts.LabelOpts(font_size=10),
        ),
        tooltip_opts=opts.TooltipOpts(trigger='axis'),
        legend_opts=opts.LegendOpts(pos_bottom=0),
    )
    # Grille étendue en largeur, avec la place du nom d'axe et de la légende en bas
    line.options['grid'] = {'left': '2%', 'right': '2%', 'top': 16, 'bottom': 72, 'containLabel': True}
    return line.render_embed()
