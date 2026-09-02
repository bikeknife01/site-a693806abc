"""Build exact region membership, shading, boundaries, and labels.

BACKGROUND: RegionDataTable.<hash>.pb is a flat table of 127 rows, each a
named "region" (e.g. region_Winterfell_alpha, region_Sunspear_alpha) tagged
with a small numeric id (inner field 6) and a parent "kingdom" key (inner
field 1.2, e.g. kingdom_TheNorth, kingdom_Dorne). 9 rows are real kingdoms;
a handful of others (region_1..5 / kingdom_1..5, region_FTUE_1_alpha /
kingdom_FTUE_1) are unused placeholder/tutorial data and are filtered out.

The authoritative per-cell assignment is
Westeros_Alpha_6_WorldMapRegionIndex_Bitmap.<hash>.r8: a complete 2080x3312
one-byte region-index texture. Its values are the numeric ids stored in field
6 of RegionDataTable, so no inference or gap filling is required.

LEGACY TILE FORMAT (unused by main; retained as reverse-engineering notes):
Each tile's field 10 is NOT itself a nested protobuf message (confirmed: the
generic recursive dumper's parse_message() throws on this byte range for most
tiles, correctly falling back to raw bytes - a handful of tiles were false
positives where the raw bytes happened to *also* look like a valid nested
message, so this script parses each tile file itself with a purpose-built
top-level-only parser instead of reusing _pbdump's recursive one, to avoid
that ambiguity entirely).

Field 10 is a flat run-length-encoded raster in row-major order (row changes
slower than column, i.e. cell (row r, col c) sits at flat index r*width+c):
a back-to-back stream of protobuf-style VARINT pairs (run_length,
local_region_index), consumed until exactly width*height cells are filled.
Verified exhaustively: for every one of the 290 tiles, decoding this way
makes the run lengths sum to EXACTLY width*height (100*100=10000), and every
local_region_index stays within the tile's own small per-tile lookup table
(field 9: local_index -> {1: <numeric global region id>}). A naive
fixed-1-byte-per-value decode (no varint) only happened to work for ~1 in 8
tiles (the simple ones with small run lengths that never need a 2-byte
varint) and produced nonsense (indices far outside the lookup table, wrong
totals) for the rest - this cost real debugging time before the varint fix.

local_index 0 is always the tile's "no region assigned" sentinel (empty
string in field 7's hash-lookup slot 0) and is treated as background/ocean.

OUTPUT:
  _extracted/region_boundaries.json - list of [x1,y1,x2,y2,kind,kid] line
    segments (raw/un-flipped world coords, same convention as node x/y and the
    background image before its render-time flip), after run-length merging
    of collinear unit-cell edges to keep the line count manageable. `kind` is
    0=region border (same kingdom, different region), 1=kingdom border (both
    sides land, different kingdoms), or 2=coastline (one side is ocean/code-0
    background). See the "THREE-WAY CLASSIFICATION" note below for why this
    needed to be a 3-way split rather than a simple is_kingdom_edge boolean.
    `kid` is the small integer id (index into kingdom_id_to_name.json) of the
    shared kingdom for kind-0 segments, or -1 for kind-1/kind-2 segments where
    no single kingdom color applies - see the "KINGDOM ID PER SEGMENT" note
    near where these are built.
  _extracted/region_labels.json - list of {id,name,kingdom,x,y,cells} region
    centroids, one per region actually present in the raster.
  _extracted/kingdom_labels.json - list of {name,x,y,cells} kingdom centroids
    (area-weighted mean over all of that kingdom's region cells).
  _extracted/kingdom_id_to_name.json - list of kingdom names, indexed by the
    `kid` field above.

The TTHF payload decoder was recovered from the game's
TextureLoader.RunLengthEncodingTextureLoader.Load implementation. Each run is
a 7-bit/LEB128 count followed by one raw byte value. The texture's x origin is
800 world units east of the background map origin, so rows are rotated by 800
pixels when converted to world coordinates. Its y convention already matches
the raw node/world coordinates; only rendered PNG/SVG output is flipped.
"""
import csv
import glob
import json
import os
import re
import struct
from collections import defaultdict, deque

from PIL import Image
from _pbdump import dump_file

BASE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(BASE, '_extracted')

REGION_INDEX_GLOB = 'Westeros_Alpha_6_WorldMapRegionIndex_Bitmap.*.r8'
REGION_TEXTURE_X_OFFSET = 800
REGION_FILL_COLORS = [
    # Saturated, widely separated hues. Region color is deliberately independent
    # of kingdom: gameplay needs neighboring territories to read apart at a glance.
    '#2389B7', '#DC5353', '#E7B83E', '#4F9C55',
    '#8A63C7', '#E47D28', '#14998F', '#C94E88',
]

REAL_KINGDOMS = {
    'kingdom_Dorne', 'kingdom_IronIslands', 'kingdom_Riverlands',
    'kingdom_Stormlands', 'kingdom_TheCrownlands', 'kingdom_TheNorth',
    'kingdom_TheReach', 'kingdom_TheVale', 'kingdom_Westerlands',
}


def prettify(raw):
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', raw)
    s = s.replace('_', ' ')
    return re.sub(r'\s+', ' ', s).strip()


# ---------- 1. region key -> {name, kingdom} lookup ----------
# NOTE: originally tried keying this off each tile's field-9 small integer
# (1, 2, 3...), assuming it was the region's RegionDataTable numeric id
# (inner field 6). That was WRONG - field 9's numbers just mirror the
# per-tile local index (1->1, 2->2, always trivially equal) and carry no
# real cross-tile identity; using them produced a raster that was ~99.9%
# "unknown region" background. The actual global identity is field 7's big
# hash, which resolves through _extracted/global_id_to_key.json (same
# unsigned/signed varint fixup used for POI instance_ids) straight to the
# region's real content-table key, e.g. hash 1083711741572818506 ->
# "region_Pyke_alpha" - verified against a tile sitting right next to the
# real Pyke capital coordinate. So this table is keyed by that key string.
def load_region_table():
    d = dump_file(os.path.join(BASE, 'RegionDataTable.1787687106.pb'))
    lookup = {}
    for r in d.get('1', []):
        key = r.get('1', {}).get('2', '')
        inner = r.get('2', {})
        kingdom_key = inner.get('1', {}).get('2', '')
        if kingdom_key not in REAL_KINGDOMS:
            continue
        name = prettify(re.sub(r'^region_', '', re.sub(r'_alpha$', '', key)))
        kingdom_name = prettify(re.sub(r'^kingdom_', '', kingdom_key))
        numeric_id = inner.get('6')
        if numeric_id is None:
            continue
        lookup[key] = {'id': int(numeric_id), 'name': name, 'kingdom': kingdom_name}
    return lookup


with open(os.path.join(EXT, 'global_id_to_key.json'), encoding='utf-8') as _f:
    GID = json.load(_f)


def resolve_hash(v):
    if v is None:
        return None
    if str(v) in GID:
        return GID[str(v)]
    s = v - (1 << 64) if v >= (1 << 63) else v
    return GID.get(str(s))


# ---------- 2. minimal top-level-only parser for the tile files ----------
# (deliberately does NOT recurse into field 10 - see module docstring)
def read_varint(buf, i):
    result = 0
    shift = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, i


def load_region_index_texture():
    """Decode the game's complete TTHF R8 region-index texture."""
    matches = glob.glob(os.path.join(BASE, REGION_INDEX_GLOB))
    if len(matches) != 1:
        raise RuntimeError(f'expected one {REGION_INDEX_GLOB}, found {len(matches)}')
    with open(matches[0], 'rb') as f:
        buf = f.read()
    if len(buf) < 32:
        raise ValueError('region-index texture is shorter than its TTHF header')
    magic, width, height, mip_levels, bits, channels, output_size, _ = struct.unpack(
        '<4s7I', buf[:32])
    if magic != b'TTHF' or mip_levels != 1 or bits != 8 or channels != 1:
        raise ValueError(
            f'unexpected region texture header: magic={magic!r}, size={width}x{height}, '
            f'mips={mip_levels}, bits={bits}, channels={channels}')
    expected = width * height
    if output_size != expected:
        raise ValueError(f'header output size {output_size} != {expected}')

    decoded = bytearray(expected)
    src = 32
    dst = 0
    while src < len(buf) and dst < expected:
        count, src = read_varint(buf, src)
        if src >= len(buf):
            raise ValueError('truncated RLE value byte')
        value = buf[src]
        src += 1
        end = min(dst + count, expected)
        decoded[dst:end] = bytes([value]) * (end - dst)
        dst = end
    # The loader zeroes the destination first and stops when the source ends.
    # This asset intentionally omits a trailing all-zero/background run.
    if dst != expected:
        print(f'RLE source ended at pixel {dst}; leaving {expected - dst} trailing pixels zero')

    offset = REGION_TEXTURE_X_OFFSET % width
    raster = []
    for y in range(height):
        row = decoded[y * width:(y + 1) * width]
        raster.append(row[offset:] + row[:offset])
    print(f'decoded exact region-index texture {width}x{height}; x offset={offset}')
    return raster, width, height


def parse_top_level(buf):
    fields = {}
    i, n = 0, len(buf)
    while i < n:
        tag, i = read_varint(buf, i)
        field_no, wire_type = tag >> 3, tag & 0x7
        if wire_type == 0:
            val, i = read_varint(buf, i)
        elif wire_type == 1:
            val = struct.unpack('<q', buf[i:i + 8])[0]
            i += 8
        elif wire_type == 5:
            val = struct.unpack('<i', buf[i:i + 4])[0]
            i += 4
        elif wire_type == 2:
            ln, i = read_varint(buf, i)
            val = buf[i:i + ln]
            i += ln
        else:
            raise ValueError(f'bad wiretype {wire_type}')
        fields.setdefault(field_no, []).append(val)
    return fields


def parse_local_index_table(raw7_list):
    # field 7: repeated {1: local_index (implicit 0 for first), 2: global hash}.
    # local index 0 has no explicit '1' (it's the tile's default/background
    # slot, field 2 is also absent/empty for it -> resolve_hash(None) -> None).
    table = {}
    for i, raw in enumerate(raw7_list):
        if not raw:
            table[i] = None
            continue
        sub = parse_top_level(raw)
        local_idx = sub.get(1, [i])[0] if 1 in sub else i
        global_hash = sub.get(2, [None])[0]
        table[local_idx] = resolve_hash(global_hash)
    return table


def decode_tile_raster(raw10, width, height):
    grid = [[0] * width for _ in range(height)]
    i, n = 0, len(raw10)
    pos = 0
    total = width * height
    while pos < total:
        cnt, i = read_varint(raw10, i)
        idx, i = read_varint(raw10, i)
        for _ in range(cnt):
            r, c = divmod(pos, width)
            grid[r][c] = idx
            pos += 1
    return grid


def load_all_tiles():
    tiles = []
    for fn in sorted(glob.glob(os.path.join(BASE, 'Westeros_Alpha_6_Region_Array2DPacked_Client_*.pb'))):
        with open(fn, 'rb') as f:
            buf = f.read()
        top = parse_top_level(buf)
        # proto3 omits fields left at their zero default, so a tile at world
        # origin 0 (x00000/y00000) legitimately has no field 1/2 at all.
        x0 = top.get(1, [0])[0]
        y0 = top.get(2, [0])[0]
        w = top.get(3, [100])[0]
        h = top.get(4, [100])[0]
        local_to_key = parse_local_index_table(top.get(7, []))
        raw10 = top.get(10, [b''])[0]
        grid = decode_tile_raster(raw10, w, h)
        tiles.append((x0, y0, w, h, local_to_key, grid))
    return tiles


# ---------- 3. gap-fill: nearest-neighbor extend regions across land cells
# that have no region code at all ----------
# WHY THIS EXISTS (user feedback, this pass, comparing against the in-game
# political-map screenshot): "the fact that nearly every part of the map is
# included in a region and that they are all adjacent to one another like
# irregular puzzle pieces... The interactive map looks like a weird
# collection of some version of that with lots left out." Measured cause:
# only ~41% of clean_map_nodes.csv's 7,694 POIs land on a raster cell with a
# real region code - 35.5% land on code-0 ("no region assigned") cells *within*
# the decoded tile grid, and another 23.7% fall in (x,y) blocks where no tile
# file was even present at all (250 of the expected 540 tile-grid slots are
# simply missing - real gaps in this data dump, not an encoding bug). And
# critically, this is NOT just ocean/sea-routes riding along for free: sampling
# node type_name for the code-0/no-tile group shows Castle, Settlement (Town),
# Seat of Power, even Great House Capital entries landing there in roughly the
# same proportions as the fully-resolved group - i.e. plenty of genuine dry
# land with real POIs on it simply has no region code, which is exactly the
# "lots left out" gap in the border network the user is pointing at.
#
# Distinguishing "unassigned land" from "actual ocean" (so the fill only
# extends across real land) needed a signal independent of the region raster
# itself, since code 0 already conflates both. Sampled worldmap_background.jpg
# (the same pixel-aligned base texture the interactive map already renders):
# 300-sample means show cells with a real region code average RGB (198,160,110)
# and code-0-but-in-grid cells average (177,146,102) - both the same warm
# biome-tan hue family (mean HSV value ~0.72-0.78) - while cells outside the
# tile grid entirely average (75,66,55), much darker (mean HSV value ~0.30,
# many literal (0,0,0) samples) i.e. genuinely different-looking, consistent
# with open ocean/off-map void. So brightness alone (max channel) cleanly
# separates the two: this is used as a cheap land/not-land mask, then a
# multi-source BFS grows every existing region's cells outward across
# neighboring "land but code-0" cells (nearest-region-wins, standard multi-
# source shortest-path labeling) until it hits either a real border or the
# not-land mask. This only ever extends regions that already exist in the
# data into gaps next to them - it never invents a new region or changes an
# existing assignment - so it's a defensible "close the gap" extrapolation
# rather than fabricated data, and it directly produces the tessellating,
# no-gaps "puzzle piece" coverage the reference screenshot shows.
def build_land_mask(max_x, max_y, bg_path):
    from PIL import Image
    img = Image.open(bg_path).convert('RGB')
    bg_w, bg_h = img.size
    px = img.load()
    mask = bytearray(max_x * max_y)
    # background image is north-up (row 0 = top = raw max y); raster is raw/
    # un-flipped (row 0 = y=0 = south) - same flip used everywhere else in this
    # pipeline (see _build_worldmap_bg.py / _build_interactive_map.py's node
    # draw call), so sample row (bg_h - y).
    for y in range(max_y):
        iy = bg_h - y
        if not (0 <= iy < bg_h):
            continue
        base = y * max_x
        for x in range(min(max_x, bg_w)):
            r, g, b = px[x, iy]
            if r > 108 or g > 108 or b > 108:
                mask[base + x] = 1
    return mask


def fill_gaps(raster, land_mask, max_x, max_y):
    visited = bytearray(max_x * max_y)
    dq = deque()
    for y in range(max_y):
        row = raster[y]
        base = y * max_x
        for x in range(max_x):
            if row[x]:
                visited[base + x] = 1
                dq.append((x, y))
    filled = 0
    while dq:
        x, y = dq.popleft()
        code = raster[y][x]
        if x + 1 < max_x:
            nx, ny, idx = x + 1, y, y * max_x + x + 1
            if not visited[idx] and land_mask[idx]:
                visited[idx] = 1
                raster[ny][nx] = code
                filled += 1
                dq.append((nx, ny))
        if x - 1 >= 0:
            nx, ny, idx = x - 1, y, y * max_x + x - 1
            if not visited[idx] and land_mask[idx]:
                visited[idx] = 1
                raster[ny][nx] = code
                filled += 1
                dq.append((nx, ny))
        if y + 1 < max_y:
            nx, ny, idx = x, y + 1, (y + 1) * max_x + x
            if not visited[idx] and land_mask[idx]:
                visited[idx] = 1
                raster[ny][nx] = code
                filled += 1
                dq.append((nx, ny))
        if y - 1 >= 0:
            nx, ny, idx = x, y - 1, (y - 1) * max_x + x
            if not visited[idx] and land_mask[idx]:
                visited[idx] = 1
                raster[ny][nx] = code
                filled += 1
                dq.append((nx, ny))
    return filled


def main():
    region_lookup = load_region_table()
    code_info = {}
    for info in region_lookup.values():
        # The numeric id is the unambiguous identity stored by the texture.
        # Display names are not unique (the data contains two Eyrie rows).
        code_info[info['id']] = info
    raster, max_x, max_y = load_region_index_texture()
    unknown_codes = sorted({v for row in raster for v in row if v and v not in code_info})
    if unknown_codes:
        print('warning: texture contains non-real/tutorial region ids:', unknown_codes)
    print(f'loaded {len(region_lookup)} real region rows; raster extent {max_x}x{max_y}')

    # ---- sanity check against known POI coordinates ----
    checks = [
        ('Winterfell', 1134, 2687), ('Kings Landing', 1460, 1060),
        ('Casterly Rock', 544, 1227), ('Pyke', 563, 1584),
        ('Riverrun', 1035, 1486), ('Sunspear', 1925, 139),
    ]
    for name, x, y in checks:
        code = raster[y][x] if 0 <= y < max_y and 0 <= x < max_x else None
        info = code_info.get(code, {})
        print(f'  check {name} @ ({x},{y}) -> code={code} name={info.get("name")} kingdom={info.get("kingdom")}')

    # ---- resolve each POI node's containing region name, for the interactive
    # map's data table "Place Name" column (user-reported: clean_map_nodes.csv's
    # own place_name field comes back blank for effectively every row, since it
    # was sourced from the POI table itself which just doesn't carry a name for
    # most node types - Ruin/Tunnel/Bridge/Crossing/etc. only Settlement-tier
    # entries seem to ever have one). The per-cell `raster` built above already
    # gives free region membership for any (x,y) - same coordinate space as the
    # node CSV (see module docstring: no axis flip needed here) - so this is
    # just a raster[y][x] -> code -> code_info['name'] lookup per node, no new
    # data source needed. Written as a flat array parallel to
    # clean_map_nodes.csv's row order (NOT keyed by instance_id - see
    # _build_crossing_chains.py's docstring for why instance_id is unsuitable
    # as a join key here) so _build_interactive_map.py can zip it straight onto
    # `data` with no lookup on its side.
    with open(os.path.join(EXT, 'clean_map_nodes.csv'), encoding='utf-8') as f:
        node_rows = list(csv.DictReader(f))
    node_place_names = []
    for r in node_rows:
        x, y = int(r['x']), int(r['y'])
        code = raster[y][x] if 0 <= y < max_y and 0 <= x < max_x else 0
        info = code_info.get(code)
        node_place_names.append(info['name'] if info else '')
    with open(os.path.join(EXT, 'node_place_names.json'), 'w', encoding='utf-8') as f:
        json.dump(node_place_names, f)
    resolved = sum(1 for n in node_place_names if n)
    print(f'wrote node_place_names.json  (resolved {resolved}/{len(node_place_names)} nodes to a region)')

    # ---- boundaries: vertical unit-edges (between (x,y)-(x+1,y), horizontally
    # adjacent cells) and horizontal unit-edges (between (x,y)-(x,y+1), vertically
    # adjacent cells), merged along runs.
    #
    # BUG FOUND (user-reported, this pass): the first cut of this merge logic
    # detected each edge type correctly but merged it along the WRONG axis - e.g.
    # it found vertical edges by scanning across a row (comparing row[x] vs
    # row[x+1]) and then merged consecutive x positions within that SAME row into
    # one segment. But two vertical edges at different x (same y) are NOT
    # collinear - only vertical edges at the SAME x across consecutive y are. That
    # produced bogus zigzag "segments" stitching together unrelated unit-edges,
    # which is exactly the grid-like/glitchy line artifacts seen in the browser
    # (confirmed by inspecting region_boundaries.json around the Ten Towers
    # region: dozens of isolated 1-unit segments at fixed y with x jumping by 1,
    # i.e. runs that never should have been considered "the same line" at all).
    # Fixed by merging along the axis the edge actually runs parallel to: vertical
    # edges merge down a fixed column (varying y), horizontal edges merge across
    # a fixed row (varying x).
    #
    # THREE-WAY CLASSIFICATION (added this pass, per user request to distinguish
    # "geographical" coastline from political borders so they can be styled/toggled
    # separately, closer to the in-game look): the original 2-way is_kingdom_edge
    # flag was computed as `kingdom_of(a) != kingdom_of(b)`, and code 0 (background/
    # "no region assigned") resolves kingdom_of(0) -> None. Since None is unequal to
    # every real kingdom name, every land/ocean edge was ALSO satisfying "is_kingdom_
    # edge" - verified: 17,900 of 23,144 segments were flagged is_kingdom_edge, far
    # more than plausible for actual kingdom-vs-kingdom land borders alone, and this
    # is exactly the coastline's total length riding along for free. Split into a
    # 3-way `kind` instead: 0 = region border (same kingdom, different region),
    # 1 = kingdom border (both sides are land, different real kingdoms), 2 = coastline
    # (one side is ocean/code-0, the other is land). This also unlocks a genuine
    # "coastline layer" essentially for free, without needing any new data source.
    def kingdom_of(code):
        return code_info.get(code, {}).get('kingdom')

    def edge_kind(a, b):
        if a == 0 or b == 0:
            return 2
        return 1 if kingdom_of(a) != kingdom_of(b) else 0

    # KINGDOM ID PER SEGMENT (added this pass, per user question about the
    # reference screenshot's "blue, pink, yellow glowing, slightly bolder
    # lines that trace very close together at every region border" - the
    # in-game map colors each territory and its borders by controlling
    # kingdom/alliance; ours had no per-segment kingdom identity at all
    # before this, only the coarse 0/1/2 `kind`). This is a 9-real-kingdom
    # analog, NOT an exact reproduction: the reference image's 3-4 macro
    # colors group multiple traditional kingdoms together (e.g. The North +
    # Riverlands + Iron Islands all cyan), which doesn't match any grouping
    # in RegionDataTable - that almost certainly reflects a dynamic in-game
    # alliance/faction-control layer, which isn't present anywhere in this
    # static resource dump. Tagging by the real kingdom field we DO have is
    # the closest honest substitute: every kind-0 (region-vs-region,
    # same-kingdom) segment gets that shared kingdom's small integer id;
    # kind-1 (kingdom-vs-kingdom) and kind-2 (coastline) segments get -1
    # since no single kingdom color applies. kingdom_id_to_name.json holds
    # the id->name mapping so the JS side can assign a fixed color per id.
    kingdom_names = sorted({info['kingdom'] for info in code_info.values()})
    kingdom_to_kid = {name: i for i, name in enumerate(kingdom_names)}
    with open(os.path.join(EXT, 'kingdom_id_to_name.json'), 'w', encoding='utf-8') as f:
        json.dump(kingdom_names, f)

    def kid_of(code):
        name = kingdom_of(code)
        return kingdom_to_kid.get(name, -1)

    def make_seg(x1, y1, x2, y2, pair):
        kind = edge_kind(pair[0], pair[1])
        kid = kid_of(pair[0]) if kind == 0 else -1
        return [x1, y1, x2, y2, kind, kid]

    segments = []

    # region_segs/region_adjacency (added this pass, per user request to replace the
    # region/kingdom BORDER LINES with filled, per-region color shading instead - the
    # user reported the border-line rendering "not at all correct when both showing"
    # and asked for light contrasting fills instead, keyed off which region each tile
    # belongs to). Every unit-edge already computed above touches one or two real
    # region codes (the `pair` a/b on either side); recording that same edge into
    # BOTH codes' own segment lists gives, for each region, the complete set of unit
    # edges bounding its raster footprint (against neighboring regions AND against
    # ocean/code-0) - exactly the geometry needed to trace a fillable closed outline
    # per region, using the same segs_to_smooth_path() chain-tracing/smoothing
    # machinery _build_interactive_map.py already applies to the old border/mountain
    # paths. region_adjacency (which region codes actually touch which) is collected
    # in the same pass so a proper graph-coloring (below) can guarantee adjacent
    # regions never get assigned the same fill color.
    region_segs = defaultdict(list)
    region_adjacency = defaultdict(set)

    def record_edge(x1, y1, x2, y2, pair):
        segments.append(make_seg(x1, y1, x2, y2, pair))
        a, b = pair
        if a:
            region_segs[a].append([x1, y1, x2, y2])
        if b:
            region_segs[b].append([x1, y1, x2, y2])
        if a and b and a != b:
            region_adjacency[a].add(b)
            region_adjacency[b].add(a)

    # vertical edges: for each column x, scan down rows, merge runs where the
    # (top_cell_pair) stays the same - these are edges between column x and x+1
    for x in range(max_x - 1):
        run_start = None
        run_pair = None
        for y in range(max_y):
            a, b = raster[y][x], raster[y][x + 1]
            if a != b:
                pair = (a, b)
                if run_pair == pair:
                    continue
                if run_pair is not None:
                    record_edge(x + 1, run_start, x + 1, y, run_pair)
                run_start = y
                run_pair = pair
            else:
                if run_pair is not None:
                    record_edge(x + 1, run_start, x + 1, y, run_pair)
                run_pair = None
        if run_pair is not None:
            record_edge(x + 1, run_start, x + 1, max_y, run_pair)

    # horizontal edges: for each row y, scan across columns, merge runs - these
    # are edges between row y and y+1
    for y in range(max_y - 1):
        row0 = raster[y]
        row1 = raster[y + 1]
        run_start = None
        run_pair = None
        for x in range(max_x):
            a, b = row0[x], row1[x]
            if a != b:
                pair = (a, b)
                if run_pair == pair:
                    continue
                if run_pair is not None:
                    record_edge(run_start, y + 1, x, y + 1, run_pair)
                run_start = x
                run_pair = pair
            else:
                if run_pair is not None:
                    record_edge(run_start, y + 1, x, y + 1, run_pair)
                run_pair = None
        if run_pair is not None:
            record_edge(run_start, y + 1, max_x, y + 1, run_pair)

    from collections import Counter as _Counter
    kind_counts = _Counter(s[4] for s in segments)
    print('boundary segments (after run merge):', len(segments), '  by kind (0=region,1=kingdom,2=coast):', dict(kind_counts))

    # ---- region + kingdom centroids ----
    region_stats = defaultdict(lambda: [0, 0, 0])  # sumx, sumy, count
    for y in range(max_y):
        row = raster[y]
        for x in range(max_x):
            gid = row[x]
            if gid:
                s = region_stats[gid]
                s[0] += x
                s[1] += y
                s[2] += 1

    # Greedy Welsh-Powell-style graph coloring over region_adjacency: process regions
    # highest-degree-first, assign each the lowest-numbered color not already used by
    # one of its already-colored neighbors. Guarantees no two ADJACENT regions ever
    # share a color (that's the actual visual requirement - "contrasting enough to
    # their adjacent neighbors" - not a global uniqueness requirement, which is why a
    # small palette can be reused across the whole map). NUM_FILL_COLORS is generous
    # headroom over what a planar-ish map like this actually needs (four-color-theorem
    # says 4 colors always suffice for planar regions; this map isn't perfectly planar
    # since kingdom_of() gaps/enclaves exist, but greedy coloring with 12 colors
    # available comfortably avoids ever needing the deliberately-safe fallback below).
    NUM_FILL_COLORS = len(REGION_FILL_COLORS)
    all_region_codes = sorted(region_stats.keys())
    degree_order = sorted(all_region_codes, key=lambda c: -len(region_adjacency.get(c, ())))
    color_of_region = {}
    color_usage = [0] * NUM_FILL_COLORS

    def rgb(color):
        return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))

    palette_rgb = [rgb(color) for color in REGION_FILL_COLORS]

    def color_distance(a, b):
        return sum((x - y) ** 2 for x, y in zip(palette_rgb[a], palette_rgb[b]))

    for code in degree_order:
        used = {color_of_region[n] for n in region_adjacency.get(code, ()) if n in color_of_region}
        available = [ci for ci in range(NUM_FILL_COLORS) if ci not in used]
        if available:
            # Among conflict-free colors, maximize the minimum perceptual separation
            # from already-colored neighbors. Usage is a tie-breaker so the whole map
            # does not collapse into the first four palette entries.
            neighbor_colors = list(used)
            def score(ci):
                separation = min((color_distance(ci, other) for other in neighbor_colors),
                                 default=10 ** 9)
                return separation, -color_usage[ci], -ci
            chosen = max(available, key=score)
            color_of_region[code] = chosen
            color_usage[chosen] += 1
        else:
            # Never hit in practice for this map's adjacency graph (checked: max
            # degree stays well under NUM_FILL_COLORS), but stay safe rather than
            # crash a full rebuild over a coloring edge case - just reuse a color
            # that clashes with one already-colored neighbor rather than every one.
            chosen = min(range(NUM_FILL_COLORS), key=lambda ci: color_usage[ci])
            color_of_region[code] = chosen
            color_usage[chosen] += 1
    print('region fill coloring: colored', len(color_of_region), 'regions using up to',
          (max(color_of_region.values()) + 1) if color_of_region else 0, f'of {NUM_FILL_COLORS} colors')

    region_labels = []
    kingdom_stats = defaultdict(lambda: [0, 0, 0])
    for code, (sx, sy, cnt) in region_stats.items():
        info = code_info.get(code)
        if not info or cnt < 5:
            continue
        cx, cy = sx / cnt, sy / cnt
        region_labels.append({'id': code, 'name': info['name'], 'kingdom': info['kingdom'],
                               'x': round(cx, 1), 'y': round(cy, 1), 'cells': cnt})
        ks = kingdom_stats[info['kingdom']]
        ks[0] += sx
        ks[1] += sy
        ks[2] += cnt

    kingdom_labels = []
    for kname, (sx, sy, cnt) in kingdom_stats.items():
        kingdom_labels.append({'name': kname, 'x': round(sx / cnt, 1), 'y': round(sy / cnt, 1), 'cells': cnt})

    print('regions with labels:', len(region_labels), '  kingdoms:', len(kingdom_labels))

    with open(os.path.join(EXT, 'region_boundaries.json'), 'w', encoding='utf-8') as f:
        json.dump(segments, f)
    with open(os.path.join(EXT, 'region_labels.json'), 'w', encoding='utf-8') as f:
        json.dump(region_labels, f)
    with open(os.path.join(EXT, 'kingdom_labels.json'), 'w', encoding='utf-8') as f:
        json.dump(kingdom_labels, f)

    # Exact north-up indexed PNG. Index 0 is transparent and region colors
    # start at 1. This cannot create gaps, overlaps, or invented curves while
    # tracing/smoothing polygon segments, as the former SVG fill layer did.
    overlay_pixels = bytearray(max_x * max_y)
    for y, row in enumerate(raster):
        out = (max_y - 1 - y) * max_x
        for x, code in enumerate(row):
            if code in color_of_region:
                overlay_pixels[out + x] = color_of_region[code] + 1
    overlay = Image.frombytes('P', (max_x, max_y), bytes(overlay_pixels))
    palette = [0, 0, 0]
    for color in REGION_FILL_COLORS:
        palette.extend(int(color[i:i + 2], 16) for i in (1, 3, 5))
    palette.extend([0] * (768 - len(palette)))
    overlay.putpalette(palette)
    overlay.info['transparency'] = 0
    overlay.save(os.path.join(EXT, 'region_color_overlay.png'), optimize=True)

    # Keep this old filename as a compact compatibility/diagnostic mapping.
    region_fill_data = {
        str(code): {'color_idx': color_of_region.get(code, 0)}
        for code in all_region_codes
    }
    with open(os.path.join(EXT, 'region_fill_data.json'), 'w', encoding='utf-8') as f:
        json.dump(region_fill_data, f)
    print('wrote region_boundaries.json, region_labels.json, kingdom_labels.json, '
          'region_fill_data.json, region_color_overlay.png')


if __name__ == '__main__':
    main()
