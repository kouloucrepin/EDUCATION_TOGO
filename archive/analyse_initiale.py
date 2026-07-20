import pandas as pd
import numpy as np
import os, json

data_path = r'C:\Users\Ultra Tech\Desktop\SOLUTION1\Competition 3\data'
results = {}

files = [
    '01-etablissements-scolaires.csv',
    '02-toilettes-scolaires.csv',
    '03-batiments-electrification.csv',
    '04-bibliotheques.csv',
    '05-professeurs-schema.csv',
    '06-education-resultats-scolaires.csv',
    '07-sdg4-data-togo.csv',
    '08-taux-promotion-primaire-region.csv',
    '09-admission-bepc-region-sexe.csv',
    '10-transition-primaire-secondaire.csv',
    '11-adolescents-non-scolarises.csv',
    '12-statistiques-secondaire.csv',
    '13-enseignants-prescolaire-inspection.csv',
    '14-projet-coso-education.csv',
    '16-education-togo-banque-mondiale.csv'
]

for fname in files:
    path = os.path.join(data_path, fname)
    print(f'========== {fname} ==========')
    try:
        if fname == '05-professeurs-schema.csv':
            df = pd.read_csv(path, encoding='utf-8', nrows=5)
        else:
            df = pd.read_csv(path, encoding='utf-8', low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding='latin1', low_memory=False)
    except Exception as e:
        print(f'  ERREUR: {e}')
        continue

    nrows = len(df)
    ncols = len(df.columns)
    print(f'  Dimensions: {nrows} lignes x {ncols} colonnes')
    print(f'  Mémoire: {df.memory_usage(deep=True).sum() / 1024**2:.1f} Mo')

    # Missing values
    miss = df.isnull().sum()
    miss_pct = (miss / nrows * 100).round(1) if nrows > 0 else miss
    high_miss = miss_pct[miss_pct > 80]
    med_miss = miss_pct[(miss_pct > 20) & (miss_pct <= 80)]

    if nrows > 0:
        print(f'  NA>80%: {len(high_miss)} colonnes')
        if len(med_miss) > 0:
            print(f'  NA 20-80%: {len(med_miss)} colonnes')
        print(f'  NA=0%: {len(miss_pct[miss_pct == 0])} colonnes completement remplies')

    # Numeric summary
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) > 0:
        print(f'  Colonnes numeriques: {len(num_cols)}')
        for col in num_cols[:8]:
            nona = df[col].dropna()
            if len(nona) > 0:
                print(f'    {col}: N={len(nona)}, min={nona.min()}, max={nona.max()}, mean={nona.mean():.2f}, median={nona.median():.2f}, null={miss_pct[col]}%')
            else:
                print(f'    {col}: TOUTES NULLES')

    # Categorical summary
    cat_cols = df.select_dtypes(include=['object']).columns
    if len(cat_cols) > 0:
        print(f'  Colonnes categorielles: {len(cat_cols)}')
        for col in cat_cols[:6]:
            nunique = df[col].nunique()
            top_vals = df[col].value_counts().head(5).to_dict()
            print(f'    {col}: {nunique} uniques, top={top_vals}')

    # Region analysis
    for rcol in ['region_nom_bdd', 'région', 'Region', 'region', 'REGION']:
        if rcol in df.columns:
            print(f'  Distribution region ({rcol}):')
            region_dist = df[rcol].value_counts(dropna=False)
            for r, c in region_dist.items():
                print(f'    {r}: {c:,} ({c/nrows*100:.1f}%)')

    # Temporal
    for dcol in ['Date', 'date', 'year', 'Year', 'annee', 'Année', 'etablissement_creation_date']:
        if dcol in df.columns:
            print(f'  Annees couvertes ({dcol}): {sorted(df[dcol].dropna().unique())[:20]}')

    print()
