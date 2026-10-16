const cache=new Map();let lastRequest=0;
export async function searchAddresses(query,fetcher=fetch){
 const text=query.trim();if(text.length<3)throw Error('יש להזין כתובת עם שם עיר.');
 if(cache.has(text))return cache.get(text);
 if(Date.now()-lastRequest<1200)throw Error('יש להמתין רגע לפני חיפוש נוסף.');
 lastRequest=Date.now();
 const params=new URLSearchParams({q:text,format:'jsonv2',addressdetails:'1',limit:'5',countrycodes:'il','accept-language':'he',viewbox:'34.70,32.18,34.90,31.97',bounded:'1'});
 const response=await fetcher(`https://nominatim.openstreetmap.org/search?${params}`,{signal:AbortSignal.timeout(15000),referrerPolicy:'strict-origin-when-cross-origin'});
 if(!response.ok)throw Error('שירות איתור הכתובות אינו זמין כרגע. נסו שוב מאוחר יותר.');
 const data=await response.json();if(!Array.isArray(data))throw Error('התקבלה תשובה לא תקינה משירות הכתובות.');
 const results=data.filter(p=>{
  const city=p.address?.city||p.address?.town||p.address?.municipality||'';
  return /חולון|בת.?ים|תל.?אביב/.test(city)&&Number.isFinite(Number(p.lat))&&Number.isFinite(Number(p.lon))&&Number(p.lat)>=31.97&&Number(p.lat)<=32.18&&Number(p.lon)>=34.70&&Number(p.lon)<=34.90;
 }).map(p=>({label:p.display_name,lat:Number(p.lat),lng:Number(p.lon),precision:p.address?.house_number?'כתובת שאותרה — מיקום משוער':'אזור או רחוב — ללא התאמה למספר בית'}));
 cache.set(text,results);return results;
}
