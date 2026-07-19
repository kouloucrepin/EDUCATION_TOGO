"""Outils exposés au modèle sur la route base de données.

execute_python  : exécute du pandas dans un sandbox (le modèle GÉNÈRE le code
                  puis l'exécute ici — la « génération » n'est pas un outil
                  séparé, c'est la réponse du modèle elle-même).
get_schema      : catalogue YAML complet, ou détail réel d'un DataFrame.
sample_data     : lignes d'exemple d'un DataFrame.
find_similar_values : recherche floue d'une valeur (régions, indicateurs…).
"""
import builtins
import contextlib
import difflib
import io
import threading
import unicodedata

import pandas as pd
import numpy as np

from . import config, connaissances, donnees

# --------------------------------------------------------------------------
# Sandbox d'exécution
# --------------------------------------------------------------------------
_MODULES_AUTORISES = {'pandas', 'numpy', 'math', 're', 'datetime', 'difflib',
                      'json', 'statistics', 'collections', 'unicodedata'}

_NOMS_BUILTINS_SURS = [
    'abs', 'all', 'any', 'bool', 'dict', 'divmod', 'enumerate', 'filter',
    'float', 'format', 'frozenset', 'int', 'isinstance', 'issubclass', 'iter',
    'len', 'list', 'map', 'max', 'min', 'next', 'print', 'range', 'repr',
    'reversed', 'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple',
    'type', 'zip', 'Exception', 'ValueError', 'KeyError', 'TypeError',
    'IndexError', 'ZeroDivisionError', 'StopIteration', 'True', 'False', 'None',
]


def _import_sur(nom, *args, **kwargs):
    if nom.split('.')[0] not in _MODULES_AUTORISES:
        raise ImportError(f'module interdit dans le sandbox : {nom}')
    return __import__(nom, *args, **kwargs)


def _builtins_surs():
    surs = {n: getattr(builtins, n) for n in _NOMS_BUILTINS_SURS if hasattr(builtins, n)}
    surs['__import__'] = _import_sur
    return surs


def _tronquer(texte, limite=None):
    limite = limite or config.MAX_SORTIE_OUTIL
    texte = str(texte)
    if len(texte) > limite:
        return texte[:limite] + f'\n… [tronqué à {limite} caractères]'
    return texte


def execute_python(code):
    """Exécute du code pandas. `dfs['06']`… sont des copies ; pd/np disponibles.
    Le code doit produire sa sortie via print() ou une variable `resultat`."""
    env = {
        '__builtins__': _builtins_surs(),
        'pd': pd, 'np': np,
        'dfs': donnees.copies(),
    }
    capture = {}

    def _executer():
        tampon = io.StringIO()
        try:
            with contextlib.redirect_stdout(tampon):
                exec(code, env)  # noqa: S102 — sandbox restreint ci-dessus
            capture['stdout'] = tampon.getvalue()
        except Exception as e:  # noqa: BLE001 — renvoyé au modèle pour correction
            capture['stdout'] = tampon.getvalue()
            capture['erreur'] = f'{type(e).__name__}: {e}'

    fil = threading.Thread(target=_executer, daemon=True)
    fil.start()
    fil.join(config.TIMEOUT_EXEC)
    if fil.is_alive():
        return f'ERREUR : temps d\'exécution dépassé (> {config.TIMEOUT_EXEC}s). Simplifie ton code.'

    morceaux = []
    if capture.get('stdout'):
        morceaux.append(capture['stdout'].rstrip())
    if 'resultat' in env and env['resultat'] is not None:
        morceaux.append(repr(env['resultat']))
    if capture.get('erreur'):
        morceaux.append('ERREUR : ' + capture['erreur'])
    return _tronquer('\n'.join(morceaux) or '(aucune sortie — utilise print() ou la variable resultat)')


# --------------------------------------------------------------------------
# Introspection
# --------------------------------------------------------------------------
def get_schema(cle=None):
    """Sans argument : le catalogue YAML. Avec une clé : la structure réelle du df."""
    if not cle:
        return _tronquer(connaissances.schemas(), 6000)
    df = donnees.obtenir(cle)
    lignes = [f"dfs['{cle}'] — {df.shape[0]} lignes × {df.shape[1]} colonnes"]
    for col in df.columns:
        lignes.append(f'  {col} : {df[col].dtype}')
    return _tronquer('\n'.join(lignes))


def sample_data(cle, n=3):
    """n lignes d'exemple (1 à 10) du DataFrame demandé."""
    n = max(1, min(int(n), 10))
    df = donnees.obtenir(cle)
    return _tronquer(df.head(n).to_string(max_colwidth=40))


# --------------------------------------------------------------------------
# Recherche floue
# --------------------------------------------------------------------------
def _normaliser(texte):
    texte = unicodedata.normalize('NFD', str(texte))
    return ''.join(c for c in texte if unicodedata.category(c) != 'Mn').lower().strip()


def find_similar_values(terme, cle='', colonne=''):
    """Cherche `terme` dans les colonnes texte (insensible casse/accents + difflib)."""
    terme_norm = _normaliser(terme)
    cles_ciblees = [cle] if cle else donnees.cles()
    trouvailles = []
    for k in cles_ciblees:
        df = donnees.obtenir(k)
        colonnes = [colonne] if colonne else [c for c in df.columns if df[c].dtype == object]
        for col in colonnes:
            if col not in df.columns:
                continue
            valeurs = df[col].dropna().astype(str).unique()
            if len(valeurs) > 5000:      # colonnes quasi uniques (noms d'écoles…) : limiter
                valeurs = valeurs[:5000]
            normalisees = {v: _normaliser(v) for v in valeurs}
            exactes = [v for v, nv in normalisees.items() if terme_norm in nv]
            proches = difflib.get_close_matches(terme_norm, list(normalisees.values()), n=3, cutoff=0.75)
            floues = [v for v, nv in normalisees.items() if nv in proches]
            for v in dict.fromkeys(exactes + floues):
                trouvailles.append(f"dfs['{k}'] · colonne {col!r} · valeur {v!r}")
                if len(trouvailles) >= 25:
                    return _tronquer('\n'.join(trouvailles))
    return _tronquer('\n'.join(trouvailles) or f'Aucune valeur proche de {terme!r} trouvée.')


# --------------------------------------------------------------------------
# Génération de graphiques (affichés dans le chatbot du dashboard)
# --------------------------------------------------------------------------
# Magasin par thread : le fragment HTML (lourd) ne transite JAMAIS par le
# modèle — l'outil ne lui renvoie qu'un marqueur [GRAPHIQUE_n] à placer dans
# la réponse ; le serveur remplace le marqueur par le fragment au rendu.
_graphiques_local = threading.local()


def _magasin_graphiques():
    if not hasattr(_graphiques_local, 'items'):
        _graphiques_local.items = {}
        _graphiques_local.compteur = 0
    return _graphiques_local


TYPES_GRAPHIQUES = ('bar', 'line', 'pie', 'scatter', 'funnel', 'radar', 'sankey')


def generer_graphique(type_graphique, titre='', categories=None, series=None, liens=None):
    """Crée un graphique ECharts affichable dans le chatbot.

    type_graphique : bar | line | pie | scatter | funnel | radar | sankey
    categories : étiquettes (axe X, parts du pie/funnel, axes du radar)
    series     : dict {nom_de_serie: [valeurs]} — pie/funnel : 1re série seulement
    liens      : POUR SANKEY UNIQUEMENT : [[source, cible, valeur], ...]
    Retourne un marqueur [GRAPHIQUE_n] à insérer dans la reponse_finale."""
    from pyecharts.charts import Bar, Funnel, Line, Pie, Radar, Sankey, Scatter
    from pyecharts import options as popts
    from modules_visu.embed import chart_fragment

    if type_graphique not in TYPES_GRAPHIQUES:
        return f"ERREUR : type_graphique doit être parmi {TYPES_GRAPHIQUES}."
    categories = [str(c) for c in (categories or [])]
    series = series or {}

    def _nombre(v):
        return None if v is None else float(v)

    init = popts.InitOpts(width='100%', height='280px', bg_color='transparent')

    if type_graphique == 'sankey':
        if not liens:
            return "ERREUR : sankey exige 'liens': [[source, cible, valeur], ...]."
        noeuds = []
        for src, cible, _ in liens:
            for n in (str(src), str(cible)):
                if n not in noeuds:
                    noeuds.append(n)
        chart = Sankey(init_opts=init).add(
            '', [{'name': n} for n in noeuds],
            [{'source': str(s), 'target': str(c), 'value': _nombre(v)} for s, c, v in liens],
            linestyle_opt=popts.LineStyleOpts(opacity=0.4, curve=0.5, color='source'),
            label_opts=popts.LabelOpts(font_size=10),
            node_width=14, node_gap=8)
        chart.set_global_opts(tooltip_opts=popts.TooltipOpts(trigger='item'))

    elif not categories or not series:
        return 'ERREUR : categories (liste) et series (dict nom -> valeurs) sont requis.'

    elif type_graphique in ('pie', 'funnel'):
        nom, valeurs = next(iter(series.items()))
        paires = [(c, _nombre(v)) for c, v in zip(categories, valeurs)]
        if type_graphique == 'pie':
            chart = Pie(init_opts=init).add(nom, paires, radius=['35%', '65%'],
                                            label_opts=popts.LabelOpts(font_size=10))
        else:
            chart = Funnel(init_opts=init).add(nom, paires,
                                               label_opts=popts.LabelOpts(font_size=10))
        chart.set_global_opts(
            legend_opts=popts.LegendOpts(pos_bottom=0,
                                         textstyle_opts=popts.TextStyleOpts(font_size=10)))

    elif type_graphique == 'radar':
        maxi = max(max(_nombre(v) or 0 for v in vals) for vals in series.values()) * 1.15
        chart = Radar(init_opts=init)
        chart.add_schema(
            schema=[popts.RadarIndicatorItem(name=c, max_=round(maxi, 1)) for c in categories],
            textstyle_opts=popts.TextStyleOpts(font_size=10))
        for nom, valeurs in series.items():
            chart.add(nom, [{'value': [_nombre(v) for v in valeurs], 'name': nom}],
                      areastyle_opts=popts.AreaStyleOpts(opacity=0.15),
                      label_opts=popts.LabelOpts(is_show=False))
        chart.set_global_opts(
            legend_opts=popts.LegendOpts(pos_bottom=0,
                                         textstyle_opts=popts.TextStyleOpts(font_size=10)))

    else:  # bar | line | scatter — axe X commun + une ou plusieurs séries Y
        classes = {'bar': Bar, 'line': Line, 'scatter': Scatter}
        chart = classes[type_graphique](init_opts=init)
        chart.add_xaxis(categories)
        for nom, valeurs in series.items():
            options = {'label_opts': popts.LabelOpts(is_show=False)}
            if type_graphique == 'line':
                options['is_smooth'] = True
            if type_graphique == 'scatter':
                options['symbol_size'] = 10
            chart.add_yaxis(nom, [_nombre(v) for v in valeurs], **options)
        chart.set_global_opts(
            legend_opts=popts.LegendOpts(pos_top=0,
                                         textstyle_opts=popts.TextStyleOpts(font_size=10)),
            xaxis_opts=popts.AxisOpts(axislabel_opts=popts.LabelOpts(font_size=9, rotate=30)),
            yaxis_opts=popts.AxisOpts(axislabel_opts=popts.LabelOpts(font_size=9)),
            tooltip_opts=popts.TooltipOpts(trigger='axis'),
        )
        chart.options['grid'] = {'left': '2%', 'right': '3%', 'top': 28,
                                 'bottom': 4, 'containLabel': True}

    mag = _magasin_graphiques()
    mag.compteur += 1
    cle = f'GRAPHIQUE_{mag.compteur}'
    mag.items[cle] = chart_fragment(chart.render_embed())
    return (f'{cle} créé ({type_graphique}). '
            f'Insère le marqueur [{cle}] seul sur une ligne dans ta reponse_finale, '
            'avec ton analyse autour.')


def consommer_graphiques():
    """Récupère et vide les graphiques créés pendant la question en cours."""
    mag = _magasin_graphiques()
    items = dict(mag.items)
    mag.items.clear()
    return items


OUTILS = {
    'execute_python': execute_python,
    'get_schema': get_schema,
    'sample_data': sample_data,
    'find_similar_values': find_similar_values,
    'generer_graphique': generer_graphique,
}
