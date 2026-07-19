"""Configuration de l'agent IA du Dashboard Éducation Togo."""
import os

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_CONNAISSANCE = os.path.join(RACINE, 'connaissance_ia')
DOSSIER_DATA = os.path.join(RACINE, 'data')


def _charger_env():
    """Charge le fichier .env du projet si les variables ne sont pas déjà posées."""
    chemin = os.path.join(RACINE, '.env')
    if not os.path.exists(chemin):
        return
    # utf-8-sig : tolère le BOM que certains éditeurs Windows ajoutent en tête
    with open(chemin, encoding='utf-8-sig') as f:
        for ligne in f:
            ligne = ligne.strip().lstrip('﻿')
            if not ligne or ligne.startswith('#') or '=' not in ligne:
                continue
            cle, _, valeur = ligne.partition('=')
            os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))


_charger_env()

# --- Modèle (API Gemini, offre gratuite) -----------------------------------
GEMMA_API_KEY = os.environ.get('GEMMA_API_KEY', '')
# Principal : flash-lite (mesuré ~3-4 s par question contre 90-160 s pour
# Gemma 4 26B, JSON fiable du premier coup).
# Replis ordonnés du plus rapide au plus lent — tous gratuits et vérifiés
# accessibles avec la clé : 2.5 Flash (rapide, plus gros), 3 Flash preview
# (rapide mais preview), puis Gemma 4 26B (le plus lent, gros quota journalier).
# Le tout surchargeable via le .env (GEMMA_MODEL / GEMMA_FALLBACK_MODELS).
MODELE = os.environ.get('GEMMA_MODEL', 'models/gemini-flash-lite-latest')
MODELES_REPLI = [m.strip() for m in os.environ.get(
    'GEMMA_FALLBACK_MODELS',
    'models/gemini-2.5-flash,models/gemini-3-flash-preview,models/gemma-4-26b-a4b-it'
).split(',') if m.strip()]
URL_API = 'https://generativelanguage.googleapis.com/v1beta/{modele}:generateContent'

# --- Limites (fenêtre de contexte réduite de Gemma : on reste frugal) ------
MAX_ITERATIONS = 20          # itérations internes maxi (routage + réflexions + outils)
MAX_SORTIE_OUTIL = 3500      # caractères max renvoyés au modèle par un outil
MAX_CHARS_PROMPT = 22000     # garde-fou global sur la taille d'un prompt assemblé
MAX_TOKENS_REPONSE = 1024
TIMEOUT_EXEC = 8             # secondes max pour un code pandas généré
TAILLE_MEMOIRE = 3           # nombre d'échanges gardés en mémoire
TEMPERATURE = 0.2

# --- Fichiers CSV exposés au sandbox (clés = celles du catalogue YAML) ------
FICHIERS_DFS = {
    '01': '01-etablissements-scolaires.csv',
    '02': '02-toilettes-scolaires.csv',
    '03': '03-batiments-electrification.csv',
    '04': '04-bibliotheques.csv',
    '06': '06-education-resultats-scolaires.csv',
    '07': '07-sdg4-data-togo.csv',
    '08': '08-taux-promotion-primaire-region.csv',
    '09': '09-admission-bepc-region-sexe.csv',
    '10': '10-transition-primaire-secondaire.csv',
    '12': '12-statistiques-secondaire.csv',
    '13': '13-enseignants-prescolaire-inspection.csv',
    '14': '14-projet-coso-education.csv',
    '16': '16-education-togo-banque-mondiale.csv',
}
