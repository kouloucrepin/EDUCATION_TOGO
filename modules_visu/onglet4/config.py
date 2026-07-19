import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

FICHIERS = {
    'bepc': '09-admission-bepc-region-sexe.csv',
    'prescolaire': '13-enseignants-prescolaire-inspection.csv',
}

REGIONS_09 = ['Togo', 'Lom\u00e9-Golfe', 'Maritime', 'Plateaux',
              'Plateaux Ouest', 'Plateaux Est',
              'Centrale', 'Kara', 'Savanes']

REGIONS_09_SIMPLE = ['Togo', 'Lom\u00e9-Golfe', 'Maritime', 'Centrale', 'Kara', 'Savanes']

TOGO_GEOJSON = os.path.join(DATA_PATH, '..', 'data_togo', 'togo_regions.geojson')

COULEURS_SEXE = {
    'Total': '#006A4E',
    'F\u00e9minin': '#e91e63',
    'Masculin': '#1976d2',
}

INSPECTIONS_REGIONS = {
    'T.R.Grand Lom\u00e9': 'Grand Lom\u00e9',
    'T.R.Maritime': 'Maritime',
    'T.R.Plateaux Est': 'Plateaux Est',
    'T.R.Plateaux Ouest': 'Plateaux Ouest',
    'T.R.Centrale': 'Centrale',
    'T.R.Kara': 'Kara',
    'T.R. Savanes': 'Savanes',
}
