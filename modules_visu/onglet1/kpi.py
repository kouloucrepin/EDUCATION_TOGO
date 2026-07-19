from pyecharts.charts import Gauge, Line
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode

from ..embed import chart_fragment


def _formater_valeur(v, unite):
    if v is None:
        return 0, unite
    if unite == 'Md FCFA' and abs(v) > 1e8:
        return round(v / 1e9, 1), 'Md FCFA'
    if unite == 'Md FCFA':
        return round(v, 1), 'Md FCFA'
    return round(v, 1), unite


def _formater_evolution(pts, unite):
    if pts is None:
        return None
    val, unite = _formater_valeur(abs(pts), unite)
    sign = '+' if pts >= 0 else '-'
    return f"{sign}{val}{unite}"


def _evolution_text(recup):
    cfg = recup['cfg']
    _, unite = _formater_valeur(recup['valeur'], cfg['unite'])
    parts = []

    if recup['evolution_prev_pts'] is not None:
        parts.append(f"N-1: {_formater_evolution(recup['evolution_prev_pts'], unite)}")

    if recup['evolution_pic_pts'] is not None:
        an = recup['annee_pic']
        parts.append(f"vs pic {an}: {_formater_evolution(recup['evolution_pic_pts'], unite)}")

    if recup['multiplicateur'] is not None and recup['multiplicateur'] >= 2:
        parts.append(f"\u00d7{recup['multiplicateur']:.1f} depuis 2013")

    if recup['evolution_pts'] is not None and not parts:
        parts.append(f"{_formater_evolution(recup['evolution_pts'], unite)} en 10 ans")
    elif recup['evolution_pct'] is not None and not parts:
        val = recup['evolution_pct']
        sign = '+' if val >= 0 else ''
        parts.append(f"{sign}{val:.1f}% en 10 ans")

    return ' \u00b7 '.join(parts) if parts else ''


def kpi_card_html(recup):
    cfg = recup['cfg']
    valeur = recup['valeur'] or 0
    unite_brute = cfg['unite']
    couleur = cfg['couleur']
    label = cfg['label']

    valeur_affichee, unite_aff = _formater_valeur(valeur, unite_brute)
    max_val = cfg['max']
    if max_val is not None and unite_brute == 'Md FCFA':
        max_val, _ = _formater_valeur(max_val, unite_brute)
    if max_val is None:
        max_val = valeur_affichee * 1.5 if valeur_affichee > 0 else 100

    detail_formatter = '{value} ' + unite_aff

    gauge = (
        Gauge(init_opts=opts.InitOpts(width='100%', height='200px', bg_color='transparent'))
        .add(
            series_name='',
            data_pair=[('', valeur_affichee)],
            min_=0,
            max_=max_val,
            split_number=5,
            center=['50%', '55%'],
            radius='75%',
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(width=8, color=[
                    [0.3, couleur], [0.7, couleur], [1, couleur],
                ])
            ),
            detail_label_opts=opts.GaugeDetailOpts(
                formatter=detail_formatter,
                font_size=22,
                color=couleur,
                offset_center=[0, '65%'],
            ),
            title_label_opts=opts.GaugeTitleOpts(
                offset_center=[0, '88%'], font_size=11, color='#999',
            ),
            pointer=opts.GaugePointerOpts(length='50%', width=3,
                itemstyle_opts=opts.ItemStyleOpts(color=couleur)),
            itemstyle_opts=opts.ItemStyleOpts(color=couleur),
        )
        .set_global_opts(tooltip_opts=opts.TooltipOpts(is_show=False))
    )

    series = recup['full_series']
    spark = None
    if series and len(series) > 1:
        x = [str(s[0]) for s in series]
        if unite_brute == 'Md FCFA':
            y = [round(s[1] / 1e9, 1) for s in series]
        else:
            y = [round(s[1], 1) for s in series]
        tooltip_unite = ' Md FCFA' if unite_brute == 'Md FCFA' else ('' if unite_brute == '%' else ' ' + unite_brute)
        spark = (
            Line(init_opts=opts.InitOpts(width='100%', height='88px', bg_color='transparent'))
            .add_xaxis(x)
            .add_yaxis('', y, is_smooth=True, symbol='none',
                linestyle_opts=opts.LineStyleOpts(width=1.5, color=couleur),
                areastyle_opts=opts.AreaStyleOpts(opacity=0.3, color=couleur),
                label_opts=opts.LabelOpts(is_show=False),
                # Points d'attention : maximum (couleur du KPI) et minimum (rouge)
                markpoint_opts=opts.MarkPointOpts(
                    data=[
                        opts.MarkPointItem(type_='max', name='Maximum',
                                           symbol='circle', symbol_size=9,
                                           itemstyle_opts=opts.ItemStyleOpts(
                                               color=couleur, border_color='#fff', border_width=1.5)),
                        opts.MarkPointItem(type_='min', name='Minimum',
                                           symbol='circle', symbol_size=9,
                                           itemstyle_opts=opts.ItemStyleOpts(
                                               color='#EF3340', border_color='#fff', border_width=1.5)),
                    ],
                    label_opts=opts.LabelOpts(is_show=True, position='top',
                                              font_size=9, font_weight='bold',
                                              color='#4A5568'),
                ))
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(is_show=False),
                yaxis_opts=opts.AxisOpts(is_show=False),
                tooltip_opts=opts.TooltipOpts(
                    is_show=True, trigger='axis',
                    # Les points sont des paires [ann\u00e9e, valeur] : n'afficher que la valeur
                    formatter=JsCode(
                        "function(params){var p=params[0];"
                        "var v=Array.isArray(p.value)?p.value[1]:p.value;"
                        "return 'Ann\\u00e9e : '+p.axisValue+'<br/>Valeur : '+v+'" + tooltip_unite + "';}"
                    ),
                ),
            )
        )
        # Marges pour que les points min/max et leurs \u00e9tiquettes ne soient pas rogn\u00e9s
        spark.options['grid'] = {'top': 18, 'bottom': 14, 'left': 8, 'right': 10}

    evolution_txt = _evolution_text(recup)

    # render_embed() retourne un document complet : on n'embarque que le fragment div+script
    gauge_html = chart_fragment(gauge.render_embed())
    spark_html = chart_fragment(spark.render_embed()) if spark else ''
    chart_id = f"kpi_{cfg['id']}"

    return f'''<div id="{chart_id}" class="kpi-card">
  <div class="kpi-label">{label}</div>
  <div class="kpi-gauge">{gauge_html}</div>
  <div class="kpi-spark">{spark_html}</div>
  <div class="kpi-evolution">{evolution_txt}</div>
</div>'''


def kpi_gauge_html(rows):
    parts = []
    for r in rows:
        parts.append(kpi_card_html(r))
    return '\n'.join(parts)
