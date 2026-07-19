import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

FICHIERS = {
    'promotion': '08-taux-promotion-primaire-region.csv',
    'bepc': '09-admission-bepc-region-sexe.csv',
    'transition': '10-transition-primaire-secondaire.csv',
    'statistiques': '12-statistiques-secondaire.csv',
    'resultats': '06-education-resultats-scolaires.csv',
}

REGIONS = ['Togo', 'Lomé-Golfe', 'Maritime', 'Plateaux', 'Centrale', 'Kara', 'Savanes']

REGION_08_MAP = {
    'TOGO': 'Togo', 'Lomé-Golfe': 'Lomé-Golfe',
    'Maritime': 'Maritime', 'Plateaux': 'Plateaux',
    'Centrale': 'Centrale', 'Kara': 'Kara', 'Savanes': 'Savanes',
}

COULEURS_REGIONS = {
    'Togo': '#006A4E', 'Lomé-Golfe': '#00A86B',
    'Maritime': '#006A4E', 'Plateaux': '#FFCE00',
    'Centrale': '#EF3340', 'Kara': '#0033A0', 'Savanes': '#D4A017',
}

# Palette distincte par région pour les graphiques multi-séries
# (la charte ci-dessus partage le même vert entre Togo et Maritime)
COULEURS_REGIONS_DISTINCTES = {
    'Togo': '#006A4E',
    'Lomé-Golfe': '#00A86B',
    'Maritime': '#3182CE',
    'Plateaux': '#D4A017',
    'Centrale': '#EF3340',
    'Kara': '#0033A0',
    'Savanes': '#805AD5',
}

INDICATEURS_HEATMAP = [
    'Promotion primaire\n(2019)',
    'Transition P→S\n(2022)',
    'Admission BEPC\n(2022)',
    'Scolarisation\ncollège (2022)',
    'Achèvement\ncollège (2022)',
]
