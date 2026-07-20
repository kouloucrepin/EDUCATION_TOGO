"""Chargement paresseux des DataFrames exposés au sandbox (clés '01'..'16')."""
import os
import threading

import pandas as pd

from . import config

_dfs = {}
_verrou = threading.Lock()


def _lire_csv(chemin):
    try:
        return pd.read_csv(chemin, encoding='utf-8', low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(chemin, encoding='latin1', low_memory=False)


def _nettoyer(cle, df):
    """Nettoyages ciblés pour que le sandbox compte comme le dashboard.

    COSO (clé '14') : latitude/longitude = 0 sont des coordonnées ABSENTES
    (non géolocalisées), pas le point (0,0). On les remet à NaN pour que
    df['14']['latitude'].notna() donne bien les 86 projets géolocalisés
    (et non 154, qui inclut les 68 lignes à 0)."""
    if cle == '14':
        for col in ('latitude', 'longitude'):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df.loc[df[col] == 0, col] = float('nan')
    return df


def obtenir(cle):
    """Retourne le DataFrame original (NE PAS exposer directement au sandbox)."""
    if cle not in config.FICHIERS_DFS:
        raise KeyError(f"clé inconnue : {cle!r} — clés valides : {sorted(config.FICHIERS_DFS)}")
    with _verrou:
        if cle not in _dfs:
            df = _lire_csv(os.path.join(config.DOSSIER_DATA, config.FICHIERS_DFS[cle]))
            _dfs[cle] = _nettoyer(cle, df)
    return _dfs[cle]


class CopiesParesseuses(dict):
    """dict de DataFrames copiés À LA DEMANDE : seuls les df réellement
    utilisés par le code généré sont lus/copiés (gain de temps et de RAM).
    Note : les valeurs restent None tant qu'elles n'ont pas été accédées
    via dfs['cle'] — itérer sur .values() n'est pas supporté."""

    def __init__(self):
        super().__init__({cle: None for cle in config.FICHIERS_DFS})

    def __getitem__(self, cle):
        valeur = super().__getitem__(cle)   # KeyError naturelle si clé inconnue
        if valeur is None:
            valeur = obtenir(cle).copy()
            super().__setitem__(cle, valeur)
        return valeur


def copies():
    """Copies paresseuses de tous les DataFrames pour le sandbox."""
    return CopiesParesseuses()


def cles():
    return sorted(config.FICHIERS_DFS)
