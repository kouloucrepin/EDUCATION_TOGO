import pandas as pd

df = pd.read_csv(
    r'C:\Users\Ultra Tech\Desktop\SOLUTION1\Competition 3\data\06-education-resultats-scolaires.csv'
)

indics = [
    "Taux d'ach\u00e8vement ou de diplomation",
    "Taux de scolarisation",
    "D\u00e9penses annuelles d'\u00e9ducation",
    "Part du Budget allou\u00e9 \u00e0 l'\u00e9ducation (%)",
]

print("=== VALEURS 2022 (source: 06-education-resultats-scolaires.csv) ===\n")

for ind in indics:
    sub = df[(df['indicateurs'] == ind) & (df['Date'] == 2022) & (df['secteur'] == 'Total')]
    if sub.empty:
        print(f"{ind}: AUCUNE DONNEE pour 2022")
        continue
    for _, r in sub.iterrows():
        val = r['Value']
        niv = r['niveau']
        if val >= 1e9:
            val_str = f"{val/1e9:.1f} Md FCFA"
        else:
            val_str = f"{val}%"
        print(f"  {ind:45s} | {niv:20s} | {val_str}")
    print()
