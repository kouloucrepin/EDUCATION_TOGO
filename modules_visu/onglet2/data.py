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


def _norm_insp(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.upper().replace('-', ' ').replace("'", ' ').replace('IEPP ', '')
    return ' '.join(s.split())


def _build_teacher_inspection_map(presco_inspections, school_inspections):
    OVERRIDES = {
        'Agoenyive Est': 'IEPP Ago\u00e9-Nyiv\u00e9-Est',
        'Agoenyive Ouest': 'IEPP Ago\u00e9-Nyiv\u00e9-Ouest',
        'Ogou Nord': 'IEPP Ogou',
        'Ogou Sud': 'IEPP Ogou',
    }
    school_norm = {}
    for s in school_inspections:
        sn = _norm_insp(s)
        school_norm.setdefault(sn, []).append(s)

    presco_names = [p for p in presco_inspections if not p.startswith('T.')]
    mapping = {}
    for p in presco_names:
        if p in OVERRIDES:
            mapping[p] = OVERRIDES[p]
        else:
            pn = _norm_insp(p)
            matches = school_norm.get(pn, [])
            if len(matches) == 1:
                mapping[p] = matches[0]
    return mapping


PRESCO_REGION_MAP = {
    'T.R.Grand Lom\u00e9': 'Maritime',
    'T.R.Maritime': 'Maritime',
    'T.R.Plateaux Est': 'Plateaux',
    'T.R.Plateaux Ouest': 'Plateaux',
    'T.R.Centrale': 'Centrale',
    'T.R.Kara': 'Kara',
    'T.R. Savanes': 'Savanes',
}


def get_teacher_region_agg(dfs):
    if 'prescolaire' not in dfs:
        return {}
    presco = dfs['prescolaire']
    agg = {}
    for _, r in presco.iterrows():
        insp = r['inspections']
        sexe = str(r['sexe'])
        val = pd.to_numeric(r['Value'], errors='coerce')
        if pd.isna(val):
            continue
        if insp in PRESCO_REGION_MAP:
            region = PRESCO_REGION_MAP[insp]
        elif insp == 'T.G\u00e9n\u00e9ral':
            continue
        else:
            continue
        d = agg.setdefault(region, {'total': 0, 'F\u00e9minin': 0, 'Masculin': 0})
        if sexe == 'Total':
            d['total'] += int(val)
        elif sexe in d:
            d[sexe] += int(val)
    return agg


def get_teacher_by_inspection(dfs):
    if 'prescolaire' not in dfs:
        return {}
    presco = dfs['prescolaire']
    school = dfs['etablissements']
    map_p2s = _build_teacher_inspection_map(
        presco['inspections'].dropna().unique(),
        school['inspection_tutelle'].dropna().unique(),
    )
    result = {}
    for _, r in presco.iterrows():
        insp = r['inspections']
        sexe = str(r['sexe'])
        val = pd.to_numeric(r['Value'], errors='coerce')
        if pd.isna(val):
            continue
        if insp not in map_p2s:
            continue
        school_insp = map_p2s[insp]
        d = result.setdefault(school_insp, {'total': 0, 'F\u00e9minin': 0, 'Masculin': 0})
        if sexe == 'Total':
            d['total'] += int(val)
        elif sexe in d:
            d[sexe] += int(val)
    return result


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
    _teachers = None
    if 'prescolaire' in dfs:
        _teachers = get_teacher_by_inspection(dfs)
    points = []
    for _, r in df.iterrows():
        lon, lat = _parse_point(r['geometry'])
        if lon is not None:
            insp = r.get('inspection_tutelle', '')
            t = _teachers.get(insp, {}) if _teachers else {}
            points.append({
                'lat': lat, 'lon': lon,
                'nom': r.get('etablissement_nom', ''),
                'region': r.get('region_nom_bdd', ''),
                'prefecture': r.get('prefecture_nom_bdd', ''),
                'categorie': r.get('etablissement_categorie', ''),
                'inspection': insp,
                'commune': r.get('commune_nom_bdd', ''),
                'terrain_sport': r.get('terrain_sport', ''),
                'enseignants_total': t.get('total', None),
                'enseignants_femmes': t.get('F\u00e9minin', None),
                'enseignants_hommes': t.get('Masculin', None),
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

    def _hier_seg(h, i):
        # hierarchy = VILLAGE > CANTON > COMMUNE > PREFECTURE > REGION
        parts = [p.strip() for p in str(h).split('>')]
        return parts[i] if len(parts) >= abs(i) else ''

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
            'region': _hier_seg(r.get('hierarchy', ''), -1),
            'prefecture': _hier_seg(r.get('hierarchy', ''), -2),
        })
    return rows


def get_counters(dfs, regions=None, prefecture=None, commune=None):
    ecoles = get_ecoles_points(dfs, regions, prefecture, commune)
    toilettes = get_toilettes_points(dfs, regions, prefecture, commune)

    total_ecoles = len(ecoles)

    df = filter_territoire(dfs['etablissements'], regions, prefecture, commune)
    terrain_sport_oui = len(df[df['terrain_sport'] == 'Oui'])
    terrain_sport_pct = round(terrain_sport_oui / total_ecoles * 100, 1) if total_ecoles else 0

    # Nombre de blocs de toilettes recensés (chiffre fiable et affiché).
    # NB : ~86 % des points n'ont pas de nom d'établissement et les coordonnées
    # ne coïncident pas avec celles des écoles → impossible de calculer un vrai
    # « % d'écoles avec toilettes ». On expose donc le nombre de blocs et, à
    # titre indicatif, la densité (blocs par établissement).
    toilettes_total = len(toilettes) if toilettes else 0
    toilettes_par_ecole = round(toilettes_total / total_ecoles, 2) if total_ecoles else 0
    # conservés pour l'export standalone (dashboard_html) — ne pas afficher tels quels
    toilettes_etab = len(set(p['etab'] for p in toilettes if p.get('etab'))) if toilettes else 0
    toilettes_pct = round(toilettes_etab / total_ecoles * 100, 1) if total_ecoles else 0

    coso = get_coso_projets(dfs, regions, prefecture, commune)
    total_coso = len(coso) if coso else 0
    coso_regions = len({p['region'] for p in coso if p.get('region')}) if coso else 0
    coso_prefectures = len({p['prefecture'] for p in coso if p.get('prefecture')}) if coso else 0

    cat_counts = df['etablissement_categorie'].value_counts()
    primaire = int(cat_counts.get('Ecole primaire', 0))
    college = int(cat_counts.get('College', 0))
    lycee = int(cat_counts.get('Lyc\u00e9e', 0))

    bat_df = filter_territoire(dfs['batiments'], regions, prefecture, commune)
    batiments = len(bat_df)
    # Ancienneté moyenne des bâtiments (âge = 2024 - année de construction,
    # années plausibles 1950-2024 ; le fichier mêle int et 'Nsp').
    _an = pd.to_numeric(bat_df['batiment_annee'], errors='coerce') if 'batiment_annee' in bat_df.columns else None
    if _an is not None:
        _an = _an[(_an >= 1950) & (_an <= 2024)]
        anciennete_moyenne = round(2024 - _an.mean(), 1) if len(_an) else 0
    else:
        anciennete_moyenne = 0

    biblio_df = filter_territoire(dfs['bibliotheques'], regions, prefecture, commune)
    bibliotheques = biblio_df['etablissement_nom'].nunique() if 'etablissement_nom' in biblio_df.columns else 0

    if 'prescolaire' in dfs:
        presco = dfs['prescolaire']
        if regions and not prefecture and not commune:
            teacher_agg = get_teacher_region_agg(dfs)
            enseignants_total = sum(v['total'] for r, v in teacher_agg.items() if r in regions)
            enseignants_femmes = sum(v['F\u00e9minin'] for r, v in teacher_agg.items() if r in regions)
            enseignants_hommes = sum(v['Masculin'] for r, v in teacher_agg.items() if r in regions)
        else:
            gen = presco[presco['inspections'] == 'T.G\u00e9n\u00e9ral']
            enseignants_total = int(pd.to_numeric(gen[gen['sexe'] == 'Total']['Value'], errors='coerce').sum())
            enseignants_femmes = int(pd.to_numeric(gen[gen['sexe'] == 'F\u00e9minin']['Value'], errors='coerce').sum())
            enseignants_hommes = int(pd.to_numeric(gen[gen['sexe'] == 'Masculin']['Value'], errors='coerce').sum())
    else:
        enseignants_total = enseignants_femmes = enseignants_hommes = 0

    return {
        'total_ecoles': total_ecoles,
        'primaire': primaire,
        'college': college,
        'lycee': lycee,
        'anciennete_moyenne': anciennete_moyenne,
        'toilettes_total': toilettes_total,
        'toilettes_par_ecole': toilettes_par_ecole,
        'toilettes_etab': toilettes_etab,
        'toilettes_pct': toilettes_pct,
        'terrain_sport': terrain_sport_oui,
        'terrain_sport_pct': terrain_sport_pct,
        'batiments': batiments,
        'bibliotheques': bibliotheques,
        'enseignants_total': enseignants_total,
        'enseignants_femmes': enseignants_femmes,
        'enseignants_hommes': enseignants_hommes,
        'total_coso': total_coso,
        'coso_regions': coso_regions,
        'coso_prefectures': coso_prefectures,
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
