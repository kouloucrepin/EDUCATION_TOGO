import pandas as pd
import os
import re
import unicodedata
from .config import DATA_PATH, FICHIERS


def _norm_txt(s):
    """Majuscules sans accents (pour la recherche dans la hiérarchie COSO)."""
    s = ''.join(c for c in unicodedata.normalize('NFD', str(s))
                if unicodedata.category(c) != 'Mn')
    return s.upper().strip()


def _parse_point(geom_str):
    m = re.search(r'POINT\s*\(([\d\.\-]+)\s+([\d\.\-]+)\)', geom_str)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


def load_onglet2_data():
    dfs = {}
    for key, fname in FICHIERS.items():
        path = os.path.join(DATA_PATH, fname)
        try:
            dfs[key] = pd.read_csv(path, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            dfs[key] = pd.read_csv(path, encoding='latin1', low_memory=False)
        dfs[key] = dfs[key].drop_duplicates()
    return dfs


def filter_region(df, regions=None):
    if regions and 'region_nom_bdd' in df.columns:
        return df[df['region_nom_bdd'].isin(regions)]
    return df


def filter_territoire(df, regions=None, prefecture=None, commune=None):
    """Filtre en cascade région / préfecture / commune (colonnes des fichiers 01-03)."""
    out = filter_region(df, regions)
    if prefecture and 'prefecture_nom_bdd' in out.columns:
        out = out[out['prefecture_nom_bdd'] == prefecture]
    if commune and 'commune_nom_bdd' in out.columns:
        out = out[out['commune_nom_bdd'] == commune]
    return out


def get_territoires(dfs):
    """Arbre Région → Préfecture → [Communes] issu du fichier 01."""
    df = dfs['etablissements'][
        ['region_nom_bdd', 'prefecture_nom_bdd', 'commune_nom_bdd']
    ].dropna().drop_duplicates()
    arbre = {}
    for r, p, c in df.itertuples(index=False):
        arbre.setdefault(str(r), {}).setdefault(str(p), set()).add(str(c))
    return {
        r: {p: sorted(cs) for p, cs in sorted(prefs.items())}
        for r, prefs in sorted(arbre.items())
    }


def get_ecoles_points(dfs, regions=None, prefecture=None, commune=None):
    df = filter_territoire(dfs['etablissements'], regions, prefecture, commune)
    points = []
    for _, r in df.iterrows():
        lon, lat = _parse_point(r['geometry'])
        if lon is not None:
            points.append({
                'lat': lat, 'lon': lon,
                'nom': r.get('etablissement_nom', ''),
                'region': r.get('region_nom_bdd', ''),
                'prefecture': r.get('prefecture_nom_bdd', ''),
                'categorie': r.get('etablissement_categorie', ''),
                'inspection': r.get('inspection_tutelle', ''),
                'commune': r.get('commune_nom_bdd', ''),
            })
    return points


def get_toilettes_points(dfs, regions=None, prefecture=None, commune=None):
    df = filter_territoire(dfs['toilettes'], regions, prefecture, commune)
    points = []
    for _, r in df.iterrows():
        lon, lat = _parse_point(r['geometry'])
        if lon is not None:
            points.append({
                'lat': lat, 'lon': lon,
                'type': r.get('toilette_type', ''),
                'region': r.get('region_nom_bdd', ''),
                'etab': r.get('etab_nom', ''),
            })
    return points


def get_batiments_points(dfs, regions=None, prefecture=None, commune=None):
    """Un point par bâtiment scolaire (fichier 03). Les géométries sont des
    MULTIPOLYGON : on prend le premier sommet comme position (les bâtiments
    font quelques mètres, la perte de précision est invisible à ces zooms)."""
    df = filter_territoire(dfs['batiments'], regions, prefecture, commune)
    coords = df['geometry'].astype(str).str.extract(r'\(+\s*([\d\.\-]+)\s+([\d\.\-]+)')
    lon = pd.to_numeric(coords[0], errors='coerce')
    lat = pd.to_numeric(coords[1], errors='coerce')
    points = []
    for lo, la, fonction, annee, region in zip(
            lon, lat, df['batiment_fonction'], df['batiment_annee'], df['region_nom_bdd']):
        if pd.notna(lo) and pd.notna(la):
            # 5 décimales ≈ 1 m : suffisant, et ~2 fois moins d'octets dans
            # le HTML de la carte (28 000 points embarqués)
            points.append({
                'lat': round(float(la), 5), 'lon': round(float(lo), 5),
                'fonction': fonction, 'annee': annee, 'region': region,
            })
    return points


def get_coso_projets(dfs, regions=None, prefecture=None, commune=None):
    df = dfs['coso'].copy()
    df = df[(df['latitude'].notna()) & (df['longitude'].notna())]
    df = df[(df['latitude'] != 0) & (df['longitude'] != 0)]
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])

    # La hiérarchie COSO est en majuscules sans accents :
    # VILLAGE > CANTON > COMMUNE > PREFECTURE > REGION
    hier_norm = df['hierarchy'].astype(str).map(_norm_txt)
    if regions:
        cibles = [_norm_txt(r) for r in regions]
        df = df[hier_norm.apply(lambda h: any(c in h for c in cibles))]
        hier_norm = hier_norm.loc[df.index]
    if prefecture:
        df = df[hier_norm.str.contains(_norm_txt(prefecture), regex=False)]
        hier_norm = hier_norm.loc[df.index]
    if commune:
        df = df[hier_norm.str.contains(_norm_txt(commune), regex=False)]

    rows = []
    for _, r in df.iterrows():
        def _safe_int(v):
            try:
                x = pd.to_numeric(v, errors='coerce')
                return int(x) if not pd.isna(x) else 0
            except:
                return 0
        rows.append({
            'lat': r['latitude'], 'lon': r['longitude'],
            'titre': r.get('title', ''),
            'type': r.get('type', ''),
            'status': r.get('status', ''),
            'cout': pd.to_numeric(r.get('estimated_cost', 0), errors='coerce') or 0,
            'salles': _safe_int(r.get('number_of_classrooms', 0)),
            'latrines': _safe_int(r.get('number_of_latrine_blocks', 0)),
            'localite': r.get('location_name', ''),
        })
    return rows


def get_counters(dfs, regions=None, prefecture=None, commune=None):
    ecoles = get_ecoles_points(dfs, regions, prefecture, commune)
    toilettes = get_toilettes_points(dfs, regions, prefecture, commune)
    coso = get_coso_projets(dfs, regions, prefecture, commune)

    total_ecoles = len(ecoles)
    total_toilettes = len(toilettes)
    total_coso = len(coso)
    total_salles = sum(p['salles'] for p in coso)
    ratio_toilettes = round(total_toilettes / total_ecoles, 2) if total_ecoles else 0

    return {
        'total_ecoles': total_ecoles,
        'total_toilettes': total_toilettes,
        'total_coso': total_coso,
        'total_salles': total_salles,
        'ratio_toilettes': ratio_toilettes,
    }


def get_coso_aggregation(dfs, regions=None, prefecture=None, commune=None):
    coso = get_coso_projets(dfs, regions, prefecture, commune)

    from collections import Counter
    types = Counter(p['type'] for p in coso)
    status = Counter(p['status'] for p in coso)

    type_rows = sorted(types.items(), key=lambda x: -x[1])
    status_rows = sorted(status.items(), key=lambda x: -x[1])

    return type_rows, status_rows


def get_coso_croise(dfs, regions=None, prefecture=None, commune=None):
    """Répartition des statuts d'avancement POUR CHAQUE type de projet COSO.
    Sert au filtrage croisé du dashboard : clic sur une barre des types
    → camembert des statuts restreint à ce type."""
    from collections import Counter
    coso = get_coso_projets(dfs, regions, prefecture, commune)
    croise = {}
    for p in coso:
        croise.setdefault(p['type'], Counter())[p['status']] += 1
    return {t: dict(c.most_common()) for t, c in croise.items()}


def get_categorie_counts(dfs, regions=None):
    points = get_ecoles_points(dfs, regions)
    from collections import Counter
    return Counter(p['categorie'] for p in points)
