# Conception de l'agent IA — Dashboard Éducation Togo

Ce document explique comment l'assistant IA du dashboard (package `agent_ia/`,
~830 lignes de Python) a été conçu, comment il raisonne, et pourquoi nous avons
délibérément choisi de **ne pas** utiliser LangChain ni LangGraph.

---

## 1. Vue d'ensemble

L'agent répond à des questions en langage naturel (français ou anglais) sur le
système éducatif togolais 2013-2022. Il s'appuie sur deux sources de vérité :

- **13 fichiers CSV ouverts** (`data/`) chargés en DataFrames pandas — pour
  tout ce qui est chiffres, statistiques, comparaisons, évolutions ;
- **5 fichiers de connaissance** (`connaissance_ia/`) rédigés à la main —
  catalogue des schémas (YAML), présentation de la plateforme, termes clés,
  sources, règles de rédaction.

Le modèle utilisé est **Gemini Flash Lite** (API Gemini, offre gratuite), avec
une cascade de replis vers Gemini 2.5 Flash, Gemini 3 Flash preview puis
Gemma 4 26B en cas de quota épuisé ou d'erreur serveur.

## 2. Le pipeline : router → répondre

Chaque question suit un chemin en deux temps, plafonné à
`MAX_ITERATIONS = 20` appels LLM :

```
                                 ┌────────────────────────────────────────────┐
 question ──► ROUTEUR (1 appel)──┤ "connaissance"  → RAG sur les fichiers md  │
              classe la question │ "bdd"           → boucle d'outils pandas   │
              en 3 routes        │ "hors_contexte" → réponse polie + exemples │
                                 └────────────────────────────────────────────┘
```

### Route `connaissance` (questions sur la plateforme, définitions, sources)

Un seul appel LLM : le prompt embarque l'intégralité de la documentation
(`CATALOGUE_PLATFORME.md` + `CATALOGUE_TERMES_CLES.md` + `CATALOGUE_SOURCES.md`)
et impose de répondre **exclusivement** depuis celle-ci. C'est du RAG sans base
vectorielle : le corpus tient entièrement dans la fenêtre de contexte, donc
l'indexation/embedding n'apporterait que de la complexité et un risque de
rappel partiel.

### Route `bdd` (chiffres, calculs, classements, graphiques)

C'est le cœur agentique : une **boucle d'outils** où le modèle décide à chaque
tour soit d'appeler un outil, soit de livrer sa `reponse_finale`. Le prompt
initial contient le catalogue YAML des 13 DataFrames (colonnes, types, pièges
connus — lignes de totaux à ne pas sommer, orthographes de régions
incohérentes entre fichiers…).

Cinq outils sont exposés :

| Outil | Rôle |
|---|---|
| `execute_python` | exécute du pandas généré par le modèle dans un sandbox |
| `get_schema` | catalogue YAML complet, ou structure réelle d'un DataFrame |
| `sample_data` | quelques lignes d'exemple d'un DataFrame |
| `find_similar_values` | recherche floue (accents/casse/difflib) d'une valeur |
| `generer_graphique` | crée un graphique ECharts (bar, line, pie, scatter, funnel, radar, sankey) |

Le prompt impose une **étape 0** : vérifier dans le catalogue que les variables
demandées existent vraiment avant d'appeler le moindre outil. Si la donnée
n'existe pas (âge des enseignants, salaires…), le modèle doit répondre
immédiatement en trois temps — « j'aurais besoin de… / or je dispose de… /
donc impossible » — puis proposer le calcul possible le plus proche.

### Route `hors_contexte`

Aucun appel LLM supplémentaire : message fixe qui recadre le périmètre de
l'assistant et propose des exemples de questions (liste `SUGGESTIONS`).

## 3. Le « function calling » maison : un protocole JSON

Gemma ne supporte **ni le rôle `system`, ni le function calling natif**. Les
appels d'outils passent donc par un protocole texte : à chaque tour, le modèle
doit répondre *uniquement* par un objet JSON —
`{"outil": "...", "arguments": {...}}` ou `{"reponse_finale": "..."}` — et le
résultat de l'outil est réinjecté dans la conversation au tour suivant.

L'extraction est volontairement défensive (`_extraire_json`) : on scanne le
texte pour tous les objets `{...}` équilibrés (en ignorant les accolades dans
les chaînes) et on garde le **dernier** JSON exploitable, car ces modèles
« raisonnent à voix haute » avant de conclure — la vraie décision est en fin
de texte.

## 4. Le sandbox `execute_python`

C'est le point le plus sensible : on exécute du code généré par un LLM. Le
sandbox (dans `outils.py`) applique une défense en profondeur :

- **builtins filtrés** : liste blanche d'une quarantaine de fonctions sûres
  (`open`, `eval`, `exec`, `getattr`… sont absents) ;
- **imports en liste blanche** : `pandas`, `numpy`, `math`, `re`, `datetime`,
  `json`, `statistics`, `collections`, `unicodedata` — rien d'autre ;
- **copies paresseuses des DataFrames** : le code reçoit `dfs['06']`… en copie
  (les originaux sont inaltérables), et seuls les df réellement accédés sont
  copiés (gain RAM/temps) ;
- **timeout** de 8 s dans un thread séparé ;
- **sortie tronquée** à 3 500 caractères avant d'être renvoyée au modèle
  (protection de la fenêtre de contexte) ;
- les erreurs Python sont **renvoyées au modèle**, qui corrige son code et
  réessaie — c'est la boucle d'auto-réparation.

## 5. Les graphiques : le HTML ne transite jamais par le modèle

Quand le modèle appelle `generer_graphique`, le fragment ECharts (plusieurs Ko
de HTML/JS) est stocké dans un magasin par thread ; l'outil ne renvoie au
modèle qu'un **marqueur** `[GRAPHIQUE_n]` à placer dans sa réponse. Au rendu,
le serveur Flask remplace le marqueur par le fragment. On économise ainsi des
milliers de tokens et on élimine tout risque que le modèle « abîme » le HTML.

## 6. Robustesse : les garde-fous

| Garde-fou | Où | Pourquoi |
|---|---|---|
| Cascade multi-modèles avec retries (429/5xx, backoff) | `llm.py` | offre gratuite = quotas serrés |
| Relances correctives ciblées (JSON invalide, gabarit recopié, outil inconnu) | `agent.py` | on redemande en expliquant l'erreur plutôt que d'échouer |
| Message anti-enlisement à mi-parcours (« tu tournes en rond, conclus ») | `_repondre_bdd` | éviter de brûler les 20 itérations |
| Longueur de réponse bornée (15 lignes, 20 avec tableau) | `_limiter_lignes` | lisibilité dans la bulle de chat |
| Prompt plafonné à 22 000 caractères | `_llm` | petite fenêtre de contexte |
| Routage de secours par mots-clés si le JSON du routeur est illisible | `router` | jamais d'échec silencieux |
| Mémoire courte (3 derniers échanges, résumés à 300 caractères) | `memoire.py` | questions de suivi sans exploser le prompt |
| Trace complète de chaque étape (`self.trace`) | `agent.py` | débogage et démonstration |
| Un agent par session navigateur, éviction au-delà de 30 | `app.py` | isolation des conversations |

## 7. Pourquoi ni LangChain ni LangGraph ?

Le choix a été **évalué puis écarté**, pour des raisons techniques précises —
pas par ignorance des frameworks.

### 7.1 Leur cœur de valeur ne fonctionne pas avec notre modèle

L'essentiel de la valeur de LangChain pour un agent (`bind_tools`,
`create_tool_calling_agent`, les `ToolNode` de LangGraph) repose sur le
**function calling natif** de l'API sous-jacente. Gemma n'en a pas, ni de rôle
`system`. Il aurait donc fallu écrire *quand même* notre protocole JSON, notre
extracteur défensif et nos relances correctives — puis les faire cohabiter
avec les abstractions du framework au lieu de les brancher directement. Le
framework ne remplaçait aucune des ~300 lignes difficiles ; il n'aurait fait
qu'ajouter une couche autour.

### 7.2 Le graphe est trivial — LangGraph résout un problème qu'on n'a pas

Notre topologie complète : **1 routeur → 3 branches, dont 1 boucle bornée**.
Elle s'exprime en un `if/elif/else` et une boucle `for` de 40 lignes,
lisibles d'un trait. LangGraph apporte sa vraie valeur sur les checkpoints,
la reprise d'état persistée, le parallélisme entre nœuds, le human-in-the-loop,
les graphes multi-agents cycliques — aucun de ces besoins n'existe ici.
Utiliser un moteur de graphe pour trois branches, c'est de la généralité
spéculative (YAGNI).

### 7.3 Empreinte : la cible de déploiement est un Space gratuit

L'application tourne sur Hugging Face Spaces (CPU, offre gratuite) avec
`requirements.txt` de **5 dépendances** (flask, pandas, numpy, pyecharts,
folium). `langchain` + `langgraph` tirent des dizaines de paquets transitifs
(pydantic et son pinning de versions, langchain-core, langsmith, tenacity,
orjson…) : image Docker plus lourde, démarrage à froid plus lent, et surtout
une surface de conflits de versions célèbre pour casser les builds — un risque
inacceptable pendant une compétition. Notre client LLM (`llm.py`) fait
**65 lignes en stdlib pure** (`urllib`), zéro dépendance.

### 7.4 La contrainte dominante est la frugalité en tokens — un réglage fin

Avec une petite fenêtre de contexte et des quotas gratuits, chaque caractère
compte. Nos budgets sont réglés à la main et visibles dans `config.py` :
troncature des sorties d'outils (3 500 car.), plafond de prompt (22 000 car.),
mémoire résumée (3 × 300 car.), catalogue YAML compact plutôt que des
descriptions verbeuses. Les templates et wrappers génériques d'un framework
ajoutent du texte qu'on ne contrôle pas, exactement là où on ne peut pas se le
permettre.

### 7.5 Sécurité : le vrai sujet est le sandbox, et aucun framework ne le fournit

Le risque n°1 de cet agent est l'exécution de code généré. L'outil équivalent
de LangChain (`PythonREPLTool` / `PythonAstREPLTool`) est **documenté comme non
sandboxé** — il exécute le code dans le processus hôte. Notre sandbox maison
(builtins filtrés, imports en liste blanche, timeout, copies des données,
sortie bornée) est précisément la partie qu'il aurait fallu écrire soi-même de
toute façon.

### 7.6 Débogage et pédagogie

Chaque appel LLM, chaque outil, chaque résultat est consigné dans
`self.trace` : le comportement de l'agent se lit et se rejoue sans
instrumentation externe (LangSmith…). Dans un cadre de compétition, un
pipeline de ~300 lignes dont chaque décision est visible et justifiable vaut
mieux qu'un empilement d'abstractions : le jury peut auditer l'algorithme en
entier, nous pouvons corriger n'importe quel comportement en touchant la ligne
exacte qui le produit.

### 7.7 Quand est-ce que ces frameworks redeviendraient pertinents ?

Par honnêteté : si le besoin évoluait vers du **multi-agent** avec
orchestration complexe, des **checkpoints persistés** (reprise de conversation
après redémarrage), du **streaming token par token**, un **RAG vectoriel** sur
un gros corpus, ou l'interchangeabilité fréquente de fournisseurs LLM à
function calling natif — alors LangGraph/LangChain mériteraient une
réévaluation. Pour un assistant mono-agent, frugal, sur données tabulaires
locales et modèle sans function calling, le code direct est le bon outil.

## 8. Paramètres (config.py)

| Paramètre | Valeur | Rôle |
|---|---|---|
| `MODELE` | `gemini-flash-lite-latest` | ~3-4 s/question, JSON fiable |
| `MODELES_REPLI` | 2.5 Flash → 3 Flash preview → Gemma 4 26B | continuité de service |
| `MAX_ITERATIONS` | 20 | plafond d'appels LLM par question |
| `MAX_SORTIE_OUTIL` | 3 500 car. | protège la fenêtre de contexte |
| `MAX_CHARS_PROMPT` | 22 000 car. | idem, côté prompt assemblé |
| `MAX_TOKENS_REPONSE` | 1 024 | réponses courtes par construction |
| `TIMEOUT_EXEC` | 8 s | code pandas généré |
| `TAILLE_MEMOIRE` | 3 échanges | suivi de conversation frugal |
| `TEMPERATURE` | 0.2 | réponses factuelles et stables |

La clé API (`GEMMA_API_KEY`) n'est jamais dans le code : elle vient du `.env`
local (ignoré par git et Docker) ou des secrets du Space.

## 9. Fichiers du package

| Fichier | Lignes | Responsabilité |
|---|---|---|
| `agent.py` | ~290 | routeur, routes, boucle d'outils, extraction JSON, garde-fous |
| `outils.py` | ~280 | les 5 outils, sandbox, magasin de graphiques |
| `llm.py` | ~65 | client REST Gemini + cascade de replis (stdlib pure) |
| `config.py` | ~65 | budgets, modèles, chemins, chargement du `.env` |
| `donnees.py` | ~55 | DataFrames paresseux et copies pour le sandbox |
| `connaissances.py` | ~37 | lecture (cachée) des fichiers `connaissance_ia/` |
| `memoire.py` | ~29 | mémoire courte de conversation |
