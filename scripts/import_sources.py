"""Import the supplied municipal PDFs. Coordinates are never inferred here."""
import hashlib
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from bidi.algorithm import get_display

ROOT = Path(__file__).resolve().parents[1]
CASE = re.compile(r'03-\d{4}-\d{4}')

def text(pdf):
    return subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)

def clean(s):
    return re.sub('[\u202a-\u202e\u200e\u200f\u2066-\u2069]', '', s)

def column(words, low, high):
    selected = [w for w in words if low <= float(w.get('xMin')) < high]
    lines = {}
    for w in selected:
        lines.setdefault(round(float(w.get('yMin'))), []).append(w)
    return ' '.join(get_display(' '.join(w.text or '' for w in sorted(line, key=lambda w:float(w.get('xMin')))), base_dir='R') for _,line in sorted(lines.items())).strip()

def tel_aviv(pdf):
    date=datetime.strptime(re.search(r'תאריך\s*(\d{2}/\d{2}/\d{4})',clean(text(pdf))).group(1),'%d/%m/%Y').date().isoformat()
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp) / 'bbox.html'
        subprocess.run(['pdftotext', '-bbox', str(pdf), str(target)], check=True)
        pages = ET.parse(target).getroot().findall('.//{*}page')
    records = []
    for page_number, page in enumerate(pages, 1):
        words = page.findall('{*}word')
        cases = sorted([w for w in words if CASE.fullmatch(w.text or '')],key=lambda w:float(w.get('yMin')))
        for index, case in enumerate(cases):
            y=float(case.get('yMin'))
            # Midpoints isolate each row, including multiline address/status cells.
            low=(float(cases[index-1].get('yMin'))+y)/2 if index else y-6
            high=(float(cases[index+1].get('yMin'))+y)/2 if index+1<len(cases) else y+15
            row=[w for w in words if low<=float(w.get('yMin'))<high]
            address=column(row,390,504)
            code=column(row,375,389)
            status=column(row,122,219)
            occupancy=column(row,220,260)
            records.append({'id':case.text,'city':'תל אביב','address':address or f'כתובת חסרה במקור · תיק {case.text}',
                'address_missing':not bool(address),'category':'dangerous','source_date':date,'source_page':page_number,
                'case_id':case.text,'section':code,'treatment':status,'occupancy':occupancy,
                'notes':f'סעיף {code} · {status} · {occupancy}', 'lat':None,'lng':None})
    declared=int(re.search(r'לדו"ח\s+(\d+)', clean(text(pdf))).group(1))
    if len(records)!=declared:
        raise ValueError(f'Tel Aviv extracted {len(records)} rows, PDF declares {declared}')
    return records

def holon(pdf):
    date=datetime.strptime(re.search(r'תאריך עדכון\s*(\d{1,2}/\d{1,2}/\d{4})',clean(text(pdf))).group(1),'%d/%m/%Y').date().isoformat()
    records=[];category='dangerous';serials={'dangerous':[],'pal-kal':[]}
    for page_number,page in enumerate(clean(text(pdf)).split('\f'),1):
        for line in page.splitlines():
            if 'מבני פלקל' in line:category='pal-kal'
            match=re.match(r'^\s*(\d+(?:\+\d+)?)\s+(\d{4})\s+(.+?)\s+(\d+)\s*$',line)
            if not match:continue
            parcel,block,address,serial=match.groups()
            extracted_address=address
            # These three bidi extraction corrections were checked against the rendered PDF.
            corrections={5:'אילת 36 (חניון מרכז מסחרי)',23:"אהרונוביץ' 40, דירה 6",28:"שד' קוגל 18 ג'"}
            if category=='dangerous':address=corrections.get(int(serial),address)
            serials[category].append(int(serial))
            records.append({'id':f'holon-{category}-{serial}','city':'חולון','address':address,
                'category':category,'extracted_address':extracted_address,'source_date':date,'source_page':page_number,
                'parcel':parcel,'block':block,'notes':f'גוש {block} · חלקה {parcel}', 'lat':None,'lng':None})
    for category,numbers in serials.items():
        if numbers != list(range(1,max(numbers)+1)):
            raise ValueError(f'Holon non-contiguous row extraction: {category}')
    return records

def main():
    ta=ROOT/'data/sources/tel-aviv.pdf';ho=ROOT/'data/sources/holon.pdf'
    if not ta.exists():ta=ROOT/'public/sources/tel-aviv.pdf'
    if not ho.exists():ho=ROOT/'public/sources/holon.pdf'
    ta_records=tel_aviv(ta);ho_records=holon(ho)
    records=ta_records+ho_records
    target=ROOT/'public/data/buildings.json'
    if target.exists():
        old={r['id']:r for r in json.loads(target.read_text())['records']}
        for record in records:
            previous=old.get(record['id'],{})
            if previous.get('address')==record['address']:
                record.update({k:v for k,v in previous.items() if k in ('lat','lng') or k.startswith('geocode_')})
    payload={'records':records,'sources':[
        {'city':'תל אביב','file':'tel-aviv.pdf','date':ta_records[0]['source_date'],'sha256':hashlib.sha256(ta.read_bytes()).hexdigest()},
        {'city':'חולון','file':'holon.pdf','date':ho_records[0]['source_date'],'sha256':hashlib.sha256(ho.read_bytes()).hexdigest()}],
        'audit':{'tel_aviv_rows':len(ta_records),'holon_dangerous_rows':sum(r['city']=='חולון' and r['category']=='dangerous' for r in records),
        'holon_pal_kal_rows':sum(r['category']=='pal-kal' for r in records),
        'missing_addresses':sum(r.get('address_missing',False) for r in records),
        'notes':['חולון: שורות 69 ו־70 ברשימת המבנים המסוכנים ריקות במקור ולא יובאו.', 'תל אביב: כמה תיקים עשויים להתייחס לאותה כתובת. ספירת הרשומות היא ספירת תיקים, לא מספר מבנים ייחודיים.']}}
    temporary=target.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    temporary.replace(target)
    print(json.dumps(payload['audit'],ensure_ascii=False,indent=2))

if __name__=='__main__':
    from data_lock import data_lock
    with data_lock():main()
