import pandas as pd
import numpy as np
import os

data_path = r'C:\Users\Ultra Tech\Desktop\SOLUTION1\Competition 3\data'

# === 06 - Résultats clés ===
print("========== 06 - INDICATEURS CLÉS ==========")
df6 = pd.read_csv(os.path.join(data_path, '06-education-resultats-scolaires.csv'), encoding='utf-8')
for ind in ['Taux d\'achèvement ou de diplomation', 'Taux de scolarisation', 'Dépenses annuelles d\'éducation', 'Part du budget alloué à l\'éducation']:
    sub = df6[df6['indicateurs'] == ind]
    print(f'\n--- {ind} ---')
    for niv in sub['niveau'].unique():
        sn = sub[sub['niveau'] == niv].sort_values('Date')
        print(f'  [{niv}] ', end='')
        for _, r in sn.iterrows():
            val = r['Value']
            if val > 1000:
                print(f'{int(r["Date"])}:{val/1e9:.2f}Md ', end='')
            else:
                print(f'{int(r["Date"])}:{val:.1f}% ', end='')
        print()

# === 08 - Taux promotion primaire ===
print('\n\n========== 08 - TAUX PROMOTION PRIMAIRE ==========')
df8 = pd.read_csv(os.path.join(data_path, '08-taux-promotion-primaire-region.csv'), encoding='utf-8')
for region in df8['région'].unique():
    vals = df8[(df8['région']==region) & (df8['sexe']=='Total')].sort_values('Date')
    if len(vals) > 0:
        print(f'  {region}: min={vals["Value"].min():.1f}%, max={vals["Value"].max():.1f}%, dernier={vals["Value"].iloc[-1]:.1f}% ({int(vals["Date"].iloc[-1])})')

# === 09 - BEPC ===
print('\n\n========== 09 - ADMISSION BEPC ==========')
df9 = pd.read_csv(os.path.join(data_path, '09-admission-bepc-region-sexe.csv'), encoding='utf-8')
for region in df9['région'].unique():
    vals = df9[(df9['région']==region) & (df9['sexe']=='Total')].sort_values('Date')
    if len(vals) > 0:
        print(f'  {region}: min={vals["Value"].min():.1f}%, max={vals["Value"].max():.1f}%, dernier={vals["Value"].iloc[-1]:.1f}% ({int(vals["Date"].iloc[-1])})')

# === 10 - Transition ===
print('\n\n========== 10 - TRANSITION PRIMAIRE/SECONDAIRE ==========')
df10 = pd.read_csv(os.path.join(data_path, '10-transition-primaire-secondaire.csv'), encoding='utf-8')
for region in df10['région'].unique():
    vals = df10[(df10['région']==region) & (df10['sexe']=='Total')].sort_values('Date')
    if len(vals) > 0:
        print(f'  {region}: min={vals["Value"].min():.1f}%, max={vals["Value"].max():.1f}%, dernier={vals["Value"].iloc[-1]:.1f}% ({int(vals["Date"].iloc[-1])})')

# === 12 - Secondaire ===
print('\n\n========== 12 - SECONDAIRE 2015 ==========')
df12 = pd.read_csv(os.path.join(data_path, '12-statistiques-secondaire.csv'), encoding='utf-8')
for reg in df12['region'].unique():
    for ind in df12['indicateur'].unique():
        sub = df12[(df12['region']==reg) & (df12['indicateur']==ind) & (df12['secteur']=='Collège') & (df12['sexe']=='Total')]
        if len(sub) > 0 and ind != 'Nombre de salles de classe':
            print(f'  {reg} - {ind}: {int(sub["Value"].values[0])}')

# === 13 - Préscolaire ===
print('\n\n========== 13 - PRÉSCOLAIRE ==========')
df13 = pd.read_csv(os.path.join(data_path, '13-enseignants-prescolaire-inspection.csv'), encoding='utf-8')
total = df13[(df13['sexe']=='Total')]['Value'].sum()
femmes = df13[(df13['sexe']=='Féminin')]['Value'].sum()
hommes = df13[(df13['sexe']=='Masculin')]['Value'].sum()
print(f'  Total enseignants préscolaire: {total}')
print(f'  Femmes: {femmes} ({femmes/total*100:.1f}%)')
print(f'  Hommes: {hommes} ({hommes/total*100:.1f}%)')
top5 = df13[df13['sexe']=='Total'].sort_values('Value', ascending=False).head(5)
print('  Top 5 inspections:')
for _, r in top5.iterrows():
    print(f'    {r["inspections"]}: {int(r["Value"])}')

# === 14 - COSO ===
print('\n\n========== 14 - COSO PROJETS ==========')
df14 = pd.read_csv(os.path.join(data_path, '14-projet-coso-education.csv'), encoding='utf-8')
print(f'  Types: {df14["type"].value_counts().to_dict()}')
print(f'  Statuts: {df14["status"].value_counts(dropna=False).to_dict()}')
print(f'  Avancement moyen: {df14["progress_percent"].dropna().mean():.1f}%')
print(f'  Salles de classe: total={df14["number_of_classrooms"].sum()}, mean={df14["number_of_classrooms"].mean():.1f}')
print(f'  Blocs latrines: total={df14["number_of_latrine_blocks"].sum()}')
print(f'  Coût estimé total: {df14["estimated_cost"].dropna().sum()/1e9:.2f} milliards')

# === 16 - BM indicateurs éducation ===
print('\n\n========== 16 - BM INDICATEURS ÉDUCATION ==========')
df16 = pd.read_csv(os.path.join(data_path, '16-education-togo-banque-mondiale.csv'), encoding='utf-8')
edu_indicators = [c for c in df16['Indicator Name'].unique() if any(k in str(c).lower() for k in ['school', 'education', 'literacy', 'enrol', 'primary', 'secondary', 'teacher', 'pupil', 'student'])]
print(f'  Indicateurs éducation: {len(edu_indicators)}')
for ind in sorted(edu_indicators)[:20]:
    sub = df16[df16['Indicator Name'] == ind].dropna(subset=['Value']).sort_values('Year')
    if len(sub) > 0:
        print(f'    {ind}: dernier={sub["Value"].iloc[-1]:.2f} ({int(sub["Year"].iloc[-1])})')

# === Cartographie régions ===
print('\n\n========== STANDARDISATION NOMS RÉGIONS ==========')
regions_01 = set(df6['region_nom_bdd'].unique()) if 'region_nom_bdd' in df6.columns else set()
for fn, name in [('01', 'Établissements'), ('02', 'Toilettes'), ('03', 'Bâtiments')]:
    df = pd.read_csv(os.path.join(data_path, f'{fn}-*.csv'), encoding='utf-8', nrows=0)
    
# Check regions in file 01 properly
df1 = pd.read_csv(os.path.join(data_path, '01-etablissements-scolaires.csv'), encoding='utf-8', low_memory=False)
print(f'  Regions (Établissements): {df1["region_nom_bdd"].value_counts().to_dict()}')
print(f'  Préfectures (Établissements): {sorted(df1["prefecture_nom_bdd"].unique())}')
