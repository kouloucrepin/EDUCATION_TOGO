import pandas as pd
from pyecharts.charts import Line
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from .config import COULEURS


def get_evolution_data(df_resultats, indicateur="Taux d'achèvement ou de diplomation", secteur='Total'):
    df = df_resultats.copy()
    df.loc[:, 'Date'] = pd.to_numeric(df['Date'], errors='coerce')
    df.loc[:, 'Value'] = pd.to_numeric(df['Value'], errors='coerce')

    niveaux = ['Primaire', 'Collège', 'Lycée', "Jardins d'enfants"]
    data = {}
    for niv in niveaux:
        sub = df[
            (df['indicateurs'] == indicateur) &
            (df['niveau'] == niv) &
            (df['secteur'] == secteur)
        ].sort_values('Date')
        if sub.empty:
            continue
        data[niv] = [
            {'annee': int(r['Date']), 'valeur': round(r['Value'], 1)}
            for _, r in sub.iterrows()
            if not pd.isna(r['Value'])
        ]
    return data


def evolution_line_chart(data, titre="Évolution des taux d'achèvement", unite='%'):
    if not data:
        return None

    couleurs_map = {
        'Primaire': '#22c55e',
        'Collège': '#f59e0b',
        'Lycée': '#ef4444',
        "Jardins d'enfants": '#3b82f6',
        'Total': '#6b7280',
    }

    all_annees = sorted(set(
        p['annee']
        for pts in data.values()
        for p in pts
    ))

    chart = (
        Line(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
        .add_xaxis([str(a) for a in all_annees])
        .set_global_opts(
            title_opts=opts.TitleOpts(title=titre, pos_left='center'),
            xaxis_opts=opts.AxisOpts(
                name='Année',
                name_location='middle',
                name_gap=30,
                type_='category',
                axislabel_opts=opts.LabelOpts(rotate=0),
            ),
            yaxis_opts=opts.AxisOpts(
                name=f'Taux ({unite})',
                type_='value',
                min_=0,
                max_=120,
                splitline_opts=opts.SplitLineOpts(is_show=True),
                axislabel_opts=opts.LabelOpts(formatter=f'{{value}}{unite}'),
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger='axis',
                formatter=JsCode(
                    """function(params) {
                        var s = '<b>' + params[0].axisValue + '</b><br/>';
                        for (var i = 0; i < params.length; i++) {
                            var v = Array.isArray(params[i].value) ? params[i].value[1] : params[i].value;
                            if (v === null || v === undefined) continue;
                            s += params[i].marker + ' ' + params[i].seriesName + ': ' + v + '%<br/>';
                        }
                        return s;
                    }"""
                ),
            ),
            legend_opts=opts.LegendOpts(pos_top='0'),
        )
    )

    for niv, pts in data.items():
        values_map = {p['annee']: p['valeur'] for p in pts}
        y_vals = [values_map.get(a, None) for a in all_annees]
        couleur = couleurs_map.get(niv, '#666')
        chart.add_yaxis(
            niv,
            y_vals,
            is_smooth=True,
            symbol='circle',
            symbol_size=8,
            linestyle_opts=opts.LineStyleOpts(width=2.5, color=couleur),
            # Points et légende dans la même couleur que la ligne
            itemstyle_opts=opts.ItemStyleOpts(color=couleur),
            areastyle_opts=opts.AreaStyleOpts(opacity=0.08, color=couleur),
            label_opts=opts.LabelOpts(is_show=True, font_size=10, position='top'),
            is_connect_nones=True,
        )

    # Grille étendue sur toute la largeur de la card
    chart.options['grid'] = {'left': '2%', 'right': '2%', 'top': 36, 'bottom': 48, 'containLabel': True}
    return chart


def evolution_line_html(data, titre="Évolution des taux d'achèvement"):
    chart = evolution_line_chart(data, titre)
    if chart is None:
        return '<p style="color:red">Aucune donnée disponible</p>'
    return f'<div id="evolution_chart">{chart.render_embed()}</div>'


def get_evolution_par_secteur(df_resultats, indicateur="Nombre d'écoles", niveau='Total'):
    """Séries 2013-2022 par secteur (Total / Public / Privé) pour un indicateur
    qui possède ce détail dans le fichier 06 (comptes d'écoles et d'enseignants)."""
    df = df_resultats.copy()
    df.loc[:, 'Date'] = pd.to_numeric(df['Date'], errors='coerce')
    df.loc[:, 'Value'] = pd.to_numeric(df['Value'], errors='coerce')

    secteurs = {
        'Total': 'Total',
        'Public': 'Public',
        'Autres (Privés, confessionnelles, etc.)': 'Privé / autres',
    }
    data = {}
    for secteur_brut, label in secteurs.items():
        sub = df[
            (df['indicateurs'] == indicateur) &
            (df['niveau'] == niveau) &
            (df['secteur'] == secteur_brut)
        ].dropna(subset=['Date', 'Value']).sort_values('Date')
        if sub.empty:
            continue
        data[label] = [
            {'annee': int(r['Date']), 'valeur': round(r['Value'], 0)}
            for _, r in sub.iterrows()
        ]
    return data


def evolution_secteur_chart(data, titre=''):
    """Courbes par secteur (valeurs en effectifs, pas en %)."""
    if not data:
        return None

    couleurs = {'Total': '#006A4E', 'Public': '#0033A0', 'Privé / autres': '#D4A017'}
    all_annees = sorted(set(p['annee'] for pts in data.values() for p in pts))

    chart = (
        Line(init_opts=opts.InitOpts(width='100%', height='380px', bg_color='transparent'))
        .add_xaxis([str(a) for a in all_annees])
        .set_global_opts(
            title_opts=opts.TitleOpts(title=titre, pos_left='center'),
            xaxis_opts=opts.AxisOpts(
                name='Année', name_location='middle', name_gap=30,
                type_='category',
                axislabel_opts=opts.LabelOpts(rotate=0),
            ),
            yaxis_opts=opts.AxisOpts(
                name='Nombre',
                type_='value',
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger='axis',
                formatter=JsCode(
                    """function(params) {
                        var s = '<b>' + params[0].axisValue + '</b><br/>';
                        for (var i = 0; i < params.length; i++) {
                            var v = Array.isArray(params[i].value) ? params[i].value[1] : params[i].value;
                            if (v === null || v === undefined) continue;
                            s += params[i].marker + ' ' + params[i].seriesName + ': ' + Number(v).toLocaleString('fr-FR') + '<br/>';
                        }
                        return s;
                    }"""
                ),
            ),
            legend_opts=opts.LegendOpts(pos_top='0'),
        )
    )

    for label, pts in data.items():
        valeurs = {p['annee']: p['valeur'] for p in pts}
        couleur = couleurs.get(label, '#666')
        chart.add_yaxis(
            label,
            [valeurs.get(a) for a in all_annees],
            is_smooth=True,
            symbol='circle',
            symbol_size=7,
            linestyle_opts=opts.LineStyleOpts(width=2.5, color=couleur),
            # Points et légende dans la même couleur que la ligne
            itemstyle_opts=opts.ItemStyleOpts(color=couleur),
            areastyle_opts=opts.AreaStyleOpts(opacity=0.06, color=couleur),
            label_opts=opts.LabelOpts(is_show=False),
            is_connect_nones=True,
        )

    chart.options['grid'] = {'left': '2%', 'right': '2%', 'top': 36, 'bottom': 48, 'containLabel': True}
    return chart


def evolution_secteur_html(data, titre=''):
    chart = evolution_secteur_chart(data, titre)
    if chart is None:
        return '<p style="color:red">Aucune donnée disponible</p>'
    return f'<div>{chart.render_embed()}</div>'


def area_chart_univarie(series, titre="", unite='%', couleur='#22c55e', largeur='100%', hauteur='300px'):
    """Area chart pour une seule série (liste de dicts {annee, valeur} ou tuples)."""
    if not series:
        return None
    if isinstance(series[0], dict):
        x = [str(s['annee']) for s in series]
        y = [round(s['valeur'], 1) for s in series]
    else:
        x = [str(s[0]) for s in series]
        y = [round(s[1], 1) for s in series]

    chart = (
        Line(init_opts=opts.InitOpts(width=largeur, height=hauteur, bg_color='transparent'))
        .add_xaxis(x)
        .add_yaxis(
            '',
            y,
            is_smooth=True,
            symbol='circle',
            symbol_size=6,
            linestyle_opts=opts.LineStyleOpts(width=2.5, color=couleur),
            itemstyle_opts=opts.ItemStyleOpts(color=couleur),
            areastyle_opts=opts.AreaStyleOpts(opacity=0.35, color=couleur),
            label_opts=opts.LabelOpts(is_show=True, font_size=10, position='top',
                formatter=f'{{c}}{unite}'),
            is_connect_nones=True,
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=titre, pos_left='center', title_textstyle_opts=opts.TextStyleOpts(font_size=14)),
            xaxis_opts=opts.AxisOpts(name='Année', name_location='middle', name_gap=30,
                type_='category',
                axislabel_opts=opts.LabelOpts(rotate=0)),
            yaxis_opts=opts.AxisOpts(type_='value',
                splitline_opts=opts.SplitLineOpts(is_show=True),
                axislabel_opts=opts.LabelOpts(formatter=f'{{value}}{unite}')),
            tooltip_opts=opts.TooltipOpts(trigger='axis',
                # Les points sont des paires [année, valeur] : n'afficher que la valeur
                formatter=JsCode(
                    "function(params){var p=params[0];"
                    "var v=Array.isArray(p.value)?p.value[1]:p.value;"
                    "return p.axisValue+'<br/>'+v+'" + unite + "';}"
                )),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    chart.options['grid'] = {'left': '2%', 'right': '2%', 'top': 24, 'bottom': 44, 'containLabel': True}
    return chart


def area_chart_univarie_html(series, titre="", unite='%', couleur='#22c55e'):
    chart = area_chart_univarie(series, titre, unite, couleur)
    if chart is None:
        return '<p style="color:red">Aucune donnée</p>'
    return f'<div>{chart.render_embed()}</div>'
