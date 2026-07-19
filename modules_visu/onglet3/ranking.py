from pyecharts.charts import Bar
from pyecharts import options as opts

from .config import REGIONS
from .data import get_ranking_data


def ranking_matrix(dfs, sexe='Total', annees=None):
    """Scores composites par année (lignes) et région (colonnes)."""
    if annees is None:
        annees = list(range(2014, 2023))
    lignes = []
    for an in annees:
        scores = {r['region']: r['score'] for r in get_ranking_data(dfs, annee=an, sexe=sexe)}
        lignes.append({'annee': an, 'scores': scores})
    return lignes


def ranking_matrix_html(dfs, sexe='Total'):
    """Tableau années × régions des scores composites, avec en-tête et pied
    figés (classes .tbl-root du dashboard) et moyenne par région en pied."""
    lignes = ranking_matrix(dfs, sexe=sexe)

    def _classe(v):
        if v is None:
            return 'cell-nd'
        if v >= 76:
            return 'cell-green'
        if v >= 70:
            return 'cell-yellow'
        return 'cell-red'

    def _fmt(v):
        return f'{v:.1f}'.replace('.', ',') if v is not None else 'N/D'

    html = ['<div class="tbl-root"><table class="heatmap-table">']
    html.append('<thead><tr><th>Année</th>')
    for reg in REGIONS:
        html.append(f'<th>{reg}</th>')
    html.append('</tr></thead><tbody>')

    for l in lignes:
        html.append(f'<tr><td><strong>{l["annee"]}</strong></td>')
        for reg in REGIONS:
            v = l['scores'].get(reg)
            html.append(f'<td class="{_classe(v)}">{_fmt(v)}</td>')
        html.append('</tr>')

    html.append('</tbody><tfoot><tr><td><strong>Moyenne</strong></td>')
    for reg in REGIONS:
        vals = [l['scores'].get(reg) for l in lignes if l['scores'].get(reg) is not None]
        moyenne = sum(vals) / len(vals) if vals else None
        html.append(f'<td><strong>{_fmt(moyenne)}</strong></td>')
    html.append('</tr></tfoot></table></div>')
    return ''.join(html)


def ranking_bar_html(dfs, annee=None, sexe='Total'):
    """Classement des régions par score composite, en barres colorées
    (vert : podium, or : milieu, rouge : dernière)."""
    rows = [r for r in get_ranking_data(dfs, annee=annee, sexe=sexe) if r['score'] is not None]

    donnees = []
    for i, r in enumerate(rows):
        if i < 3:
            couleur = '#006A4E'
        elif i == len(rows) - 1:
            couleur = '#EF3340'
        else:
            couleur = '#B8860B'
        donnees.append({'value': r['score'], 'itemStyle': {'color': couleur}})

    bar = (
        Bar(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
        .add_xaxis([r['region'] for r in rows])
        .add_yaxis('Score composite', donnees, category_gap='40%',
                   label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=0, font_size=10, interval=0)),
            yaxis_opts=opts.AxisOpts(
                min_=0, max_=100,
                splitline_opts=opts.SplitLineOpts(is_show=True)),
            tooltip_opts=opts.TooltipOpts(trigger='axis'),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    bar.options['grid'] = {'left': '2%', 'right': '2%', 'top': 20, 'bottom': 6, 'containLabel': True}
    return bar.render_embed()


def ranking_table_html(dfs, annee=None, sexe='Total'):
    rows = get_ranking_data(dfs, annee=annee, sexe=sexe)

    html = '''<table class="rank-table">
<thead>
<tr>
  <th>Rang</th>
  <th>R\u00e9gion</th>
  <th>Score</th>
  <th>Transition</th>
  <th>BEPC</th>
  <th>Promotion</th>
  <th>Alerte</th>
</tr>
</thead>
<tbody>'''

    for r in rows:
        def _fmt(v):
            return f'{v:.1f}%' if v is not None else 'N/D'
        if r['score'] is None:
            classe = 'rank-nd'
        else:
            classe = 'rank-down' if r['score'] < 70 else ('rank-mid' if r['score'] < 80 else 'rank-up')
        html += f'''<tr>
  <td class="rank-num">{r['rang']}</td>
  <td><strong>{r['region']}</strong></td>
  <td class="{classe}"><strong>{_fmt(r['score'])}</strong></td>
  <td>{_fmt(r['transition'])}</td>
  <td>{_fmt(r['bepc'])}</td>
  <td>{_fmt(r['promotion'])}</td>
  <td style="text-align:center;font-size:18px;">{r['alerte']}</td>
</tr>'''

    html += '''</tbody></table>'''
    return html
