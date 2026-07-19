"""agent_ia — assistant IA du Dashboard Éducation Togo (Gemma via API Gemini).

Usage :
    from agent_ia import AgentEducation
    agent = AgentEducation()
    print(agent.repondre("Combien d'écoles compte le Togo ?")['reponse'])
"""
from .agent import AgentEducation, SUGGESTIONS
from .memoire import Memoire
from . import outils, connaissances, donnees, config

__all__ = ['AgentEducation', 'SUGGESTIONS', 'Memoire',
           'outils', 'connaissances', 'donnees', 'config']
