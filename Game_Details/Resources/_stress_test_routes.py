"""Stress-test map routing against the full-resolution terrain evidence.

This compares the legacy strict 2x2 reduction (all four pixels must be clear)
with the topology-preserving reduction used by the interactive map (at least
half clear, plus known occupiable node centers). It samples deterministic local
routes, where accidental loss of a one-tile pass is easiest to detect.
"""
import argparse
import csv
import heapq
import json
import math
import os
import random

from PIL import Image, ImageFilter


BASE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(BASE, '_extracted')
CELL = 2
TRANSIT_TYPES = {'Crossing', 'Tunnel', 'Bridge', 'Harbor/Dock'}


def nearest_cell(x, y, grid, width, height, world_height):
    bx = max(0, min(width - 1, round(x / CELL)))
    by = max(0, min(height - 1, round((world_height - y) / CELL)))
    for radius in range(9):
        best = None
        for yy in range(max(0, by - radius), min(height, by + radius + 1)):
            for xx in range(max(0, bx - radius), min(width, bx + radius + 1)):
                if radius and xx not in (bx - radius, bx + radius) and yy not in (by - radius, by + radius):
                    continue
                idx = yy * width + xx
                if grid[idx]:
                    distance = math.hypot(xx - bx, yy - by)
                    if best is None or distance < best[0]:
                        best = (distance, idx)
        if best:
            return best[1]
    return None


def shortest_path(grid, width, height, start, goal, margin=100):
    """Bounded A* matching the browser's eight-way, no-corner-squeeze movement."""
    sx, sy = start % width, start // width
    gx, gy = goal % width, goal // width
    x0, x1 = max(0, min(sx, gx) - margin), min(width - 1, max(sx, gx) + margin)
    y0, y1 = max(0, min(sy, gy) - margin), min(height - 1, max(sy, gy) + margin)
    scores = {start: 0.0}
    heap = [(math.hypot(sx - gx, sy - gy) * CELL, start)]
    closed = set()
    directions = ((-1, 0, CELL), (1, 0, CELL), (0, -1, CELL), (0, 1, CELL),
                  (-1, -1, CELL * math.sqrt(2)), (1, -1, CELL * math.sqrt(2)),
                  (-1, 1, CELL * math.sqrt(2)), (1, 1, CELL * math.sqrt(2)))
    while heap:
        _, current = heapq.heappop(heap)
        if current in closed:
            continue
        if current == goal:
            return scores[current]
        closed.add(current)
        cx, cy = current % width, current // width
        for dx, dy, cost in directions:
            nx, ny = cx + dx, cy + dy
            if nx < x0 or nx > x1 or ny < y0 or ny > y1:
                continue
            nxt = ny * width + nx
            if not grid[nxt]:
                continue
            if dx and dy and (not grid[cy * width + nx] or not grid[ny * width + cx]):
                continue
            candidate = scores[current] + cost
            if candidate >= scores.get(nxt, math.inf):
                continue
            scores[nxt] = candidate
            estimate = math.hypot(nx - gx, ny - gy) * CELL
            heapq.heappush(heap, (candidate + estimate, nxt))
    return None


def build_grids(rows):
    background = Image.open(os.path.join(EXT, 'worldmap_background.jpg')).convert('RGB')
    region = Image.open(os.path.join(EXT, 'region_color_overlay.png')).convert('P')
    mountain = Image.open(os.path.join(EXT, 'mountain_overlay.png')).convert('P')
    world_width, world_height = background.size
    width, height = math.ceil(world_width / CELL), math.ceil(world_height / CELL)

    river_bytes = bytearray(world_width * world_height)
    bg = background.load()
    for y in range(world_height):
        offset = y * world_width
        for x in range(world_width):
            red, green, blue = bg[x, y]
            if red >= 170 and green >= 145 and blue >= 155 and abs(red - blue) <= 55:
                river_bytes[offset + x] = 255
    river = Image.frombytes('L', background.size, bytes(river_bytes)).filter(ImageFilter.MaxFilter(3))
    rp, gp, mp = river.load(), region.load(), mountain.load()

    strict = bytearray(width * height)
    resilient = bytearray(width * height)
    partial_cells = 0
    for gy in range(height):
        y0, y1 = gy * CELL, min(world_height, (gy + 1) * CELL)
        for gx in range(width):
            x0, x1 = gx * CELL, min(world_width, (gx + 1) * CELL)
            samples = (x1 - x0) * (y1 - y0)
            clear = sum(
                bool(gp[x, y]) and mp[x, y] != 1 and not rp[x, y]
                for y in range(y0, y1) for x in range(x0, x1)
            )
            idx = gy * width + gx
            strict[idx] = clear == samples
            resilient[idx] = clear * 2 >= samples
            partial_cells += strict[idx] == 0 and resilient[idx] == 1

    node_overrides = 0
    for row in rows:
        if row['type_name'] in TRANSIT_TYPES:
            continue
        gx = max(0, min(width - 1, round(int(row['x']) / CELL)))
        gy = max(0, min(height - 1, round((world_height - int(row['y'])) / CELL)))
        idx = gy * width + gx
        if not resilient[idx]:
            node_overrides += 1
            resilient[idx] = 1
    return strict, resilient, width, height, world_height, partial_cells, node_overrides


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', type=int, default=80)
    parser.add_argument('--seed', type=int, default=7404)
    parser.add_argument('--json', help='optional report path')
    args = parser.parse_args()
    with open(os.path.join(EXT, 'clean_map_nodes.csv'), encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))

    strict, resilient, width, height, world_height, partial, overrides = build_grids(rows)
    candidates = [row for row in rows if row['type_name'] not in TRANSIT_TYPES]
    rng = random.Random(args.seed)
    pairs = []
    attempts = 0
    while len(pairs) < args.pairs and attempts < args.pairs * 1000:
        attempts += 1
        a, b = rng.sample(candidates, 2)
        direct = math.hypot(int(a['x']) - int(b['x']), int(a['y']) - int(b['y']))
        if 30 <= direct <= 220:
            pairs.append((a, b, direct))

    missing_legacy = shorter = resilient_failures = detours = 0
    examples = []
    for a, b, direct in pairs:
        old_a = nearest_cell(int(a['x']), int(a['y']), strict, width, height, world_height)
        old_b = nearest_cell(int(b['x']), int(b['y']), strict, width, height, world_height)
        new_a = nearest_cell(int(a['x']), int(a['y']), resilient, width, height, world_height)
        new_b = nearest_cell(int(b['x']), int(b['y']), resilient, width, height, world_height)
        old_distance = shortest_path(strict, width, height, old_a, old_b) if old_a is not None and old_b is not None else None
        new_distance = shortest_path(resilient, width, height, new_a, new_b) if new_a is not None and new_b is not None else None
        if new_distance is None:
            resilient_failures += 1
            continue
        if old_distance is None:
            missing_legacy += 1
        elif new_distance < old_distance * 0.9:
            shorter += 1
        ratio = new_distance / direct
        if ratio > 2.5:
            detours += 1
        if (old_distance is None or (old_distance and new_distance < old_distance * .9) or ratio > 2.5) and len(examples) < 20:
            examples.append({
                'from': [int(a['x']), int(a['y']), a['type_name'], a['place_name']],
                'to': [int(b['x']), int(b['y']), b['type_name'], b['place_name']],
                'direct': round(direct, 1),
                'legacy': None if old_distance is None else round(old_distance, 1),
                'current': round(new_distance, 1),
                'current_ratio': round(ratio, 2),
            })

    report = {
        'scope': ('Ground-only local routes; transit portals are intentionally excluded so '
                  'this isolates terrain-grid corridor loss. Unroutable or long samples may '
                  'legitimately require a bridge, crossing, harbor, dock, or tunnel.'),
        'seed': args.seed, 'pairs_tested': len(pairs),
        'grid': {'width': width, 'height': height, 'cell_size': CELL},
        'legacy_walkable_cells': sum(strict), 'current_walkable_cells': sum(resilient),
        'one_tile_corridor_cells_recovered': partial,
        'known_occupiable_node_cells_recovered': overrides,
        'legacy_routes_recovered': missing_legacy,
        'routes_shortened_over_10_percent': shorter,
        'ground_only_unroutable_samples': resilient_failures,
        'ground_only_detours_over_2_5x_direct': detours,
        'examples': examples,
    }
    print(json.dumps(report, indent=2))
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as handle:
            json.dump(report, handle, indent=2)
            handle.write('\n')


if __name__ == '__main__':
    main()
