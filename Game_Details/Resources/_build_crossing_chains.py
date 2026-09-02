"""Reconstructs the "crossing chains" that connect Harbor/Dock and Crossing nodes
into sea-route (or river-ford) paths, so the interactive map can draw them as
lines when a node is selected.

BACKGROUND (user-confirmed from in-game observation): Harbor/Dock and Crossing
nodes look the same in-game ("docks") and each one connects to something on
the other side - i.e. a Harbor/Dock is the start of a series of Crossing
nodes that string together into a route, ending back on ordinary land POIs
(a town, ruin cluster, etc). This was verified empirically: every Harbor's
nearest Crossing is close (median ~15 units), and walking outward from a
harbor along consistently-bearinged nearby crossings produces a chain that
terminates hundreds of units away right next to normal land POIs.

The Rtree leaf protobuf has no explicit "connects to" field (verified: every
leaf has only fields 1-5, no adjacency/path id), so the chain graph has to be
reconstructed purely from (x, y) proximity among Crossing + Harbor/Dock nodes.

ALGORITHM (validated by hand against the harbor-at-(1568,498) example, which
correctly recovers a ~20-node chain ending at a Settlement/Ruin cluster
~576 units away):
  1. Base skeleton = mutual 2-nearest-neighbor graph over all Crossing +
     Harbor/Dock nodes (an edge (a,b) is kept only if b is among a's 2
     closest same-set neighbors AND a is among b's 2 closest). This alone
     produces clean degree<=2 paths (chains) with zero false branching -
     confirmed: max degree 2, 227 components.
  2. Rare branch/"V" attachment (per user: real but rare, never more than a
     handful of endpoints meeting at one point): for any node left with
     degree < 2 after step 1 (an unresolved chain endpoint), try to attach
     it to the *closest* endpoint-or-node in a *different* component within
     a tight 30-unit radius (close to the 95th-percentile nearest-neighbor
     spacing of ~21 units seen across the whole node set). This is
     deliberately conservative: a naive "connect anything within threshold X"
     pass created ~140 spurious degree>=3 nodes just from ordinary chain
     density; restricting the second pass to only touch still-open endpoints
     brings that down to 4 true branch points, matching the user's "rare V
     config, never more than 3 endpoints" description.

Output: _extracted/crossing_chains.json - a flat list of
[row_idx_a, row_idx_b] pairs, where row_idx is each node's 0-based position in
clean_map_nodes.csv. That CSV's row order lines up 1:1 with the `data` array
_build_interactive_map.py builds (it iterates the same rows in the same
order with no re-sort), so these indices can be used directly as indices into
`data` with no further lookup needed on the JS side.

NOTE: `instance_id` was tried first as the join key and is WRONG for this
purpose - it is not a unique per-placement id. Verified: clean_map_nodes.csv
has 7,694 rows but only 227 distinct instance_id values (one id repeats 780
times), because instance_id is actually a shared content/template reference,
not a per-instance placement id. Using it as a dict key silently collapsed
many distinct Crossing/Harbor nodes onto a single "last one wins" data index,
which produced degenerate self-loop edges like [i, i] once resolved back to
`data` indices in _build_interactive_map.py. Row position is unique and stable
instead, so it's used as the identifier here.
"""
import csv
import json
import math
import os
from collections import Counter

BASE = os.path.dirname(__file__)
EXT = os.path.join(BASE, '_extracted')

K = 2
MUTUAL_MAXD = 120     # cap on the base mutual-NN edges (well above typical spacing)
BRANCH_MAXD = 30       # tight cap for the rare-branch attachment pass


def main():
    with open(os.path.join(EXT, 'clean_map_nodes.csv'), encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    # Keep each node's original 0-based row position (see module docstring: this,
    # not instance_id, is the stable unique identifier that lines up with `data`
    # in _build_interactive_map.py).
    node_entries = [(i, r) for i, r in enumerate(rows) if r['type_name'] in ('Crossing', 'Harbor/Dock')]
    row_idx = [i for i, r in node_entries]
    nodes = [r for i, r in node_entries]
    n = len(nodes)
    xs = [int(r['x']) for r in nodes]
    ys = [int(r['y']) for r in nodes]

    def dist(i, j):
        return math.hypot(xs[i] - xs[j], ys[i] - ys[j])

    D = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dd = dist(i, j)
            D[i][j] = D[j][i] = dd

    knn = [sorted(range(n), key=lambda j, i=i: D[i][j] if j != i else 1e18)[:K] for i in range(n)]

    edges = set()
    for i in range(n):
        for j in knn[i]:
            if D[i][j] <= MUTUAL_MAXD and i in knn[j]:
                edges.add((min(i, j), max(i, j)))

    def build_adj(edge_set):
        adj = [[] for _ in range(n)]
        for a, b in edge_set:
            adj[a].append(b)
            adj[b].append(a)
        return adj

    def components(adj):
        seen = [False] * n
        comp_id = [-1] * n
        comps = []
        for i in range(n):
            if seen[i]:
                continue
            stack, comp = [i], [i]
            seen[i] = True
            while stack:
                u = stack.pop()
                for v in adj[u]:
                    if not seen[v]:
                        seen[v] = True
                        comp.append(v)
                        stack.append(v)
            cid = len(comps)
            for x in comp:
                comp_id[x] = cid
            comps.append(comp)
        return comps, comp_id

    adj = build_adj(edges)
    _, comp_id = components(adj)
    deg = [len(a) for a in adj]

    candidates = []
    for i in range(n):
        if deg[i] >= 2:
            continue
        for j in range(n):
            if i == j or comp_id[i] == comp_id[j]:
                continue
            if D[i][j] <= BRANCH_MAXD:
                candidates.append((D[i][j], i, j))
    candidates.sort()
    for _, i, j in candidates:
        if deg[i] < 2 and comp_id[i] != comp_id[j]:
            edges.add((min(i, j), max(i, j)))
            deg[i] += 1
            deg[j] += 1
            old, new = comp_id[i], comp_id[j]
            for x in range(n):
                if comp_id[x] == old:
                    comp_id[x] = new

    adj = build_adj(edges)
    comps, _ = components(adj)
    degs = [len(a) for a in adj]

    id_pairs = [[row_idx[a], row_idx[b]] for a, b in sorted(edges)]
    out_path = os.path.join(EXT, 'crossing_chains.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(id_pairs, f)

    print(f'nodes considered (Crossing + Harbor/Dock): {n}')
    print(f'edges written: {len(id_pairs)}   components: {len(comps)}')
    print('degree distribution:', dict(Counter(degs)))
    print('components with >=3 members:', sum(1 for c in comps if len(c) >= 3))
    print('wrote', out_path)


if __name__ == '__main__':
    main()
