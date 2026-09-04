"""Build the interactive map's routing-oriented mountain barrier layer.

TerrainDataTable explicitly classifies mountain mesh fragments. Those fragments
trace the game's irregular ridge networks, but they are often separated by small
gaps or form hollow contours. This builder joins only nearby fragments, fills
closed mountain interiors, removes small unsupported decorative fragments, and
uses tunnel pairs only to bridge a missing section that can attach to decoded
mountain geometry.

The resource raster is deliberately not inverted: it records placed resources,
not every level-bearing/occupiable tile, and treating each zero as a mountain
creates false speckles across open plains.
"""
import csv
import glob
import json
import math
import os
from collections import deque

from PIL import Image, ImageDraw, ImageFilter
from _pbdump import dump_file
from _build_region_data import (
    parse_top_level, decode_tile_raster, load_region_index_texture, resolve_hash,
)

BASE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(BASE, '_extracted')
MOUNTAIN_CONFIRMED_COLOR = '#5b4636'
# Visual context only. Palette index 2 must remain distinct from the confirmed
# index 1 because the route builder deliberately treats this inferred envelope
# as passable terrain.
MOUNTAIN_DERIVED_COLOR = '#7a583b'


def load_terrain_category_names():
    """Return {terrain asset key: Default/Coast/Mountain/...}."""
    path = next(iter(glob.glob(os.path.join(BASE, 'TerrainDataTable.*.pb'))), None)
    if not path:
        raise FileNotFoundError('TerrainDataTable.*.pb')
    result = {}
    for row in dump_file(path).get('1', []):
        inner = row.get('2', {})
        if isinstance(inner, dict) and inner.get('1'):
            result[inner['1']] = inner.get('11')
    return result


def load_terrain_tiles(name_to_category):
    """Decode terrain rasters to category strings at world-cell resolution."""
    tiles = []
    pattern = os.path.join(BASE, 'Westeros_Alpha_6_Terrain_Array2DPacked_*.pb')
    for filename in sorted(glob.glob(pattern)):
        with open(filename, 'rb') as f:
            top = parse_top_level(f.read())
        x0 = top.get(1, [0])[0]
        y0 = top.get(2, [0])[0]
        width = top.get(3, [100])[0]
        height = top.get(4, [100])[0]

        slot_to_key = {}
        for position, raw in enumerate(top.get(7, [])):
            sub = parse_top_level(raw) if raw else {}
            slot = sub.get(1, [position])[0]
            slot_to_key[slot] = resolve_hash(sub.get(2, [None])[0])

        local_to_category = {0: None}
        for raw in top.get(9, []):
            sub = parse_top_level(raw) if raw else {}
            local_index = sub.get(1, [0])[0]
            inner_raw = sub.get(2, [b''])[0]
            inner = parse_top_level(inner_raw) if inner_raw else {}
            slot = inner.get(1, [None])[0]
            local_to_category[local_index] = name_to_category.get(slot_to_key.get(slot))

        raster = decode_tile_raster(top.get(10, [b''])[0], width, height)
        categories = [[local_to_category.get(value) for value in row] for row in raster]
        tiles.append((x0, y0, width, height, categories))
    return tiles


def extract_boundaries(mask, max_x, max_y):
    """Run-merge unit edges separating mountain and non-mountain cells."""
    segments = []
    for x in range(max_x - 1):
        run_start = None
        for y in range(max_y):
            edge = mask[y * max_x + x] != mask[y * max_x + x + 1]
            if edge and run_start is None:
                run_start = y
            elif not edge and run_start is not None:
                segments.append([x + 1, run_start, x + 1, y, 0])
                run_start = None
        if run_start is not None:
            segments.append([x + 1, run_start, x + 1, max_y, 0])
    for y in range(max_y - 1):
        run_start = None
        row0 = y * max_x
        row1 = (y + 1) * max_x
        for x in range(max_x):
            edge = mask[row0 + x] != mask[row1 + x]
            if edge and run_start is None:
                run_start = x
            elif not edge and run_start is not None:
                segments.append([run_start, y + 1, x, y + 1, 0])
                run_start = None
        if run_start is not None:
            segments.append([run_start, y + 1, max_x, y + 1, 0])
    return segments


def main():
    region_raster, max_x, max_y = load_region_index_texture()
    total = max_x * max_y
    # 0=no terrain evidence, 1=land/default, 2=coast, 3=shipped mountain.
    terrain = bytearray(total)
    terrain_tiles = load_terrain_tiles(load_terrain_category_names())
    terrain_code = {'Default': 1, 'Coast': 2, 'Mountain': 3}
    for x0, y0, width, height, grid in terrain_tiles:
        for local_y, row in enumerate(grid):
            y = y0 + local_y
            if not 0 <= y < max_y:
                continue
            offset = y * max_x
            for local_x, category in enumerate(row):
                x = x0 + local_x
                code = terrain_code.get(category, 0)
                if code and 0 <= x < max_x:
                    terrain[offset + x] = code

    # The resource raster describes placed resource content, not a complete
    # walkability/occupancy classification. Its zero-valued cells must therefore
    # never be inverted into mountains: doing so creates isolated speckles across
    # otherwise-open plains. Start strictly with the game's Mountain category.
    exact_mask = bytearray(1 if value == 3 else 0 for value in terrain)

    # Mountain assets describe many adjacent ridge/face fragments. Join only
    # fragments separated by a few cells, then fill closed interiors. This turns
    # the shipped fragments into irregular contiguous ranges without inventing
    # isolated barriers in unrelated open terrain.
    exact_image = Image.frombytes(
        'L', (max_x, max_y), bytes(255 if value else 0 for value in exact_mask))
    range_image = exact_image.filter(ImageFilter.MaxFilter(13))
    range_image = range_image.filter(ImageFilter.MinFilter(7))

    # Flood the exterior background. Any zero-valued area not reached from an
    # image corner is enclosed by a mountain contour and belongs to that range.
    flood = range_image.copy()
    for seed in ((0, 0), (max_x - 1, 0), (0, max_y - 1), (max_x - 1, max_y - 1)):
        ImageDraw.floodfill(flood, seed, 128)
    flood_pixels = flood.tobytes()

    with open(os.path.join(EXT, 'clean_map_nodes.csv'), encoding='utf-8') as f:
        node_rows = list(csv.DictReader(f))
    tunnels = [(int(row['x']), int(row['y'])) for row in node_rows
               if row['type_name'] == 'Tunnel']

    # Remove isolated decorative fragments. Preserve any component close to a
    # tunnel because it is routing-relevant even when its visible area is small.
    candidate = bytearray(value != 128 for value in flood_pixels)
    protected = bytearray(total)
    for x, y in tunnels:
        for yy in range(max(0, y - 8), min(max_y, y + 9)):
            start = yy * max_x + max(0, x - 8)
            end = yy * max_x + min(max_x, x + 9)
            protected[start:end] = b'\x01' * (end - start)

    kept = bytearray(total)
    components_kept = components_removed = 0
    for start, value in enumerate(candidate):
        if value != 1:
            continue
        candidate[start] = 2
        queue = deque([start])
        component = []
        is_protected = False
        while queue:
            current = queue.popleft()
            component.append(current)
            is_protected = is_protected or bool(protected[current])
            y, x = divmod(current, max_x)
            for yy in range(max(0, y - 1), min(max_y, y + 2)):
                first = yy * max_x + max(0, x - 1)
                last = yy * max_x + min(max_x, x + 2)
                for neighbor in range(first, last):
                    if candidate[neighbor] == 1:
                        candidate[neighbor] = 2
                        queue.append(neighbor)
        if len(component) >= 500 or (is_protected and len(component) >= 120):
            components_kept += 1
            for index in component:
                kept[index] = 1
        else:
            components_removed += 1

    # A mutual-nearest tunnel pair is strong evidence of a ridge crossing. Add a
    # short, gently irregular perpendicular range only where the terrain raster
    # has no nearby mountain signal (usually an absent terrain chunk).
    nearest = []
    for i, (x, y) in enumerate(tunnels):
        nearest.append(min(
            (math.hypot(x - ox, y - oy), j)
            for j, (ox, oy) in enumerate(tunnels) if j != i))
    tunnel_pairs = [
        (tunnels[i], tunnels[j])
        for i, (distance, j) in enumerate(nearest)
        if i < j and nearest[j][1] == i and distance <= 20
    ]

    def has_kept_mountain_near(x, y, radius=8):
        for yy in range(max(0, y - radius), min(max_y, y + radius + 1)):
            start = yy * max_x + max(0, x - radius)
            end = yy * max_x + min(max_x, x + radius + 1)
            if any(kept[start:end]):
                return True
        return False

    def nearest_kept_mountain(x, y, radius=45):
        best = None
        best_distance = radius + 1
        for yy in range(max(0, round(y) - radius), min(max_y, round(y) + radius + 1)):
            start = yy * max_x
            for xx in range(max(0, round(x) - radius), min(max_x, round(x) + radius + 1)):
                if not kept[start + xx]:
                    continue
                distance = math.hypot(xx - x, yy - y)
                if distance < best_distance:
                    best_distance = distance
                    best = (xx, yy)
        return best

    inferred_image = Image.new('L', (max_x, max_y), 0)
    inferred_draw = ImageDraw.Draw(inferred_image)
    inferred_pairs = 0
    for (x1, y1), (x2, y2) in tunnel_pairs:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if has_kept_mountain_near(round(mx), round(my)):
            continue
        dx, dy = x2 - x1, y2 - y1
        distance = math.hypot(dx, dy)
        if not distance:
            continue
        along_x, along_y = dx / distance, dy / distance
        across_x, across_y = -along_y, along_x
        half_span = 26
        endpoint_a = (mx - across_x * half_span, my - across_y * half_span)
        endpoint_b = (mx + across_x * half_span, my + across_y * half_span)
        attach_a = nearest_kept_mountain(*endpoint_a)
        attach_b = nearest_kept_mountain(*endpoint_b)
        # A floating stroke is not a mountain range. If neither end can attach
        # to decoded mountain geometry, leave this tunnel pair unclassified.
        if not attach_a and not attach_b:
            continue
        endpoint_a = attach_a or endpoint_a
        endpoint_b = attach_b or endpoint_b
        # Deterministic bends avoid synthetic ruler-straight barrier strokes.
        bend = ((x1 * 17 + y1 * 31 + x2 * 7 + y2 * 13) % 7) - 3
        points = []
        for fraction, curve in ((0, 0), (0.25, bend), (0.5, -bend),
                                (0.75, bend / 2), (1, 0)):
            points.append((
                endpoint_a[0] + (endpoint_b[0] - endpoint_a[0]) * fraction + along_x * curve,
                endpoint_a[1] + (endpoint_b[1] - endpoint_a[1]) * fraction + along_y * curve,
            ))
        inferred_draw.line(points, fill=255, width=max(8, round(distance + 3)), joint='curve')
        inferred_pairs += 1

    inferred_pixels = inferred_image.tobytes()
    mask = bytearray(total)
    confirmed = derived = 0
    for i, exact in enumerate(exact_mask):
        if kept[i] and exact:
            mask[i] = 1
            confirmed += 1
        elif kept[i]:
            mask[i] = 2
            derived += 1
        elif inferred_pixels[i]:
            y, x = divmod(i, max_x)
            # Region code zero is open water. A two-cell neighborhood tolerates
            # the narrow zero seams used by some political borders.
            is_land = any(
                region_raster[yy][xx] != 0
                for yy in range(max(0, y - 2), min(max_y, y + 3))
                for xx in range(max(0, x - 2), min(max_x, x + 3))
            )
            if is_land:
                mask[i] = 2
                derived += 1

    # Flip raw game y to the north-up image convention used by the map SVG.
    pixels = bytearray(total)
    for y in range(max_y):
        source = y * max_x
        destination = (max_y - 1 - y) * max_x
        pixels[destination:destination + max_x] = mask[source:source + max_x]
    overlay = Image.frombytes('P', (max_x, max_y), bytes(pixels))
    palette = [0, 0, 0]
    for color in (MOUNTAIN_CONFIRMED_COLOR, MOUNTAIN_DERIVED_COLOR):
        palette.extend(int(color[i:i + 2], 16) for i in (1, 3, 5))
    palette.extend([0] * (768 - len(palette)))
    overlay.putpalette(palette)
    overlay.info['transparency'] = 0
    overlay.save(os.path.join(EXT, 'mountain_overlay.png'), optimize=True)

    segments = extract_boundaries(mask, max_x, max_y)
    with open(os.path.join(EXT, 'mountain_boundaries.json'), 'w', encoding='utf-8') as f:
        json.dump(segments, f, separators=(',', ':'))

    print(f'world raster: {max_x}x{max_y}')
    print(f'mountain barriers: {confirmed:,} shipped + {derived:,} connected/inferred')
    print(f'range components: {components_kept} kept, {components_removed} tiny fragments removed')
    print(f'tunnel-supported missing ridges: {inferred_pairs}')
    print(f'mountain boundary segments: {len(segments):,}')
    print('wrote', os.path.join(EXT, 'mountain_overlay.png'))
    print('wrote', os.path.join(EXT, 'mountain_boundaries.json'))


if __name__ == '__main__':
    main()
