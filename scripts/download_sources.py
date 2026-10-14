"""Download original municipal sources with TLS validation; preserve old files on failure."""
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'tel-aviv':'https://www.tel-aviv.gov.il/Residents/Construction/DocLib1/רשימת מבנים מסוכנים פעילים.pdf',
 'holon':'https://www.holon.muni.il/CityHall/Documents/רשימת מבנים מסוכנים חדש ומונגש - - 15.7.26.pdf',
}
for city,url in SOURCES.items():
    response=requests.get(url,timeout=60,headers={'User-Agent':'NafaDangerMap/0.1 (https://github.com/igor-mish/danger_map)'})
    response.raise_for_status()
    if not response.content.startswith(b'%PDF'):raise ValueError(f'{city}: source did not return PDF')
    target=ROOT/f'data/sources/{city}.pdf'
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_suffix('.tmp');temporary.write_bytes(response.content);temporary.replace(target)
    print(f'{city}: downloaded {len(response.content)} bytes. Run import_sources.py and review the audit before publishing changed data.')
