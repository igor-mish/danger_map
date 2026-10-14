import copy
import json
from pathlib import Path
import unittest
from bat_yam import bat_yam

class BatYamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot=json.loads((Path(__file__).resolve().parents[1]/'public/sources/bat-yam.json').read_text())
    def test_complete_geometries_and_raw_statuses(self):
        rows=bat_yam(self.snapshot)
        self.assertEqual(len(rows),205)
        self.assertEqual({r['source_object_id'] for r in rows},set(self.snapshot['expected_object_ids']))
        self.assertEqual(sum(r['status_code']=='פ' for r in rows),198)
        self.assertEqual(sum(r['status_code']=='ל' for r in rows),7)
        self.assertTrue(all(31.98<r['lat']<32.06 and 34.70<r['lng']<34.80 for r in rows))
        self.assertEqual(len({r['case_id'] for r in rows}),169)
        self.assertEqual(len({r['address'] for r in rows}),145)
        self.assertEqual(rows[0]['source_date'],'2026-10-14')
    def test_missing_rows_and_swapped_coordinates_are_rejected(self):
        partial=copy.deepcopy(self.snapshot);partial['data']['features'].pop()
        with self.assertRaises(ValueError):bat_yam(partial)
        swapped=copy.deepcopy(self.snapshot);g=swapped['data']['features'][0]['geometry'];g['x'],g['y']=g['y'],g['x']
        with self.assertRaises(ValueError):bat_yam(swapped)
    def test_transfer_limit_is_rejected(self):
        partial=copy.deepcopy(self.snapshot);partial['data']['exceededTransferLimit']=True
        with self.assertRaises(ValueError):bat_yam(partial)

if __name__=='__main__':unittest.main()
