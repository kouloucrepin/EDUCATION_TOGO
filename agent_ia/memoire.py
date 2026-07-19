"""Mémoire courte : les 5 derniers échanges (question + résumé de réponse)."""
from collections import deque

from . import config


class Memoire:
    def __init__(self, taille=None):
        self._echanges = deque(maxlen=taille or config.TAILLE_MEMOIRE)

    def ajouter(self, question, reponse):
        resume = str(reponse).replace('\n', ' ')
        if len(resume) > 300:
            resume = resume[:300] + '…'
        self._echanges.append((str(question)[:200], resume))

    def texte(self):
        if not self._echanges:
            return ''
        lignes = ['Historique des derniers échanges (pour les questions de suivi) :']
        for i, (q, r) in enumerate(self._echanges, 1):
            lignes.append(f'{i}. Q: {q}\n   R: {r}')
        return '\n'.join(lignes)

    def vider(self):
        self._echanges.clear()

    def __len__(self):
        return len(self._echanges)
