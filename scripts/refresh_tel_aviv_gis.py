"""Download and validate a full public Tel Aviv GIS snapshot. No API key required."""
from datetime import datetime,timezone
import json
from pathlib import Path
import requests
from data_lock import data_lock
from tel_aviv_gis import enrich_tel_aviv

ROOT=Path(__file__).resolve().parents[1]
SERVICE='https://gisn.tel-aviv.gov.il/arcgis/rest/services/WM/IView2WM/MapServer/591'

def download(session):
    def query(**params):
        response=session.get(SERVICE+'/query',params={'f':'json',**params},timeout=45)
        response.raise_for_status();data=response.json()
        if data.get('error'):raise ValueError(data['error'])
        return data
    expected=query(where='1=1',returnIdsOnly='true');ids=expected['objectIds'];field=expected['objectIdFieldName']
    if not ids or len(ids)!=len(set(ids)):raise ValueError('Invalid/empty Tel Aviv ID response; existing snapshot retained')
    result=None;features=[]
    for start in range(0,len(ids),300):
        part=query(objectIds=','.join(str(x) for x in ids[start:start+300]),outFields='*',returnGeometry='true',outSR=3857)
        if part.get('exceededTransferLimit'):raise ValueError('Transfer limit exceeded')
        if result is None:result={k:v for k,v in part.items() if k!='features'}
        features.extend(part['features'])
    returned=[f['attributes'][field] for f in features]
    if len(returned)!=len(set(returned)) or set(returned)!=set(ids):raise ValueError('Incomplete or duplicate Tel Aviv features')
    if set(query(where='1=1',returnIdsOnly='true')['objectIds'])!=set(ids):raise ValueError('Layer changed during download; retry later')
    result['features']=features
    snapshot={'layer_id':591,'service_url':SERVICE,'captured_at':datetime.now(timezone.utc).isoformat(),'request_filter':'1=1',
        'all_layer_records_verified':True,'expected_object_ids':ids,'object_id_field':field,'data':result}
    enrich_tel_aviv([],snapshot)  # Validate geometry, identifiers and schema before saving.
    return snapshot

if __name__=='__main__':
    with data_lock(),requests.Session() as session:
        snapshot=download(session);target=ROOT/'public/sources/tel-aviv-gis.json';temporary=target.with_suffix('.tmp')
        temporary.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2));temporary.replace(target)
        print(f"Downloaded and validated {len(snapshot['data']['features'])} Tel Aviv GIS records. Run scripts/import_sources.py to update the map dataset, then build and publish.")
