import collections
import json
from pathlib import Path
import unittest
from geocode import query_address,suitable
from data_lock import data_lock

class ImportTests(unittest.TestCase):
    def test_parallel_updates_are_rejected(self):
        with data_lock():
            with self.assertRaises(SystemExit):
                with data_lock():
                    self.fail('Parallel updater acquired the same dataset lock')
    def test_source_counts_and_provenance(self):
        data=json.loads((Path(__file__).resolve().parents[1]/'public/data/buildings.json').read_text())
        rows=data['records'];counts=collections.Counter((r['city'],r['category']) for r in rows)
        self.assertEqual(counts[('תל אביב','dangerous')],615)
        self.assertEqual(counts[('חולון','dangerous')],70)
        self.assertEqual(counts[('חולון','pal-kal')],17)
        self.assertEqual(counts[('בת ים','dangerous')],205)
        self.assertEqual({r['source_date'] for r in rows if r['city']=='חולון'},{'2026-07-15'})
        self.assertEqual(len({r['id'] for r in rows}),907)
        self.assertTrue(all(r['source_page']>0 for r in rows if r['city']!='בת ים'))
        self.assertEqual(sum(r.get('address_missing',False) for r in rows),1)
    def test_tel_aviv_full_table_fields(self):
        rows=json.loads((Path(__file__).resolve().parents[1]/'public/data/buildings.json').read_text())['records']
        row=next(r for r in rows if r['id']=='03-2026-0456')
        self.assertEqual(row['occupancy'],'מאוכלס')
        self.assertEqual(row['treatment'],'המתנה לאישורי מסירה')
        self.assertEqual(row['case_opened'],'06/09/2026')
        self.assertEqual(row['last_visit'],'26/08/2026')
        self.assertEqual(row['treatment_since'],'15/09/2026')
        self.assertEqual(row['preserved_marker'],'')
        marked=next(r for r in rows if r['id']=='03-2024-0730')
        self.assertEqual(marked['preserved_marker'],'*')
        self.assertTrue(all(r['preserved_marker'] in ('','*') for r in rows if r['city']=='תל אביב'))
    def test_address_numbers_and_ambiguity(self):
        self.assertEqual(query_address({'address':'אוסישקין, רחוב 2א'}),('אוסישקין','2א'))
        self.assertEqual(query_address({'address':"אהרונוביץ' 40, דירה 6"}),("אהרונוביץ'",'40'))
        self.assertIsNone(query_address({'address':"אהרונוביץ' 22-28"}))
        self.assertIsNone(query_address({'address':'חסר','address_missing':True}))
    def test_reject_city_street_or_number_mismatch(self):
        c={'lat':'32.07','lon':'34.78','address':{'city':'תל אביב-יפו','country_code':'il','road':'אוסישקין','house_number':'2א'}}
        self.assertTrue(suitable({'city':'תל אביב'},'אוסישקין','2א',c))
        self.assertFalse(suitable({'city':'חולון'},'אוסישקין','2א',c))
        self.assertFalse(suitable({'city':'תל אביב'},'אוסישקין','20',c))
        self.assertFalse(suitable({'city':'תל אביב'},'אלנבי','2א',c))

if __name__=='__main__':unittest.main()
