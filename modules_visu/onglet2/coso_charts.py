from pyecharts.charts import Bar, Pie
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode


def _clean_label(l):
    import re
    return re.sub(r'\s+\d+\.?\d*%$', '', l)


def coso_type_bar_html(type_rows):
    labels = [t for t, _ in type_rows]
    values = [v for _, v in type_rows]

    def _wrap_label(l, max_chars=16, max_lines=3):
        import textwrap
        lines = textwrap.wrap(l, width=max_chars)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1].rstrip(',; ') + '...'
        return '\n'.join(lines) if len(lines) > 1 else l

    bar = (
        Bar(init_opts=opts.InitOpts(width='100%', height='380px',
                                     bg_color='transparent'))
        .add_xaxis([_wrap_label(l) for l in labels])
        .add_yaxis('Projets', values, category_gap='50%',
                   itemstyle_opts=opts.ItemStyleOpts(
                       color=JsCode(
                           "function(p){var c=['#22c55e','#92400e','#f59e0b','#3b82f6','#f97316','#ef4444','#8b5cf6'];return c[p.dataIndex%c.length];}"
                       )))
        .set_global_opts(
            # Pas de titre interne : la card du dashboard porte déjà le titre
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(
                rotate=0, font_size=10, interval=0,
            )),
            yaxis_opts=opts.AxisOpts(name='Nombre de projets'),
            tooltip_opts=opts.TooltipOpts(trigger='axis'),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    bar.options['grid'] = {'top': 24, 'left': '3%', 'right': '3%', 'bottom': '3%', 'containLabel': True}
    return bar.render_embed()


def coso_status_pie_html(status_rows):
    cleaned = [(_clean_label(s), v) for s, v in status_rows]
    pie = (
        Pie(init_opts=opts.InitOpts(width='100%', height='380px',
                                     bg_color='transparent'))
        .add('', cleaned,
             radius=['32%', '68%'],
             center=['50%', '44%'],
             label_opts=opts.LabelOpts(formatter='{b}: {c} ({d}%)',
                                       font_size=11))
        .set_global_opts(
            # Pas de titre interne : la card du dashboard porte déjà le titre
            tooltip_opts=opts.TooltipOpts(trigger='item',
                                          formatter='{b}: {c} ({d}%)'),
            legend_opts=opts.LegendOpts(pos_bottom=0, item_width=12, item_height=12),
        )
    )
    return pie.render_embed()
