"""Enrich PDF records using exact-address municipal GIS evidence, without case-ID inference."""
from collections import defaultdict
import re
import unicodedata
from pyproj import Geod,Transformer

TYPES={'רחוב','דרך','שדרות','שביל','כיכר','ככר','סמטה','סמטת'}

def normalized(value):
    return re.sub(r'[^\w]','',unicodedata.normalize('NFKC',str(value))).casefold()

def street_key(value):
    return tuple(sorted(normalized(w) for w in value.split() if normalized(w) not in TYPES))

def pdf_key(address):
    text=re.sub(r',\s*(?:רחוב|דרך|שדרות|שביל|כיכר|ככר|סמטה|סמטת)\s+',' ',address)
    match=re.fullmatch(r'(.*?)\s+(\d+)([א-תA-Za-z]?)',text)
    if not match:return None
    return street_key(match[1]),str(int(match[2])),normalized(match[3])

def enrich_tel_aviv(records,snapshot):
    data=snapshot['data']
    if data['spatialReference'].get('latestWkid',data['spatialReference']['wkid'])!=3857 or data.get('exceededTransferLimit'):
        raise ValueError('Unexpected Tel Aviv GIS CRS or transfer limit')
    if snapshot.get('all_layer_records_verified'):
        field=snapshot['object_id_field'];actual=[f['attributes'][field] for f in data['features']]
        if len(actual)!=len(set(actual)) or set(actual)!=set(snapshot['expected_object_ids']):raise ValueError('Incomplete verified Tel Aviv snapshot')
    transformer=Transformer.from_crs(3857,4326,always_xy=True);geod=Geod(ellps='WGS84');index=defaultdict(list);seen=set()
    for f in data['features']:
        a=f['attributes'];uid=a['UniqueId']
        if uid in seen:raise ValueError('Duplicate Tel Aviv GIS identifier')
        seen.add(uid);lng,lat=transformer.transform(f['geometry']['x'],f['geometry']['y'])
        if not (34.70<lng<34.90 and 31.99<lat<32.18):raise ValueError('Invalid Tel Aviv GIS point')
        if a.get('ms_bayit') is None or not float(a['ms_bayit']).is_integer():continue
        key=(street_key(a['shem_rechov']),str(int(a['ms_bayit'])),normalized(a.get('knisa') or ''))
        index[key].append({'unique_id':uid,'order_type':a['sug_tzav'],'order_description':a['t_tzav'],'findings':a.get('t_mimzaim') or '',
            'location_description':a.get('t_mikum') or '', 'imported_at':a.get('date_import'),'address':a.get('t_ktovet'), 'lat':lat,'lng':lng})
    stats={'features':len(seen),'pdf_records_matched':0,'pdf_records_located':0,'ambiguous_matches':0}
    for r in records:
        if r['city']!='תל אביב':continue
        matches=sorted(index.get(pdf_key(r['address']),[]),key=lambda f:f['unique_id'])
        if not matches:continue
        stats['pdf_records_matched']+=1
        r.update(gis_address_records=matches,gis_captured_at=snapshot['captured_at'])
        spread=max((geod.inv(a['lng'],a['lat'],b['lng'],b['lat'])[2] for a in matches for b in matches),default=0)
        if spread>5:
            stats['ambiguous_matches']+=1;r['gis_location_match']='multiple separated points';continue
        point=matches[0]
        r.pop('geocode_osm_id',None);r.pop('geocode_display_name',None)
        r.update(lat=point['lat'],lng=point['lng'],gis_location_match='exact address',gis_point_ids=[p['unique_id'] for p in matches],
            geocode_provider='Tel Aviv municipal GIS',geocode_label='מיקום מה־GIS העירוני של תל אביב · התאמת כתובת',location_precision='municipal-building')
        stats['pdf_records_located']+=1
    return stats
