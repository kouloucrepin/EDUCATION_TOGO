"""
data-pipeline.py
Pipeline de données : lit les CSVs → calcule les métriques → exporte data.json
Usage : python data-pipeline.py
"""

import pandas as pd
import numpy as np
import json, os, warnings
warnings.filterwarnings('ignore')

DATA = r'C:\Users\Ultra Tech\Desktop\SOLUTION1\Competition 3\data'
OUT = r'C:\Users\Ultra Tech\Desktop\SOLUTION1\Competition 3\dashboard-data.json'

def load_csv(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        print(f'  [MANQUANT] {name}')
        return None
    return pd.read_csv(path, encoding='utf-8', low_memory=False)

print('='*60)
print('PIPELINE DE DONNÉES — ÉDUCATION TOGO')
print('='*60)

# ===== 1. CHARGEMENT =====
print('\n--- Chargement des fichiers ---')

df1 = load_csv('01-etablissements-scolaires.csv')
df2 = load_csv('02-toilettes-scolaires.csv')
df3 = load_csv('03-batiments-electrification.csv')
df4 = load_csv('04-bibliotheques.csv')
df6 = load_csv('06-education-resultats-scolaires.csv')
df8 = load_csv('08-taux-promotion-primaire-region.csv')
df9 = load_csv('09-admission-bepc-region-sexe.csv')
df10 = load_csv('10-transition-primaire-secondaire.csv')
df12 = load_csv('12-statistiques-secondaire.csv')
df13 = load_csv('13-enseignants-prescolaire-inspection.csv')
df14 = load_csv('14-projet-coso-education.csv')
df16 = load_csv('16-education-togo-banque-mondiale.csv')

# ===== 2. MÉTRIQUES CLÉS =====
print('\n--- Calcul des indicateurs ---')

dashboard = {}

# --- KPI onglet 1 ---
if df6 is not None:
    def get_val(ind, niv='Total', annee=2022, secteur='Total'):
        q = df6[(df6['indicateurs']==ind) & (df6['Date']==annee)]
        if niv != 'Tous':
            q = q[q['niveau']==niv]
        if secteur != 'Tous':
            q = q[q['secteur']==secteur]
        return float(q['Value'].iloc[0]) if len(q) > 0 else None

    dashboard['kpi'] = {
        'achevement_primaire': get_val("Taux d'achèvement ou de diplomation", 'Primaire', 2022),
        'achevement_college': get_val("Taux d'achèvement ou de diplomation", 'Collège', 2022),
        'achevement_lycee': get_val("Taux d'achèvement ou de diplomation", 'Lycée', 2022),
        'scolarisation_prescolaire': get_val('Taux de scolarisation', "Jardins d'enfants", 2022),
        'depenses': get_val("Dépenses annuelles d'éducation", 'Total', 2022),
        'part_budget': get_val("Part du Budget alloué à l'éducation (%)", 'Total', 2022),
    }
    print(f'  KPI : {dashboard["kpi"]}')

    # Séries temporelles achèvement
    series = {}
    for niv in ['Primaire', 'Collège', 'Lycée']:
        sub = df6[(df6['indicateurs']=="Taux d'achèvement ou de diplomation") & (df6['niveau']==niv) & (df6['secteur']=='Total')]
        series[niv] = {int(r['Date']): float(r['Value']) for _, r in sub.iterrows()}
    dashboard['achevement_series'] = series
    print(f'  Séries achèvement : {len(series)} niveaux')

    # Budget vs résultats (scatter)
    scatter = []
    sub = df6[(df6['indicateurs']=="Part du Budget alloué à l'éducation (%)") & (df6['niveau']=='Total')]
    ach = df6[(df6['indicateurs']=="Taux d'achèvement ou de diplomation") & (df6['niveau']=='Collège') & (df6['secteur']=='Total')]
    merged = sub.merge(ach, on='Date', suffixes=('_budget', '_ach'))
    for _, r in merged.iterrows():
        scatter.append({'x': round(float(r['Value_budget']),1), 'y': round(float(r['Value_ach']),1), 'year': int(r['Date'])})
    dashboard['scatter_budget'] = scatter
    print(f'  Scatter budget/achèvement : {len(scatter)} points')

    # Indicateurs détaillés (tableau)
    tableau = []
    for ind in [("Taux d'achèvement ou de diplomation", 'Primaire'),
                 ("Taux d'achèvement ou de diplomation", 'Collège'),
                 ("Taux d'achèvement ou de diplomation", 'Lycée'),
                 ('Taux de scolarisation', "Jardins d'enfants"),
                 ('Taux de scolarisation', 'Collège'),
                 ('Taux de scolarisation', 'Lycée'),
                 ("Part du Budget alloué à l'éducation (%)", 'Total'),
                 ("Dépenses annuelles d'éducation", 'Total')]:
        row = {'indicateur': ind[0], 'niveau': ind[1]}
        for an in [2013, 2018, 2022]:
            row[str(an)] = get_val(ind[0], ind[1], an)
        tableau.append(row)
    dashboard['tableau_indicateurs'] = tableau

# --- Taux régionaux (onglet 3) ---
if df8 is not None and df9 is not None and df10 is not None:
    def region_data(df, label, ref_col='région'):
        out = {}
        for reg in df[ref_col].unique():
            sub = df[(df[ref_col]==reg) & (df['sexe']=='Total')].sort_values('Date')
            if len(sub) > 0:
                out[reg] = {
                    'dernier': round(float(sub['Value'].iloc[-1]), 1),
                    'annee': int(sub['Date'].iloc[-1]),
                    'min': round(float(sub['Value'].min()), 1),
                    'max': round(float(sub['Value'].max()), 1),
                    'serie': {int(r['Date']): round(float(r['Value']), 1) for _, r in sub.iterrows()}
                }
        return out

    dashboard['promotion'] = region_data(df8, 'Taux de promotion primaire')
    dashboard['bepc'] = region_data(df9, "Admission au BEPC")
    dashboard['transition'] = region_data(df10, 'Taux de transition primaire/secondaire 1')

    # Heatmap (matrice région × indicateur)
    regions = ['Togo', 'Lomé-Golfe', 'Maritime', 'Plateaux', 'Centrale', 'Kara', 'Savanes']
    heatmap = []
    for reg in regions:
        p = df8[(df8['région']==reg) & (df8['sexe']=='Total') & (df8['Date']==2019)]['Value']
        t = df10[(df10['région']==reg) & (df10['sexe']=='Total') & (df10['Date']==2022)]['Value']
        b = df9[(df9['région']==reg) & (df9['sexe']=='Total') & (df9['Date']==2022)]['Value']
        heatmap.append({
            'region': reg,
            'promotion': round(float(p.iloc[0]),1) if len(p)>0 else None,
            'transition': round(float(t.iloc[0]),1) if len(t)>0 else None,
            'bepc': round(float(b.iloc[0]),1) if len(b)>0 else None,
        })
    dashboard['heatmap'] = heatmap
    print(f'  Heatmap : {len(heatmap)} régions')

# --- Genre (onglet 4) ---
if df9 is not None:
    bepc_fm = {}
    for sex in ['Féminin', 'Masculin']:
        sub = df9[(df9['sexe']==sex) & (df9['région']=='Togo')].sort_values('Date')
        bepc_fm[sex] = {int(r['Date']): round(float(r['Value']),1) for _, r in sub.iterrows()}
    dashboard['bepc_genre'] = bepc_fm
    print(f'  BEPC genre : {len(bepc_fm)} séries')

    # Écart par région
    gap = []
    for reg in df9['région'].unique():
        f = df9[(df9['région']==reg) & (df9['sexe']=='Féminin') & (df9['Date']==2022)]['Value']
        m = df9[(df9['région']==reg) & (df9['sexe']=='Masculin') & (df9['Date']==2022)]['Value']
        if len(f)>0 and len(m)>0:
            gap.append({'region': reg, 'filles': round(float(f.iloc[0]),1), 'garcons': round(float(m.iloc[0]),1)})
    dashboard['ecart_genre'] = gap

if df13 is not None:
    total_ens = int(df13[df13['sexe']=='Total']['Value'].sum())
    femmes = int(df13[df13['sexe']=='Féminin']['Value'].sum())
    hommes = int(df13[df13['sexe']=='Masculin']['Value'].sum())
    dashboard['enseignants_prescolaire'] = {
        'total': total_ens, 'femmes': femmes, 'hommes': hommes,
        'pct_femmes': round(femmes/total_ens*100,1) if total_ens > 0 else 0,
    }
    top = df13[df13['sexe']=='Total'].sort_values('Value', ascending=False).head(10)
    dashboard['top_inspections'] = [{'inspection': r['inspections'], 'count': int(r['Value'])} for _, r in top.iterrows()]
    print(f'  Enseignants préscolaire : {total_ens} total, {dashboard["enseignants_prescolaire"]["pct_femmes"]}% femmes')

# --- COSO (onglet 2) ---
if df14 is not None:
    types = df14['type'].value_counts().to_dict()
    status = df14['status'].value_counts(dropna=False).to_dict()
    dashboard['coso'] = {
        'types': {k: int(v) for k, v in types.items()},
        'status': {str(k) if pd.isna(k) else k: int(v) for k, v in status.items()},
        'total_projets': len(df14),
        'salles_classes': int(df14['number_of_classrooms'].dropna().sum()),
        'latrines': int(df14['number_of_latrine_blocks'].dropna().sum()),
        'cout_total': float(df14['estimated_cost'].dropna().sum()),
        'avancement_moyen': round(float(df14['progress_percent'].dropna().mean()), 1),
    }
    print(f'  COSO : {dashboard["coso"]["total_projets"]} projets, {dashboard["coso"]["avancement_moyen"]}% avancement')

# --- Établissements (onglet 2) ---
if df1 is not None:
    by_region = df1['region_nom_bdd'].value_counts().to_dict()
    dashboard['ecoles'] = {
        'total': len(df1),
        'par_region': {k: int(v) for k, v in by_region.items()},
    }
    if df2 is not None:
        dashboard['ecoles']['toilettes'] = len(df2)
        dashboard['ecoles']['toilettes_par_region'] = {k: int(v) for k, v in df2['region_nom_bdd'].value_counts().to_dict().items()}
    print(f'  Écoles : {dashboard["ecoles"]["total"]} établissements')

# --- Prévisions (onglet 5) ---
if df6 is not None:
    sub = df6[(df6['indicateurs']=="Taux d'achèvement ou de diplomation") & (df6['niveau']=='Collège') & (df6['secteur']=='Total')]
    hist = {int(r['Date']): float(r['Value']) for _, r in sub.iterrows()}
    dernier = list(hist.values())[-1] if hist else 62.7
    dashboard['previsions'] = {
        'historique': hist,
        'tendanciel': {2023: round(dernier + 2, 1), 2025: round(dernier + 5, 1), 2027: round(dernier + 8, 1), 2030: round(dernier + 12, 1)},
        'optimiste': {2023: round(dernier + 3, 1), 2025: round(dernier + 8, 1), 2027: round(dernier + 14, 1), 2030: round(dernier + 20, 1)},
        'pessimiste': {2023: round(dernier + 0.5, 1), 2025: round(dernier + 2, 1), 2027: round(dernier + 3, 1), 2030: round(dernier + 4, 1)},
    }

# ===== 3. EXPORT =====
print('\n--- Export JSON ---')
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(dashboard, f, ensure_ascii=False, indent=2)

taille = os.path.getsize(OUT) / 1024
print(f'  Fichier : {OUT}')
print(f'  Taille : {taille:.1f} Ko')
print(f'  Clés exportées : {list(dashboard.keys())}')
print('\n--- Pipeline termine avec succes ---')
