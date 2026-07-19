from pyecharts.charts import HeatMap
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from .config import REGIONS
from .data import get_heatmap_data, get_national_indicators, get_ranking_data


def heatmap_table_html(dfs, annee=None, sexe='Total'):
    """Matrice Région × Indicateur en tableau HTML à cellules colorées
    (style du mockup) avec colonne Score composite."""
    regional = get_heatmap_data(dfs, annee=annee, sexe=sexe)
    nat = get_national_indicators(dfs, annee=annee if annee else 2022)
    scores = {r['region']: r['score'] for r in get_ranking_data(dfs, annee=annee, sexe=sexe)}

    an_promo = annee if annee else 2019
    colonnes = [
        ('promotion', f"Promotion primaire ('{str(an_promo)[2:]})"),
        ('transition', 'Transition P→S'),
        ('bepc', 'Admission BEPC'),
        ('scolar', 'Scolarisation collège'),
    ]

    lignes = []
    for r in regional:
        lignes.append({
            'region': r['region'],
            'promotion': r['promotion'],
            'transition': r['transition'],
            'bepc': r['bepc'],
            'scolar': nat['scolarisation_college'],
            'score': scores.get(r['region']),
        })

    def _meilleur(cle):
        vals = [l[cle] for l in lignes if l[cle] is not None]
        return max(vals) if vals else None

    meilleurs = {cle: _meilleur(cle) for cle, _ in colonnes}

    def _classe(v, meilleur=None):
        if v is None:
            return 'cell-nd'
        if meilleur is not None and v == meilleur:
            return 'cell-best'
        if v >= 75:
            return 'cell-green'
        if v >= 60:
            return 'cell-yellow'
        return 'cell-red'

    def _classe_score(v):
        if v is None:
            return 'cell-nd'
        if v >= 76:
            return 'cell-green'
        if v >= 70:
            return 'cell-yellow'
        return 'cell-red'

    html = ['<table class="heatmap-table"><thead><tr><th>Région</th>']
    for _, libelle in colonnes:
        html.append(f'<th>{libelle}</th>')
    html.append('<th>Score</th></tr></thead><tbody>')

    for l in lignes:
        score = l['score']
        alerte = ' class="region-alerte"' if (score is not None and score < 70) else ''
        html.append(f'<tr><td{alerte}>{l["region"]}</td>')
        for cle, _ in colonnes:
            v = l[cle]
            txt = f'{v:.1f}%'.replace('.', ',') if v is not None else 'N/D'
            html.append(f'<td class="{_classe(v, meilleurs[cle])}">{txt}</td>')
        stxt = f'{score:.1f}'.replace('.', ',') if score is not None else 'N/D'
        html.append(f'<td class="{_classe_score(score)}"><strong>{stxt}</strong></td></tr>')

    html.append('</tbody></table>')
    html.append(
        '<div class="heatmap-note"><i class="fas fa-info-circle"></i> '
        'Score composite pondéré : transition 25 %, BEPC 25 %, promotion 20 %, '
        'scolarisation 15 %, achèvement 15 % (renormalisé si un indicateur manque). '
        f'Promotion primaire : dernière année disponible = {an_promo}. '
        'Scolarisation collège : valeur nationale (pas de détail régional).</div>'
    )
    return ''.join(html)


def heatmap_html(matrix):
    indicators = list(matrix[0].keys()) if matrix else []
    indicators = [i for i in indicators if i != 'region']

    data = []
    for i, r in enumerate(REGIONS):
        for j, ind in enumerate(indicators):
            val = matrix[i].get(ind) if i < len(matrix) else None
            if val is not None:
                data.append([j, i, round(val, 1)])

    vmin = 0
    vmax = 100

    hm = (
        HeatMap(init_opts=opts.InitOpts(width='100%', height='380px',
                                          bg_color='transparent'))
        .add_xaxis(indicators)
        .add_yaxis('R\u00e9gion', REGIONS, data,
                   label_opts=opts.LabelOpts(
                       is_show=True, color='#000', font_size=11,
                       formatter=JsCode(
                           "function(p){return p.data[2] != null ? p.data[2] : 'N/D';}"
                       )))
        .set_global_opts(
            # Pas de titre interne : la card du dashboard porte d\u00e9j\u00e0 le titre
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=0, font_size=10, interval=0),
                splitarea_opts=opts.SplitAreaOpts(is_show=True),
            ),
            yaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(font_size=11),
                splitarea_opts=opts.SplitAreaOpts(is_show=True),
            ),
            visualmap_opts=opts.VisualMapOpts(
                min_=vmin, max_=vmax,
                range_color=['#ef4444', '#f59e0b', '#eab308', '#22c55e'],
                pos_left='right', pos_top='center',
                orient='vertical',
                is_calculable=True,
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger='item',
                formatter=JsCode(
                    "function(p){return '<b>'+p.data[1]+'</b><br>'+p.data[0]+': <b>'+p.data[2]+'%</b>';}"
                ),
            ),
        )
    )
    return hm.render_embed()
