from pyecharts.charts import HeatMap
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from .config import REGIONS
from .data import get_heatmap_data, get_national_indicators, get_ranking_data


def heatmap_table_html(dfs, annee=None, sexe='Total'):
    """Matrice Région × Indicateur — tableau avec barres proportionnelles intégrées."""
    regional = get_heatmap_data(dfs, annee=annee, sexe=sexe)
    nat = get_national_indicators(dfs, annee=annee if annee else 2022)
    scores = {r['region']: r['score'] for r in get_ranking_data(dfs, annee=annee, sexe=sexe)}

    an_promo = annee if annee else 2019
    colonnes = [
        ('promotion', f"Promotion primaire", f"'{str(an_promo)[2:]}"),
        ('transition', 'Transition P→S', 'primaire → secondaire'),
        ('bepc', 'Admission BEPC', 'taux de réussite'),
        ('scolar', 'Scolarisation collège', 'valeur nationale'),
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

    meilleurs = {cle: _meilleur(cle) for cle, _, _ in colonnes}

    def _bar(v, meilleur=None):
        if v is None:
            return '<div class="hm-bar hm-bar-nd">N/D</div>'
        pct = min(v, 100)
        color = '#22C55E' if v >= 75 else '#EAB308' if v >= 60 else '#EF4444'
        best = ' hm-best' if meilleur is not None and v == meilleur else ''
        star = '<span class="hm-star">★</span> ' if meilleur is not None and v == meilleur else ''
        return (
            f'<div class="hm-bar{best}">'
            f'<span class="hm-fill" style="width:{pct}%;background:{color}"></span>'
            f'<span class="hm-val">{star}{v:.1f}%</span>'
            f'</div>'
        )

    def _score_bar(v):
        if v is None:
            return '<div class="hm-bar hm-bar-nd">N/D</div>'
        pct = min(v, 100)
        color = '#22C55E' if v >= 76 else '#EAB308' if v >= 70 else '#EF4444'
        return (
            f'<div class="hm-bar hm-score">'
            f'<span class="hm-fill" style="width:{pct}%;background:{color}"></span>'
            f'<span class="hm-val"><strong>{v:.1f}</strong></span>'
            f'</div>'
        )

    html = ['<table class="hm-table"><thead><tr>']
    html.append('<th class="hm-th-reg">Région</th>')
    for _, titre, sous in colonnes:
        html.append(f'<th class="hm-th"><span class="hm-titre">{titre}</span><span class="hm-soustitre">{sous}</span></th>')
    html.append('<th class="hm-th hm-th-score"><span class="hm-titre">Score</span><span class="hm-soustitre">composite</span></th>')
    html.append('</tr></thead><tbody>')

    for l in lignes:
        score = l['score']
        html.append(f'<tr class="hm-row">')
        alerte = '<span class="hm-alerte">⚠</span> ' if score is not None and score < 70 else ''
        html.append(f'<td class="hm-reg">{alerte}{l["region"]}</td>')
        for cle, _, _ in colonnes:
            v = l[cle]
            html.append(f'<td class="hm-cell">{_bar(v, meilleurs[cle])}</td>')
        html.append(f'<td class="hm-cell hm-cell-score">{_score_bar(score)}</td>')
        html.append('</tr>')

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
