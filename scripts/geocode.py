"""Rate-limited, cached Nominatim geocoding. Unmatched/ambiguous rows stay unlocated."""
import argparse
import difflib
import json
import math
from pathlib import Path
import re
import time
import unicodedata
import requests

ROOT=Path(__file__).resolve().parents[1]

def normalized(s):
    return re.sub(r'[^\w]', '', unicodedata.normalize('NFKC',s)).casefold()

def query_address(record):
    if record.get('address_missing'):return None
    text=record['address']
    # Comments/apartment/entrance are metadata, never a different house number.
    text=re.sub(r'\([^)]*\)','',text)
    text=re.sub(r',?\s*(?:דירה|כניסה)\s+.*','',text)
    text=re.sub(r',\s*(רחוב|שדרות|שביל|כיכר|דרך|סמטה|מתחם)\s+', ' ', text)
    if re.search(r'\d+\s*[-/]\s*\d+',text):return None
    match=re.search(r'^(.*?)\s+(\d+[א-ת]?(?:\s+[א-ת][\x27״]?)?)\s*$',text)
    if not match:return None
    street,house=match.groups()
    return street.strip(),house.strip()

def suitable(record,street,house,candidate):
    a=candidate.get('address',{})
    city=a.get('city') or a.get('town') or ''
    city_ok= ('תלאביב' in normalized(city) or 'telaviv' in normalized(city)) if record['city']=='תל אביב' else ('חולון' in city or city.lower()=='holon')
    if not city_ok or a.get('country_code')!='il':return False
    if normalized(a.get('house_number','')) != normalized(house):return False
    road=a.get('road','')
    def street_key(value):
        return ''.join(sorted(normalized(w) for w in value.split() if w not in ('רחוב','דרך','שדרות',"שד'",'שביל','כיכר','ככר')))
    # Common municipal short names and the established Baal Shem Tov acronym.
    aliases={'בעלשםטוב':'הבעשט'}
    short=aliases.get(normalized(street),normalized(street))
    road_tokens={normalized(w) for w in road.split()}
    exact_short_name=len(short)>=4 and short in road_tokens
    if not road or not exact_short_name and difflib.SequenceMatcher(None,street_key(street),street_key(road)).ratio()<0.80:return False
    lat,lng=float(candidate['lat']),float(candidate['lon'])
    return 31.9<lat<32.2 and 34.65<lng<34.95

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--limit',type=int,default=1000,help='Maximum new network queries')
    parser.add_argument('--city',choices=['תל אביב','חולון'],help='Limit address lookups to one city')
    args=parser.parse_args()
    target=ROOT/'public/data/buildings.json';cachepath=ROOT/'data/geocode-cache.json'
    data=json.loads(target.read_text());cache=json.loads(cachepath.read_text()) if cachepath.exists() else {}
    session=requests.Session();session.headers.update({'User-Agent':'NafaDangerMap/0.1 (https://github.com/igor-mish/danger_map)','Accept-Language':'he'})
    count=0;last=0
    for record in data['records']:
        if args.city and record['city']!=args.city:continue
        if record.get('lat') is not None:continue
        address=query_address(record)
        if not address:continue
        street,house=address;key=f"{record['city']}|{street}|{house}"
        if key not in cache:
            if count>=args.limit:continue
            time.sleep(max(0,1.1-(time.monotonic()-last)))
            response=session.get('https://nominatim.openstreetmap.org/search',params={
                'street':f'{house} {street}','city':record['city'],'countrycodes':'il','format':'jsonv2',
                'addressdetails':1,'limit':5,'accept-language':'he'},timeout=30)
            last=time.monotonic()
            # Stop on access/rate-limit errors; do not cache errors as empty results.
            response.raise_for_status()
            candidates=response.json()
            if not isinstance(candidates,list):raise ValueError('Unexpected geocoder response')
            cache[key]=candidates;count+=1
            if count % 25 == 0: print(f'Geocoding: {count} new queries; {sum(r.get("lat") is not None for r in data["records"])} located rows', flush=True)
            cachetemp=cachepath.with_suffix('.tmp')
            cachetemp.write_text(json.dumps(cache,ensure_ascii=False,indent=2))
            cachetemp.replace(cachepath)
        matches=[c for c in cache[key] if suitable(record,street,house,c)]
        # Multiple OSM features (building, address node, business) can share an address.
        # Accept only a tight spatial cluster; dispersed candidates remain unresolved.
        spread=max((math.hypot((float(a['lat'])-float(b['lat']))*111000,(float(a['lon'])-float(b['lon']))*94000) for a in matches for b in matches),default=0)
        if matches and spread<=35:
            c=min(matches,key=lambda m:0 if m.get('type') in ('house','apartments') else 1);record.update(lat=float(c['lat']),lng=float(c['lon']),geocode_label='התאמת כתובת אוטומטית · OpenStreetMap',geocode_display_name=c['display_name'],geocode_provider='Nominatim',geocode_osm_id=c.get('osm_id'))
            temporary=target.with_suffix('.tmp')
            temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2))
            temporary.replace(target)
    print(f"Mapped {sum(r.get('lat') is not None for r in data['records'])}/{len(data['records'])} source rows; new requests: {count}. Unmatched or ambiguous addresses remain in the list.")

if __name__=='__main__':
    from data_lock import data_lock
    with data_lock():main()
