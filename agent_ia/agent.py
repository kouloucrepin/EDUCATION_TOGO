"""Agent IA du Dashboard Éducation Togo.

Pipeline : question → routage (connaissance | bdd | hors_contexte) → réponse.
- connaissance : répond depuis les fichiers md (plateforme, termes clés, sources).
- bdd          : boucle d'outils avec protocole JSON (Gemma n'a pas de
                 function calling natif), catalogue YAML fourni dès le départ.
- hors_contexte: le dit poliment et suggère des questions.
Le tout est plafonné à config.MAX_ITERATIONS appels LLM par question.
"""
import json
import re

from . import config, connaissances, llm, memoire, outils

SUGGESTIONS = [
    "Combien d'écoles compte le Togo et comment se répartissent-elles par région ?",
    "Quel est l'écart filles-garçons au BEPC en 2022 ?",
    "Quelle région a le score composite le plus faible et pourquoi ?",
    "Comment a évolué la part du budget allouée à l'éducation depuis 2013 ?",
    "Que fait le projet COSO et où en sont ses chantiers ?",
    "C'est quoi le taux de transition primaire-secondaire ?",
]

_PROMPT_ROUTEUR = """Tu es le routeur de l'assistant du Dashboard Éducation Togo.
Classe la question de l'utilisateur dans UNE des routes :
- "connaissance" : présentation de la plateforme, définitions des termes clés (BEPC, taux, score composite, COSO...), sources des données, à quoi sert le dashboard.
- "bdd" : effectifs, statistiques, chiffres, distributions, comparaisons, évolutions, classements — tout ce qui demande de calculer sur les données, MÊME si tu doutes que la donnée existe (la route bdd sait expliquer ce qui manque).
- "hors_contexte" : sans rapport avec l'éducation au Togo ou la plateforme.

{memoire}

Question : {question}

Ne montre aucune réflexion. Termine ta réponse par ce JSON (rien après) :
{{"route": "connaissance" | "bdd" | "hors_contexte"}}"""

_PROMPT_CONNAISSANCE = """{regles}

Tu réponds en t'appuyant EXCLUSIVEMENT sur la documentation ci-dessous.

=== DOCUMENTATION ===
{contexte}
=== FIN DOCUMENTATION ===

{memoire}

Question de l'utilisateur : {question}

Consignes de style : réponse professionnelle et claire (5 phrases MINIMUM, JAMAIS plus de
15 lignes — 20 si elle contient un tableau), dans la langue de la question, chiffres de la documentation à l'appui quand
ils existent. Termine TOUJOURS par une question d'ouverture courte qui pousse la curiosité
de l'utilisateur vers une autre facette du dashboard (ex. une vue, un chiffre marquant).

IMPORTANT : ne montre AUCUNE réflexion, note ou brouillon. Ta réponse est UNIQUEMENT ce JSON :
{{"reponse_finale": "<écris ici ta réponse complète et rédigée>"}}"""

_PROMPT_BDD = """{regles}

Tu disposes des DataFrames pandas décrits dans ce catalogue (respecte les pièges !) :

=== CATALOGUE ===
{catalogue}
=== FIN CATALOGUE ===

{memoire}

OUTILS DISPONIBLES — dès ton PREMIER tour et à chaque tour, ta réponse est UNIQUEMENT un JSON, rien d'autre :
1. {{"outil": "get_schema", "arguments": {{"cle": "06"}}}}            → structure réelle d'un df ("cle" facultative)
2. {{"outil": "sample_data", "arguments": {{"cle": "09", "n": 3}}}}   → lignes d'exemple
3. {{"outil": "find_similar_values", "arguments": {{"terme": "lome", "cle": ""}}}} → retrouver l'orthographe exacte d'une valeur
4. {{"outil": "execute_python", "arguments": {{"code": "..."}}}}      → exécuter du pandas
5. {{"outil": "generer_graphique", "arguments": {{"type_graphique": "bar", "categories": ["Kara", "Savanes"], "series": {{"Taux (%)": [80.8, 48.9]}}}}}} → créer un graphique
6. {{"reponse_finale": "<écris ici ta réponse complète et rédigée>"}} → quand tu as le résultat

GRAPHIQUES : si l'utilisateur demande un graphique ou une visualisation, calcule d'abord
les valeurs (execute_python), appelle generer_graphique, puis insère le marqueur
[GRAPHIQUE_n] retourné, seul sur une ligne, dans ta reponse_finale.
CHOISIS LE TYPE ADAPTÉ à la question (ne mets pas "line" par défaut) :
- comparaison entre régions/catégories → "bar"
- évolution dans le temps → "line"
- répartition en parts d'un total → "pie"
- relation/corrélation entre deux mesures → "scatter"
- cascade de déperdition (entonnoir) → "funnel"
- profil multi-indicateurs comparé → "radar" (categories = noms des indicateurs)
- flux entre étapes → "sankey" (PAS de categories/series ; utiliser "liens": [["Primaire", "Collège", 63], ["Collège", "Lycée", 27]])

CONTRAINTES pour execute_python :
- pandas/numpy uniquement (pd, np, dfs déjà disponibles) ; lecture seule ; pas de fichier, réseau ni système.
- NE SOMME JAMAIS des lignes qui contiennent déjà des totaux (dfs['06'] : niveau/secteur=='Total' ;
  dfs['13'] : T.Général/T.R.*) — SÉLECTIONNE la ligne d'agrégat, sinon tu doubles ou triples les chiffres.
- Termine ton code par print(...) ou une variable `resultat` ; affiche des résultats PETITS (agrégats, .head()), jamais un df entier.
- En cas d'erreur, corrige ton code et réessaie.
- Utilise find_similar_values si un filtre ne retourne rien (noms de régions incohérents entre fichiers).

ÉTAPE 0 OBLIGATOIRE — avant d'appeler le moindre outil, vérifie dans le catalogue que les
variables demandées (dimension, année, croisement) existent vraiment dans un df.
SI CE N'EST PAS LE CAS (ex. âge des enseignants, salaire, niveau de diplôme : AUCUN df ne les a),
n'appelle AUCUN outil : donne immédiatement une reponse_finale en 3 temps :
« Pour calculer X, j'aurais besoin de … ; or je dispose seulement de … ; ce calcul est donc impossible. »
puis propose le calcul POSSIBLE le plus proche (ex. pas de distribution par âge, mais par sexe ou par région).

SOIS RAPIDE : le catalogue ci-dessus suffit presque toujours — va DIRECTEMENT à execute_python.
N'appelle get_schema ou sample_data que si le catalogue laisse un vrai doute. Vise 1 à 3 outils maximum.

La reponse_finale : professionnelle, dans la langue de la question, 5 phrases MINIMUM
(développe le chiffre : contexte, comparaison ou tendance) et JAMAIS plus de 15 lignes
(20 lignes autorisées uniquement si elle contient un tableau markdown),
cite l'année et la source en reprenant la DESCRIPTION du catalogue — jamais le numéro ou la clé
du fichier (ex. « source : admission au BEPC par région et sexe », PAS « fichier 09 » ni « dfs['09'] »),
et se termine par une courte question d'ouverture.

Question de l'utilisateur : {question}"""

_MSG_HORS_CONTEXTE = (
    "Je suis l'assistant du Dashboard Éducation Togo : je réponds aux questions sur le "
    "système éducatif togolais (2013-2022), ses données et la plateforme elle-même — "
    "votre question sort de ce cadre. Voici des exemples de ce que vous pouvez me demander :\n"
)


def _limiter_lignes(texte, maxi=None):
    """Garde-fou : 15 lignes non vides maxi — 20 si la réponse contient un tableau."""
    lignes = [l for l in str(texte).splitlines() if l.strip()]
    if maxi is None:
        contient_tableau = sum(1 for l in lignes if l.count('|') >= 2) >= 3
        maxi = 20 if contient_tableau else 15
    if len(lignes) <= maxi:
        return str(texte).strip()
    return '\n'.join(lignes[:maxi]) + ' …'


def _candidats_json(texte):
    """Tous les objets {...} équilibrés du texte (en ignorant les accolades
    à l'intérieur des chaînes JSON)."""
    candidats, pile, debut = [], 0, None
    dans_chaine = echappe = False
    for i, c in enumerate(texte):
        if dans_chaine:
            if echappe:
                echappe = False
            elif c == '\\':
                echappe = True
            elif c == '"':
                dans_chaine = False
            continue
        if c == '"':
            dans_chaine = True
        elif c == '{':
            if pile == 0:
                debut = i
            pile += 1
        elif c == '}' and pile > 0:
            pile -= 1
            if pile == 0:
                candidats.append(texte[debut:i + 1])
    return candidats


def _extraire_json(texte):
    """Dernier objet JSON exploitable de la réponse : Gemma raisonne parfois
    à voix haute avant de conclure — la vraie décision est en fin de texte."""
    for c in reversed(_candidats_json(texte)):
        try:
            obj = json.loads(c)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and ({'route', 'outil', 'reponse_finale'} & set(obj)):
            return obj
    return None


class AgentEducation:
    def __init__(self):
        self.memoire = memoire.Memoire()
        self.trace = []

    # -- utilitaires internes ------------------------------------------------
    def _llm(self, prompt, etape):
        prompt = prompt[:config.MAX_CHARS_PROMPT]
        reponse = llm.generer([{'role': 'user', 'text': prompt}])
        self.trace.append({'etape': etape, 'reponse_modele': reponse[:500]})
        return reponse

    # -- routage ---------------------------------------------------------------
    def router(self, question):
        prompt = _PROMPT_ROUTEUR.format(question=question, memoire=self.memoire.texte())
        obj = _extraire_json(self._llm(prompt, 'routage')) or {}
        route = obj.get('route', '')
        if route not in ('connaissance', 'bdd', 'hors_contexte'):
            # repli heuristique si le JSON est illisible
            mots_bdd = ('combien', 'taux', 'nombre', 'évolution', 'evolution',
                        'classement', 'comparer', 'moyenne', 'stat', '%',
                        'distribution', 'répartition', 'repartition', 'effectif',
                        'écart', 'ecart', 'part ')
            route = 'bdd' if any(m in question.lower() for m in mots_bdd) else 'connaissance'
        return route

    # -- routes ------------------------------------------------------------------
    def _repondre_connaissance(self, question):
        prompt = _PROMPT_CONNAISSANCE.format(
            regles=connaissances.regles(),
            contexte=connaissances.contexte_connaissance(),
            memoire=self.memoire.texte(),
            question=question)
        # Le JSON force le modèle à ne livrer QUE la réponse (pas son brouillon)
        for _ in range(3):
            brut = self._llm(prompt, 'connaissance')
            obj = _extraire_json(brut)
            finale = str((obj or {}).get('reponse_finale', '')).strip()
            if len(finale) >= 25 and not finale.startswith('<'):
                return _limiter_lignes(finale)
            prompt += ('\n\nRAPPEL : réponds uniquement avec le JSON '
                       '{"reponse_finale": "<ta vraie réponse rédigée>"}.')
        # dernier recours : le dernier paragraphe du texte brut, borné à 15 lignes
        paragraphes = [p for p in brut.split('\n\n') if p.strip()]
        return _limiter_lignes(paragraphes[-1] if paragraphes else brut)

    def _repondre_bdd(self, question, iterations_restantes):
        base = _PROMPT_BDD.format(
            regles=connaissances.regles(),
            catalogue=connaissances.schemas(),
            memoire=self.memoire.texte(),
            question=question)
        conversation = base
        for tour in range(iterations_restantes):
            # À mi-parcours, pousser le modèle à conclure plutôt qu'à s'acharner
            if tour == max(3, iterations_restantes // 3):
                conversation += ('\n\nATTENTION : tu tournes en rond. Si le calcul est '
                                 'impossible avec les df disponibles, donne MAINTENANT la '
                                 'reponse_finale en 3 temps (besoin de / or je dispose de / '
                                 'donc impossible) avec une alternative possible.')
            obj = _extraire_json(self._llm(conversation, 'bdd'))
            if obj is None:
                conversation += '\n\nRAPPEL : réponds uniquement avec un JSON valide (outil ou reponse_finale).'
                continue
            if 'reponse_finale' in obj:
                finale = str(obj['reponse_finale']).strip()
                # Rejeter les gabarits recopiés ("...", "<écris ici...>", vide)
                if len(finale) < 25 or finale.startswith('<'):
                    conversation += ('\n\nERREUR : ta reponse_finale est vide ou est un '
                                     'gabarit. Rédige la VRAIE réponse complète pour '
                                     "l'utilisateur dans le champ reponse_finale.")
                    continue
                return _limiter_lignes(finale)
            nom = obj.get('outil', '')
            if nom not in outils.OUTILS:
                conversation += f'\n\nERREUR : outil inconnu {nom!r}. Outils valides : {sorted(outils.OUTILS)}.'
                continue
            arguments = obj.get('arguments', {}) or {}
            try:
                resultat = outils.OUTILS[nom](**arguments)
            except TypeError as e:
                resultat = f'ERREUR arguments : {e}'
            except KeyError as e:
                resultat = f'ERREUR : {e}'
            self.trace.append({'etape': f'outil:{nom}', 'arguments': arguments,
                               'resultat': str(resultat)[:500]})
            conversation += (f'\n\n[Résultat de {nom}]\n{resultat}\n\n'
                             'Continue : nouvel outil ou {"reponse_finale": "..."}.')
        return ("Je n'ai pas réussi à aboutir dans le nombre d'itérations imparti. "
                "Pouvez-vous reformuler ou préciser votre question (année, région, indicateur) ?")

    def _hors_contexte(self):
        exemples = '\n'.join(f'• {s}' for s in SUGGESTIONS[:4])
        return _MSG_HORS_CONTEXTE + exemples

    # -- point d'entrée -------------------------------------------------------
    def repondre(self, question):
        """Répond à une question.

        Retourne {'route', 'reponse', 'graphiques', 'iterations', 'trace'} —
        'graphiques' associe chaque marqueur [GRAPHIQUE_n] présent dans la
        réponse à son fragment HTML ECharts (à injecter au rendu)."""
        self.trace = []
        outils.consommer_graphiques()          # purge d'éventuels restes du thread
        question = str(question).strip()
        route = self.router(question)
        if route == 'hors_contexte':
            reponse = self._hors_contexte()
        elif route == 'connaissance':
            reponse = self._repondre_connaissance(question)
        else:
            reponse = self._repondre_bdd(question, config.MAX_ITERATIONS - 1)
        self.memoire.ajouter(question, reponse)
        return {'route': route, 'reponse': reponse,
                'graphiques': outils.consommer_graphiques(),
                'iterations': len([t for t in self.trace if 'reponse_modele' in t]),
                'trace': list(self.trace)}
