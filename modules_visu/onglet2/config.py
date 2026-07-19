import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

FICHIERS = {
    'etablissements': '01-etablissements-scolaires.csv',
    'toilettes': '02-toilettes-scolaires.csv',
    'batiments': '03-batiments-electrification.csv',
    'bibliotheques': '04-bibliotheques.csv',
    'coso': '14-projet-coso-education.csv',
}

COULEURS_CATEGORIE = {
    'Ecole primaire': '#22c55e',
    'College': '#f59e0b',
    'Lycée': '#ef4444',
    'Jardin (maternelle)': '#3b82f6',
}

COULEURS_TOILETTE = {
    'Latrines a eau': '#2563eb',
    'Latrines seches': '#92400e',
    'Pissotieres': '#a3e635',
    'Mixte': '#06b6d4',
}

COULEURS_COSO_STATUS = {
    'Réception provisoire': '#eab308',
    'Réception définitive': '#22c55e',
    'Remise communauté': '#3b82f6',
    'Contrat signé': '#8b5cf6',
    'Technique': '#f97316',
    'Achevé': '#06b6d4',
}

COULEURS_COSO_TYPE = {
    'Bâtiments scolaires au primaire': '#22c55e',
    'Latrines': '#92400e',
    'Clôture': '#f59e0b',
    'Préscolaire': '#3b82f6',
    'Bâtiments scolaires au premier cycle du secondaire (CEG)': '#f97316',
    'Lycée': '#ef4444',
    'Bibliothèque': '#8b5cf6',
}

CARTE_CENTRE = [8.6, 0.8]
CARTE_ZOOM = 8
