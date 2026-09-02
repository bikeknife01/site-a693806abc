"""Scan every .pb file in this folder and harvest the {fixed64_id -> string_key}
pairs that appear throughout (the game seems to assign a stable 64-bit ID to
every content key, reused everywhere that key is referenced). Build one big
reverse-lookup dict so opaque IDs seen elsewhere (e.g. in spatial indexes)
can be resolved back to their readable key.
"""
import sys, os, glob, json
sys.path.insert(0, os.path.dirname(__file__))
from _pbdump import parse_message

BASE = os.path.dirname(__file__)

id_to_key = {}
key_to_id = {}

def single(v):
    """parse_message stores every field as a list of occurrences; unwrap a
    single-occurrence list to its bare value."""
    if isinstance(v, list) and len(v) == 1:
        return v[0]
    return v

def walk(node):
    if isinstance(node, dict):
        if '1' in node and '2' in node and set(node.keys()) <= {'1', '2'}:
            v1 = single(node.get('1'))
            v2 = single(node.get('2'))
            if isinstance(v1, dict) and '_fixed64_int' in v1 and isinstance(v2, str) and v2:
                idval = v1['_fixed64_int']
                id_to_key.setdefault(idval, set()).add(v2)
                key_to_id.setdefault(v2, set()).add(idval)
        for v in node.values():
            walk(v)
    elif isinstance(node, list):
        for v in node:
            walk(v)

files = sorted(glob.glob(os.path.join(BASE, '*.pb')))
print(f'scanning {len(files)} .pb files...')
ok, fail = 0, 0
for i, path in enumerate(files):
    try:
        data = open(path, 'rb').read()
        parsed = parse_message(data, 0, len(data))
        walk(parsed)
        ok += 1
    except Exception as e:
        fail += 1
    if (i+1) % 200 == 0:
        print(f'  ...{i+1}/{len(files)} done, {len(id_to_key)} ids so far')

print(f'done. ok={ok} fail={fail} unique ids={len(id_to_key)} unique keys={len(key_to_id)}')

# collapse sets to lists for JSON, flag any id with >1 distinct key (collision/ambiguous)
collisions = {k: list(v) for k, v in id_to_key.items() if len(v) > 1}
print('ids mapping to >1 distinct key:', len(collisions))

out = {str(k): list(v)[0] if len(v) == 1 else list(v) for k, v in id_to_key.items()}
with open(os.path.join(BASE, '_extracted', 'global_id_to_key.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print('saved global_id_to_key.json with', len(out), 'entries')
