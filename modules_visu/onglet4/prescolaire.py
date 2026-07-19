from pyecharts.charts import Bar, Pie
from pyecharts import options as opts
from .data import get_prescolaire_data, get_prescolaire_par_inspection, get_prescolaire_matrice
# Rendu de tableau avec en-tête/pied figés et filtres intégrés (mutualisé avec l'onglet 1)
from ..onglet1.table import _render_table

ROSE = '#e91e63'
BLEU = '#1976d2'


def prescolaire_table_html(dfs, root_id='tbl_presco'):
    """Tableau Année | Région | Masculin | Féminin | Total, avec filtres
    intégrés à l'en-tête (année, région) et en-tête/pied figés."""
    rows = get_prescolaire_matrice(dfs)
    if not rows:
        return '<p style="color:#C53030;padding:12px">Aucune donnée préscolaire.</p>'

    headers = ['Année', 'Région', 'Masculin', 'Féminin', 'Total']
    filtres = {}  # pas de filtres d'en-tête sur ce tableau (7 lignes, lisible d'un bloc)

    def _fmt(v):
        return f'{v:,}'.replace(',', ' ') if v is not None else 'N/D'

    body = []
    for r in rows:
        body.append([
            (str(r['annee']), False),
            (r['region'], False),
            (f'<span style="color:{BLEU};font-weight:600">{_fmt(r["masculin"])}</span>', True),
            (f'<span style="color:{ROSE};font-weight:600">{_fmt(r["feminin"])}</span>', True),
            (f'<strong>{_fmt(r["total"])}</strong>', True),
        ])

    total_nat = get_prescolaire_data(dfs)
    footer = (f'<i class="fas fa-database" style="margin-right:5px;opacity:0.6"></i>'
              f'Source : INSEED - fichier 13, agrégats régionaux T.R.* (sans double comptage) · '
              f'<span class="tbl-count">{len(rows)}</span> / {len(rows)} lignes · '
              f'Total national : {total_nat["total"]:,} enseignants'.replace(',', ' '))
    return _render_table(headers, filtres, body, footer, root_id)

# Couleur par zone (heuristique sur le nom de l'inspection)
_ZONES = [
    (('lomé', 'lome', 'agoè', 'agoe', 'golfe', 'ave', 'zio', 'lacs', 'vo ', 'yoto', 'bas mono'), '#006A4E'),
    (('tône', 'tone', 'tandjoar', 'cinkass', 'kpendjal', 'oti', 'savan'), '#D4A017'),
    (('tchaoudjo', 'blitta', 'sotouboua', 'tchamba', 'mo'), '#3182CE'),
    (('kozah', 'kara', 'binah', 'assoli', 'bassar', 'dankpen', 'doufelgou', 'keran', 'kéran'), '#805AD5'),
]


def _couleur_inspection(nom):
    n = str(nom).lower()
    for cles, couleur in _ZONES:
        if any(k in n for k in cles):
            return couleur
    return '#22865F'


def top_inspections_bar_html(dfs, top=10):
    """Top des inspections locales par effectifs préscolaires
    (agrégats T.Général / T.R.* exclus par get_prescolaire_par_inspection)."""
    items = get_prescolaire_par_inspection(dfs)[:top]
    donnees = [{'value': it['total'], 'itemStyle': {'color': _couleur_inspection(it['inspection'])}}
               for it in items]

    bar = (
        Bar(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
        .add_xaxis([it['inspection'] for it in items])
        .add_yaxis('Enseignants', donnees, category_gap='40%',
                   label_opts=opts.LabelOpts(is_show=True, position='top',
                                             font_size=10, color='#4A5568',
                                             font_weight='bold'))
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=30, font_size=9, interval=0)),
            yaxis_opts=opts.AxisOpts(
                splitline_opts=opts.SplitLineOpts(is_show=True)),
            tooltip_opts=opts.TooltipOpts(trigger='axis'),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    bar.options['grid'] = {'left': '2%', 'right': '2%', 'top': 16, 'bottom': 6, 'containLabel': True}
    return bar.render_embed()


def prescolaire_pie_html(dfs):
    data = get_prescolaire_data(dfs)

    pie = (
        Pie(init_opts=opts.InitOpts(width='100%', height='340px',
                                     bg_color='transparent'))
        .add(
            '',
            [('Femmes', data['femmes']), ('Hommes', data['hommes'])],
            radius=['45%', '72%'],
            center=['50%', '46%'],
            label_opts=opts.LabelOpts(
                is_show=True,
                formatter='{b}: {d}% ({c})',
                font_size=12,
            ),
        )
        .set_global_opts(
            # Pas de titre interne : la card du dashboard porte d\u00e9j\u00e0 le titre
            legend_opts=opts.LegendOpts(pos_bottom=0),
            tooltip_opts=opts.TooltipOpts(
                trigger='item',
                formatter='{b}: {c} ({d}%)'),
        )
    )
    # Palette li\u00e9e au genre : rose = Femmes, bleu = Gar\u00e7ons/Hommes
    # (le kwarg color de Pie.add est ignor\u00e9 par pyecharts, on fixe la palette du chart)
    pie.options['color'] = ['#e91e63', '#1976d2']
    return pie.render_embed()
