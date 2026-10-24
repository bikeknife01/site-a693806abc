import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('publisher', ROOT / 'Game_Details/Resources/_publish_atlas_maps.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class AtlasPublicationTests(unittest.TestCase):
    def test_seasons_use_separate_assets_and_correct_encyclopedia_targets(self):
        # Keep temporary files inside the writable repository on Windows.
        scratch = ROOT / '.tmp-atlas-tests'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            output = Path(temp)
            publisher.publish(output)
            self.assertEqual((output / 'index.html').read_bytes(), publisher.SELECTOR.read_bytes())
            for slug, source, _ in publisher.MAPS:
                html = (output / f'{slug}.html').read_text(encoding='utf-8')
                for asset in publisher.ASSETS:
                    self.assertIn(f'href="assets/{slug}/{asset}"', html)
                    self.assertEqual((output / 'assets' / slug / asset).read_bytes(), (source / asset).read_bytes())
                exact_link = "${encodeURIComponent(d.sid.split(':')[1])}"
                if slug == 'season2':
                    self.assertIn(exact_link, html)
                else:
                    self.assertNotIn(exact_link, html)
                    self.assertNotIn('Bravo campaign · Showing', html)
                if slug == 'season3':
                    self.assertIn('Season 3 · Campaign Charlie', html)
                    self.assertIn('terrain coverage is partial', html)

    def test_charlie_export_matches_manifest_and_contains_new_seats(self):
        source = publisher.EXTRACTED / 'seasons/season3'
        manifest = json.loads((source / 'source_manifest.json').read_text())
        for item in manifest['generated']:
            self.assertEqual(hashlib.sha256((source / item['file']).read_bytes()).hexdigest(), item['sha256'])
        with (source / 'clean_map_nodes.csv').open(encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), manifest['poi_count'])
        self.assertEqual(manifest['map_prefix'], 'Westeros_Charlie_3_ScalingRuins')
        self.assertTrue(all(r['template_key'] and 'unknown' not in r['type_name'].lower() for r in rows))
        seats = {r['place_name']: (int(r['x']), int(r['y'])) for r in rows if r['place_name']}
        self.assertEqual(seats['Antlers'], (1485, 1232))
        self.assertEqual(seats['Hayford'], (1225, 1136))
        names = json.loads((source / 'node_place_names.json').read_text())
        self.assertEqual(len(names), len(rows))
        for a, b in json.loads((source / 'crossing_chains.json').read_text()):
            self.assertNotEqual(a, b)
            self.assertTrue(0 <= a < len(rows) and 0 <= b < len(rows))


if __name__ == '__main__':
    unittest.main()
