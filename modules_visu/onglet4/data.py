import pandas as pd
import os
from .config import DATA_PATH, FICHIERS, REGIONS_09, REGIONS_09_SIMPLE, INSPECTIONS_REGIONS


def load_onglet4_data():
    dfs = {}
    for key, fname in FICHIERS.items():
        path = os.path.join(DATA_PATH, fname)
        try:
            dfs[key] = pd.read_csv(path, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            dfs[key] = pd.read_csv(path, encoding='latin1', low_memory=False)
        dfs[key] = dfs[key].drop_duplicates()
    return dfs


def get_bepc_data(dfs, region='Togo', sexes=None):
    if sexes is None:
        sexes = ['Total', 'F\u00e9minin', 'Masculin']
    df = dfs['bepc']
    sub = df[(df['r\u00e9gion'] == region) & (df['sexe'].isin(sexes))].copy()
    sub['Date'] = pd.to_numeric(sub['Date'], errors='coerce')
    sub['Value'] = pd.to_numeric(sub['Value'], errors='coerce')
    sub = sub.dropna(subset=['Date', 'Value']).sort_values(['sexe', 'Date'])

    series = {}
    for s in sexes:
        pts = sub[sub['sexe'] == s]
        series[s] = [(int(d), round(v, 1)) for d, v in zip(pts['Date'], pts['Value'])]
    return series


def get_bepc_by_region_sexe(dfs, annee=2022):
    df = dfs['bepc']
    sub = df[(df['Date'] == annee)].copy()
    regions = [r for r in REGIONS_09 if r in sub['r\u00e9gion'].values]
    rows = []
    for r in regions:
        def val(sexe):
            v = sub[(sub['r\u00e9gion'] == r) & (sub['sexe'] == sexe)]['Value']
            if len(v) == 0:
                return None
            return round(pd.to_numeric(v.iloc[0], errors='coerce'), 1)
        rows.append({
            'region': r,
            'F\u00e9minin': val('F\u00e9minin'),
            'Masculin': val('Masculin'),
            'Total': val('Total'),
        })
    return rows


def get_ecart_regional(dfs, annee=2022):
    rows = get_bepc_by_region_sexe(dfs, annee=annee)
    for r in rows:
        f = r['F\u00e9minin']
        m = r['Masculin']
        if f is not None and m is not None:
            r['ecart'] = round(m - f, 1)
        else:
            r['ecart'] = None
    return rows


def get_prescolaire_data(dfs):
    df = dfs['prescolaire']
    general = df[df['inspections'] == 'T.G\u00e9n\u00e9ral'].copy()
    general['Value'] = pd.to_numeric(general['Value'], errors='coerce')

    def val(sexe):
        v = general[general['sexe'] == sexe]['Value']
        return int(v.iloc[0]) if len(v) > 0 else 0

    total = val('Total')
    return {
        'total': total,
        'femmes': val('F\u00e9minin'),
        'hommes': val('Masculin'),
        'pct_femmes': round(val('F\u00e9minin') / total * 100, 1) if total else 0,
    }


def get_prescolaire_par_inspection(dfs):
    df = dfs['prescolaire']
    # Exclure T.Général et T.R.* lignes
    mask = ~df['inspections'].str.startswith('T.')
    local = df[mask].copy()
    local = local[local['sexe'] == 'Total'].copy()
    local['Value'] = pd.to_numeric(local['Value'], errors='coerce')
    local = local.dropna(subset=['Value']).sort_values('Value', ascending=False)
    items = []
    for _, r in local.iterrows():
        items.append({
            'inspection': r['inspections'],
            'total': int(r['Value']),
        })
    return items


def get_prescolaire_matrice(dfs):
    """Répartition des enseignants du préscolaire : une ligne par (année, région)
    avec effectifs Masculin / Féminin / Total (agrégats régionaux T.R.*,
    donc sans double comptage des inspections locales)."""
    df = dfs['prescolaire'].copy()
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df['Date'] = pd.to_numeric(df['Date'], errors='coerce')

    rows = []
    for code, nom in INSPECTIONS_REGIONS.items():
        sub = df[df['inspections'] == code]
        for annee in sorted(sub['Date'].dropna().unique()):
            s_annee = sub[sub['Date'] == annee]

            def _val(sexe):
                v = s_annee[s_annee['sexe'] == sexe]['Value']
                return int(v.iloc[0]) if len(v) > 0 and not pd.isna(v.iloc[0]) else None

            rows.append({
                'annee': int(annee),
                'region': nom,
                'masculin': _val('Masculin'),
                'feminin': _val('Féminin'),
                'total': _val('Total'),
            })
    rows.sort(key=lambda r: (r['annee'], -(r['total'] or 0)))
    return rows


def get_prescolaire_par_region(dfs):
    items = []
    for code, nom in INSPECTIONS_REGIONS.items():
        sub = dfs['prescolaire'][
            (dfs['prescolaire']['inspections'] == code) &
            (dfs['prescolaire']['sexe'] == 'Total')
        ]
        if len(sub) == 0:
            continue
        v = pd.to_numeric(sub['Value'].iloc[0], errors='coerce')
        if pd.isna(v):
            continue
        fem = dfs['prescolaire'][
            (dfs['prescolaire']['inspections'] == code) &
            (dfs['prescolaire']['sexe'] == 'F\u00e9minin')
        ]
        fv = pd.to_numeric(fem['Value'].iloc[0], errors='coerce') if len(fem) > 0 else 0
        items.append({
            'region': nom,
            'total': int(v),
            'femmes': int(fv) if not pd.isna(fv) else 0,
        })
    total = sum(i['total'] for i in items)
    for i in items:
        i['pct'] = round(i['total'] / total * 100, 1) if total else 0
    return items
