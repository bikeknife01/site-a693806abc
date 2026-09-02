import json, csv, os, re
from _pbdump import dump_file

BASE = os.path.dirname(__file__)
EXT = os.path.join(BASE, '_extracted')

def as_text(v):
    if isinstance(v, dict):
        v = v.get('1', '')
    if isinstance(v, str):
        return v.strip()
    return v

# ---------- global id -> content-table-key lookup ----------
# IMPORTANT: the Rtree leaf's `instance_id` is stored as an UNSIGNED 64-bit value,
# but the harvested global_id_to_key.json was built from signed int64 protobuf
# varints, so roughly half the real keys (any negative id) were invisible under
# a naive str(id) lookup. Converting unsigned -> signed (two's complement) before
# the second lookup attempt fixes this and takes resolution from ~85% to 100%
# (verified: all 7,694 nodes resolve with this fix).
with open(os.path.join(EXT, 'global_id_to_key.json'), encoding='utf-8') as f:
    GID = json.load(f)

def resolve_key(instance_id):
    if instance_id is None:
        return None
    try:
        u = int(instance_id)
    except (TypeError, ValueError):
        return None
    if str(u) in GID:
        return GID[str(u)]
    s = u - (1 << 64) if u >= (1 << 63) else u
    return GID.get(str(s))

# ---------- classification derived from the resolved template key ----------
# This REPLACES the old numeric type_code -> name guesswork. With 100% of
# instance_ids resolving to real content-table keys (poiNode__<base>_..._alpha),
# we can read the true semantic type directly off the key instead of guessing
# from the Rtree's field-4 code, which turned out to just be a footprint/model
# size-class id (see notes below) rather than a meaningful type or tier.
#
# KEY FINDING (this reverse-engineering pass): the field-4 "type_code" does NOT
# encode Seat-of-Power tier/level at all. Codes 12 and 16 (previously guessed as
# "regional" vs "capital-tier" SOP) both turned out to contain a random mix of
# ordinary named Seats of Power (poiNode__sop_<Name>_alpha) - e.g. code 16
# contains Flint's Finger (user-confirmed in-game as only Level 2) right next to
# Casterly Rock (poiNode__capital_CasterlyRock_alpha, a true Great House
# capital). The 7 "UNKNOWN_*" codes (24/28/30/40/49/56/64) are likewise not
# unknown at all - they are simply the other 7 Great House capitals, each with
# its own unique (larger) bbox footprint: Harrenhal, Pyke, Riverrun/Sunspear,
# Dragonstone/Winterfell, The Eyrie, Oldtown, Storm's End. In short: type_code
# is a MODEL/FOOTPRINT SIZE bucket, not a semantic type or a level.
#
# The true type comes from the base of the resolved key (poiNode__<base>_...):
#   ruin, town, harbor, castle, bridge, tunnel, crossing, dragonsanctum,
#   sop (ordinary named Seat of Power), capital (Great House capital seat).
#
# Also key: `sop_*` and `capital_*` keys carry NO level suffix in their static
# template name (unlike ruin/town/castle/bridge/tunnel/crossing/dragonsanctum,
# which all have an explicit lvl1-lvl5 suffix baked into the key). This means
# a Seat of Power's or Capital's CURRENT level (1-4, the thing shown in the
# in-game icon) is dynamic per-season game state - who currently controls/has
# upgraded that seat - and is simply not present anywhere in this static
# resource dump. It cannot be derived from type_code, bbox, or variant; those
# were red herrings. Only the *place identity* (which named seat/capital it is)
# is static and extractable.
BASE_TYPE_NAMES = {
    'ruin': 'Ruin',
    'town': 'Settlement (Town)',
    'harbor': 'Harbor/Dock',
    'castle': 'Castle',
    'bridge': 'Bridge',
    'tunnel': 'Tunnel',
    'crossing': 'Crossing',
    'dragonsanctum': 'Dragon Sanctum',
    'sop': 'Seat of Power',
    'capital': 'Great House Capital',
}

def prettify_name(raw):
    # CamelCase -> spaced words, e.g. "FlintsFinger" -> "Flints Finger"
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', raw)
    return s

def classify(key, type_code_int):
    if not key:
        return (f'UNKNOWN_{type_code_int}', None, None)
    k = key.replace('poiNode_Shared__', '').replace('poiNode__', '')
    m = re.match(r'^([a-zA-Z]+)', k)
    base = (m.group(1) if m else k).lower()
    lvl_m = re.search(r'lvl?0?(\d+)', k, re.IGNORECASE)
    level = int(lvl_m.group(1)) if lvl_m else None
    name = None
    type_name = BASE_TYPE_NAMES.get(base, f'Unknown ({base})')
    if base in ('sop', 'capital'):
        nm = re.match(r'^(?:sop|capital)_([A-Za-z]+)', k)
        if nm:
            name = prettify_name(nm.group(1))
        if base == 'capital' and 'kingslanding' in k.lower():
            type_name = 'World Capital'
    return (type_name, name, level)

# ---------- Rtree spatial leaves ----------
rtree = dump_file(os.path.join(BASE, 'Westeros_Alpha_6_Poi_Rtree_Client.1784834687.pb'))
leaves = rtree.get('1', [])

rows = []
unresolved = 0
for leaf in leaves:
    pos = leaf.get('1', {})
    x = pos.get('1') if isinstance(pos, dict) else None
    y = pos.get('2') if isinstance(pos, dict) else None
    bbox = leaf.get('2', {})
    inst = leaf.get('3', {})
    instance_id = inst.get('1') if isinstance(inst, dict) else inst
    type_code_raw = leaf.get('4')
    type_code = as_text(type_code_raw)
    try:
        type_code_int = int(type_code)
    except (TypeError, ValueError):
        type_code_int = None
    variant = as_text(leaf.get('5'))

    key = resolve_key(instance_id)
    if key is None:
        unresolved += 1
    type_name, place_name, level = classify(key, type_code_int)

    rows.append({
        'x': x,
        'y': y,
        'bbox_w': bbox.get('3') if isinstance(bbox, dict) else '',
        'bbox_h': bbox.get('4') if isinstance(bbox, dict) else '',
        'type_code': type_code,
        'type_name': type_name,
        'place_name': place_name or '',
        'level': level if level is not None else '',
        'variant': variant,
        'instance_id': instance_id,
        'template_key': key or '',
    })

rows.sort(key=lambda r: (r['y'] or 0, r['x'] or 0))

with open(os.path.join(EXT, 'clean_map_nodes.csv'), 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['x', 'y', 'bbox_w', 'bbox_h', 'type_code', 'type_name', 'place_name',
                  'level', 'variant', 'instance_id', 'template_key']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

with open(os.path.join(EXT, 'clean_poi_type_legend.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['type_name', 'count', 'has_static_level', 'has_place_name'])
    from collections import Counter
    c = Counter(r['type_name'] for r in rows)
    has_level = {r['type_name'] for r in rows if r['level'] != ''}
    has_name = {r['type_name'] for r in rows if r['place_name'] != ''}
    for name, cnt in c.most_common():
        w.writerow([name, cnt, 'yes' if name in has_level else 'no', 'yes' if name in has_name else 'no'])

from collections import Counter
c = Counter(r['type_name'] for r in rows)
print('total map nodes:', len(rows), '  unresolved instance_ids:', unresolved)
for name, cnt in c.most_common():
    print(f'  {name}: {cnt}')
