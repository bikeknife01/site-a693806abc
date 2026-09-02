import json, csv, os

BASE = os.path.dirname(__file__)
EXT = os.path.join(BASE, '_extracted')

def load(name):
    return json.load(open(os.path.join(EXT, name), encoding='utf-8'))

def key(node):
    """Given a {'1': {...}, '2': 'the_key'} id-block, return the string key, or None."""
    if isinstance(node, dict) and '2' in node and isinstance(node['2'], str):
        return node['2']
    return None

def as_text(v):
    """Some fields parse ambiguously as either a plain string or a
    single-field nested message ({'1': 'text'}) depending on byte luck.
    Normalize both shapes down to plain text."""
    if isinstance(v, dict):
        v = v.get('1', '')
    if isinstance(v, str):
        return v.strip()
    return v

def loc(locale, k, default=''):
    k = as_text(k)
    if not k:
        return default
    return locale.get(k, k)

locale = load('locale_enUS.json')

# ---------- Dragon stat types ----------
stat_table = load('DragonStatTable.1784834962.json')['1']
with open(os.path.join(EXT, 'clean_dragon_stats.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['key', 'display_name'])
    for item in stat_table:
        k = key(item['1'])
        w.writerow([k, as_text(item['2'])])

# ---------- Dragon rarities (star tiers) ----------
rarity_table = load('DragonRarityTable.1784834962.json')['1']
with open(os.path.join(EXT, 'clean_dragon_rarities.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['key', 'display_name', 'sort_order_field14'])
    for item in rarity_table:
        k = key(item['1'])
        body = item['2']
        name = body.get('1') if isinstance(body, dict) else None
        order = body.get('14') if isinstance(body, dict) else None
        w.writerow([k, name, order])

# ---------- Dragon breeds ----------
try:
    breed_table = load('DragonBreedTable.1784834962.json')['1']
    with open(os.path.join(EXT, 'clean_dragon_breeds.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['key', 'raw_body'])
        for item in breed_table:
            k = key(item['1'])
            w.writerow([k, json.dumps(item.get('2'), ensure_ascii=False)])
except FileNotFoundError:
    pass

# ---------- Habits ----------
habits_table = load('dragonHabitsTable_merged.1787687230.json')['1']
habit_rows = []
for item in habits_table:
    k = key(item['1'])
    body = item.get('2', {})
    name_key = body.get('2') if isinstance(body, dict) else None
    desc_key = body.get('3') if isinstance(body, dict) else None
    icon = as_text(body.get('4')) if isinstance(body, dict) else None
    ability_key = key(body.get('5')) if isinstance(body, dict) else None
    habit_rows.append({
        'key': k,
        'name': loc(locale, name_key),
        'description': loc(locale, desc_key),
        'icon': icon,
        'ability_key': ability_key,
    })
with open(os.path.join(EXT, 'clean_dragon_habits.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['key', 'name', 'description', 'icon', 'ability_key'])
    w.writeheader()
    w.writerows(habit_rows)

habits_by_key = {r['key']: r for r in habit_rows}

# ---------- Master dragon list ----------
dragon_table = load('dragonTable_merged.1787687230.json')['1']
dragon_rows = []
for item in dragon_table:
    k = key(item['1'])
    body = item.get('2', {})
    name_key = body.get('1')
    desc_key = body.get('2')
    icon = as_text(body.get('3'))
    rarity_key = key(body.get('4'))
    affinity_key = key(body.get('5'))
    breed_key = key(body.get('6'))
    shard_key = key(body.get('7'))
    command_key = key(body.get('8'))
    habit_slots_raw = body.get('9', [])
    if isinstance(habit_slots_raw, dict):
        habit_slots_raw = [habit_slots_raw]
    habit_keys = [key(h) for h in habit_slots_raw]
    habit_names = [habits_by_key.get(hk, {}).get('name', hk) for hk in habit_keys]
    row = {
        'key': k,
        'name': loc(locale, name_key),
        'description': loc(locale, desc_key),
        'icon': icon,
        'rarity': rarity_key,
        'affinity': affinity_key,
        'breed': breed_key,
        'shard_item': shard_key,
        'unique_command': command_key,
    }
    for i in range(6):
        row[f'habit_slot_{i+1}_key'] = habit_keys[i] if i < len(habit_keys) else ''
        row[f'habit_slot_{i+1}_name'] = habit_names[i] if i < len(habit_names) else ''
    dragon_rows.append(row)

fieldnames = ['key', 'name', 'description', 'icon', 'rarity', 'affinity', 'breed', 'shard_item', 'unique_command']
for i in range(6):
    fieldnames += [f'habit_slot_{i+1}_key', f'habit_slot_{i+1}_name']

with open(os.path.join(EXT, 'clean_dragons.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(dragon_rows)

print(f"dragons: {len(dragon_rows)}, habits: {len(habit_rows)}, rarities: {len(rarity_table)}, stats: {len(stat_table)}")
