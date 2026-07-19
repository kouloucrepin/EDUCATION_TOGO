import pandas as pd
import os
from .config import DATA_PATH, FICHIERS, KPI_CONFIG


def load_onglet1_data():
    dfs = {}
    for key, fname in FICHIERS.items():
        path = os.path.join(DATA_PATH, fname)
        try:
            dfs[key] = pd.read_csv(path, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            dfs[key] = pd.read_csv(path, encoding='latin1', low_memory=False)
        dfs[key] = dfs[key].drop_duplicates()
    return dfs


def filter_data(df, niveau=None, annee_min=None, annee_max=None, secteur='Total'):
    out = df.copy()
    if 'Date' in out.columns:
        out['Date'] = pd.to_numeric(out['Date'], errors='coerce')
        if annee_min is not None:
            out = out[out['Date'] >= annee_min]
        if annee_max is not None:
            out = out[out['Date'] <= annee_max]
    if niveau and 'niveau' in out.columns and niveau != 'Tous':
        out = out[out['niveau'] == niveau]
    if secteur and 'secteur' in out.columns:
        out = out[out['secteur'] == secteur]
    return out


def get_kpi_data(df_resultats, annee=None, secteur='Total'):
    if annee is None:
        annee = int(df_resultats['Date'].max())
    else:
        annee = int(annee)
    rows = []
    for cfg in KPI_CONFIG:
        sub = df_resultats[
            (df_resultats['indicateurs'] == cfg['indicator']) &
            (df_resultats['niveau'] == cfg['niveau']) &
            (df_resultats['secteur'] == secteur)
        ].copy()
        sub.loc[:, 'Date'] = pd.to_numeric(sub['Date'], errors='coerce')
        sub.loc[:, 'Value'] = pd.to_numeric(sub['Value'], errors='coerce')
        sub = sub.dropna(subset=['Value'])
        sub = sub.sort_values('Date')

        full_series = [(int(r['Date']), r['Value']) for _, r in sub.iterrows()]
        values_by_year = dict(full_series)

        val_actuelle = values_by_year.get(annee)
        val_2013 = values_by_year.get(2013)
        val_prev = values_by_year.get(annee - 1) if annee > 2013 else None

        # Pic (hors année courante)
        autres = {d: v for d, v in values_by_year.items() if d != annee}
        val_pic = max(autres.values()) if autres else None
        annee_pic = max(autres, key=autres.get) if autres else None

        # Évolutions
        evolution_pts = None
        evolution_pct = None
        evolution_prev_pts = None
        evolution_prev_pct = None
        evolution_pic_pts = None
        evolution_pic_pct = None
        multiplicateur = None

        if val_actuelle is not None and val_2013 is not None:
            if cfg['unite'] == 'Md FCFA':
                evolution_pct = ((val_actuelle - val_2013) / val_2013 * 100) if val_2013 != 0 else None
            else:
                evolution_pts = val_actuelle - val_2013
                if val_2013 != 0:
                    multiplicateur = val_actuelle / val_2013

        if val_actuelle is not None and val_prev is not None:
            if cfg['unite'] == 'Md FCFA':
                evolution_prev_pct = ((val_actuelle - val_prev) / val_prev * 100) if val_prev != 0 else None
            else:
                evolution_prev_pts = val_actuelle - val_prev

        if val_actuelle is not None and val_pic is not None and val_pic != val_actuelle:
            if cfg['unite'] == 'Md FCFA':
                evolution_pic_pct = ((val_actuelle - val_pic) / val_pic * 100) if val_pic != 0 else None
            else:
                evolution_pic_pts = val_actuelle - val_pic

        rows.append({
            'cfg': cfg,
            'valeur': val_actuelle,
            'annee': annee,
            'val_2013': val_2013,
            'val_prev': val_prev,
            'val_pic': val_pic,
            'annee_pic': annee_pic,
            'evolution_pts': evolution_pts,
            'evolution_pct': evolution_pct,
            'evolution_prev_pts': evolution_prev_pts,
            'evolution_prev_pct': evolution_prev_pct,
            'evolution_pic_pts': evolution_pic_pts,
            'evolution_pic_pct': evolution_pic_pct,
            'multiplicateur': multiplicateur,
            'full_series': full_series,
        })
    return rows


def get_funnel_data(df_resultats, annee=None):
    if annee is None:
        annee = int(df_resultats['Date'].max())

    niveaux = ['Primaire', 'Collège', 'Lycée']
    indicateur = "Taux d'achèvement ou de diplomation"
    data = []

    for niv in niveaux:
        sub = df_resultats[
            (df_resultats['indicateurs'] == indicateur) &
            (df_resultats['niveau'] == niv) &
            (df_resultats['secteur'] == 'Total')
        ].copy()
        sub.loc[:, 'Date'] = pd.to_numeric(sub['Date'], errors='coerce')
        row = sub[sub['Date'] == annee]
        if len(row) > 0:
            val = pd.to_numeric(row['Value'].iloc[0], errors='coerce')
            if not pd.isna(val):
                data.append({'niveau': niv, 'taux': val})
    return data


def get_funnel_evolution_data(df_resultats):
    """Taux d'achèvement des 3 niveaux de l'entonnoir, année par année.

    Retourne {'annees': [2013, ...], 'series': {'Primaire': [...], ...}}
    (None quand la valeur manque pour une année)."""
    niveaux = ['Primaire', 'Collège', 'Lycée']
    indicateur = "Taux d'achèvement ou de diplomation"

    sub = df_resultats[
        (df_resultats['indicateurs'] == indicateur) &
        (df_resultats['niveau'].isin(niveaux)) &
        (df_resultats['secteur'] == 'Total')
    ].copy()
    sub.loc[:, 'Date'] = pd.to_numeric(sub['Date'], errors='coerce')
    sub.loc[:, 'Value'] = pd.to_numeric(sub['Value'], errors='coerce')
    sub = sub.dropna(subset=['Date'])

    annees = sorted(int(a) for a in sub['Date'].unique())
    series = {}
    for niv in niveaux:
        par_annee = sub[sub['niveau'] == niv].set_index('Date')['Value'].to_dict()
        series[niv] = [
            round(par_annee[a], 1) if a in par_annee and not pd.isna(par_annee[a]) else None
            for a in annees
        ]
    return {'annees': annees, 'series': series}


def get_scatter_data(df_resultats):
    budget = df_resultats[
        (df_resultats['indicateurs'] == "Part du Budget alloué à l'éducation (%)") &
        (df_resultats['niveau'] == 'Total') &
        (df_resultats['secteur'] == 'Total')
    ].copy()
    budget.loc[:, 'Date'] = pd.to_numeric(budget['Date'], errors='coerce')
    budget = budget[['Date', 'Value']].rename(columns={'Value': 'part_budget'})

    depenses = df_resultats[
        (df_resultats['indicateurs'] == "Dépenses annuelles d'éducation") &
        (df_resultats['niveau'] == 'Total') &
        (df_resultats['secteur'] == 'Total')
    ].copy()
    depenses.loc[:, 'Date'] = pd.to_numeric(depenses['Date'], errors='coerce')
    depenses = depenses[['Date', 'Value']].rename(columns={'Value': 'depenses'})

    achevements = df_resultats[
        (df_resultats['indicateurs'] == "Taux d'achèvement ou de diplomation") &
        (df_resultats['secteur'] == 'Total')
    ].copy()
    achevements.loc[:, 'Date'] = pd.to_numeric(achevements['Date'], errors='coerce')
    achevements = achevements[['Date', 'niveau', 'Value']].rename(columns={'Value': 'achevement'})

    rows = []
    for niv in ['Primaire', 'Collège', 'Lycée']:
        ach = achevements[achevements['niveau'] == niv]
        merged = budget.merge(ach, on='Date')
        merged = merged.merge(depenses, on='Date')
        for _, r in merged.iterrows():
            d = int(r['Date'])
            b = pd.to_numeric(r['part_budget'], errors='coerce')
            a = pd.to_numeric(r['achevement'], errors='coerce')
            dep = pd.to_numeric(r['depenses'], errors='coerce')
            if not pd.isna(b) and not pd.isna(a):
                rows.append({
                    'annee': d,
                    'part_budget': round(b, 1),
                    'achevement': round(a, 1),
                    'depenses': round(dep / 1e9, 1) if not pd.isna(dep) else None,
                    'niveau': niv,
                })
    return rows
