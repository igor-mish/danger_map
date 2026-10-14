"""Import all records from the public Bat Yam ArcGIS snapshot, preserving status codes."""
from datetime import datetime
from zoneinfo import ZoneInfo
from pyproj import Transformer


def bat_yam(snapshot):
    data=snapshot['data'];features=data['features']
    if snapshot['layer_id']!=17 or data['spatialReference']['wkid']!=2039:
        raise ValueError('Unexpected Bat Yam layer or CRS')
    ids=[f['attributes']['OBJECTID'] for f in features]
    if len(ids)!=len(set(ids)) or set(ids)!=set(snapshot['expected_object_ids']) or data.get('exceededTransferLimit'):
        raise ValueError('Bat Yam snapshot is incomplete or contains duplicate IDs')
    capture_date=datetime.fromisoformat(snapshot['captured_at'].replace('Z','+00:00')).astimezone(ZoneInfo('Asia/Jerusalem')).date().isoformat()
    transformer=Transformer.from_crs(2039,4326,always_xy=True)
    records=[]
    for feature in features:
        a=feature['attributes'];g=feature['geometry']
        lng,lat=transformer.transform(g['x'],g['y'])
        if not (31.98<lat<32.06 and 34.70<lng<34.80):
            raise ValueError(f"Invalid Bat Yam coordinates: {a['OBJECTID']}")
        x,y=transformer.transform(lng,lat,direction='INVERSE')
        if abs(x-g['x'])>0.1 or abs(y-g['y'])>0.1:
            raise ValueError('Coordinate round trip failed')
        address=' '.join(str(v).strip() for v in [a.get('St_name'),a.get('H_num')] if v is not None)
        records.append({'id':f"bat-yam-{a['OBJECTID']}",'city':'בת ים','address':address or f"כתובת חסרה במקור · רשומה {a['OBJECTID']}",
            'address_missing':not bool(address),'category':'dangerous','source_date':capture_date,'captured_at':snapshot['captured_at'],
            'case_id':a['Tik_Pikuch'],'status_code':a['Status'],'announcement_date':a['Announcement_date'],'end_date':a['End_date'],
            'block':a['Gush'],'parcel':a['Helka'],'case_url':a['LinkToTik'],'source_object_id':a['OBJECTID'],'source_layer':17,
            'source_attributes':a,'source_geometry':g,'lat':lat,'lng':lng,'geocode_label':'מיקום מה־GIS העירוני · המרה מרשת ישראל',
            'notes':f"גוש {a['Gush']} · חלקה {a['Helka']}"})
    return records
