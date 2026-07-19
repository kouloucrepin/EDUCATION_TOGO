from pyecharts.charts import Radar
from pyecharts import options as opts
from .config import COULEURS_REGIONS, REGIONS, COULEURS_REGIONS_DISTINCTES as COULEURS_RADAR
from .data import get_heatmap_data, get_national_indicators


def radar_comparison_html(dfs, region_a='Kara', region_b='Savanes',
                          annee=None, sexe='Total'):
    regional = get_heatmap_data(dfs, annee=annee, sexe=sexe)
    nat_annee = annee if annee else 2022
    national = get_national_indicators(dfs, annee=nat_annee)

    def _val(region, key):
        for r in regional:
            if r['region'] == region:
                if key == 'scolarisation':
                    return national['scolarisation_college'] or 0
                if key == 'achevement':
                    return national['achevement_college'] or 0
                if key == 'promotion':
                    return r['promotion'] or 0
                if key == 'transition':
                    return r['transition'] or 0
                if key == 'bepc':
                    return r['bepc'] or 0
        return 0

    axes = [
        {'name': 'Promotion\nprimaire', 'max': 100},
        {'name': 'Transition\nP\u2192S', 'max': 100},
        {'name': 'Admission\nBEPC', 'max': 100},
        {'name': 'Scolarisation\ncoll\u00e8ge', 'max': 100},
        {'name': 'Ach\u00e8vement\ncoll\u00e8ge', 'max': 100},
    ]

    keys = ['promotion', 'transition', 'bepc', 'scolarisation', 'achevement']

    radar = (
        Radar(init_opts=opts.InitOpts(width='100%', height='380px',
                                       bg_color='transparent'))
        .add_schema(
            schema=axes,
            shape='polygon',
            center=['50%', '48%'],
            radius='72%',
            textstyle_opts=opts.TextStyleOpts(font_size=10),
            splitarea_opt=opts.SplitAreaOpts(is_show=True),
        )
    )

    if region_a == 'Toutes' or region_b == 'Toutes':
        # Mode « tout comparer » : les 7 profils superposés, remplissage léger
        for reg in REGIONS:
            radar.add(reg, [[_val(reg, k) for k in keys]],
                      color=COULEURS_RADAR.get(reg, '#666'),
                      linestyle_opts=opts.LineStyleOpts(width=2),
                      areastyle_opts=opts.AreaStyleOpts(opacity=0.04),
                      label_opts=opts.LabelOpts(is_show=False))
    else:
        radar.add(region_a, [[_val(region_a, k) for k in keys]],
                  color=COULEURS_REGIONS.get(region_a, '#006A4E'),
                  linestyle_opts=opts.LineStyleOpts(width=2),
                  areastyle_opts=opts.AreaStyleOpts(opacity=0.15))
        radar.add(region_b, [[_val(region_b, k) for k in keys]],
                  color=COULEURS_REGIONS.get(region_b, '#ef4444'),
                  linestyle_opts=opts.LineStyleOpts(width=2),
                  areastyle_opts=opts.AreaStyleOpts(opacity=0.15))

    radar.set_global_opts(
        # Pas de titre interne : la card du dashboard porte déjà le titre
        tooltip_opts=opts.TooltipOpts(trigger='item'),
        legend_opts=opts.LegendOpts(pos_bottom=0, item_width=14, item_height=9,
                                    textstyle_opts=opts.TextStyleOpts(font_size=10)),
    )
    return radar.render_embed()
