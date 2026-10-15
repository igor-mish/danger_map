"""Apply user-supplied B144 address responses; preserve PDF case identity."""
def enrich_holon(records,snapshot):
    sources={(r['category'],r['address'],str(r['block']),str(r['parcel'])):r for r in snapshot['records']}
    if len(sources)!=len(snapshot['records']):raise ValueError('Duplicate B144 record')
    for r in records:
        if r['city']!='חולון':continue
        source=sources.get((r['category'],r['address'],str(r['block']),str(r['parcel'])))
        if source is None:raise ValueError('Missing Holon address evidence')
        points=source['locations']
        if not points:raise ValueError('Missing B144 points')
        for p in points:
            if not p['address'].startswith('חולון,') or not(31.97<p['lat']<32.05 and 34.74<p['lng']<34.84):raise ValueError('Invalid B144 address/coordinate')
        # Retain the previously reviewed GovMap parcel evidence for Wolfson 26.
        if r.get('location_precision')=='parcel':continue
        for k in ['geocode_osm_id','geocode_display_name','location_source_url']:r.pop(k,None)
        r.update(lat=points[0]['lat'],lng=points[0]['lng'],locations=points,location_precision='address',
            geocode_provider='B144 / Zoomap',geocode_label='איתור כתובת · B144 / Zoomap · לא אומת מול חלקה או כניסה',
            geocode_evidence=source['evidence'])
        if r['address'].startswith('בעל שם טוב'):r['geocode_label']+=' · קיימת אי־התאמה למיקום הקודם'
        if 'חניון' in r['address']:r['geocode_label']+=' · מיקום החניון עצמו לא אומת'
