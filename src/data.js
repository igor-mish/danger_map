const base = import.meta.env?.BASE_URL || '/';
export const sources = [
 {id:'tel-aviv',city:'תל אביב',date:'08.10.2026',localUrl:`${base}sources/tel-aviv.pdf`,url:'https://www.tel-aviv.gov.il/Residents/Construction/DocLib1/רשימת מבנים מסוכנים פעילים.pdf'},
 {id:'holon',city:'חולון',date:'15.07.2026',localUrl:`${base}sources/holon.pdf`,url:'https://www.holon.muni.il/CityHall/Documents/רשימת מבנים מסוכנים חדש ומונגש - - 15.7.26.pdf'},
 {id:'bat-yam',city:'בת ים',date:'14.10.2026',dateKind:'snapshot',localUrl:`${base}sources/bat-yam.json`,url:'https://batyam.complot.co.il/searchdbuilding/#search'}
];
export function normalizeRows(rows) {
 const errors=[], records=[];
 rows.forEach((r,i)=>{
  const city=String(r.city??'').trim(),address=String(r.address??'').trim();
  if(!sources.some(s=>s.city===city)||!address){errors.push(`שורה ${i+2}: נדרשות עיר נתמכת וכתובת`);return;}
  const lat=Number(r.lat),lng=Number(r.lng);
  const positioned=String(r.lat??'').trim()!==''&&String(r.lng??'').trim()!==''&&Number.isFinite(lat)&&Number.isFinite(lng)&&lat>=31.9&&lat<=32.2&&lng>=34.65&&lng<=34.95;
  records.push({...r,id:r.id||`${city}:${address}:${i}`,category:r.category==='pal-kal'?'pal-kal':'dangerous',city,address,lat:positioned?lat:null,lng:positioned?lng:null,source:sources.find(s=>s.city===city),source_date:String(r.source_date??''),notes:String(r.notes??''),positioned});
 });
 return {records,errors};
}
function addressTokens(text){
 const aliases={'ככר':'כיכר','ויצמן':'וייצמן'};
 return String(text??'').normalize('NFKC').toLowerCase().replace(/[\u0591-\u05c7]/g,'').replace(/["'׳״]/g,'').replace(/(\d)([א-ת])/g,'$1 $2').match(/[\p{L}]+|\d+/gu)?.map(w=>aliases[w]||w).filter(w=>!['רחוב','רח','שדרות','שד','כיכר','דרך','סמטה'].includes(w))||[];
}
export function filterRecords(records,city,query){
 const wanted=addressTokens(query);
 return records.filter(r=>{
  if(city&&r.city!==city)return false;
  const fields=[r.address,r.city,...(r.locations||[]).map(p=>p.address)].join(' ');
  const available=addressTokens(fields);
  return wanted.every(q=>available.some(w=>/^\d+$/.test(q)?w===q:w.includes(q)));
 });
}

export function nearbyRecords(records,center,radius){
 const radians=Math.PI/180;
 return records.filter(r=>(r.locations?.length?r.locations:[r]).some(p=>{
  if(p.lat==null||p.lng==null)return false;
  const a=(p.lat-center.lat)*radians,b=(p.lng-center.lng)*radians;
  const h=Math.sin(a/2)**2+Math.cos(center.lat*radians)*Math.cos(p.lat*radians)*Math.sin(b/2)**2;
  return 6371000*2*Math.asin(Math.sqrt(Math.min(1,h)))<=radius;
 }));
}
