"""Cross-reference helper: given one or more real in-game (x, y) coordinates
(plus what the user knows that POI actually is), find the nearest node(s) in
clean_map_nodes.csv and print every raw field for comparison.

Usage:
    python _lookup_coord.py X Y [RADIUS] ["known_type_label"]

Example:
    python _lookup_coord.py 1203 884 15 "real Seat of Power"
    python _lookup_coord.py 1203 884            # radius defaults to 25, label optional

If you don't know the exact coordinate-system alignment, just run with a
generous radius (e.g. 50-100) and eyeball which nearby node looks like a
plausible match (right bbox size class, etc).
"""
import csv, sys, os, math

BASE = os.path.dirname(__file__)
EXT = os.path.join(BASE, '_extracted')

def load_rows():
    with open(os.path.join(EXT, 'clean_map_nodes.csv'), encoding='utf-8') as f:
        return list(csv.DictReader(f))

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    x = float(sys.argv[1])
    y = float(sys.argv[2])
    radius = float(sys.argv[3]) if len(sys.argv) > 3 else 25.0
    label = sys.argv[4] if len(sys.argv) > 4 else '(unspecified)'

    rows = load_rows()
    hits = []
    for r in rows:
        try:
            rx, ry = float(r['x']), float(r['y'])
        except (TypeError, ValueError):
            continue
        d = math.hypot(rx - x, ry - y)
        if d <= radius:
            hits.append((d, r))
    hits.sort(key=lambda t: t[0])

    print(f'Query: ({x}, {y})  radius={radius}  known_type="{label}"')
    print(f'Found {len(hits)} node(s) within radius:')
    for d, r in hits:
        print(f"  dist={d:6.2f}  x={r['x']:>6} y={r['y']:>6}  "
              f"type_code={r['type_code']:>4}  type_name={r['type_name']:<12}  "
              f"bbox={r['bbox_w']}x{r['bbox_h']}  variant={r['variant']}  "
              f"instance_id={r['instance_id']}")
    if not hits:
        print('  (none found - try a larger radius, or the coordinate systems may not align 1:1)')

if __name__ == '__main__':
    main()
