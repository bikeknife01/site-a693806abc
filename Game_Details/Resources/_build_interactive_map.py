import csv, json, math, os, random

BASE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(BASE, '_extracted')

with open(os.path.join(EXT, 'clean_map_nodes.csv'), encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

# Per-node region name (see _build_region_data.py: computed there via a free
# raster[y][x] lookup against the same region raster used for borders/labels,
# and written parallel to clean_map_nodes.csv's row order). clean_map_nodes.csv's
# own place_name column is blank for almost every row (user-reported), so this
# fills the table's "Place Name" column with the containing region's name
# instead, falling back to it only when place_name itself is empty.
with open(os.path.join(EXT, 'node_place_names.json'), encoding='utf-8') as f:
    node_place_names = json.load(f)
assert len(node_place_names) == len(rows)

data = []
for r, region_name in zip(rows, node_place_names):
    data.append({
        'x': int(r['x']),
        'y': int(r['y']),
        'w': int(r['bbox_w']) if r['bbox_w'] else 1,
        'h': int(r['bbox_h']) if r['bbox_h'] else 1,
        't': r['type_name'],
        'c': r['type_code'],
        'v': r['variant'],
        'id': r['instance_id'],
        'n': r['place_name'] or region_name,
        'rg': region_name,  # containing region name, kept separate from 'n' (which falls back
                             # to this same value when place_name is blank) so the UI can show
                             # "Region: X" as extra context without it duplicating the title
                             # when a node has no real name of its own.
        'hn': bool(r['place_name']),  # True if this node has its own real place_name (not just
                                       # the region fallback) - lets the UI offer a "declutter"
                                       # toggle that hides the ~4700 generic same-named Ruin
                                       # dots without hiding real named landmarks.
        'lvl': r['level'],
    })

data_json = json.dumps(data, separators=(',', ':'))

# Crossing/Harbor "chain" edges (see _build_crossing_chains.py): Harbor/Dock nodes are
# the start of a strung-together series of Crossing nodes forming a sea/ford route that
# ends back on ordinary land POIs. crossing_chains.json stores each node by its 0-based
# row position in clean_map_nodes.csv (NOT instance_id - instance_id turned out to be a
# shared content/template reference rather than a unique per-placement id: only 227
# distinct values across all 7,694 rows, one repeated 780 times - using it as a dict key
# silently collapsed distinct nodes onto a single "last one wins" index and produced
# degenerate self-loop edges). Row position is stable and lines up 1:1 with `data` here
# since `data` is built by iterating the same CSV rows in the same order above, so the
# indices can be used directly with no further lookup.
with open(os.path.join(EXT, 'crossing_chains.json'), encoding='utf-8') as f:
    chain_edges = json.load(f)
assert all(0 <= a < len(data) and 0 <= b < len(data) for a, b in chain_edges)
chain_edges_json = json.dumps(chain_edges, separators=(',', ':'))

# Region/kingdom political boundaries + name labels (see _build_region_data.py).
# Boundary segments and label coordinates are stored in the SAME raw world-space
# convention as node x/y (no flip baked in), so rather than flip every one of the
# ~91.8k boundary line endpoints in Python, the boundary <path> elements are wrapped
# in an SVG group with a `translate(0,BG_H) scale(1,-1)` transform that does the
# y-flip once, at render time, for the whole layer - identical visual result to the
# per-node `cy = BG_H - d.y` flip used everywhere else, just applied as one group
# transform since path data can't be flipped after the fact per-coordinate. Text
# labels CANNOT use that trick (a scale(1,-1) on a <g> would flip the glyphs
# upside down too), so label y-coordinates are flipped explicitly below instead.
with open(os.path.join(EXT, 'region_labels.json'), encoding='utf-8') as f:
    region_labels = json.load(f)
with open(os.path.join(EXT, 'kingdom_labels.json'), encoding='utf-8') as f:
    kingdom_labels = json.load(f)


def segs_to_smooth_path(segs, jitter=False):
    # Chain the flat, unordered [x1,y1,x2,y2] unit-run segments into ordered
    # polylines, then smooth each chain before drawing it.
    #
    # WHY THIS IS NEEDED (user-reported): the raw segments are exactly
    # right-angle unit-grid boundaries (built by run-length-merging raster
    # cell edges - see _build_region_data.py), so rendering them as straight
    # M...L...L polylines produces a harsh "staircase"/blocky look. Spot-
    # checked one such straight run directly against the decoded per-cell
    # raster (region 43 vs region 1 sat on a dead-straight cut from y=1422 to
    # y=1500 at x=1300) and confirmed it's genuine per-cell data, not a
    # decode bug - the interior region/kingdom raster is just a coarse
    # rectilinear zone assignment, unlike the coastline which happens to
    # trace real organic terrain. So instead of "fixing" the data (there's
    # nothing wrong with it), this smooths the RENDERING only.
    #
    # FIRST ATTEMPT (superseded): a single quadratic-through-midpoints pass
    # (straight to mid(P0,P1), then Q through each interior Pi to
    # mid(Pi,Pi+1), then straight to Pn). This rounds each individual corner,
    # but a chain built from mostly 1-3 unit-long runs (measured: ~70% of
    # region-border segments are length 1-3 world units) has a corner every
    # couple of pixels, so rounding each corner in isolation still reads as a
    # jittery wobble rather than a smooth curve - which is exactly what the
    # user flagged as "unnatural"/"blocky" even after this pass was in place.
    #
    # CURRENT APPROACH: Chaikin corner-cutting (the standard GIS technique
    # for smoothing raster-derived boundary polylines, e.g. coastline
    # generalization). Each iteration replaces every edge (P, Q) with two new
    # points at 1/4 and 3/4 along it, which repeatedly cuts corners rather
    # than rounding them one at a time - a few iterations converges toward a
    # true quadratic B-spline through the original points, which averages
    # away short-run jitter over a wider window instead of treating each
    # corner independently. True chain ENDPOINTS (junctions where 3+ regions
    # meet, or dead ends - the only points in a chain with degree != 2, since
    # that's how chains are split below) are kept fixed and never cut, so no
    # geography is discarded or invented - only the interior wiggle between
    # fixed junctions is smoothed.
    #
    # STILL NOT ENOUGH (user-reported again, after the above was shipped):
    # Chaikin only has something to work with where a chain already zigzags
    # between several points. But plenty of region edges are a single long
    # DEAD-STRAIGHT run with no interior points at all between two junctions
    # (measured example: the x=1300 cut is one unbroken edge from y=1422 to
    # y=1500 - 78 units, zero interior vertices) - no amount of corner-cutting
    # can un-straighten a line that has no corners to cut. These long, exactly
    # tile-grid-aligned runs (x/y a multiple of the 100-unit tile size) are
    # genuine per-cell data, but they visually read as "obviously artificial"
    # precisely because they're so straight and so grid-aligned - nothing
    # organic looks like that. jitter=True (used only for the region-border
    # layer, not mountain/coast, per user feedback that it's specifically
    # region borders that look "unnatural") adds a bounded fractal midpoint
    # displacement pass BEFORE Chaikin: recursively split each long edge at
    # its midpoint, nudge that midpoint sideways (perpendicular to the edge)
    # by a random amount that shrinks each recursion level, stop once
    # sub-edges get short. This is the standard "fractal coastline" trick
    # (e.g. classic Voss/Mandelbrot midpoint-displacement) used to turn
    # blocky administrative-style data into natural-looking wiggly borders.
    # It's a cosmetic-only jitter - zero-mean (equally likely either side of
    # the true line), seeded deterministically so rebuilds are reproducible,
    # and true chain endpoints (junctions) are never moved - so it doesn't
    # relocate any region, it just breaks up dead-straight runs before they
    # reach the Chaikin pass, which then smooths the added wiggle into a
    # flowing curve instead of a ruler-straight line.
    from collections import defaultdict

    adj = defaultdict(list)
    edge_set = set()
    for x1, y1, x2, y2, *_ in segs:
        a, b = (x1, y1), (x2, y2)
        key = (a, b) if a <= b else (b, a)
        if key in edge_set:
            continue
        edge_set.add(key)
        adj[a].append(b)
        adj[b].append(a)

    def edge_key(a, b):
        return (a, b) if a <= b else (b, a)

    visited = set()
    chains = []

    # pass 1: walk chains starting from junctions/dead-ends (degree != 2)
    for start in list(adj.keys()):
        if len(adj[start]) == 2:
            continue
        for nb in adj[start]:
            ek = edge_key(start, nb)
            if ek in visited:
                continue
            visited.add(ek)
            chain = [start, nb]
            prev, cur = start, nb
            while len(adj[cur]) == 2:
                n1, n2 = adj[cur]
                nxt = n2 if n1 == prev else n1
                ek2 = edge_key(cur, nxt)
                if ek2 in visited:
                    break
                visited.add(ek2)
                chain.append(nxt)
                prev, cur = cur, nxt
            chains.append(chain)

    # pass 2: whatever's left is pure closed loops (every node degree 2)
    for start in list(adj.keys()):
        if len(adj[start]) != 2:
            continue
        for nb in adj[start]:
            ek = edge_key(start, nb)
            if ek in visited:
                continue
            visited.add(ek)
            chain = [start, nb]
            prev, cur = start, nb
            while cur != start and len(adj[cur]) == 2:
                n1, n2 = adj[cur]
                nxt = n2 if n1 == prev else n1
                ek2 = edge_key(cur, nxt)
                if ek2 in visited:
                    break
                visited.add(ek2)
                chain.append(nxt)
                prev, cur = cur, nxt
            chains.append(chain)

    def fractalize_chain(pts):
        # Insert jittered midpoints into long straight runs within one chain
        # (see comment above). Deterministic per-edge seed (derived from the
        # edge's own endpoint coordinates) so the output doesn't depend on
        # dict/set iteration order and rebuilds are reproducible byte-for-byte.
        MIN_LEN = 14          # below this, leave the edge alone - Chaikin
                               # already handles short runs fine on its own
        MAX_DEPTH = 5
        BASE_DISP = 0.22       # displacement as a fraction of edge length

        def recurse(p, q, depth):
            length = math.hypot(q[0] - p[0], q[1] - p[1])
            if length < MIN_LEN or depth >= MAX_DEPTH:
                return [p, q]
            seed = f'{p[0]:.1f},{p[1]:.1f},{q[0]:.1f},{q[1]:.1f},{depth}'
            rng = random.Random(seed)
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            nx, ny = -(q[1] - p[1]) / length, (q[0] - p[0]) / length
            disp = rng.uniform(-1, 1) * BASE_DISP * length * (0.6 ** depth)
            mx += nx * disp
            my += ny * disp
            left = recurse(p, (mx, my), depth + 1)
            right = recurse((mx, my), q, depth + 1)
            return left[:-1] + right

        out = [pts[0]]
        for i in range(len(pts) - 1):
            seg = recurse(pts[i], pts[i + 1], 0)
            out.extend(seg[1:])
        return out

    def chaikin(pts, iterations=2):
        closed = len(pts) > 2 and pts[0] == pts[-1]
        for _ in range(iterations):
            n = len(pts)
            out = []
            if closed:
                # every vertex (including the arbitrary start/close point,
                # which isn't a real feature - just where the loop walk
                # happened to begin) gets cut, then re-closed at the end.
                for i in range(n - 1):
                    p, q = pts[i], pts[(i + 1) % (n - 1)]
                    out.append((0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]))
                    out.append((0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]))
                out.append(out[0])
            else:
                # true endpoints (junctions/dead-ends) are fixed - never cut -
                # only the interior degree-2 wiggle gets smoothed.
                out.append(pts[0])
                for i in range(n - 1):
                    p, q = pts[i], pts[i + 1]
                    if i == 0:
                        out.append(p)
                    a = (0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1])
                    b = (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])
                    out.append(a)
                    out.append(b)
                out.append(pts[-1])
            pts = out
        return pts

    parts = []
    for pts in chains:
        if len(pts) < 3:
            if jitter:
                pts = fractalize_chain(pts)
            else:
                (x1, y1), (x2, y2) = pts[0], pts[-1]
                parts.append(f'M{x1} {y1}L{x2} {y2}')
                continue
        elif jitter:
            pts = fractalize_chain(pts)
        smoothed = chaikin(pts)
        d = f'M{smoothed[0][0]:.1f} {smoothed[0][1]:.1f}'
        for x, y in smoothed[1:]:
            d += f'L{x:.1f} {y:.1f}'
        parts.append(d)
    return ''.join(parts)


# _build_region_data.py writes an exact north-up transparent PNG directly
# from the game's complete region-index texture. Keeping the authoritative
# raster as an image avoids SVG polygon tracing, smoothing, and synthetic
# jitter changing the actual borders.
region_overlay_path = os.path.join(EXT, 'region_color_overlay.png')
if not os.path.exists(region_overlay_path):
    raise FileNotFoundError('run _build_region_data.py to create region_color_overlay.png')

# Routing barrier raster reconstructed from the game's explicit Mountain terrain
# fragments, joined into contiguous ranges with conservative tunnel-supported
# gap repairs (see _build_terrain_data.py).
mountain_overlay_path = os.path.join(EXT, 'mountain_overlay.png')
if not os.path.exists(mountain_overlay_path):
    raise FileNotFoundError('run _build_terrain_data.py to create mountain_overlay.png')

# Per-kingdom colored border-glow LINES were removed entirely per user request
# ("the kingdom lines are useless so lose them altogether") - the actual
# stroke-path layer is gone. Kingdom NAME labels are kept ("the names are
# fine") and still get a per-kingdom tint, so we keep just the trivial
# name->color lookup used for that text tinting.
with open(os.path.join(EXT, 'kingdom_id_to_name.json'), encoding='utf-8') as f:
    kingdom_id_to_name = json.load(f)

KINGDOM_COLORS = ['#4FC3F7', '#F06292', '#FFD54F', '#81C784', '#BA68C8',
                   '#FF8A65', '#4DB6AC', '#9575CD', '#DCE775']

kingdom_color_by_name = {
    name: KINGDOM_COLORS[i % len(KINGDOM_COLORS)]
    for i, name in enumerate(kingdom_id_to_name)
}
kingdom_colors_json = json.dumps(kingdom_color_by_name)

region_labels_json = json.dumps(region_labels, separators=(',', ':'))
kingdom_labels_json = json.dumps(kingdom_labels, separators=(',', ':'))

types = sorted({d['t'] for d in data}, key=lambda t: -sum(1 for d in data if d['t'] == t))

PALETTE = ['#4C9AFF', '#57D9A3', '#FFAB00', '#FF5630', '#998DD9', '#00B8D9',
           '#79E2F2', '#C1C7D0', '#B25FA6', '#6554C0', '#36B37E', '#FF8B00',
           '#DE350B', '#00A3BF', '#8993A4', '#403294', '#5243AA', '#008DA6']
color_map = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(types)}

# Crossing markers auto-assigned to PALETTE[2] = '#FFAB00' (amber), which sits at
# almost the same hue (~40) as the yellow-orange background tint covering most of
# the southern half of the map (Westerlands/Vale/Crownlands/Reach/Stormlands/Dorne
# all render in that warm tan/orange family - see _build_worldmap_bg.py), so the
# dots nearly vanished into the terrain there (user-reported). Overridden to a dark
# brown: same warm hue family (~30) so it still visually "belongs" with the other
# earth-toned markers, but its much lower value/saturation (0.36/0.75 vs ~0.9/0.78
# for the background) keeps it clearly readable instead of blending in.
color_map['Crossing'] = '#4A2E12'
color_json = json.dumps(color_map)

xs = [d['x'] for d in data]
ys = [d['y'] for d in data]
minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

# Real decoded world-map texture (the active campaign's WorldMap diffuse bitmap,
# ASTC-decoded), used purely as a visual backdrop. Its pixel space lines up 1:1 with the
# node x/y coordinates (confirmed by overlaying all 7,694 nodes on it and checking they
# fall on land / avoid water / cluster on roads), so it's placed at x=0,y=0 with its
# native pixel dimensions, no scaling needed.
from PIL import Image as _Image, ImageFilter as _ImageFilter
_bg_path = os.path.join(EXT, 'worldmap_background.jpg')
BG_W, BG_H = _Image.open(_bg_path).size
if _Image.open(region_overlay_path).size != (BG_W, BG_H):
    raise ValueError('region_color_overlay.png dimensions do not match worldmap_background.jpg')
if _Image.open(mountain_overlay_path).size != (BG_W, BG_H):
    raise ValueError('mountain_overlay.png dimensions do not match worldmap_background.jpg')

# Browser-side route finding uses a 2x2-world-tile navigation cell. Rivers are often
# only a few pixels wide, so the former 4x4 grid could collapse them out of existence.
# The region-index raster identifies open water, but internal rivers remain assigned
# to their surrounding region. Those rivers are the distinctive pale mauve/cyan lines
# in the aligned diffuse map, so detect them separately and dilate by one pixel to
# close anti-aliased diagonal gaps. A navigation cell is walkable when at least half
# of its source pixels are genuinely passable. Requiring all four pixels in a 2x2
# cell erased legitimate one-world-tile corridors whenever the grid happened to
# straddle a mountain edge. Requiring two pixels preserves those corridors without
# allowing an isolated passable corner to punch through a barrier. The
# mountain overlay's palette value 2 is only a light-brown inferred range
# envelope; it is useful visual context, but the game evidence does not support
# treating it as impassable. Transit
# structures are punched out here and selectively reopened in JavaScript according to
# the requested level range.
ROUTE_CELL = 2
ROUTE_W = math.ceil(BG_W / ROUTE_CELL)
ROUTE_H = math.ceil(BG_H / ROUTE_CELL)
_route_bg = _Image.open(_bg_path).convert('RGB')
_route_region = _Image.open(region_overlay_path).convert('P')
_route_mountain = _Image.open(mountain_overlay_path).convert('P')
_route_bg_px = _route_bg.load()
_route_region_px = _route_region.load()
_route_mountain_px = _route_mountain.load()

# The four broad land palettes are brown, green, tan, and orange. Their blue channel
# is either low or their red channel is below this threshold; the waterway stroke is
# consistently light and nearly neutral after the background's cosmetic shading pass.
_river_pixels = bytearray(BG_W * BG_H)
for _y in range(BG_H):
    for _x in range(BG_W):
        _r, _g, _b = _route_bg_px[_x, _y]
        if _r >= 170 and _g >= 145 and _b >= 155 and abs(_r - _b) <= 55:
            _river_pixels[_y * BG_W + _x] = 255
_route_river = _Image.frombytes('L', (BG_W, BG_H), bytes(_river_pixels)).filter(
    _ImageFilter.MaxFilter(3))
_route_river_px = _route_river.load()
route_grid = bytearray(ROUTE_W * ROUTE_H)
for gy in range(ROUTE_H):
    y0, y1 = gy * ROUTE_CELL, min(BG_H, (gy + 1) * ROUTE_CELL)
    for gx in range(ROUTE_W):
        x0, x1 = gx * ROUTE_CELL, min(BG_W, (gx + 1) * ROUTE_CELL)
        samples = (x1 - x0) * (y1 - y0)
        passable_samples = 0
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                if (_route_region_px[xx, yy]
                        and _route_mountain_px[xx, yy] != 1
                        and not _route_river_px[xx, yy]):
                    passable_samples += 1
        if passable_samples * 2 >= samples:
            route_grid[gy * ROUTE_W + gx] = 1

# Placed resources and POIs are authoritative positive evidence of an occupiable
# tile. Reopen their exact navigation cell after raster reduction; otherwise a
# one-pixel terrain disagreement can make a real level-bearing tile impossible to
# select as a route endpoint. Transit structures remain closed below and are only
# reopened when their level is eligible for the requested route.
TRANSIT_TYPES = {'Crossing', 'Tunnel', 'Bridge', 'Harbor/Dock'}
for d in data:
    if d['t'] in TRANSIT_TYPES:
        continue
    gx = max(0, min(ROUTE_W - 1, round(d['x'] / ROUTE_CELL)))
    gy = max(0, min(ROUTE_H - 1, round((BG_H - d['y']) / ROUTE_CELL)))
    route_grid[gy * ROUTE_W + gx] = 1

for d in data:
    if d['t'] not in TRANSIT_TYPES:
        continue
    gx = round(d['x'] / ROUTE_CELL)
    gy = round((BG_H - d['y']) / ROUTE_CELL)
    for yy in range(max(0, gy - 2), min(ROUTE_H, gy + 3)):
        for xx in range(max(0, gx - 2), min(ROUTE_W, gx + 3)):
            route_grid[yy * ROUTE_W + xx] = 0

# Compact alternating-value run lengths (far smaller than JSON-ing every cell).
route_runs = []
route_first = route_grid[0] if route_grid else 0
run_value = route_first
run_length = 0
for value in route_grid:
    if value == run_value:
        run_length += 1
    else:
        route_runs.append(run_length)
        run_value = value
        run_length = 1
if route_grid:
    route_runs.append(run_length)
route_runs_json = json.dumps(route_runs, separators=(',', ':'))

# Tunnels are stored as paired portal mouths rather than explicit graph edges.  The
# same conservative mutual-nearest rule used by _build_terrain_data.py recovers those
# pairs and avoids connecting unrelated nearby tunnels.
tunnel_indices = [i for i, d in enumerate(data) if d['t'] == 'Tunnel']
tunnel_edges = []
if len(tunnel_indices) > 1:
    nearest = {}
    for i in tunnel_indices:
        nearest[i] = min(
            (math.hypot(data[i]['x'] - data[j]['x'], data[i]['y'] - data[j]['y']), j)
            for j in tunnel_indices if j != i
        )
    tunnel_edges = [[i, j] for i, (distance, j) in nearest.items()
                    if i < j and nearest[j][1] == i and distance <= 20]
tunnel_edges_json = json.dumps(tunnel_edges, separators=(',', ':'))

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet">
<title>Interactive Atlas</title>
<style>
  :root { --bg:#0f1115; --panel:#171a21; --border:#2a2f3a; --text:#e7e9ee; --muted:#9aa3b2; --accent:#4C9AFF; }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; height:100%; background:var(--bg); color:var(--text); font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
  /* Three-column layout: the map is tall/portrait-shaped, so at wide viewports a
     top/bottom split around it leaves dead space on either side. Instead the two
     control panels flank the map left and right, each running the full viewport
     height - #filtersPanel (search + all filters) on the left, #sidebar (results
     table) on the right, per user request. */
  #app { display:flex; height:100vh; width:100vw; overflow:hidden; }
  /* Narrowed from an earlier 300px: Filter by Type and Filter by Territory were both
     switched from a 2-column layout to a single stacked column (see #typeList and
     #kingdomList/#regionList below) specifically so this panel could shrink further
     without clipping/cramming long type or region names. */
  #filtersPanel { width:220px; min-width:220px; background:var(--panel); border-right:1px solid var(--border); overflow-y:auto; display:flex; flex-direction:column; }
  #sidebar { width:380px; min-width:380px; background:var(--panel); border-left:1px solid var(--border); display:flex; flex-direction:column; overflow:hidden; }
  .side-section { padding:10px 12px; border-bottom:1px solid var(--border); }
  .side-section:last-child { border-bottom:none; }
  .side-section h3 { font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); margin:0 0 8px; }
  .side-section h3:not(:first-child) { margin-top:4px; }
  /* Single column (was a 2-column grid) - at the narrower panel width a second column
     left too little room for longer type names like "Great House Capital". */
  #typeList { display:flex; flex-direction:column; }
  .type-row { display:flex; align-items:flex-start; gap:6px; padding:4px 2px; cursor:pointer; border-radius:4px; min-width:0; }
  .type-row:hover { background:#20242e; }
  .type-row input[type=checkbox] { margin-top:3px; flex-shrink:0; pointer-events:none; }
  .swatch { width:12px; height:12px; border-radius:3px; flex-shrink:0; margin-top:3px; }
  .type-row .type-name { min-width:0; line-height:1.3; font-size:12px; }
  .type-row .count { color:var(--muted); font-size:11px; }
  .btn-row { display:flex; gap:6px; margin-bottom:8px; }
  .btn-row button { flex:1; min-width:0; }
  button { background:#232838; color:var(--text); border:1px solid var(--border); border-radius:5px; padding:5px 8px; font-size:12px; cursor:pointer; }
  button:hover { background:#2b3145; }
  button.primary { background:var(--accent); border-color:var(--accent); color:#08111f; font-weight:600; }
  input[type=text], input[type=number], select { width:100%; background:#0f1218; border:1px solid var(--border); color:var(--text); padding:6px 8px; border-radius:5px; font-size:12px; }
  select { cursor:pointer; }
  /* Kingdom/Region (and Level, under Filter by Type) are all multi-select checkbox
     lists using the same .type-row look as the type list above, per user request -
     replaces the old single-select <select> dropdowns. Region has ~105 entries, so
     its own list (and Kingdom's, for visual consistency) is capped to a scrollable
     box rather than growing #filtersPanel to an unusable length. */
  .facet-label { font-size:11px; color:var(--muted); margin:2px 0 4px; }
  .scroll-list { max-height:150px; overflow-y:auto; border:1px solid var(--border); border-radius:5px; padding:2px 4px; margin-bottom:4px; }
  /* Level filter now lives at the top of the right-hand #sidebar panel (above the
     table), laid out as one horizontal row instead of a stacked list - per user
     request, since it's a short fixed set of values (1-5 + None) with no per-item
     count needed there. */
  #levelBar { border-bottom:1px solid var(--border); padding:8px 12px; }
  #levelList.horizontal-list { display:flex; flex-direction:row; flex-wrap:wrap; gap:4px 10px; }
  #levelList.horizontal-list .type-row { padding:2px 2px; }
  #main { flex:1; display:flex; flex-direction:column; min-width:0; }
  #toolbar { padding:8px 12px; background:var(--panel); border-bottom:1px solid var(--border); display:flex; align-items:center; gap:10px; font-size:12px; color:var(--muted); }
  #toolbar .stat { color:var(--text); font-weight:600; }
  #mapwrap { flex:1; position:relative; overflow:hidden; background:#0b0d12; }
  svg { width:100%; height:100%; display:block; cursor:grab; }
  svg.dragging { cursor:grabbing; }
  .node-dot { stroke:#000; stroke-opacity:.6; stroke-width:1.2; cursor:pointer; }
  .node-dot:hover { stroke:#fff; stroke-width:2; }
  .node-dot.selected { stroke:#fff; stroke-width:3; }
  .chain-line { stroke:#ffffff; stroke-opacity:.85; stroke-linecap:round; pointer-events:none; }
  #mountainLayer, #regionColorLayer, #regionLabelLayer, #kingdomLabelLayer { pointer-events:none; }
  .region-label { fill:#fff; font-size:16px; font-weight:600; text-anchor:middle; opacity:.9; paint-order:stroke; stroke:#000; stroke-width:3px; stroke-linejoin:round; }
  .kingdom-label { fill:#FFD54A; font-size:44px; font-weight:800; letter-spacing:2px; text-anchor:middle; paint-order:stroke; stroke:#241a00; stroke-width:6px; stroke-linejoin:round; }
  #tooltip { position:absolute; pointer-events:none; background:#11141c; border:1px solid var(--border); padding:6px 10px; border-radius:6px; font-size:12px; display:none; z-index:5; white-space:nowrap; box-shadow:0 4px 12px rgba(0,0,0,.4); }
  #tooltip b { color:var(--accent); }
  #bottomhead { padding:8px 12px; display:flex; align-items:center; gap:10px; border-bottom:1px solid var(--border); }
  #bottomhead input { max-width:220px; }
  /* table-layout:fixed + an explicit colgroup (see HTML) keeps X/Y/Type/Lvl narrow and
     gives Place Name the rest, so the whole table fits inside #sidebar's width with no
     horizontal scrollbar - previously a fixed min-width:480px forced one even though
     #sidebar itself is only 380px wide. Long cell content wraps (word-break) instead
     of forcing the column wider. */
  table { width:100%; table-layout:fixed; border-collapse:collapse; font-size:12px; }
  thead th { position:sticky; top:0; background:#1d212b; text-align:left; padding:6px 6px; cursor:pointer; user-select:none; border-bottom:1px solid var(--border); color:var(--muted); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  thead th:hover { color:var(--text); }
  tbody td { padding:5px 6px; border-bottom:1px solid #1d212b; word-break:break-word; }
  /* X/Y are plain integers - keep them on one line instead of wrapping digit-by-digit. */
  tbody td:nth-child(1), tbody td:nth-child(2) { white-space:nowrap; }
  tbody tr:hover { background:#1c2029; cursor:pointer; }
  tbody tr.selected { background:#1a2a40; }
  #tablewrap { flex:1; overflow:auto; }
  #selectedbox { padding:8px 12px; border-top:1px solid var(--border); font-size:12px; }
  #selectedbox input { flex:1; }
  .zoom-controls { position:absolute; right:14px; bottom:14px; display:flex; flex-direction:column; gap:6px; z-index:4; }
  .zoom-controls button { width:32px; height:32px; font-size:16px; }
  .legend-note { font-size:11px; color:var(--muted); line-height:1.4; margin-top:14px; }
  #placeSearchWrap { position:relative; }
  /* Opens downward again - Find a Place now sits near the top of the tall left
     #filtersPanel, so there's plenty of room below and no clipping risk. */
  #placeResults { position:absolute; left:0; right:0; top:calc(100% + 4px); background:#1a1e28; border:1px solid var(--border); border-radius:6px; max-height:260px; overflow-y:auto; z-index:20; box-shadow:0 8px 20px rgba(0,0,0,.5); display:none; }
  #placeResults.open { display:block; }
  .place-result { padding:7px 10px; cursor:pointer; display:flex; align-items:baseline; gap:8px; border-bottom:1px solid #23283350; }
  .place-result:last-child { border-bottom:none; }
  .place-result:hover, .place-result.active { background:#232a3a; }
  .place-result .pr-name { font-size:12.5px; color:var(--text); font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .place-result .pr-sub { font-size:11px; color:var(--muted); margin-left:auto; flex-shrink:0; white-space:nowrap; }
  .place-empty { padding:8px 10px; font-size:12px; color:var(--muted); }
  #clusterPopup { position:absolute; display:none; background:#1a1e28; border:1px solid var(--border); border-radius:6px; max-height:220px; overflow-y:auto; z-index:6; box-shadow:0 8px 20px rgba(0,0,0,.5); min-width:160px; max-width:280px; }
  #clusterPopup.open { display:block; }
  #clusterPopup .place-header { padding:6px 10px; font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; border-bottom:1px solid var(--border); }
  .ping-ring { fill:none; stroke:#fff; stroke-width:2; opacity:0.9; pointer-events:none; animation: ping-anim 1.1s ease-out 5; }
  @keyframes ping-anim { from { r:6; opacity:0.95; stroke-width:3; } to { r:34; opacity:0; stroke-width:0.5; } }
  .ping-dot { fill:#fff4bf; stroke:#3a2600; stroke-width:1.5; pointer-events:none; animation:dot-pulse .85s ease-in-out infinite alternate; }
  @keyframes dot-pulse { from { opacity:.6; r:4; } to { opacity:1; r:7; } }
  .route-line { fill:none; stroke:#50e3c2; stroke-width:4; stroke-linecap:round; stroke-linejoin:round; vector-effect:non-scaling-stroke; pointer-events:none; filter:drop-shadow(0 0 3px rgba(22,126,108,.95)); }
  .route-endpoint { fill:#fff; stroke:#087d6b; stroke-width:3; vector-effect:non-scaling-stroke; pointer-events:none; }
  .route-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
  .route-grid .wide { grid-column:1 / -1; }
  .route-field label { display:block; color:var(--muted); font-size:9px; font-weight:800; letter-spacing:.09em; text-transform:uppercase; margin:0 0 5px; }
  .route-actions { display:flex; gap:7px; margin-top:9px; }
  .route-actions button { flex:1; }
  #routeSummary { min-height:16px; margin-top:9px; color:var(--muted); font-size:11px; line-height:1.45; }
  #routeSummary strong { color:#77ead3; }
  #routeSummary.error { color:#ee8a8a; }
  #routeItinerary { margin-top:10px; padding-top:9px; border-top:1px solid var(--border-soft); }
  #routeItinerary[hidden] { display:none; }
  .route-itinerary-title { margin-bottom:6px; color:#aebdc7; font-size:9px; font-weight:800; letter-spacing:.11em; text-transform:uppercase; }
  #routeStops { max-height:190px; margin:0; padding:0 0 0 24px; overflow-y:auto; scrollbar-color:#3b4c5b transparent; }
  #routeStops li { padding:0 0 5px 2px; color:var(--muted); font-size:10px; }
  .route-stop { width:100%; padding:6px 7px; border:1px solid #283a48; background:#101a23; text-align:left; }
  .route-stop:hover { background:#192834; border-color:#436073; }
  .route-stop-name { display:block; overflow:hidden; color:#e5edf1; font-size:11px; font-weight:700; text-overflow:ellipsis; white-space:nowrap; }
  .route-stop-meta { display:block; margin-top:2px; color:var(--muted); font-size:9.5px; line-height:1.35; }
  #selectedInfo { font-size:12px; line-height:1.5; margin-bottom:8px; min-height:16px; }
  #selectedInfo .si-name { font-weight:700; color:var(--text); font-size:13px; }
  #selectedInfo .si-sub { color:var(--muted); }
  #selectedInfo .si-empty { color:var(--muted); font-style:italic; }

  /* 2026 interface refresh: a restrained cartographer's workbench rather than
     three unrelated utility columns. Existing IDs stay intact so functionality
     remains reproducible from this builder. */
  :root {
    --bg:#090d12; --panel:#111821; --panel-2:#151f2a; --panel-3:#0d141c;
    --border:#263544; --border-soft:#1d2935; --text:#edf2f5; --muted:#8fa0ad;
    --accent:#d6a84f; --accent-strong:#f0c567; --accent-cool:#58b7c9;
    --danger:#d86565; --shadow:0 18px 45px rgba(0,0,0,.32);
  }
  html, body { background:var(--bg); font-family:"Segoe UI Variable","Segoe UI",system-ui,sans-serif; }
  #app { gap:0; }
  #filtersPanel { width:260px; min-width:260px; background:linear-gradient(180deg,#121b25 0%,#0e151d 100%); border-right:1px solid #304151; scrollbar-color:#3b4c5b transparent; }
  #sidebar { width:410px; min-width:410px; background:linear-gradient(180deg,#121a23 0%,#0d141c 100%); border-left:1px solid #304151; box-shadow:-12px 0 30px rgba(0,0,0,.16); }
  .brand-block { padding:20px 18px 18px; border-bottom:1px solid var(--border); background:radial-gradient(circle at 15% 0%,rgba(214,168,79,.15),transparent 46%); }
  .brand-kicker, .panel-kicker { color:var(--accent); font-size:10px; font-weight:800; letter-spacing:.18em; text-transform:uppercase; }
  .brand-block h1, .results-header h2 { margin:5px 0 3px; font-family:Georgia,"Times New Roman",serif; font-weight:600; letter-spacing:.02em; color:#f4ead8; }
  .brand-block h1 { font-size:24px; }
  .brand-block p { margin:0; color:var(--muted); font-size:12px; line-height:1.45; }
  .side-section { padding:0; border-bottom:1px solid var(--border-soft); }
  .section-toggle { width:100%;display:flex;align-items:center;justify-content:space-between;padding:15px 16px 10px;border:0;border-radius:0;background:transparent;color:#c9d4dc;font-size:10px;font-weight:800;letter-spacing:.13em;text-align:left;text-transform:uppercase; }
  .section-toggle::after { content:"▾";font-size:12px;color:#738793;transition:transform .16s ease; }
  .section-toggle:hover { background:rgba(255,255,255,.025);border-color:transparent; }
  .section-toggle:focus-visible { outline:2px solid var(--accent-cool);outline-offset:-3px; }
  .side-section.collapsed .section-toggle { padding-bottom:15px; }
  .side-section.collapsed .section-toggle::after { transform:rotate(-90deg); }
  .side-section.collapsed .section-body { display:none; }
  .section-body { padding:0 16px 15px; }
  .facet-label { color:#8496a4; text-transform:uppercase; letter-spacing:.08em; font-size:9px; font-weight:700; margin:6px 0; }
  input[type=text], input[type=number], select { background:#0a1118; border-color:#2c3c4b; border-radius:8px; padding:8px 10px; font-size:12px; transition:border-color .15s,box-shadow .15s; }
  input:focus, select:focus { outline:none; border-color:var(--accent-cool); box-shadow:0 0 0 3px rgba(88,183,201,.12); }
  button { background:#1b2733; border-color:#314352; border-radius:8px; padding:7px 10px; transition:background .15s,border-color .15s,transform .15s; }
  button:hover { background:#243443; border-color:#466074; }
  button:active { transform:translateY(1px); }
  button:focus-visible, .type-row:focus-visible { outline:2px solid var(--accent-cool); outline-offset:2px; }
  button.primary { background:var(--accent); border-color:var(--accent); color:#171109; }
  .scroll-list { max-height:210px; background:#0b1219; border-color:#263744; border-radius:8px; padding:4px; scrollbar-color:#3b4c5b transparent; }
  .type-row { padding:5px 6px; border-radius:6px; transition:background .12s,opacity .12s; }
  .type-row:hover { background:#1b2a36; }
  .type-row input[type=checkbox] { accent-color:var(--accent-cool); }
  #main { background:#070b10; }
  #toolbar { min-height:48px; padding:8px 16px; background:rgba(13,20,28,.96); border-bottom-color:#304151; letter-spacing:.01em; }
  #toolbar .map-title { color:#dce5ea; font-weight:650; }
  #toolbar .status-pill { display:inline-flex;align-items:center;gap:6px;padding:5px 9px;border:1px solid #2b3d4c;border-radius:999px;background:#111b24; }
  #toolbar .status-dot { width:6px;height:6px;border-radius:50%;background:#69c58c;box-shadow:0 0 0 3px rgba(105,197,140,.12); }
  #mapwrap { margin:10px; border:1px solid #2b3a48; border-radius:12px; box-shadow:var(--shadow); background:#080c11; }
  #mapwrap::after { content:"";position:absolute;inset:0;pointer-events:none;border-radius:11px;box-shadow:inset 0 0 45px rgba(0,0,0,.42);z-index:3; }
  .zoom-controls { right:16px;bottom:16px;gap:7px; }
  .zoom-controls button { width:36px;height:36px;background:rgba(15,24,33,.92);backdrop-filter:blur(8px);box-shadow:0 5px 18px rgba(0,0,0,.3); }
  .node-dot { transition:stroke-width .12s,filter .12s; }
  .node-dot:hover { filter:drop-shadow(0 0 5px rgba(255,255,255,.8)); }
  .node-dot.selected { stroke:var(--accent-strong);stroke-width:4;filter:drop-shadow(0 0 8px rgba(240,197,103,.95)); }
  .ping-ring { stroke:var(--accent-strong); }
  #tooltip { background:rgba(10,16,23,.96);border-color:#3a4d5d;border-radius:9px;padding:9px 11px;box-shadow:0 12px 30px rgba(0,0,0,.42);backdrop-filter:blur(8px); }
  .results-header { padding:18px 16px 13px;border-bottom:1px solid var(--border);background:radial-gradient(circle at 100% 0%,rgba(88,183,201,.11),transparent 50%); }
  .results-header h2 { font-size:21px;margin-bottom:7px; }
  .results-meta { display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:11px; }
  #levelBar { padding:10px 14px;border-bottom-color:var(--border-soft);background:#101821; }
  #levelList.horizontal-list { gap:5px; }
  #levelList.horizontal-list .type-row { padding:4px 7px;background:#17232e;border:1px solid #2a3b49;border-radius:999px; }
  #bottomhead { padding:10px 12px;border-bottom-color:var(--border-soft);background:#0f171f; }
  #bottomhead input { max-width:none; }
  #tablewrap { scrollbar-color:#3b4c5b transparent; }
  table { font-size:11.5px; }
  thead th { top:0;background:#17222c;padding:8px 6px;border-bottom-color:#344756;color:#a6b6c1; }
  tbody td { padding:7px 6px;border-bottom-color:#1b2833; }
  tbody tr { transition:background .12s,box-shadow .12s;scroll-margin:80px; }
  tbody tr:nth-child(even) { background:rgba(255,255,255,.012); }
  tbody tr:hover { background:#192631; }
  tbody tr.selected { background:linear-gradient(90deg,rgba(214,168,79,.24),rgba(88,183,201,.10));box-shadow:inset 3px 0 0 var(--accent-strong); }
  #selectedbox { padding:14px 15px 15px;border-top:1px solid #3a4c5a;background:linear-gradient(180deg,#17232d,#101820);box-shadow:0 -12px 30px rgba(0,0,0,.18); }
  #selectedInfo { min-height:40px;margin-bottom:10px; }
  #selectedInfo .si-name { color:#f4ead8;font-family:Georgia,"Times New Roman",serif;font-size:15px; }
  .coordinate-row { display:grid;grid-template-columns:1fr auto;gap:8px;align-items:end; }
  .coordinate-field label { display:block;color:var(--muted);font-size:9px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin:0 0 5px; }
  #selectedCoord { font-family:"Cascadia Mono",Consolas,monospace;font-size:13px;color:var(--accent-strong); }
  #copyBtn.copied { background:#245d43;border-color:#3e8b65;color:#e9fff4; }
  #placeResults, #clusterPopup { background:#111b24;border-color:#354858;border-radius:9px;box-shadow:0 16px 38px rgba(0,0,0,.48); }
  .layer-list { gap:4px !important;margin:0; }
  .layer-list label { width:100%;padding:6px 7px;border-radius:6px;color:#b7c5ce !important;transition:background .12s; }
  .layer-list label:hover { background:#1a2834; }
  .compact-actions { margin:-2px 0 8px; }
  .compact-actions button { padding:4px 8px;font-size:10px;text-transform:uppercase;letter-spacing:.07em;font-weight:750; }
  @media (max-width:1250px) {
    #filtersPanel { width:230px;min-width:230px; }
    #sidebar { width:360px;min-width:360px; }
    .brand-block { padding:15px 14px; }
    .brand-block h1 { font-size:21px; }
  }
</style>
</head>
<body>
<div id="app">
  <div id="filtersPanel">
    <div class="brand-block">
      <div class="brand-kicker">Strategic cartography</div>
      <h1>Westeros Atlas</h1>
      <p>Explore territories, inspect map nodes, and evaluate routes around mountain barriers.</p>
    </div>
    <div class="side-section collapsed">
      <button class="section-toggle" type="button" aria-expanded="false">Find a Place</button>
      <div class="section-body">
        <div id="placeSearchWrap">
          <input type="text" id="placeSearch" placeholder="Place, region, or 1234, 1234…" autocomplete="off">
          <div id="placeResults"></div>
        </div>
      </div>
    </div>

    <div class="side-section collapsed">
      <button class="section-toggle" type="button" aria-expanded="false">Route Calculator</button>
      <div class="section-body">
        <div class="route-grid">
          <div class="route-field wide">
            <label for="routeStart">Start coordinates</label>
            <input type="text" id="routeStart" placeholder="1234, 1234">
          </div>
          <div class="route-field wide">
            <label for="routeEnd">End coordinates</label>
            <input type="text" id="routeEnd" placeholder="(1500, 900)">
          </div>
          <div class="route-field">
            <label for="routeMinLevel">Minimum transit level</label>
            <select id="routeMinLevel"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option></select>
          </div>
          <div class="route-field">
            <label for="routeMaxLevel">Maximum transit level</label>
            <select id="routeMaxLevel"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5" selected>5</option></select>
          </div>
        </div>
        <div class="route-actions"><button id="routeCalc" class="primary" type="button">Find route</button><button id="routeClear" type="button">Clear</button></div>
        <div id="routeSummary">Uses eligible crossings, tunnels, bridges, docks, and harbors.</div>
        <div id="routeItinerary" hidden>
          <div class="route-itinerary-title">Transit itinerary</div>
          <ol id="routeStops"></ol>
        </div>
      </div>
    </div>

    <div class="side-section collapsed">
      <button class="section-toggle" type="button" aria-expanded="false">Filter by Region</button>
      <div class="section-body">
        <div class="btn-row compact-actions">
          <button id="regionAll" type="button">All</button>
          <button id="regionNone" type="button">None</button>
        </div>
        <div id="regionList" class="scroll-list"></div>
        <div class="legend-note" style="margin-top:7px;">Region colors are assigned for maximum contrast between touching territories.</div>
      </div>
    </div>

    <div class="side-section collapsed">
      <button class="section-toggle" type="button" aria-expanded="false">Filter by Type</button>
      <div class="section-body">
        <div class="btn-row compact-actions">
          <button id="typeAll" type="button">All</button>
          <button id="typeNone" type="button">None</button>
        </div>
        <div id="typeList"></div>
        <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);cursor:pointer;margin-top:8px;" title="Hides nodes with no real name of their own (mostly generic Ruin/Tunnel/Crossing dots) - keeps Castles, Settlements, and other landmarks with an actual place name.">
          <input type="checkbox" id="namedOnlyToggle"> Only named places
        </label>
      </div>
    </div>

    <div class="side-section collapsed">
      <button class="section-toggle" type="button" aria-expanded="false">Map Layers</button>
      <div class="section-body">
        <div class="btn-row layer-list" style="flex-direction:column;align-items:flex-start;gap:5px;">
          <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);cursor:pointer;">
            <input type="checkbox" id="regionBorderToggle" checked> Region colors
          </label>
          <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);cursor:pointer;" title="Dark brown is decoded impassable Mountain terrain. Faint brown is an inferred range envelope shown for geographic context and remains passable to routing.">
            <input type="checkbox" id="mountainToggle" checked> Mountain terrain
          </label>
          <div class="legend-note" style="margin:2px 7px 5px;">
            <span style="color:#5b4636;">&#9632;</span> confirmed barrier &nbsp;
            <span style="color:#9a8067;">&#9632;</span> inferred context (passable)
          </div>
          <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);cursor:pointer;">
            <input type="checkbox" id="kingdomLabelToggle"> Kingdom names
          </label>
          <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);cursor:pointer;">
            <input type="checkbox" id="regionLabelToggle" checked> Region names
          </label>
        </div>
      </div>
    </div>
  </div>

  <div id="main">
    <div id="toolbar">
      <span class="map-title">Interactive world map · Bravo</span>
      <span class="status-pill"><span class="status-dot"></span> Bravo campaign · Showing <span class="stat" id="shownCount">0</span> / TOTAL_COUNT_PLACEHOLDER nodes</span>
      <span style="margin-left:auto;">Scroll to zoom · Drag to pan · Esc to clear selection</span>
    </div>
    <div id="mapwrap">
      <svg id="svg" viewBox="VIEWBOX_PLACEHOLDER">
        <defs>
          <!-- Soft border-glow filter (see below): the in-game reference map shows
               political borders as a soft highlighted band rather than a hairline,
               so the coast/region borders are drawn twice - a wide blurred "glow"
               copy using this filter, plus a thin crisp core line on top - instead
               of a single hard stroke. stdDeviation is in world units (~1 unit per
               bg pixel), so it stays a fixed physical width on the ground
               regardless of stroke-width; it does NOT stay constant in screen
               pixels while zooming (no non-scaling-stroke equivalent exists for
               filters), but that's an acceptable tradeoff for a cosmetic
               soft-highlight effect. -->
          <filter id="borderGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="5"></feGaussianBlur>
          </filter>
        </defs>
        <image id="bgImage" href="worldmap_background.jpg" x="0" y="0" width="BG_W_PLACEHOLDER" height="BG_H_PLACEHOLDER" preserveAspectRatio="none"></image>
        <!-- Pixel-exact shading decoded from the game's region-index texture.
             The PNG is already north-up and aligned to the background. -->
        <image id="regionColorLayer" href="region_color_overlay.png" x="0" y="0"
               width="BG_W_PLACEHOLDER" height="BG_H_PLACEHOLDER"
               preserveAspectRatio="none" opacity="0.38"></image>
        <!-- Per-class PNG alpha keeps confirmed barriers prominent while inferred
             range context stays deliberately faint. -->
        <image id="mountainLayer" href="mountain_overlay.png" x="0" y="0"
               width="BG_W_PLACEHOLDER" height="BG_H_PLACEHOLDER"
               preserveAspectRatio="none"></image>
        <g id="chainLayer"></g>
        <g id="routeLayer"></g>
        <g id="dotsLayer"></g>
        <g id="pingLayer"></g>
        <g id="regionLabelLayer"></g>
        <g id="kingdomLabelLayer" style="display:none"></g>
      </svg>
      <div id="tooltip"></div>
      <div id="clusterPopup"></div>
      <div class="zoom-controls">
        <button id="zoomIn" title="Zoom in">+</button>
        <button id="zoomReset" title="Reset view">&#8634;</button>
        <button id="zoomOut" title="Zoom out">-</button>
      </div>
    </div>
  </div>

  <div id="sidebar">
    <div class="results-header">
      <div class="panel-kicker">Node explorer</div>
      <h2>Map nodes</h2>
      <div class="results-meta"><span>Select a row or marker for details</span><span id="tableInfo"></span></div>
    </div>
    <div id="levelBar">
      <div class="facet-label">Level</div>
      <div id="levelList" class="horizontal-list"></div>
    </div>
    <div id="bottomhead">
      <input type="text" id="tableFilter" placeholder="Filter visible nodes…">
      <button id="tableFilterClear" title="Clear table filter" style="margin-left:6px;">Clear</button>
    </div>
    <div id="tablewrap">
      <table>
        <colgroup>
          <col style="width:40px"><col style="width:40px"><col style="width:60px">
          <col><col style="width:32px">
        </colgroup>
        <thead><tr>
          <th data-key="x">X</th><th data-key="y">Y</th><th data-key="t">Type</th>
          <th data-key="n">Place Name</th><th data-key="lvl">Lvl</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div id="selectedbox">
      <div id="selectedInfo"><span class="si-empty">click a node, table row, or search result to select it</span></div>
      <div class="coordinate-row">
        <div class="coordinate-field">
          <label for="selectedCoord">In-game coordinates</label>
          <input type="text" id="selectedCoord" readonly placeholder="Select a node">
        </div>
        <button id="copyBtn" title="Copy coordinates in game format">Copy</button>
      </div>
    </div>
  </div>
</div>

<script>
const DATA = DATA_PLACEHOLDER;
DATA.forEach((d, i) => d.idx = i); // stable index into DATA, used to look up chain adjacency
const COLORS = COLOR_PLACEHOLDER;
const TYPES = TYPES_PLACEHOLDER;
// Harbor/Dock -> Crossing "chain" edges, as [dataIndexA, dataIndexB] pairs. Reconstructed
// from spatial proximity (see _build_crossing_chains.py) since the game's own data has no
// explicit adjacency field. Used to draw the sea/ford route a selected node belongs to.
const CHAIN_EDGES = CHAIN_EDGES_PLACEHOLDER;
const TUNNEL_EDGES = TUNNEL_EDGES_PLACEHOLDER;
const ROUTE_CELL = ROUTE_CELL_PLACEHOLDER;
const ROUTE_W = ROUTE_W_PLACEHOLDER, ROUTE_H = ROUTE_H_PLACEHOLDER;
const ROUTE_FIRST = ROUTE_FIRST_PLACEHOLDER;
const ROUTE_RUNS = ROUTE_RUNS_PLACEHOLDER;
const chainAdj = new Map();
CHAIN_EDGES.forEach(([a, b]) => {
  if (!chainAdj.has(a)) chainAdj.set(a, []);
  if (!chainAdj.has(b)) chainAdj.set(b, []);
  chainAdj.get(a).push(b);
  chainAdj.get(b).push(a);
});
const BOUNDS = { minx: MINX_PLACEHOLDER, maxx: MAXX_PLACEHOLDER, miny: MINY_PLACEHOLDER, maxy: MAXY_PLACEHOLDER };
const BG_W = BG_W_PLACEHOLDER, BG_H = BG_H_PLACEHOLDER;
const svgNS = 'http://www.w3.org/2000/svg';

// ---------- region/kingdom name labels (see _build_region_data.py) ----------
// Boundary lines themselves are static <path> elements already baked into the SVG
// markup (see build script) with a y-flip group transform; only the text labels
// need building here in JS, since a flip transform on a <g> would render text
// upside-down, so each label's y is flipped explicitly (same `BG_H - y` convention
// used for every node dot).
const REGION_LABELS = REGION_LABELS_PLACEHOLDER;
const KINGDOM_LABELS = KINGDOM_LABELS_PLACEHOLDER;
// name -> hex color (see _build_interactive_map.py) - applied to each
// kingdom's name label text so each kingdom reads as a distinct color.
const KINGDOM_COLORS = KINGDOM_COLORS_PLACEHOLDER;
const regionLabelLayer = document.getElementById('regionLabelLayer');
const kingdomLabelLayer = document.getElementById('kingdomLabelLayer');

function makeLabel(x, y, text, cls) {
  const t = document.createElementNS(svgNS, 'text');
  t.setAttribute('x', x);
  t.setAttribute('y', BG_H - y);
  t.setAttribute('class', cls);
  t.textContent = text;
  return t;
}
REGION_LABELS.forEach(r => regionLabelLayer.appendChild(makeLabel(r.x, r.y, r.name, 'region-label')));
KINGDOM_LABELS.forEach(k => {
  const el = makeLabel(k.x, k.y, k.name.toUpperCase(), 'kingdom-label');
  if (KINGDOM_COLORS[k.name]) el.style.fill = KINGDOM_COLORS[k.name];
  kingdomLabelLayer.appendChild(el);
});

// Each left-panel tool group can be collapsed independently without changing the
// active filters or clearing values inside it.
document.querySelectorAll('.section-toggle').forEach(toggle => {
  toggle.addEventListener('click', () => {
    const section = toggle.closest('.side-section');
    const collapsed = section.classList.toggle('collapsed');
    toggle.setAttribute('aria-expanded', String(!collapsed));
  });
});

document.getElementById('regionBorderToggle').onchange = (e) => {
  document.getElementById('regionColorLayer').style.display = e.target.checked ? '' : 'none';
};
document.getElementById('mountainToggle').onchange = (e) => {
  document.getElementById('mountainLayer').style.display = e.target.checked ? '' : 'none';
};
document.getElementById('kingdomLabelToggle').onchange = (e) => {
  kingdomLabelLayer.style.display = e.target.checked ? '' : 'none';
};
document.getElementById('regionLabelToggle').onchange = (e) => {
  regionLabelLayer.style.display = e.target.checked ? '' : 'none';
};

// ---------- Filter by Territory (kingdom / region dropdowns) ----------
// region_labels.json already carries each region's containing kingdom (see
// _build_region_data.py), so that mapping is reused here rather than re-derived -
// same data source REGION_LABELS/KINGDOM_LABELS already use for the map's own
// name labels.
const KINGDOM_OF_REGION = {};
REGION_LABELS.forEach(r => { KINGDOM_OF_REGION[r.name] = r.kingdom; });
const ALL_KINGDOM_NAMES = [...new Set(REGION_LABELS.map(r => r.kingdom))].sort();
const ALL_REGION_NAMES = [...new Set(REGION_LABELS.map(r => r.name))].sort();

// Kingdom and Region are independent multi-select checkbox facets (mirroring the
// Filter by Type list's own checkbox-list pattern) - both default to "everything
// checked" so neither filters anything until the user actively unchecks an entry,
// same default-on behavior as activeTypes. The two facets AND together (a node must
// pass both its kingdom's checkbox AND its own region's checkbox); replaces the old
// single-select dropdowns' one-at-a-time cascading behavior per user request for
// multi-select.
const activeKingdoms = new Set(ALL_KINGDOM_NAMES);
const activeRegions = new Set(ALL_REGION_NAMES);

function buildFacetList(containerEl, values, activeSet, opts) {
  const rowEls = new Map();
  values.forEach(v => {
    const row = document.createElement('div');
    row.className = 'type-row';
    const label = (opts && opts.label) ? opts.label(v) : v;
    if (opts && opts.title) row.title = opts.title(v);
    row.innerHTML = `<input type="checkbox" checked><span class="type-name">${label}</span>`;
    const checkbox = row.querySelector('input');
    rowEls.set(v, { row, checkbox });
    row.addEventListener('click', () => {
      if (activeSet.has(v)) activeSet.delete(v); else activeSet.add(v);
      sync(v);
      render();
    });
    containerEl.appendChild(row);
  });
  function sync(v) {
    const { row, checkbox } = rowEls.get(v);
    const on = activeSet.has(v);
    row.style.opacity = on ? '1' : '0.35';
    checkbox.checked = on;
  }
  function syncAll() { values.forEach(sync); }
  return { syncAll };
}

const regionFacet = buildFacetList(document.getElementById('regionList'), ALL_REGION_NAMES, activeRegions, { title: r => KINGDOM_OF_REGION[r] || '' });
document.getElementById('regionAll').onclick = () => {
  ALL_REGION_NAMES.forEach(name => activeRegions.add(name));
  regionFacet.syncAll();
  render();
};
document.getElementById('regionNone').onclick = () => {
  activeRegions.clear();
  regionFacet.syncAll();
  render();
};

// default view: fill #mapwrap's full height with the background image (h = BG_H
// always) and pick a width that matches #mapwrap's own aspect ratio, so the map is
// flush against the top and bottom edges with zero letterboxing on that axis - per
// user request. (A static full-image viewBox left the *height* unconstrained on wide
// windows, which was fine, but on narrower windows - where the flanking filter/results
// panels eat a bigger share of total width - width became the constraining dimension
// instead, pushing the visible image away from the top/bottom edges.) Clamped so it
// never zooms in past the real image width, and never crops below the actual node/POI
// extent even on a very narrow window.
const mapwrapRect = document.getElementById('mapwrap').getBoundingClientRect();
const containerAspect = mapwrapRect.width / (mapwrapRect.height || 1);
let vbW = BG_H * containerAspect;
vbW = Math.max(vbW, (BOUNDS.maxx - BOUNDS.minx) * 1.05);
vbW = Math.min(vbW, BG_W);
const vb = { x: (BG_W - vbW) / 2, y: 0, w: vbW, h: BG_H };

const svg = document.getElementById('svg');
svg.setAttribute('viewBox', `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);

const activeTypes = new Set(TYPES);
let selected = null;
let filtered = [];

// Display-only shortening for the (verbose, CSV-sourced) type name - the underlying
// value is still 'Settlement (Town)' everywhere (TYPES/activeTypes/COLORS/d.t all
// keep the full string, since that's what filtering keys off of) - this only swaps
// what's rendered on screen, to compress the type list and the results table's
// Type column enough to drop its scrollbar.
function typeLabel(t) { return t === 'Settlement (Town)' ? 'Town' : t; }

// ---------- sidebar type list ----------
const typeListEl = document.getElementById('typeList');
const typeRowEls = new Map(); // type -> {row, checkbox}
const counts = {};
DATA.forEach(d => counts[d.t] = (counts[d.t]||0) + 1);
TYPES.forEach(t => {
  const row = document.createElement('div');
  row.className = 'type-row';
  row.title = `${t} (${counts[t]||0})`;
  row.innerHTML = `<input type="checkbox" checked><span class="swatch" style="background:${COLORS[t]}"></span><span class="type-name">${typeLabel(t)} <span class="count">${counts[t]||0}</span></span>`;
  row.dataset.type = t;
  const checkbox = row.querySelector('input');
  typeRowEls.set(t, { row, checkbox });
  row.addEventListener('click', () => {
    if (activeTypes.has(t)) activeTypes.delete(t); else activeTypes.add(t);
    syncTypeRow(t);
    render();
  });
  typeListEl.appendChild(row);
});

function syncTypeRow(t) {
  const { row, checkbox } = typeRowEls.get(t);
  const on = activeTypes.has(t);
  row.style.opacity = on ? '1' : '0.35';
  checkbox.checked = on;
}

document.getElementById('typeAll').onclick = () => {
  TYPES.forEach(type => activeTypes.add(type));
  TYPES.forEach(syncTypeRow);
  render();
};
document.getElementById('typeNone').onclick = () => {
  activeTypes.clear();
  TYPES.forEach(syncTypeRow);
  render();
};


let namedOnly = false;
document.getElementById('namedOnlyToggle').onchange = (e) => {
  namedOnly = e.target.checked;
  render();
};

// ---------- level filter (multi-select, under Filter by Type) ----------
// '' is the "no numeric tier" bucket - 94 nodes (Seat of Power / Great House Capital /
// World Capital) have a blank level in the source CSV since those landmark types don't
// carry the same 1-5 ruin/settlement tier concept the rest of the data uses.
const levelCounts = {};
DATA.forEach(d => levelCounts[d.lvl] = (levelCounts[d.lvl]||0) + 1);
const LEVEL_VALUES = [...new Set(DATA.map(d => d.lvl))].sort((a, b) => {
  if (a === '') return 1;
  if (b === '') return -1;
  return Number(a) - Number(b);
});
function levelLabel(lvl) { return lvl === '' ? 'None' : `${lvl}`; }
function levelTitle(lvl) { return lvl === '' ? 'No Level' : `Lvl ${lvl}`; }
const activeLevels = new Set(LEVEL_VALUES);
const levelFacet = buildFacetList(document.getElementById('levelList'), LEVEL_VALUES, activeLevels, {
  label: lvl => levelLabel(lvl),
  title: lvl => `${levelTitle(lvl)} (${levelCounts[lvl]||0})`
});

// ---------- rendering ----------
let dotEls = new Map(); // data index -> circle element

function render() {
  filtered = DATA.filter(d => {
    if (!activeTypes.has(d.t)) return false;
    if (namedOnly && !d.hn) return false;
    if (!activeLevels.has(d.lvl)) return false;
    // A handful of nodes (34) have no containing region at all (d.rg === '', outside
    // every raster region) - they aren't represented by any Kingdom/Region checkbox,
    // so they're left unaffected by these two facets rather than getting silently
    // hidden by default just for lacking a territory to match against.
    const kOfNode = KINGDOM_OF_REGION[d.rg];
    if (kOfNode && !activeKingdoms.has(kOfNode)) return false;
    if (d.rg && !activeRegions.has(d.rg)) return false;
    return true;
  });
  document.getElementById('shownCount').textContent = filtered.length;
  renderMap();
  renderTable();
}

const currentScale = () => vbState.w / (svg.clientWidth || 1000);

const dotsLayer = document.getElementById('dotsLayer');
const chainLayer = document.getElementById('chainLayer');
const routeLayer = document.getElementById('routeLayer');
const pingLayer = document.getElementById('pingLayer');
// Background image / mountain shading are now always on - the toggles for these were
// removed from the UI (per user request) since they added little value; no JS needed.

// Walk the whole connected chain-network the selected node belongs to (not just its
// immediate neighbor) so a full Harbor-to-Crossing-to-...-to-landfall route is drawn.
function chainComponent(startIdx) {
  const seen = new Set([startIdx]);
  const stack = [startIdx];
  while (stack.length) {
    const u = stack.pop();
    for (const v of (chainAdj.get(u) || [])) {
      if (!seen.has(v)) { seen.add(v); stack.push(v); }
    }
  }
  return seen;
}

function renderChain() {
  chainLayer.innerHTML = '';
  if (!selected || selected.idx === undefined || !chainAdj.has(selected.idx)) return;
  const members = chainComponent(selected.idx);
  const drawn = new Set();
  members.forEach(u => {
    (chainAdj.get(u) || []).forEach(v => {
      const key = u < v ? `${u}_${v}` : `${v}_${u}`;
      if (drawn.has(key)) return;
      drawn.add(key);
      const a = DATA[u], b = DATA[v];
      const line = document.createElementNS(svgNS, 'line');
      line.setAttribute('x1', a.x); line.setAttribute('y1', BG_H - a.y);
      line.setAttribute('x2', b.x); line.setAttribute('y2', BG_H - b.y);
      line.setAttribute('class', 'chain-line');
      line.setAttribute('stroke-width', Math.max(currentScale() * 1.5, 1));
      chainLayer.appendChild(line);
    });
  });
}

// ---------- dense-cluster click picker ----------
// Many POIs sit within a handful of world-units of each other (ruin/tunnel clusters,
// city districts), which at typical zoom levels render as overlapping/touching dots -
// clicking one could easily mean the user wanted a different node hiding right behind
// it. Instead of guessing, when a click has more than one currently-visible (`filtered`)
// node within a small screen-relative radius, show a small picker list near the cursor
// instead of jumping straight to selectNode; a single match still selects immediately.
const clusterPopupEl = document.getElementById('clusterPopup');

function findNearby(d) {
  const rad = currentScale() * 10; // ~10 screen px, so the hit test scales with zoom
  return filtered.filter(o => Math.hypot(o.x - d.x, o.y - d.y) <= rad);
}

function showClusterPopup(ev, nodes) {
  const wrapRect = document.getElementById('mapwrap').getBoundingClientRect();
  clusterPopupEl.innerHTML = `<div class="place-header">${nodes.length} overlapping nodes</div>` +
    nodes.map((n, i) => `<div class="place-result" data-i="${i}"><span class="pr-name">${n.n || typeLabel(n.t)}</span><span class="pr-sub">${typeLabel(n.t)}</span></div>`).join('');
  clusterPopupEl.style.left = (ev.clientX - wrapRect.left + 10) + 'px';
  clusterPopupEl.style.top = (ev.clientY - wrapRect.top + 10) + 'px';
  clusterPopupEl.classList.add('open');
  [...clusterPopupEl.querySelectorAll('.place-result')].forEach(el => {
    // mousedown (not click) so this fires before any document-level mousedown
    // dismiss-handler would otherwise close the popup first.
    el.addEventListener('mousedown', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const n = nodes[+el.dataset.i];
      hideClusterPopup();
      selectNode(n);
    });
  });
}

function hideClusterPopup() {
  clusterPopupEl.classList.remove('open');
  clusterPopupEl.innerHTML = '';
}

function renderMap() {
  dotsLayer.innerHTML = '';
  const r = Math.max(currentScale() * 3.8, 3);
  filtered.forEach(d => {
    const c = document.createElementNS(svgNS, 'circle');
    c.setAttribute('cx', d.x);
    // Raw node y is stored in the game's native texture-space convention (row 0 = bottom),
    // which is vertically flipped relative to standard screen/SVG space (row 0 = top).
    // Confirmed via the 11 Great House Capitals: sorting by raw y put Sunspear (Dorne,
    // true south) at the lowest y and Winterfell (true north) at the highest y - the
    // exact opposite of a north-up screen. We flip only here, at draw time, so every
    // other use of d.y (tooltip, table, range-filter, coordinate box) keeps showing the
    // raw in-game coordinate the user reads off their own screenshots.
    c.setAttribute('cy', BG_H - d.y);
    c.setAttribute('r', r);
    c.setAttribute('fill', COLORS[d.t] || '#888');
    c.setAttribute('class', 'node-dot' + (selected === d ? ' selected' : ''));
    c.setAttribute('tabindex', '0');
    c.setAttribute('role', 'button');
    c.setAttribute('aria-label', `${d.n || typeLabel(d.t)}, ${d.x}, ${d.y}`);
    c.addEventListener('mousemove', (ev) => showTooltip(ev, d));
    c.addEventListener('mouseleave', hideTooltip);
    c.addEventListener('click', (ev) => {
      ev.stopPropagation();
      hideClusterPopup();
      const nearby = findNearby(d);
      if (nearby.length > 1) {
        // Select the marker that actually received the click immediately so the
        // coordinates/detail card always updates; the picker remains available
        // for choosing another marker in the same dense cluster.
        selectNode(d);
        showClusterPopup(ev, nearby);
      } else {
        selectNode(d);
      }
    });
    c.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        selectNode(d);
      }
    });
    dotsLayer.appendChild(c);
  });
  renderChain();
}

function renderTable() {
  const tbody = document.getElementById('tbody');
  const qf = document.getElementById('tableFilter').value.trim().toLowerCase();
  let rows = filtered;
  if (qf) rows = rows.filter(d => d.t.toLowerCase().includes(qf) || (d.n && d.n.toLowerCase().includes(qf)));
  const cap = 500;
  document.getElementById('tableInfo').textContent = rows.length > cap
    ? `${cap} of ${rows.length}` : `${rows.length} visible`;
  tbody.innerHTML = '';
  let visibleRows = rows.slice(0, cap);
  // A map/search selection may sit beyond the 500-row render cap or outside the
  // right-panel quick filter. Pin it into the rendered slice so selection always
  // has a corresponding visible, highlightable table row.
  if (selected && !visibleRows.includes(selected)) {
    visibleRows = [selected, ...visibleRows.slice(0, cap - 1)];
  }
  visibleRows.forEach(d => {
    const tr = document.createElement('tr');
    if (selected === d) tr.classList.add('selected');
    tr.dataset.idx = d.idx;
    tr.tabIndex = 0;
    tr.setAttribute('aria-selected', selected === d ? 'true' : 'false');
    tr.innerHTML = `<td>${d.x}</td><td>${d.y}</td><td><span class="swatch" style="background:${COLORS[d.t]};display:inline-block;margin-right:6px;width:9px;height:9px;border-radius:2px;"></span>${typeLabel(d.t)}</td><td>${d.n||''}</td><td>${d.lvl||''}</td>`;
    tr.addEventListener('click', () => selectNode(d, { flyTo: true }));
    tr.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        selectNode(d, { flyTo: true });
      }
    });
    tbody.appendChild(tr);
  });
  if (selected) {
    requestAnimationFrame(() => {
      const row = tbody.querySelector('tr.selected');
      if (row) row.scrollIntoView({ block: 'center', behavior: 'smooth' });
    });
  }
}

function renderSelectedInfo(d) {
  const box = document.getElementById('selectedInfo');
  if (!d) {
    box.innerHTML = '<span class="si-empty">click a node, table row, or search result to select it</span>';
    return;
  }
  const bits = [`<span class="si-name">${d.n || typeLabel(d.t)}</span> <span class="si-sub">- ${typeLabel(d.t)}</span>`];
  if (d.rg && d.rg !== d.n) bits.push(`<span class="si-sub">Region: ${d.rg}</span>`);
  if (d.lvl) bits.push(`<span class="si-sub">Lvl ${d.lvl}</span>`);
  box.innerHTML = bits.join('<br>');
}

function selectNode(d, opts) {
  selected = d;
  document.getElementById('selectedCoord').value = `${d.x}, ${d.y}`;
  renderSelectedInfo(d);
  renderMap();
  renderTable();
  if (opts && opts.flyTo) flyToWorld(d.x, d.y);
  showPing(d.x, d.y);
}

document.getElementById('copyBtn').onclick = () => {
  // In-game linkable coordinates are written as "(x, y)" (parens, comma+space) -
  // user asked for the copied text to match that format automatically rather
  // than the plain "x,y" shown in the read-only field, so this builds it fresh
  // from the selected node instead of just copying the field's own text.
  if (!selected) return;
  const val = `(${selected.x}, ${selected.y})`;
  const inp = document.getElementById('selectedCoord');
  const prevVal = inp.value;
  try { navigator.clipboard.writeText(val); } catch(e) {}
  inp.value = val;
  inp.select();
  try { document.execCommand('copy'); } catch(e) {}
  inp.value = prevVal;
  const btn = document.getElementById('copyBtn');
  btn.textContent = 'Copied';
  btn.classList.add('copied');
  setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 1200);
};

document.getElementById('tableFilter').oninput = renderTable;
document.getElementById('tableFilterClear').onclick = () => {
  const el = document.getElementById('tableFilter');
  el.value = '';
  renderTable();
  el.focus();
};

// Sort headers track one shared { key, asc } instead of a per-column toggle memory,
// so a small arrow glyph can be shown on whichever single column is currently driving
// the sort (switching columns always starts ascending - the common table-UX default).
const sortThs = [...document.querySelectorAll('thead th')];
sortThs.forEach(th => { th.dataset.baseLabel = th.textContent; });
let sortState = { key: null, asc: true };
function updateSortIndicators() {
  sortThs.forEach(th => {
    const arrow = th.dataset.key === sortState.key ? (sortState.asc ? ' ▲' : ' ▼') : '';
    th.textContent = th.dataset.baseLabel + arrow;
  });
}
sortThs.forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.key;
    const asc = sortState.key === key ? !sortState.asc : true;
    filtered.sort((a,b) => {
      let av = a[key], bv = b[key];
      if (key === 'id') { av = BigInt(av); bv = BigInt(bv); return asc ? (av<bv?-1:av>bv?1:0) : (av>bv?-1:av<bv?1:0); }
      if (typeof av === 'string') return asc ? av.localeCompare(bv) : bv.localeCompare(av);
      return asc ? av-bv : bv-av;
    });
    sortState = { key, asc };
    updateSortIndicators();
    renderTable();
  });
});

// ---------- tooltip ----------
const tooltip = document.getElementById('tooltip');
function showTooltip(ev, d) {
  tooltip.style.display = 'block';
  const wrapRect = document.getElementById('mapwrap').getBoundingClientRect();
  tooltip.style.left = (ev.clientX - wrapRect.left + 14) + 'px';
  tooltip.style.top = (ev.clientY - wrapRect.top + 10) + 'px';
  const nameLine = d.n ? `<b>${d.n}</b> - ${typeLabel(d.t)}` : `<b>${typeLabel(d.t)}</b>`;
  const regionLine = (d.rg && d.rg !== d.n) ? `<br><span style="color:#9aa3b2;">${d.rg}</span>` : '';
  const lvlLine = d.lvl ? `<br>static tier: level ${d.lvl}` : '';
  tooltip.innerHTML = `${nameLine}${regionLine}${lvlLine}<br>x: ${d.x}, y: ${d.y}<br>size: ${d.w}x${d.h}<br><span style="color:#9aa3b2;font-size:11px;">id: ${d.id}</span>`;
}
function hideTooltip() { tooltip.style.display = 'none'; }

// ---------- zoom & pan ----------
let vbState = { ...vb };
// renderMap() rebuilds every dot (and its 3 event listeners) from scratch via
// innerHTML='' + createElementNS for each of the `filtered` nodes - a real mousewheel
// gesture (especially high-poll-rate mice / trackpads) can fire dozens of 'wheel' events
// per second, and calling applyViewBox() -> renderMap() synchronously on *every one* of
// those was doing a full dot-layer rebuild dozens of times a second, which is what made
// wheel-zoom feel so much worse than the +/- buttons (each button click is just one
// applyViewBox() call). The viewBox attribute itself is still updated immediately on every
// call (so the background image and existing dots track the cursor with zero lag) - only
// the expensive dot rebuild is coalesced to at most once per animation frame via rAF.
let renderRAF = null;
function applyViewBox() {
  svg.setAttribute('viewBox', `${vbState.x} ${vbState.y} ${vbState.w} ${vbState.h}`);
  if (renderRAF === null) {
    renderRAF = requestAnimationFrame(() => { renderRAF = null; renderMap(); });
  }
}

function screenToSvg(clientX, clientY) {
  const rect = svg.getBoundingClientRect();
  const sx = vbState.x + (clientX - rect.left) / rect.width * vbState.w;
  const sy = vbState.y + (clientY - rect.top) / rect.height * vbState.h;
  return [sx, sy];
}

svg.addEventListener('wheel', (ev) => {
  ev.preventDefault();
  const [sx, sy] = screenToSvg(ev.clientX, ev.clientY);
  // Half the prior per-tick change (2.5% instead of 5%) for finer wheel control.
  // Max zoom-out is capped at vb.w (the dynamically-fitted default view) so the map
  // cannot be pulled beyond its fitted extent into empty space.
  const factor = ev.deltaY > 0 ? 1.025 : 1/1.025;
  const newW = Math.max(20, Math.min(vb.w, vbState.w * factor));
  const newH = newW * (vbState.h / vbState.w);
  vbState.x = sx - (sx - vbState.x) * (newW / vbState.w);
  vbState.y = sy - (sy - vbState.y) * (newH / vbState.h);
  vbState.w = newW; vbState.h = newH;
  applyViewBox();
}, { passive: false });

let dragging = false, dragStart = null, vbStart = null;
svg.addEventListener('mousedown', (ev) => {
  hideClusterPopup();
  // Marker clicks are selections, not pan gestures. Starting a drag here caused
  // mouseup to rebuild the dot layer before the marker's click event could fire.
  if (ev.target.classList && ev.target.classList.contains('node-dot')) return;
  dragging = true; svg.classList.add('dragging');
  dragStart = [ev.clientX, ev.clientY];
  vbStart = { ...vbState };
});
// Dismiss the cluster picker on any click outside it (it uses mousedown internally
// on its own rows so a pick registers before this fires and closes it first).
window.addEventListener('mousedown', (ev) => {
  if (!clusterPopupEl.contains(ev.target)) hideClusterPopup();
});

// ---------- keyboard shortcuts (+/- zoom, arrow-key pan, Escape to reset selection) ----------
// Zoom/pan keys are ignored while focus is inside any text input/select (typing "-" in
// the coordinate box or arrow keys while navigating search results shouldn't hijack the
// map camera). Escape is handled globally regardless of focus, but the place-search box's
// own keydown handler (below) calls stopPropagation() when it handles Escape itself, so
// this global fallback only ever runs when nothing more specific claimed it: close the
// cluster picker if open, else deselect the currently selected node.
window.addEventListener('keydown', (ev) => {
  if (ev.key === 'Escape') {
    if (clusterPopupEl.classList.contains('open')) { hideClusterPopup(); return; }
    if (selected) {
      selected = null;
      document.getElementById('selectedCoord').value = '';
      renderSelectedInfo(null);
      pingLayer.innerHTML = '';
      renderMap();
      renderTable();
    }
    return;
  }
  const tag = document.activeElement && document.activeElement.tagName;
  if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return; // don't hijack typing
  const panStep = vbState.w * 0.08;
  if (ev.key === '+' || ev.key === '=') { ev.preventDefault(); zoomStep(1 / 1.4); }
  else if (ev.key === '-' || ev.key === '_') { ev.preventDefault(); zoomStep(1.4); }
  else if (ev.key === 'ArrowLeft') { ev.preventDefault(); vbState.x -= panStep; applyViewBox(); }
  else if (ev.key === 'ArrowRight') { ev.preventDefault(); vbState.x += panStep; applyViewBox(); }
  else if (ev.key === 'ArrowUp') { ev.preventDefault(); vbState.y -= panStep; applyViewBox(); }
  else if (ev.key === 'ArrowDown') { ev.preventDefault(); vbState.y += panStep; applyViewBox(); }
});
window.addEventListener('mousemove', (ev) => {
  if (!dragging) return;
  const rect = svg.getBoundingClientRect();
  const dx = (ev.clientX - dragStart[0]) / rect.width * vbStart.w;
  const dy = (ev.clientY - dragStart[1]) / rect.height * vbStart.h;
  vbState.x = vbStart.x - dx;
  vbState.y = vbStart.y - dy;
  svg.setAttribute('viewBox', `${vbState.x} ${vbState.y} ${vbState.w} ${vbState.h}`);
});
window.addEventListener('mouseup', () => {
  if (dragging) { dragging = false; svg.classList.remove('dragging'); renderMap(); }
});

document.getElementById('zoomIn').onclick = () => zoomStep(1/1.4);
document.getElementById('zoomOut').onclick = () => zoomStep(1.4);
document.getElementById('zoomReset').onclick = () => { vbState = { ...vb }; applyViewBox(); };
function zoomStep(factor) {
  const cx = vbState.x + vbState.w/2, cy = vbState.y + vbState.h/2;
  // Same zoom-out cap as the wheel handler above - the +/- buttons' own per-click factor
  // (1.4) is left untouched, only the max-zoom-out limit is unified to vb.w.
  const newW = Math.max(20, Math.min(vb.w, vbState.w * factor));
  const newH = newW * (vbState.h / vbState.w);
  vbState.x = cx - newW/2; vbState.y = cy - newH/2;
  vbState.w = newW; vbState.h = newH;
  applyViewBox();
}

window.addEventListener('resize', () => applyViewBox());

// ---------- fly-to + ping highlight (used by search results and table row clicks,
// which may point at a node currently far outside the visible viewport) ----------
function flyToWorld(x, y, targetW) {
  targetW = targetW || Math.max(60, Math.min(vbState.w, 260));
  const aspect = vbState.h / vbState.w;
  const newW = targetW, newH = targetW * aspect;
  const cy = BG_H - y; // screen-space y (see cy = BG_H - d.y convention used throughout)
  vbState.x = x - newW / 2;
  vbState.y = cy - newH / 2;
  vbState.w = newW; vbState.h = newH;
  applyViewBox();
}

function showPing(x, y) {
  pingLayer.innerHTML = '';
  const dot = document.createElementNS(svgNS, 'circle');
  dot.setAttribute('cx', x);
  dot.setAttribute('cy', BG_H - y);
  dot.setAttribute('r', 4);
  dot.setAttribute('class', 'ping-dot');
  const c = document.createElementNS(svgNS, 'circle');
  c.setAttribute('cx', x);
  c.setAttribute('cy', BG_H - y);
  c.setAttribute('r', 6);
  c.setAttribute('class', 'ping-ring');
  pingLayer.appendChild(dot);
  pingLayer.appendChild(c);
  setTimeout(() => {
    if (pingLayer.contains(c)) pingLayer.removeChild(c);
    if (pingLayer.contains(dot)) pingLayer.removeChild(dot);
  }, 6000);
}

// ---------- terrain-aware route calculator ----------
// The static land/mountain grid is decoded once. Each route calculation clones it,
// reopens only transit structures inside the requested level range, then runs A* with
// eight-direction movement. Crossing/harbor chains and paired tunnel mouths are graph
// portal edges; their cost remains their real world-coordinate distance, so they do
// not make the distance estimate artificially cheap.
const ROUTE_BASE = new Uint8Array(ROUTE_W * ROUTE_H);
{
  let pos = 0, value = ROUTE_FIRST;
  for (const count of ROUTE_RUNS) {
    ROUTE_BASE.fill(value, pos, pos + count);
    pos += count;
    value = value ? 0 : 1;
  }
}
const TRANSIT_TYPES = new Set(['Crossing', 'Tunnel', 'Bridge', 'Harbor/Dock']);

function routeCellFor(d) {
  const gx = Math.max(0, Math.min(ROUTE_W - 1, Math.round(d.x / ROUTE_CELL)));
  const gy = Math.max(0, Math.min(ROUTE_H - 1, Math.round((BG_H - d.y) / ROUTE_CELL)));
  return gy * ROUTE_W + gx;
}

function buildRouteWorld(minLevel, maxLevel) {
  const passable = ROUTE_BASE.slice();
  const eligible = new Set();
  // A route cell can be reopened by more than one nearby structure. Retain every
  // responsible node so the selected path can report the exact transit points it
  // relies on, rather than guessing from markers near the finished polyline.
  const transitCells = new Map();
  DATA.forEach((d, i) => {
    if (!TRANSIT_TYPES.has(d.t)) return;
    const level = Number(d.lvl);
    if (!Number.isFinite(level) || level < minLevel || level > maxLevel) return;
    eligible.add(i);
    const center = routeCellFor(d), cy = Math.floor(center / ROUTE_W), cx = center % ROUTE_W;
    // Reopen a compact 5x5 patch at an eligible structure. For bridges this is the
    // actual pass through a narrow water barrier; crossings/harbors/tunnels also gain
    // explicit portal edges below.
    for (let y = Math.max(0, cy - 2); y <= Math.min(ROUTE_H - 1, cy + 2); y++) {
      for (let x = Math.max(0, cx - 2); x <= Math.min(ROUTE_W - 1, cx + 2); x++) {
        const cell = y * ROUTE_W + x;
        if (!ROUTE_BASE[cell]) {
          if (!transitCells.has(cell)) transitCells.set(cell, []);
          transitCells.get(cell).push(i);
        }
        passable[cell] = 1;
      }
    }
  });

  const portals = new Map();
  const portalLabels = new Map();
  const portalDetails = new Map();
  function addPortal(aData, bData, kind) {
    if (!eligible.has(aData) || !eligible.has(bData)) return;
    const a = routeCellFor(DATA[aData]), b = routeCellFor(DATA[bData]);
    if (a === b) return;
    const cost = Math.hypot(DATA[aData].x - DATA[bData].x, DATA[aData].y - DATA[bData].y);
    if (!portals.has(a)) portals.set(a, []);
    if (!portals.has(b)) portals.set(b, []);
    portals.get(a).push([b, cost]);
    portals.get(b).push([a, cost]);
    const key = `${Math.min(a,b)}:${Math.max(a,b)}`;
    portalLabels.set(key, kind);
    portalDetails.set(key, { aData, bData, kind });
  }
  CHAIN_EDGES.forEach(([a, b]) => addPortal(a, b, 'crossing/harbor'));
  TUNNEL_EDGES.forEach(([a, b]) => addPortal(a, b, 'tunnel'));
  return { passable, portals, portalLabels, portalDetails, transitCells, eligible };
}

function nearestRouteCell(x, y, passable) {
  const baseX = Math.max(0, Math.min(ROUTE_W - 1, Math.round(x / ROUTE_CELL)));
  const baseY = Math.max(0, Math.min(ROUTE_H - 1, Math.round((BG_H - y) / ROUTE_CELL)));
  // Small shoreline/rounding tolerance only; never jump an endpoint across a bay or
  // an entire mountain range just to manufacture a route.
  for (let radius = 0; radius <= 8; radius++) {
    let best = -1, bestD = Infinity;
    const y0 = Math.max(0, baseY - radius), y1 = Math.min(ROUTE_H - 1, baseY + radius);
    const x0 = Math.max(0, baseX - radius), x1 = Math.min(ROUTE_W - 1, baseX + radius);
    for (let yy = y0; yy <= y1; yy++) {
      for (let xx = x0; xx <= x1; xx++) {
        if (radius && xx !== x0 && xx !== x1 && yy !== y0 && yy !== y1) continue;
        const idx = yy * ROUTE_W + xx;
        if (!passable[idx]) continue;
        const d = Math.hypot(xx - baseX, yy - baseY);
        if (d < bestD) { bestD = d; best = idx; }
      }
    }
    if (best >= 0) return best;
  }
  return -1;
}

class MinHeap {
  constructor() { this.a = []; }
  push(item) {
    const a = this.a; a.push(item); let i = a.length - 1;
    while (i) { const p = (i - 1) >> 1; if (a[p][0] <= item[0]) break; a[i] = a[p]; i = p; }
    a[i] = item;
  }
  pop() {
    const a = this.a, root = a[0], last = a.pop();
    if (a.length) {
      let i = 0;
      while (true) {
        let child = i * 2 + 1;
        if (child >= a.length) break;
        if (child + 1 < a.length && a[child + 1][0] < a[child][0]) child++;
        if (a[child][0] >= last[0]) break;
        a[i] = a[child]; i = child;
      }
      a[i] = last;
    }
    return root;
  }
  get length() { return this.a.length; }
}

function findRoute(start, end, world) {
  const startIdx = nearestRouteCell(start.x, start.y, world.passable);
  const goalIdx = nearestRouteCell(end.x, end.y, world.passable);
  if (startIdx < 0 || goalIdx < 0) return null;
  const total = ROUTE_W * ROUTE_H;
  const score = new Float64Array(total); score.fill(Infinity);
  const parent = new Int32Array(total); parent.fill(-1);
  const closed = new Uint8Array(total);
  const goalY = Math.floor(goalIdx / ROUTE_W), goalX = goalIdx % ROUTE_W;
  const heap = new MinHeap();
  score[startIdx] = 0;
  heap.push([0, startIdx]);
  const directions = [[-1,0,ROUTE_CELL],[1,0,ROUTE_CELL],[0,-1,ROUTE_CELL],[0,1,ROUTE_CELL],
    [-1,-1,ROUTE_CELL*Math.SQRT2],[1,-1,ROUTE_CELL*Math.SQRT2],[-1,1,ROUTE_CELL*Math.SQRT2],[1,1,ROUTE_CELL*Math.SQRT2]];
  while (heap.length) {
    const [, current] = heap.pop();
    if (closed[current]) continue;
    if (current === goalIdx) break;
    closed[current] = 1;
    const cy = Math.floor(current / ROUTE_W), cx = current % ROUTE_W;
    function relax(next, cost) {
      if (closed[next]) return;
      const candidate = score[current] + cost;
      if (candidate >= score[next]) return;
      score[next] = candidate; parent[next] = current;
      const ny = Math.floor(next / ROUTE_W), nx = next % ROUTE_W;
      heap.push([candidate + Math.hypot(nx - goalX, ny - goalY) * ROUTE_CELL, next]);
    }
    for (const [dx, dy, cost] of directions) {
      const nx = cx + dx, ny = cy + dy;
      if (nx < 0 || nx >= ROUTE_W || ny < 0 || ny >= ROUTE_H) continue;
      const next = ny * ROUTE_W + nx;
      if (!world.passable[next]) continue;
      // Do not squeeze diagonally between two blocked corner cells.
      if (dx && dy && (!world.passable[cy * ROUTE_W + nx] || !world.passable[ny * ROUTE_W + cx])) continue;
      relax(next, cost);
    }
    for (const [next, cost] of (world.portals.get(current) || [])) relax(next, cost);
  }
  if (!Number.isFinite(score[goalIdx])) return null;
  const indices = [];
  for (let p = goalIdx; p >= 0; p = parent[p]) { indices.push(p); if (p === startIdx) break; }
  indices.reverse();
  const used = [];
  const stops = [];
  const seenStops = new Set();
  function addStop(dataIndex) {
    if (seenStops.has(dataIndex)) return;
    seenStops.add(dataIndex);
    stops.push(dataIndex);
  }
  indices.forEach((cell, i) => {
    if (i) {
      const a = indices[i - 1], b = cell;
      const ay = Math.floor(a / ROUTE_W), ax = a % ROUTE_W;
      const by = Math.floor(b / ROUTE_W), bx = b % ROUTE_W;
      if (Math.abs(ax - bx) > 1 || Math.abs(ay - by) > 1) {
        const key = `${Math.min(a,b)}:${Math.max(a,b)}`;
        const label = world.portalLabels.get(key);
        if (label) used.push(label);
        const detail = world.portalDetails.get(key);
        if (detail) {
          const aCell = routeCellFor(DATA[detail.aData]);
          if (aCell === a) { addStop(detail.aData); addStop(detail.bData); }
          else { addStop(detail.bData); addStop(detail.aData); }
        }
      }
    }
    // Ordinary grid movement through a cell that was blocked in the base terrain
    // means this path is using the structure whose opening made it traversable.
    (world.transitCells.get(cell) || []).forEach(addStop);
  });
  const points = [{ x:start.x, y:BG_H-start.y }];
  indices.forEach(idx => points.push({ x:(idx % ROUTE_W + .5) * ROUTE_CELL, y:(Math.floor(idx / ROUTE_W) + .5) * ROUTE_CELL }));
  points.push({ x:end.x, y:BG_H-end.y });
  const startCell = points[1], endCell = points[points.length - 2];
  const distance = score[goalIdx] + Math.hypot(points[0].x-startCell.x, points[0].y-startCell.y)
    + Math.hypot(points[points.length-1].x-endCell.x, points[points.length-1].y-endCell.y);
  return { points, distance, used:[...new Set(used)], stops };
}

function drawRoute(result) {
  routeLayer.innerHTML = '';
  const line = document.createElementNS(svgNS, 'polyline');
  line.setAttribute('points', result.points.map(p => `${p.x},${p.y}`).join(' '));
  line.setAttribute('class', 'route-line');
  routeLayer.appendChild(line);
  [result.points[0], result.points[result.points.length - 1]].forEach(p => {
    const c = document.createElementNS(svgNS, 'circle');
    c.setAttribute('cx', p.x); c.setAttribute('cy', p.y); c.setAttribute('r', 7);
    c.setAttribute('class', 'route-endpoint'); routeLayer.appendChild(c);
  });
  const xs = result.points.map(p => p.x), ys = result.points.map(p => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const aspect = vbState.h / vbState.w;
  let width = Math.max(80, (maxX - minX) * 1.16, (maxY - minY) * 1.16 / aspect);
  width = Math.min(vb.w, width);
  vbState.w = width; vbState.h = width * aspect;
  vbState.x = (minX + maxX) / 2 - vbState.w / 2;
  vbState.y = (minY + maxY) / 2 - vbState.h / 2;
  applyViewBox();
}

const routeSummaryEl = document.getElementById('routeSummary');
const routeItineraryEl = document.getElementById('routeItinerary');
const routeStopsEl = document.getElementById('routeStops');
function setRouteMessage(message, error) {
  routeSummaryEl.innerHTML = message;
  routeSummaryEl.classList.toggle('error', !!error);
}
function clearRouteItinerary() {
  routeStopsEl.innerHTML = '';
  routeItineraryEl.hidden = true;
}
function renderRouteItinerary(stops) {
  clearRouteItinerary();
  if (!stops.length) return;
  stops.forEach(dataIndex => {
    const d = DATA[dataIndex];
    const li = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'route-stop';
    const name = document.createElement('span');
    name.className = 'route-stop-name';
    name.textContent = d.hn ? d.n : (d.rg ? `${typeLabel(d.t)} · ${d.rg}` : typeLabel(d.t));
    const meta = document.createElement('span');
    meta.className = 'route-stop-meta';
    const region = d.hn && d.rg && d.rg !== d.n ? ` · ${d.rg}` : '';
    meta.textContent = `${typeLabel(d.t)} · Level ${d.lvl} · (${d.x}, ${d.y})${region}`;
    button.append(name, meta);
    button.addEventListener('click', () => selectNode(d, { zoom:true }));
    li.appendChild(button);
    routeStopsEl.appendChild(li);
  });
  routeItineraryEl.hidden = false;
}
function calculateRoute() {
  const start = parseCoordinates(document.getElementById('routeStart').value);
  const end = parseCoordinates(document.getElementById('routeEnd').value);
  if (!start || !end) { setRouteMessage('Enter two numbers in both coordinate fields.', true); return; }
  if ([start, end].some(p => p.x < 0 || p.x > BG_W || p.y < 0 || p.y > BG_H)) {
    setRouteMessage(`Coordinates must be inside 0–${BG_W} X and 0–${BG_H} Y.`, true); return;
  }
  const minLevel = Number(document.getElementById('routeMinLevel').value);
  const maxLevel = Number(document.getElementById('routeMaxLevel').value);
  if (minLevel > maxLevel) { setRouteMessage('Minimum level cannot exceed maximum level.', true); return; }
  setRouteMessage('Calculating…', false);
  requestAnimationFrame(() => {
    const result = findRoute(start, end, buildRouteWorld(minLevel, maxLevel));
    if (!result) { routeLayer.innerHTML = ''; clearRouteItinerary(); setRouteMessage('No traversable route was found with this level range.', true); return; }
    drawRoute(result);
    renderRouteItinerary(result.stops);
    const via = result.used.length ? ` · uses ${result.used.join(' and ')}` : '';
    setRouteMessage(`<strong>${Math.round(result.distance).toLocaleString()} tiles</strong> · transit levels ${minLevel}–${maxLevel}${via}<br>Estimated on a ${ROUTE_CELL}-tile navigation grid.`, false);
  });
}
document.getElementById('routeCalc').onclick = calculateRoute;
document.getElementById('routeClear').onclick = () => {
  routeLayer.innerHTML = '';
  clearRouteItinerary();
  document.getElementById('routeStart').value = '';
  document.getElementById('routeEnd').value = '';
  setRouteMessage('Uses eligible crossings, tunnels, bridges, docks, and harbors.', false);
};
['routeStart','routeEnd'].forEach(id => document.getElementById(id).addEventListener('keydown', ev => {
  if (ev.key === 'Enter') { ev.preventDefault(); calculateRoute(); }
}));

// ---------- "Find a Place" search (nodes + region names + kingdom names) ----------
// A separate, non-filtering locator: unlike the coordinate-range/type/instance-id
// filters above (which hide non-matching dots), this searches by name across every
// named thing on the map and, on pick, pans/zooms the camera to it directly -
// added because with 7,694 nodes scattered across a 2080x3312 world, scrolling the
// 500-row-capped table or panning by hand to find one specific place ("where's
// Winterfell?") was impractical.
// Only nodes with a REAL own name (d.hn) are indexed here - most nodes have a blank
// place_name and 'n' falls back to their containing region's name (see the 'n'/'rg'/'hn'
// fields built in Python), so indexing every node by 'n' would flood results for a
// popular region (e.g. "Winterfell") with dozens of unrelated generic Ruin/Tunnel dots
// that just happen to sit inside it - the region entry below already covers "jump to
// that region", so this keeps search results meaning "an actual named landmark".
const SEARCH_INDEX = [];
DATA.forEach((d, i) => { if (d.hn) SEARCH_INDEX.push({ name: d.n, sub: typeLabel(d.t), x: d.x, y: d.y, idx: i }); });
REGION_LABELS.forEach(r => { if (r.name) SEARCH_INDEX.push({ name: r.name, sub: 'Region', x: r.x, y: r.y }); });
KINGDOM_LABELS.forEach(k => { if (k.name) SEARCH_INDEX.push({ name: k.name, sub: 'Kingdom', x: k.x, y: k.y }); });

const placeSearchEl = document.getElementById('placeSearch');
const placeResultsEl = document.getElementById('placeResults');
let searchMatches = [];
let searchActiveIdx = -1;

function parseCoordinates(value) {
  const matches = String(value).match(/[-+]?(?:\\d+(?:\\.\\d+)?|\\.\\d+)/g);
  if (!matches || matches.length < 2) return null;
  const x = Number(matches[0]), y = Number(matches[1]);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
  return { x, y };
}

function runSearch(q) {
  q = q.trim();
  if (!q) { searchMatches = []; return; }
  const coord = parseCoordinates(q);
  const coordinateMatches = coord && coord.x >= 0 && coord.x <= BG_W && coord.y >= 0 && coord.y <= BG_H
    ? [{ name: `(${coord.x}, ${coord.y})`, sub: 'Coordinates', x: coord.x, y: coord.y, coordinate: true }]
    : [];
  q = q.toLowerCase();
  const starts = [], contains = [];
  for (const item of SEARCH_INDEX) {
    const nl = item.name.toLowerCase();
    const p = nl.indexOf(q);
    if (p === 0) starts.push(item); else if (p > 0) contains.push(item);
  }
  const cmp = (a, b) => a.name.length - b.name.length;
  starts.sort(cmp); contains.sort(cmp);
  searchMatches = coordinateMatches.concat(starts, contains).slice(0, 12);
}

function renderSearchResults() {
  if (!searchMatches.length) {
    placeResultsEl.innerHTML = placeSearchEl.value.trim() ? '<div class="place-empty">no matches</div>' : '';
    placeResultsEl.classList.toggle('open', !!placeSearchEl.value.trim());
    return;
  }
  placeResultsEl.innerHTML = searchMatches.map((m, i) =>
    `<div class="place-result${i === searchActiveIdx ? ' active' : ''}" data-i="${i}">` +
    `<span class="pr-name">${m.name}</span><span class="pr-sub">${m.sub}</span></div>`
  ).join('');
  placeResultsEl.classList.add('open');
  [...placeResultsEl.children].forEach(el => {
    el.addEventListener('mousedown', (ev) => { ev.preventDefault(); pickSearchResult(parseInt(el.dataset.i, 10)); });
  });
}

function pickSearchResult(i) {
  const m = searchMatches[i];
  if (!m) return;
  placeSearchEl.value = m.name;
  placeResultsEl.classList.remove('open');
  searchActiveIdx = -1;
  flyToWorld(m.x, m.y, 220);
  showPing(m.x, m.y);
  if (m.idx !== undefined) selectNode(DATA[m.idx]);
}

placeSearchEl.addEventListener('input', () => {
  searchActiveIdx = -1;
  runSearch(placeSearchEl.value);
  renderSearchResults();
});
placeSearchEl.addEventListener('keydown', (ev) => {
  if (ev.key === 'ArrowDown') {
    ev.preventDefault();
    if (searchMatches.length) { searchActiveIdx = (searchActiveIdx + 1) % searchMatches.length; renderSearchResults(); }
  } else if (ev.key === 'ArrowUp') {
    ev.preventDefault();
    if (searchMatches.length) { searchActiveIdx = (searchActiveIdx - 1 + searchMatches.length) % searchMatches.length; renderSearchResults(); }
  } else if (ev.key === 'Enter') {
    ev.preventDefault();
    pickSearchResult(searchActiveIdx >= 0 ? searchActiveIdx : 0);
  } else if (ev.key === 'Escape') {
    ev.stopPropagation(); // keep this Escape scoped to "clear the search box", not also deselect the map node
    placeSearchEl.value = '';
    searchMatches = [];
    placeResultsEl.classList.remove('open');
    placeSearchEl.blur();
  }
});
placeSearchEl.addEventListener('focus', () => { if (placeSearchEl.value.trim()) renderSearchResults(); });
placeSearchEl.addEventListener('blur', () => { placeResultsEl.classList.remove('open'); });

render();
</script>
</body>
</html>
"""

html = html.replace('DATA_PLACEHOLDER', data_json)
html = html.replace('COLOR_PLACEHOLDER', color_json)
html = html.replace('CHAIN_EDGES_PLACEHOLDER', chain_edges_json)
html = html.replace('TUNNEL_EDGES_PLACEHOLDER', tunnel_edges_json)
html = html.replace('ROUTE_CELL_PLACEHOLDER', str(ROUTE_CELL))
html = html.replace('ROUTE_W_PLACEHOLDER', str(ROUTE_W)).replace('ROUTE_H_PLACEHOLDER', str(ROUTE_H))
html = html.replace('ROUTE_FIRST_PLACEHOLDER', str(route_first))
html = html.replace('ROUTE_RUNS_PLACEHOLDER', route_runs_json)
html = html.replace('REGION_LABELS_PLACEHOLDER', region_labels_json)
html = html.replace('KINGDOM_LABELS_PLACEHOLDER', kingdom_labels_json)
html = html.replace('KINGDOM_COLORS_PLACEHOLDER', kingdom_colors_json)
html = html.replace('TYPES_PLACEHOLDER', json.dumps(types))
html = html.replace('MINX_PLACEHOLDER', str(minx)).replace('MAXX_PLACEHOLDER', str(maxx))
html = html.replace('MINY_PLACEHOLDER', str(miny)).replace('MAXY_PLACEHOLDER', str(maxy))
html = html.replace('VIEWBOX_PLACEHOLDER', f'0 0 {BG_W} {BG_H}')
html = html.replace('TOTAL_COUNT_PLACEHOLDER', str(len(data)))
html = html.replace('BG_W_PLACEHOLDER', str(BG_W)).replace('BG_H_PLACEHOLDER', str(BG_H))

outpath = os.path.join(EXT, 'interactive_map.html')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(html)

print('wrote', outpath, 'size_kb=', round(os.path.getsize(outpath)/1024, 1))
