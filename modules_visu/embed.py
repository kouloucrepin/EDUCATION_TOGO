"""Utilitaire partagé : extraire le fragment embarquable (div + script)
d'un rendu pyecharts `render_embed()`, qui retourne un document HTML complet.

Utilisé par l'application Flask pour composer plusieurs graphiques
dans une même page sans imbriquer des documents <html>.
"""
import re

_RX_FRAGMENT = re.compile(
    r'(<div\s+id="[^"]+"[^>]*></div>\s*<script>.*?</script>)',
    re.DOTALL,
)
_RX_BODY = re.compile(r'<body[^>]*>(.*)</body>', re.DOTALL)


def chart_fragment(html: str) -> str:
    """Retourne uniquement le conteneur du graphique et son script d'init."""
    m = _RX_FRAGMENT.search(html)
    if m:
        return m.group(1)
    m = _RX_BODY.search(html)
    if m:
        return m.group(1).strip()
    return html
