import copy
import json
from pathlib import Path
import unittest
from tel_aviv_gis import enrich_tel_aviv,pdf_key

ROOT=Path(__file__).resolve().parents[1]

class TelAvivGISTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot=json.loads((ROOT/'public/sources/tel-aviv-gis.json').read_text())
    def test_coordinate_fill_preserves_pdf_case_details(self):
        r={'city':'תל אביב','address':'אהרונסון, רחוב 28','lat':None,'lng':None,'case_id':'keep-pdf-case','occupancy':'PDF occupancy'}
        stats=enrich_tel_aviv([r],self.snapshot)
        self.assertEqual(stats['features'],607);self.assertEqual(stats['pdf_records_located'],1)
        self.assertTrue(32<r['lat']<32.2 and 34.7<r['lng']<34.9)
        self.assertEqual(r['case_id'],'keep-pdf-case');self.assertEqual(r['occupancy'],'PDF occupancy')
        self.assertEqual(r['geocode_provider'],'Tel Aviv municipal GIS')
        self.assertTrue(r['gis_address_records'][0]['findings'])
    def test_house_number_and_entrance_are_not_conflated(self):
        self.assertNotEqual(pdf_key('אילת, רחוב 43א'),pdf_key('אילת, רחוב 43'))
        self.assertNotEqual(pdf_key('רחוב בדיקה 141'),pdf_key('רחוב בדיקה 14'))
    def test_separated_points_are_not_arbitrarily_selected(self):
        a=copy.deepcopy(self.snapshot['data']['features'][0]);b=copy.deepcopy(a)
        b['attributes']['UniqueId']='different';b['attributes']['oid_mivne']=2;b['geometry']['x']+=500
        snapshot=copy.deepcopy(self.snapshot);snapshot['data']['features']=[a,b];snapshot['expected_object_ids']=[1,2]
        r={'city':'תל אביב','address':'שלמה, דרך 151','lat':None,'lng':None}
        stats=enrich_tel_aviv([r],snapshot)
        self.assertEqual(stats['ambiguous_matches'],1);self.assertIsNone(r['lat'])
    def test_duplicate_ids_and_bad_crs_are_rejected(self):
        s=copy.deepcopy(self.snapshot);s['data']['features'].append(s['data']['features'][0])
        with self.assertRaises(ValueError):enrich_tel_aviv([],s)
        s=copy.deepcopy(self.snapshot);s['data']['spatialReference']={'wkid':2039}
        with self.assertRaises(ValueError):enrich_tel_aviv([],s)
    def test_published_coverage(self):
        rows=json.loads((ROOT/'public/data/buildings.json').read_text())['records'];rows=[r for r in rows if r['city']=='תל אביב']
        self.assertEqual(sum(r['lat'] is not None for r in rows),609)
        self.assertEqual(sum(r.get('gis_location_match')=='exact address' for r in rows),586)

if __name__=='__main__':unittest.main()
