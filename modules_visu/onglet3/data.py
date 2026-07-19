import pandas as pd
import os
from .config import DATA_PATH, FICHIERS, REGIONS, REGION_08_MAP


def load_onglet3_data():
    dfs = {}
    for key, fname in FICHIERS.items():
        path = os.path.join(DATA_PATH, fname)
        try:
            dfs[key] = pd.read_csv(path, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            dfs[key] = pd.read_csv(path, encoding='latin1', low_memory=False)
        dfs[key] = dfs[key].drop_duplicates()
    return dfs


def _rlookup(region):
    return 'TOGO' if region == 'Togo' else region


def _v(df, region, annee, sexe='Total'):
    sub = df[(df['région'] == region) & (df['Date'] == annee) & (df['sexe'] == sexe)]
    if len(sub) == 0:
        return None
    val = pd.to_numeric(sub['Value'].iloc[0], errors='coerce')
    return None if pd.isna(val) else round(val, 1)


def get_heatmap_data(dfs, annee=None, sexe='Total'):
    promo = dfs['promotion']
    bepc = dfs['bepc']
    trans = dfs['transition']

    if annee is None:
        an_promo = int(promo['Date'].max())
        an_bepc = int(bepc['Date'].max())
        an_trans = int(trans['Date'].max())
    else:
        an_promo = an_bepc = an_trans = int(annee)

    rows = []
    for r in REGIONS:
        r08 = _rlookup(r)
        r09_10 = 'Togo' if r == 'Togo' else r

        promo_val = _v(promo, r08, an_promo, sexe) if an_promo in promo['Date'].values else None
        trans_val = _v(trans, r09_10, an_trans, sexe) if an_trans in trans['Date'].values else None
        bepc_val = _v(bepc, r09_10, an_bepc, sexe) if an_bepc in bepc['Date'].values else None

        rows.append({
            'region': r,
            'promotion': promo_val,
            'transition': trans_val,
            'bepc': bepc_val,
        })
    return rows


def get_national_indicators(dfs, annee=2022):
    df6 = dfs['resultats']
    def val6(indicator, niveau):
        sub = df6[(df6['indicateurs'] == indicator) & (df6['niveau'] == niveau) & (df6['secteur'] == 'Total') & (df6['Date'] == annee)]
        if len(sub) == 0:
            return None
        v = pd.to_numeric(sub['Value'].iloc[0], errors='coerce')
        return round(v, 1) if not pd.isna(v) else None

    return {
        'scolarisation_college': val6('Taux de scolarisation', 'Collège'),
        'achevement_college': val6("Taux d'achèvement ou de diplomation", 'Collège'),
    }


def get_heatmap_matrix(dfs, annee=None, sexe='Total'):
    regional = get_heatmap_data(dfs, annee=annee, sexe=sexe)
    nat_annee = annee if annee else 2022
    national = get_national_indicators(dfs, annee=nat_annee)

    label_promo = f'Promotion primaire\n({annee or 2019})'
    label_trans = f'Transition P\u2192S\n({annee or 2022})'
    label_bepc = f'Admission BEPC\n({annee or 2022})'
    label_scolar = f'Scolarisation\ncoll\u00e8ge ({nat_annee})'
    label_ach = f'Ach\u00e8vement\ncoll\u00e8ge ({nat_annee})'

    matrix = []
    for r in regional:
        matrix.append({
            'region': r['region'],
            label_promo: r['promotion'],
            label_trans: r['transition'],
            label_bepc: r['bepc'],
            label_scolar: national['scolarisation_college'],
            label_ach: national['achevement_college'],
        })
    return matrix


def get_evolution_data(dfs, indicateur='transition', sexe='Total', regions_filter=None):
    if indicateur == 'transition':
        df = dfs['transition']
    elif indicateur == 'bepc':
        df = dfs['bepc']
    elif indicateur == 'promotion':
        df = dfs['promotion']
    else:
        return {}

    regions = regions_filter if regions_filter else REGIONS

    series = {}
    for r in regions:
        r_lookup = 'Togo' if r == 'Togo' else r
        if indicateur == 'promotion':
            r_lookup = 'TOGO' if r == 'Togo' else r
        sub = df[(df['région'] == r_lookup) & (df['sexe'] == sexe)].copy()
        sub['Date'] = pd.to_numeric(sub['Date'], errors='coerce')
        sub['Value'] = pd.to_numeric(sub['Value'], errors='coerce')
        sub = sub.dropna(subset=['Date', 'Value']).sort_values('Date')
        pts = [(int(d), round(v, 1)) for d, v in zip(sub['Date'], sub['Value'])]
        series[r] = pts
    return series


def get_ranking_data(dfs, annee=None, sexe='Total'):
    regional = get_heatmap_data(dfs, annee=annee, sexe=sexe)
    nat_annee = annee if annee else 2022
    national = get_national_indicators(dfs, annee=nat_annee)

    ranks = []
    for r in regional:
        # Score composite pondéré, renormalisé sur les composantes disponibles
        # (évite qu'un indicateur absent - ex. promotion après 2019 - écrase le score).
        # Sans AUCUNE composante régionale, le score serait purement national :
        # on renvoie None (N/D) plutôt qu'un chiffre trompeur.
        composantes = [
            (r['transition'], 0.25),
            (r['bepc'], 0.25),
            (r['promotion'], 0.20),
            (national['scolarisation_college'], 0.15),
            (national['achevement_college'], 0.15),
        ]
        a_composante_regionale = any(
            v is not None for v in (r['transition'], r['bepc'], r['promotion'])
        )
        disponibles = [(v, w) for v, w in composantes if v is not None]
        poids_total = sum(w for _, w in disponibles)
        if a_composante_regionale and poids_total > 0:
            score = round(sum(v * w for v, w in disponibles) / poids_total, 1)
        else:
            score = None
        ranks.append({
            'region': r['region'],
            'score': score,
            'promotion': r['promotion'],
            'transition': r['transition'],
            'bepc': r['bepc'],
        })
    ranks.sort(key=lambda x: -(x['score'] if x['score'] is not None else float('-inf')))
    for i, r in enumerate(ranks):
        r['rang'] = i + 1
        if r['score'] is None:
            r['alerte'] = '-'
        else:
            r['alerte'] = '\U0001f534' if r['score'] < 70 else ('\U0001f7e1' if r['score'] < 80 else '\U0001f7e2')
    return ranks
