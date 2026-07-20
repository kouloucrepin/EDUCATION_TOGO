"""Télécharge les dernières données depuis opendata.gouv.tg
et remplace les fichiers dans data/.
Usage : python scripts/update_data.py
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

FILES = {
    '01-etablissements-scolaires.csv':
        'https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-etablissements-scolaires-au-togo/20241218-202046/file-etablissements-scolaires-18-12-2024-20-42-43.csv',
    '02-toilettes-scolaires.csv':
        'https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-etablissements-scolaires-toilettes-au-togo/20241218-202710/file-etablissements-scolaires-toilettes-18-12-2024-20-45-49.csv',
    '03-batiments-electrification.csv':
        'https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-etablissements-scolaires-batiments-statut-delectrification-au-togo/20241218-211936/file-etablissements-scolaires-batiments-statut-delectrification-18-12-2024-20-44-15.csv',
    '04-bibliotheques.csv':
        'https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-les-etablissements-scolaires-bibliotheques-au-togo/20241218-211605/file-etablissements-scolaires-bibliotheques-18-12-2024-20-43-45.csv',
    '06-education-resultats-scolaires.csv':
        'https://opendata.gouv.tg/s/resources/donnees-ouvertes-sur-leducation-et-les-resultats-scolaires-au-togo/20250108-181843/observationdata-aqbqam.csv',
}


def download(url: str, dest: str) -> tuple[int, int, int]:
    req = urllib.request.Request(url, headers={'User-Agent': 'TogoDashboard/1.0'})
    resp = urllib.request.urlopen(req, timeout=120)
    size = 0
    chunk_count = 0
    # Écriture atomique : on télécharge dans un fichier temporaire puis on le
    # bascule d'un coup vers le nom final. Ainsi un téléchargement interrompu
    # ne laisse JAMAIS un CSV vide/partiel à la place du fichier valide
    # (cause de l'EmptyDataError qui plantait le serveur).
    tmp = dest + '.tmp'
    try:
        with open(tmp, 'wb') as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                size += len(chunk)
                chunk_count += 1
        if size == 0:
            raise ValueError('réponse vide (0 octet)')
        os.replace(tmp, dest)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return resp.status, size, chunk_count


def run(log) -> tuple[int, list[str]]:
    ok = 0
    errors = []
    for fname, url in FILES.items():
        dest = os.path.join(DATA_DIR, fname)
        log(f'{fname} → téléchargement...')
        try:
            status, size, _ = download(url, dest)
            log(f'  OK ({status}, {size / 1024 / 1024:.1f} Mo)')
            ok += 1
        except Exception as e:
            msg = f'  ERREUR : {e}'
            log(msg)
            errors.append(f'{fname} : {e}')

    ts_path = os.path.join(DATA_DIR, '.last_update')
    with open(ts_path, 'w') as f:
        f.write(str(int(time.time())))

    return ok, errors


def run_stream():
    """Générateur qui yield des dicts de progression pour SSE."""
    ok = 0
    errors = []
    total = len(FILES)
    for idx, (fname, url) in enumerate(FILES.items(), 1):
        dest = os.path.join(DATA_DIR, fname)
        yield {'type': 'file', 'file': fname, 'status': 'downloading', 'current': idx, 'total': total}
        try:
            status, size, chunks = download(url, dest)
            yield {'type': 'file', 'file': fname, 'status': 'ok', 'size_mb': round(size / 1024 / 1024, 1), 'current': idx, 'total': total}
            ok += 1
        except Exception as e:
            yield {'type': 'file', 'file': fname, 'status': 'error', 'error': str(e), 'current': idx, 'total': total}
            errors.append(f'{fname} : {e}')

    ts_path = os.path.join(DATA_DIR, '.last_update')
    with open(ts_path, 'w') as f:
        f.write(str(int(time.time())))

    yield {'type': 'done', 'ok': ok, 'total': total, 'errors': errors}


if __name__ == '__main__':
    def echo(msg):
        print(msg)
        sys.stdout.flush()
    ok, errors = run(echo)
    print(f'\n{ok}/{len(FILES)} fichiers mis à jour.')
    if errors:
        print(f'{len(errors)} erreur(s) :')
        for e in errors:
            print(f'  - {e}')
