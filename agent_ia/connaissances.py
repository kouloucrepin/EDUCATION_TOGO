"""Chargement des fichiers de connaissance (dossier connaissance_ia/)."""
import os
from functools import lru_cache

from . import config


@lru_cache(maxsize=None)
def lire(nom):
    chemin = os.path.join(config.DOSSIER_CONNAISSANCE, nom)
    with open(chemin, encoding='utf-8') as f:
        return f.read().strip()


def regles():
    return lire('RULES.txt')


def plateforme():
    return lire('CATALOGUE_PLATFORME.md')


def sources():
    return lire('CATALOGUE_SOURCES.md')


def termes_cles():
    return lire('CATALOGUE_TERMES_CLES.md')


def schemas():
    return lire('CATALOGUE_SCHEMAS.yml')


def contexte_connaissance():
    """Contexte de la route 'connaissance' : plateforme + termes + sources."""
    return '\n\n'.join([plateforme(), termes_cles(), sources()])
