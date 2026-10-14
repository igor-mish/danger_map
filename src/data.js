const base = import.meta.env?.BASE_URL || '/';
export const sources = [
 {id:'tel-aviv',city:'תל אביב',date:'08.10.2026',localUrl:`${base}sources/tel-aviv.pdf`,url:'https://www.tel-aviv.gov.il/Residents/Construction/DocLib1/רשימת מבנים מסוכנים פעילים.pdf'},
 {id:'holon',city:'חולון',date:'19.05.2026',localUrl:`${base}sources/holon.pdf`,url:'https://www.holon.muni.il/CityHall/Documents/רשימת מבנים מסוכנים חדש ומונגש - 190526 (002).pdf'}
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
export function filterRecords(records,city,query){return records.filter(r=>(!city||r.city===city)&&`${r.address} ${r.city}`.includes(query.trim()));}
