import pandas as pd
import numpy as np
from .config import COULEURS
import html as html_mod


def indicator_table(df_resultats, niveau=None, secteur='Total'):
    df = df_resultats.copy()
    df['Date'] = pd.to_numeric(df['Date'], errors='coerce')
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

    if niveau and niveau != 'Tous':
        df = df[df['niveau'] == niveau]
    if secteur:
        df = df[df['secteur'] == secteur]

    indicateurs_interet = [
        "Taux d'achèvement ou de diplomation",
        'Taux de scolarisation',
        "Dépenses annuelles d'éducation",
        "Part du Budget alloué à l'éducation (%)",
        "Nombre d'écoles",
        "Nombre d'enseignants",
    ]

    annees_cibles = [2013, 2015, 2018, 2022]
    rows = []
    for ind in indicateurs_interet:
        for niv in ['Primaire', 'Collège', 'Lycée', "Jardins d'enfants"]:
            sub = df[(df['indicateurs'] == ind) & (df['niveau'] == niv)]
            if sub.empty:
                continue
            vals = {}
            for a in annees_cibles:
                r = sub[sub['Date'] == a]
                if not r.empty:
                    vals[a] = r['Value'].iloc[0]
                else:
                    vals[a] = None

            val_2013 = vals.get(2013)
            val_2022 = vals.get(2022)
            if val_2013 is not None and val_2022 is not None:
                variation = val_2022 - val_2013
                if val_2013 != 0:
                    pct_var = (variation / val_2013) * 100
                else:
                    pct_var = None
            else:
                variation = None
                pct_var = None

            if val_2022 is not None and val_2013 is not None:
                tendance = '↗' if val_2022 > val_2013 else ('↘' if val_2022 < val_2013 else '→')
            else:
                tendance = '-'

            rows.append({
                'indicateur': ind,
                'niveau': niv,
                '2013': round(val_2013, 1) if val_2013 is not None else '-',
                '2015': round(vals.get(2015), 1) if vals.get(2015) is not None else '-',
                '2018': round(vals.get(2018), 1) if vals.get(2018) is not None else '-',
                '2022': round(val_2022, 1) if val_2022 is not None else '-',
                'tendance': tendance,
                'variation': round(variation, 1) if variation is not None else '-',
                'pct_var': round(pct_var, 1) if pct_var is not None else '-',
                'unite': '%',
            })

    return rows


def regional_indicator_table(df_promotion, df_bepc, df_transition):
    """Vue régionale du tableau : croise les fichiers 08 (promotion),
    09 (BEPC) et 10 (transition) - seuls jeux de données à dimension régionale."""
    sources = [
        ('Taux de promotion au primaire', df_promotion, 'TOGO'),
        ("Taux d'admission au BEPC", df_bepc, 'Togo'),
        ('Taux de transition primaire→secondaire', df_transition, 'Togo'),
    ]
    regions = ['Togo', 'Lomé-Golfe', 'Maritime', 'Plateaux', 'Centrale', 'Kara', 'Savanes']
    annees_cibles = [2014, 2018, 2022]

    rows = []
    for label, df, cle_togo in sources:
        d = df.copy()
        d['Date'] = pd.to_numeric(d['Date'], errors='coerce')
        d['Value'] = pd.to_numeric(d['Value'], errors='coerce')
        d = d[d['sexe'] == 'Total'].dropna(subset=['Date', 'Value'])
        for reg in regions:
            lookup = cle_togo if reg == 'Togo' else reg
            sub = d[d['région'] == lookup].sort_values('Date')
            if sub.empty:
                continue
            par_annee = {int(a): v for a, v in zip(sub['Date'], sub['Value'])}
            vals = {a: round(par_annee[a], 1) if a in par_annee else None for a in annees_cibles}

            premiere = round(float(sub['Value'].iloc[0]), 1)
            derniere = round(float(sub['Value'].iloc[-1]), 1)
            variation = round(derniere - premiere, 1)
            tendance = '↗' if variation > 0 else ('↘' if variation < 0 else '→')
            periode = f"{int(sub['Date'].iloc[0])}→{int(sub['Date'].iloc[-1])}"

            rows.append({
                'indicateur': label,
                'region': reg,
                '2014': vals[2014] if vals[2014] is not None else '-',
                '2018': vals[2018] if vals[2018] is not None else '-',
                '2022': vals[2022] if vals[2022] is not None else '-',
                'tendance': tendance,
                'variation': variation,
                'periode': periode,
            })
    return rows


# ---------------------------------------------------------------------------
# Rendu HTML (partagé entre la vue nationale et la vue régionale)
# ---------------------------------------------------------------------------

# Script de filtrage client, générique : agit sur le tableau qui contient le select
_TABLE_FILTER_SCRIPT = '''<script>
function filtrerTableau(sel){
  var root = sel.closest('.tbl-root');
  var criteres = {};
  root.querySelectorAll('.th-filter').forEach(function(s){ criteres[s.dataset.col] = s.value; });
  var visibles = 0;
  root.querySelectorAll('tbody tr').forEach(function(tr){
    var ok = true;
    for (var col in criteres) {
      if (criteres[col] && tr.cells[col].textContent.trim() !== criteres[col]) { ok = false; break; }
    }
    tr.style.display = ok ? '' : 'none';
    if (ok) visibles++;
  });
  var c = root.querySelector('.tbl-count');
  if (c) c.textContent = visibles;
}
</script>'''

_TH_STYLE = 'border:1px solid #ddd;padding:8px;background:#f5f5f5;text-align:left;font-weight:600;vertical-align:top;'
_TD_STYLE = 'border:1px solid #ddd;padding:6px 8px;'


def _options_filtre(valeurs):
    opts_html = '<option value="">Tous</option>'
    for v in valeurs:
        v_esc = html_mod.escape(str(v))
        opts_html += f'<option value="{v_esc}">{v_esc}</option>'
    return opts_html


def _badge_tendance(tendance, variation_str, titre=''):
    trend_class = {'↗': 'up', '↘': 'down', '→': 'flat'}.get(tendance, 'flat')
    titre_attr = f' title="{html_mod.escape(titre)}"' if titre else ''
    return (f'<span class="trend-badge {trend_class}"{titre_attr}>'
            f'{tendance} {html_mod.escape(str(variation_str))}</span>')


def _render_table(headers, filtres, body_rows, footer_html, root_id):
    """headers: libellés de colonnes · filtres: {index_colonne: [valeurs]} ·
    body_rows: liste de listes (contenu, déjà_html) · footer_html: contenu du tfoot."""
    lines = ['<table style="border-collapse:collapse;width:100%;font-size:12px;font-family:sans-serif;">']
    lines.append('<thead><tr>')
    for i, h in enumerate(headers):
        inner = h
        if i in filtres:
            inner = (f'<div>{h}</div>'
                     f'<select class="th-filter" data-col="{i}" onchange="filtrerTableau(this)">'
                     f'{_options_filtre(filtres[i])}</select>')
        lines.append(f'<th style="{_TH_STYLE}">{inner}</th>')
    lines.append('</tr></thead><tbody>')

    for cells in body_rows:
        lines.append('<tr>')
        for contenu, deja_html in cells:
            valeur = contenu if deja_html else html_mod.escape(str(contenu))
            lines.append(f'<td style="{_TD_STYLE}">{valeur}</td>')
        lines.append('</tr>')

    lines.append('</tbody>')
    lines.append(f'<tfoot><tr><td colspan="{len(headers)}">{footer_html}</td></tr></tfoot>')
    lines.append('</table>')
    # Pas d'overflow sur ce div : le conteneur de défilement est géré par la page
    return f'<div id="{root_id}" class="tbl-root">{"".join(lines)}{_TABLE_FILTER_SCRIPT}</div>'


def indicator_table_html(rows, root_id='indicator_table'):
    if not rows:
        return '<p style="color:#C53030;padding:12px">Aucune donnée pour ce secteur.</p>'

    headers = ['Indicateur', 'Niveau', '2013', '2015', '2018', '2022', 'Tendance 2013→2022', 'Variation']
    filtres = {
        0: sorted({r['indicateur'] for r in rows}),
        1: sorted({r['niveau'] for r in rows}),
    }

    body = []
    for r in rows:
        variation_str = r['variation']
        if isinstance(variation_str, (int, float)):
            variation_str = f"{r['variation']:+g}{r['unite']}"
        body.append([
            (r['indicateur'], False),
            (r['niveau'], False),
            (str(r['2013']), False),
            (str(r['2015']), False),
            (str(r['2018']), False),
            (str(r['2022']), False),
            (_badge_tendance(r['tendance'], variation_str), True),
            (variation_str, False),
        ])

    footer = (f'<i class="fas fa-database" style="margin-right:5px;opacity:0.6"></i>'
              f'Source : INSEED - 06-education-resultats-scolaires.csv · '
              f'<span class="tbl-count">{len(rows)}</span> / {len(rows)} lignes · valeurs en %')
    return _render_table(headers, filtres, body, footer, root_id)


def regional_indicator_table_html(rows, root_id='indicator_table_reg'):
    if not rows:
        return '<p style="color:#C53030;padding:12px">Aucune donnée régionale.</p>'

    headers = ['Indicateur', 'Région', '2014', '2018', '2022', 'Tendance', 'Variation']
    filtres = {
        0: sorted({r['indicateur'] for r in rows}),
        1: sorted({r['region'] for r in rows}),
    }

    body = []
    for r in rows:
        variation_str = f"{r['variation']:+g} pts"
        body.append([
            (r['indicateur'], False),
            (r['region'], False),
            (str(r['2014']), False),
            (str(r['2018']), False),
            (str(r['2022']), False),
            (_badge_tendance(r['tendance'], variation_str, titre=f"Période {r['periode']}"), True),
            (variation_str, False),
        ])

    footer = (f'<i class="fas fa-database" style="margin-right:5px;opacity:0.6"></i>'
              f'Sources : INSEED - fichiers 08 (promotion, jusqu\'à 2019) · 09 (BEPC) · 10 (transition) · '
              f'<span class="tbl-count">{len(rows)}</span> / {len(rows)} lignes · '
              f'tendance calculée sur la période disponible (survolez le badge)')
    return _render_table(headers, filtres, body, footer, root_id)


# ---------------------------------------------------------------------------
# Matrice de corrélation entre indicateurs nationaux (séries 2013-2022)
# ---------------------------------------------------------------------------
SERIES_CORRELATION = [
    ("Nombre d'écoles", 'Total', 'Écoles'),
    ("Nombre d'enseignants", 'Total', 'Enseignants'),
    ("Dépenses annuelles d'éducation", 'Total', 'Dépenses'),
    ("Part du Budget alloué à l'éducation (%)", 'Total', 'Budget (%)'),
    ("Taux d'achèvement ou de diplomation", 'Primaire', 'Achèv. primaire'),
    ("Taux d'achèvement ou de diplomation", 'Collège', 'Achèv. collège'),
    ("Taux d'achèvement ou de diplomation", 'Lycée', 'Achèv. lycée'),
    ('Taux de scolarisation', 'Total', 'Scolarisation'),
]


def get_correlation_data(df_resultats):
    """Matrice de corrélation de Pearson entre les séries nationales annuelles
    (secteur Total). Retourne un DataFrame carré indexé par libellés courts."""
    df = df_resultats.copy()
    df['Date'] = pd.to_numeric(df['Date'], errors='coerce')
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df = df[df['secteur'] == 'Total']

    colonnes = {}
    for indicateur, niveau, libelle in SERIES_CORRELATION:
        sub = df[(df['indicateurs'] == indicateur) & (df['niveau'] == niveau)]
        if sub.empty:
            continue
        serie = sub.groupby('Date')['Value'].mean()
        if serie.notna().sum() >= 4:      # au moins 4 années communes exigées
            colonnes[libelle] = serie
    matrice = pd.DataFrame(colonnes)
    return matrice.corr(min_periods=4)


def _cellule_correlation(r):
    if pd.isna(r):
        return '<td class="corr-nd">N/D</td>'
    # dégradé : vert Togo pour les corrélations positives, rouge pour les négatives
    alpha = round(min(abs(r), 1.0) * 0.75, 2)
    fond = f'rgba(0,106,78,{alpha})' if r >= 0 else f'rgba(239,51,64,{alpha})'
    encre = '#fff' if abs(r) > 0.55 else 'inherit'
    return f'<td style="background:{fond};color:{encre}">{r:+.2f}</td>'


def correlation_table_html(df_resultats):
    """Tableau thermique des corrélations entre indicateurs (2013-2022)."""
    corr = get_correlation_data(df_resultats)
    if corr.empty:
        return '<p style="color:red">Données insuffisantes pour les corrélations</p>'

    libelles = list(corr.columns)
    lignes = ['<table class="corr-table"><thead><tr><th></th>'
              + ''.join(f'<th>{html_mod.escape(l)}</th>' for l in libelles)
              + '</tr></thead><tbody>']
    for ligne_nom in libelles:
        cellules = ''.join(_cellule_correlation(corr.loc[ligne_nom, c]) for c in libelles)
        lignes.append(f'<tr><th>{html_mod.escape(ligne_nom)}</th>{cellules}</tr>')
    lignes.append('</tbody></table>')
    lignes.append('<div class="corr-note">Corrélation de Pearson entre les séries '
                  'annuelles nationales 2013-2022 (secteur Total) · +1 = évoluent '
                  'ensemble · -1 = évoluent en sens inverse · vert = positive, '
                  'rouge = négative.</div>')
    return '\n'.join(lignes)
