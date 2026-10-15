import unittest,json
from pathlib import Path
from copy import deepcopy
from holon_b144 import enrich_holon
ROOT=Path(__file__).resolve().parents[1]
class HolonB144Tests(unittest.TestCase):
    def test_coverage_and_multi_address_identity(self):
        rows=[r for r in json.loads((ROOT/'public/data/buildings.json').read_text())['records'] if r['city']=='חולון']
        self.assertEqual(len(rows),87)
        self.assertTrue(all(r['lat'] and r['lng'] for r in rows))
        self.assertEqual(len(next(r for r in rows if r['address']=='ראש פינה 1+3')['locations']),2)
        self.assertEqual(len(next(r for r in rows if r['address']=='ההסתדרות 94,96,98,100,102')['locations']),5)
        self.assertTrue(all('דן שומרון' not in p['address'] for r in rows for p in r.get('locations',[])))
    def test_invalid_point_rejected(self):
        snapshot=json.loads((ROOT/'public/sources/holon-b144.json').read_text())
        row={'city':'חולון',**{k:snapshot['records'][0][k] for k in ['category','address','block','parcel']}}
        snapshot['records'][0]['locations'][0]['lat']=0
        with self.assertRaises(ValueError):enrich_holon([row],snapshot)
