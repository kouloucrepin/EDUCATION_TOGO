"""Client minimal de l'API Gemini pour les modèles Gemma (REST, sans SDK).

Gemma ne supporte ni le rôle `system` ni le function calling natif :
les instructions système sont préfixées au premier message utilisateur,
et les appels d'outils passent par un protocole JSON (voir agent.py).
"""
import json
import time
import urllib.request
import urllib.error

from . import config


class ErreurLLM(RuntimeError):
    pass


def _appel_http(modele, contents, temperature):
    corps = json.dumps({
        'contents': contents,
        'generationConfig': {
            'temperature': temperature,
            'maxOutputTokens': config.MAX_TOKENS_REPONSE,
        },
    }).encode('utf-8')
    url = config.URL_API.format(modele=modele) + '?key=' + config.GEMMA_API_KEY
    requete = urllib.request.Request(
        url, data=corps, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(requete, timeout=120) as rep:
        donnees = json.loads(rep.read().decode('utf-8'))
    try:
        return donnees['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        raise ErreurLLM(f'Réponse API inattendue : {str(donnees)[:300]}')


def generer(messages, temperature=None):
    """Appelle le modèle principal, puis les replis en cas de 429/5xx.

    messages : liste de {'role': 'user'|'model', 'text': str}
    """
    if not config.GEMMA_API_KEY:
        raise ErreurLLM(
            "GEMMA_API_KEY manquante : ajoutez-la dans le fichier .env du projet "
            "(GEMMA_API_KEY=...) ou dans les variables d'environnement.")

    temperature = config.TEMPERATURE if temperature is None else temperature
    contents = [{'role': m['role'], 'parts': [{'text': m['text']}]} for m in messages]

    derniere_erreur = None
    for modele in [config.MODELE] + config.MODELES_REPLI:
        for tentative in range(3):
            try:
                return _appel_http(modele, contents, temperature)
            except urllib.error.HTTPError as e:
                derniere_erreur = f'{modele} → HTTP {e.code}'
                if e.code in (429, 500, 503):
                    time.sleep(2 * (tentative + 1))
                    continue
                break  # erreur non transitoire : essayer le modèle suivant
            except (urllib.error.URLError, TimeoutError) as e:
                derniere_erreur = f'{modele} → {e}'
                time.sleep(2)
    raise ErreurLLM(f'Tous les modèles ont échoué ({derniere_erreur}).')
