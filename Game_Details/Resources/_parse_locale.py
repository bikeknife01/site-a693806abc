import json, sys

def parse_deltas(path):
    text = open(path, 'rb').read().decode('utf-8')
    chunks = text.split('¯¯')  # "¯¯"
    out = {}
    for chunk in chunks:
        if not chunk:
            continue
        chunk = chunk.rstrip('¬')  # trailing "¬¬" leftover after split, in case
        parts = chunk.split('¬¬', 1)  # "¬¬"
        if len(parts) == 2:
            key, val = parts
            out[key] = val
    return out

if __name__ == '__main__':
    path = sys.argv[1]
    outpath = sys.argv[2]
    d = parse_deltas(path)
    print('parsed entries:', len(d))
    json.dump(d, open(outpath, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
