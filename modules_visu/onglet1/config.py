import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

FICHIERS = {
    'resultats': '06-education-resultats-scolaires.csv',
    'sdg4': '07-sdg4-data-togo.csv',
    'bm': '16-education-togo-banque-mondiale.csv',
}

COULEURS = {
    'Togo': '#006A4E',
    'Maritime': '#006A4E',
    'Plateaux': '#FFCE00',
    'Centrale': '#EF3340',
    'Kara': '#0033A0',
    'Savanes': '#D4A017',
    'Lomé-Golfe': '#00A86B',
    'Primaire': '#22c55e',
    'Collège': '#f59e0b',
    'Lycée': '#ef4444',
    'Préscolaire': '#3b82f6',
    'Total': '#6b7280',
    'vert': '#22c55e',
    'orange': '#f59e0b',
    'rouge': '#ef4444',
    'bleu': '#3b82f6',
}

NIVEAUX_MAP = {
    'Jardins d\'enfants': 'Préscolaire',
    'Primaire': 'Primaire',
    'Collège': 'Collège',
    'Lycée': 'Lycée',
    'Total': 'Total',
}

KPI_CONFIG = [
    {
        'id': 'achèvement_primaire',
        'label': 'Achèvement Primaire',
        'indicator': "Taux d'achèvement ou de diplomation",
        'niveau': 'Primaire',
        'max': 100,
        'unite': '%',
        'couleur': '#22c55e',
    },
    {
        'id': 'achèvement_collège',
        'label': 'Achèvement Collège',
        'indicator': "Taux d'achèvement ou de diplomation",
        'niveau': 'Collège',
        'max': 100,
        'unite': '%',
        'couleur': '#f59e0b',
    },
    {
        'id': 'achèvement_lycée',
        'label': 'Achèvement Lycée',
        'indicator': "Taux d'achèvement ou de diplomation",
        'niveau': 'Lycée',
        'max': 100,
        'unite': '%',
        'couleur': '#ef4444',
    },
    {
        'id': 'scolarisation_préscolaire',
        'label': 'Scolarisation Préscolaire',
        'indicator': 'Taux de scolarisation',
        'niveau': "Jardins d'enfants",
        'max': 100,
        'unite': '%',
        'couleur': '#3b82f6',
    },
    {
        'id': 'dépenses_éducation',
        'label': 'Dépenses Annuelles Éducation',
        'indicator': "Dépenses annuelles d'éducation",
        'niveau': 'Total',
        'max': None,
        'unite': 'Md FCFA',
        'couleur': '#8b5cf6',
    },
    {
        'id': 'part_budget',
        'label': 'Part du Budget Éducation',
        'indicator': "Part du Budget alloué à l'éducation (%)",
        'niveau': 'Total',
        'max': 25,
        'unite': '%',
        'couleur': '#ef4444',
    },
]
