import pandas as pd, numpy as np, os

p = r'C:\Users\Ultra Tech\Desktop\SOLUTION1\Competition 3\data'

df1 = pd.read_csv(os.path.join(p, '01-etablissements-scolaires.csv'), encoding='utf-8', low_memory=False)
df9 = pd.read_csv(os.path.join(p, '09-admission-bepc-region-sexe.csv'), encoding='utf-8')
df14 = pd.read_csv(os.path.join(p, '14-projet-coso-education.csv'), encoding='utf-8')

print('=== RATIO ELEVES/CLASSE PAR REGION ===')
for reg in df1['region_nom_bdd'].unique():
    sub = df1[df1['region_nom_bdd'] == reg]
    eleves = sub['eleve_nbr'].sum()
    classes = sub['classe_nbr'].sum()
    ratio = eleves / classes if classes > 0 else 0
    print(f'  {reg}: {int(eleves)} eleves, {int(classes)} classes -> {ratio:.1f} eleves/classe')

print('\n=== ELECTRIFICATION ===')
if 'elec_acces' in df1.columns:
    print(f'  Echantillon: {df1["elec_acces"].dropna().value_counts().head(5).to_dict()}')

print('\n=== SALLES INFO ===')
if 'salle_info' in df1.columns:
    print(f'  {df1["salle_info"].dropna().value_counts().head(5).to_dict()}')

print('\n=== COSO TYPES ===')
print(f'  Types: {df14["type"].value_counts().to_dict()}')
print(f'  Status: {df14["status"].value_counts(dropna=False).to_dict()}')
print(f'  Avancement moyen: {df14["progress_percent"].dropna().mean():.1f}%')
print(f'  Salles classe totales: {int(df14["number_of_classrooms"].dropna().sum())}')
print(f'  Latrines totales: {int(df14["number_of_latrine_blocks"].dropna().sum())}')

print('\n=== GENDER GAP BEPC 2022 ===')
for reg in df9['region'].unique():
    fvals = df9[(df9['region']==reg) & (df9['sexe']=='Feminin') & (df9['Date']==2022)]['Value']
    mvals = df9[(df9['region']==reg) & (df9['sexe']=='Masculin') & (df9['Date']==2022)]['Value']
    if len(fvals) > 0 and len(mvals) > 0:
        print(f'  {reg}: F={fvals.values[0]:.1f}% M={mvals.values[0]:.1f}% gap={mvals.values[0]-fvals.values[0]:.1f}pp')
