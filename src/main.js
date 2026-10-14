import L from 'leaflet';
import Papa from 'papaparse';
import 'leaflet/dist/leaflet.css';
import './style.css';
import {sources,normalizeRows,filterRecords} from './data.js';

const app=document.querySelector('#app');
app.innerHTML=`<header><div class="brand"><span class="logo">⌖</span><div><h1>מבנים מסוכנים</h1><p>תל אביב, חולון ובת ים · מידע ממקורות עירוניים</p></div></div><span class="badge">מפה עירונית</span></header><main><aside><div class="intro"><span class="eyebrow">מבט על העיר</span><h2>המידע במקום אחד.</h2><p>חיפוש מבנים שפורסמו ברשימות העירוניות, לפי עיר וכתובת.</p></div><div class="stats"><div><strong id="total">0</strong><span>רשומות בתצוגה</span></div><div><strong id="mapped">0</strong><span>רשומות עם מיקום</span></div></div><label for="search">חיפוש כתובת</label><input id="search" type="search" placeholder="שם רחוב או מספר בית…"><label for="city">עיר</label><select id="city"><option value="">כל הערים</option><option>תל אביב</option><option>חולון</option><option>בת ים</option></select><label class="category-toggle"><input id="pal-kal" type="checkbox"> הצגת מבני פל־קל מחולון (קטגוריה נפרדת)</label><p id="coverage" class="hint" aria-live="polite"></p><div class="list-title"><h3>תוצאות החיפוש</h3><span id="count">0</span></div><div id="results" aria-live="polite"></div><details><summary>מקורות וטעינת נתונים</summary><p>הרשימות העירוניות הן המקור לסטטוס המבנה. תאריך הרשימה אינו בהכרח תאריך העדכון האחרון.</p><div id="sources"></div><label class="upload" for="upload">טעינת CSV מאומת</label><input id="upload" type="file" accept=".csv,text/csv"><p class="hint">עמודות: city, address, lat, lng. אפשר להוסיף source_date ו־notes. כתובות ללא קואורדינטות יופיעו ברשימה בלבד. הנתונים נשארים בדפדפן.</p><button id="download">הורדת תבנית CSV</button> <button id="export">ייצוא כל הרשומות</button></details></aside><section class="map-area"><div id="map" aria-label="מפת מבנים מסוכנים"></div><div class="map-label"><span class="dot"></span>מבנה ברשימה העירונית</div><div id="status" role="status"></div><div id="placement" hidden></div></section></main><footer>המידע מוצג לעיון ואינו מחליף בדיקה עדכנית מול הרשות המקומית. בת ים: כל קודי הסטטוס מוצגים; צילום הנתונים מ־14.10.2026.</footer>`;
const map=L.map('map',{zoomControl:false}).setView([32.045,34.785],12);
L.control.zoom({position:'bottomleft'}).addTo(map);
const tiles=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',subdomains:'abc',maxZoom:19}).addTo(map);
tiles.on('tileerror',()=>{document.querySelector('#status').textContent='לא ניתן לטעון את מפת הרקע. יש לבדוק חיבור וגישה לשרת המפות.';});
const markers=L.layerGroup().addTo(map);let records=[];let imported=false;let placement=null,placementMarker=null;
let overrides={};try{overrides=JSON.parse(localStorage.getItem('nafa-map-locations')||'{}');}catch{}
const icon=L.divIcon({className:'building-marker',html:'<span></span>',iconSize:[22,22],iconAnchor:[11,11]});
function el(tag,text,className){const e=document.createElement(tag);e.textContent=text;if(className)e.className=className;return e;}
function sourceLink(source){const a=el('a',`רשימת מבנים מסוכנים · ${source.city}`);a.href=source.localUrl||source.url;a.target='_blank';a.rel='noopener noreferrer';return a;}
function caseLink(record){
 if(!record.case_url)return null;
 try{const url=new URL(record.case_url);if(url.protocol!=='https:'||url.hostname!=='handasi.complot.co.il')return null;
 const a=el('a','פתיחת תיק הפיקוח');a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';a.className='case-link';return a;}catch{return null;}
}
function detailList(record){
 const items=[];
 if(record.case_id)items.push(['מספר תיק',record.case_id]);
 if(record.city==='תל אביב')items.push(['מצב אכלוס',record.occupancy],['מצב טיפול',record.treatment],['סעיף הצו',record.section],['פתיחת תיק',record.case_opened],['ביקור אחרון',record.last_visit],['מצב טיפול מתאריך',record.treatment_since],['סימון מבנה שמור במקור',record.preserved_marker||'ללא סימון']);
 if(record.city==='בת ים')items.push(['מספר רשומה במקור',record.source_object_id],['קוד סטטוס במקור',record.status_code],['תאריך הכרזה',record.announcement_date],['תאריך סיום',record.end_date],['גוש',record.block],['חלקה',record.parcel]);
 if(record.source_date)items.push([record.city==='בת ים'?'צילום נתוני GIS':'תאריך מסמך המקור',record.source_date]);
 const dl=el('dl','','record-details');items.forEach(([label,value])=>{if(value!==undefined&&value!==null&&String(value).trim()!=='')dl.append(el('dt',label),el('dd',String(value)));});return dl;
}
sources.forEach(s=>{const box=el('div');box.append(sourceLink(s),el('p',`${s.dateKind==='snapshot'?'צילום הנתונים':'תאריך המסמך'}: ${s.date}`));const original=el('a','פתיחה באתר העירייה');original.href=s.url;original.target='_blank';original.rel='noopener noreferrer';box.append(original);document.querySelector('#sources').append(box);});
function render(){
 const selected=records.filter(r=>r.category!=='pal-kal'||document.querySelector('#pal-kal').checked);
 const visible=filterRecords(selected,document.querySelector('#city').value,document.querySelector('#search').value).sort((a,b)=>Number(Boolean(a.address_missing))-Number(Boolean(b.address_missing))||a.address.localeCompare(b.address,'he',{numeric:true}));
 document.querySelector('#total').textContent=visible.length;document.querySelector('#mapped').textContent=visible.filter(r=>r.positioned).length;document.querySelector('#count').textContent=visible.length;
 const positioned=visible.filter(r=>r.positioned).length;document.querySelector('#coverage').textContent=`${visible.length} רשומות ברשימה · ${positioned} עם מיקום · ${visible.length-positioned} ללא מיקום. כתובות ללא מיקום מופיעות ברשימה בלבד.`;
 markers.clearLayers();const list=document.querySelector('#results');list.replaceChildren();
 if(!records.length){list.append(el('h3','הנתונים העירוניים טרם נטענו'),el('p','לא נטענו רשומות. ניתן לנסות לרענן או לטעון קובץ CSV תחת ״מקורות וטעינת נתונים״.','empty'));}
 else if(!visible.length)list.append(el('p','לא נמצאו כתובות התואמות לחיפוש.','empty'));
 visible.forEach(r=>{
  const card=el('article','','card');card.append(el('small',r.city+(r.category==='pal-kal'?' · מבנה פל־קל':'')),el('h3',r.address));
  if(r.source_page)card.append(el('p',`עמוד ${r.source_page} במסמך`));
  card.append(detailList(r));if(r.notes&&r.city!=='תל אביב')card.append(el('p',r.notes));const link=caseLink(r);if(link)card.append(link);
  card.append(sourceLink(r.source));
  if(r.positioned){const content=el('div');content.append(el('strong',r.address),el('p',r.city),detailList(r));const popupCaseLink=caseLink(r);if(popupCaseLink)content.append(popupCaseLink);content.append(sourceLink(r.source),el('p',r.geocode_label||'מיקום מקובץ הנתונים'));const marker=L.marker([r.lat,r.lng],{icon}).bindPopup(content,{maxWidth:360,maxHeight:340}).addTo(markers);const b=el('button','הצגה במפה');b.onclick=()=>{map.flyTo([r.lat,r.lng],17);marker.openPopup();};card.append(b);}
  else{card.append(el('p','מיקום טרם אומת · אינו מוצג במפה','unmapped'));if(!r.address_missing){const place=el('button','סימון מיקום ידני');place.className='secondary';place.onclick=()=>beginPlacement(r);card.append(place);}}list.append(card);
 });
}
document.querySelector('#pal-kal').addEventListener('change',render);
document.querySelector('#search').addEventListener('input',render);document.querySelector('#city').addEventListener('change',render);
document.querySelector('#upload').addEventListener('change',e=>{
 const file=e.target.files[0];if(!file)return;
 Papa.parse(file,{header:true,skipEmptyLines:true,complete:result=>{
  if(result.errors.length){document.querySelector('#status').textContent='שגיאה במבנה קובץ ה־CSV. הנתונים הקודמים נשמרו.';return;}
  const parsed=normalizeRows(result.data);if(!parsed.records.length){document.querySelector('#status').textContent='לא נמצאו רשומות תקינות בקובץ. הנתונים הקודמים נשמרו.';return;}cancelPlacement();imported=true;records=parsed.records;render();document.querySelector('#status').textContent=`נטענו ${records.length} רשומות. ${records.filter(r=>!r.positioned).length} ממתינות למיקום.${parsed.errors.length?' '+parsed.errors.slice(0,3).join('; '):''}`;
  const located=records.filter(r=>r.positioned);if(located.length)map.fitBounds(located.map(r=>[r.lat,r.lng]),{padding:[40,40],maxZoom:16});
 },error:()=>{document.querySelector('#status').textContent='לא ניתן לקרוא את הקובץ.';}});
});
document.querySelector('#download').onclick=()=>{const url=URL.createObjectURL(new Blob(['\ufeffcity,address,lat,lng,source_date,notes\n'],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='buildings-template.csv';a.click();URL.revokeObjectURL(url);};
render();
fetch(`${import.meta.env.BASE_URL}data/buildings.json`).then(r=>{if(!r.ok)throw Error('data');return r.json();}).then(data=>{
 if(imported)return;
 const parsed=normalizeRows(data.records);records=parsed.records.map(r=>{const saved=overrides[r.id];return saved?.address===r.address?normalizeRows([{...r,...saved}]).records[0]:r;});render();
 const pending=records.filter(r=>r.category!=='pal-kal'&&!r.positioned).length;
 document.querySelector('#status').textContent=`נתונים מהמקורות העירוניים: ${records.filter(r=>r.city==='תל אביב').length} תיקים בתל אביב, ${records.filter(r=>r.city==='חולון'&&r.category==='dangerous').length} רשומות מבנים מסוכנים בחולון ${records.filter(r=>r.city==='בת ים').length} רשומות בבת ים (כל הסטטוסים; צילום 14.10.2026), ו־${records.filter(r=>r.category==='pal-kal').length} מבני פל־קל בקטגוריה נפרדת. ${pending} רשומות מסוכנות ממתינות למיקום. הספירה היא של רשומות; ייתכנו כמה תיקים באותה כתובת.`;
}).catch(()=>{document.querySelector('#status').textContent='טעינת הרשימות נכשלה. ניתן לרענן או לטעון CSV ידנית.';});

function cancelPlacement(){placement=null;if(placementMarker){map.removeLayer(placementMarker);placementMarker=null;}document.querySelector('#placement').hidden=true;}
function beginPlacement(record){
 cancelPlacement();placement=record;const panel=document.querySelector('#placement');panel.replaceChildren(el('strong',record.address),el('p','בחר את מיקום המבנה על המפה. שמירה תתאפשר לאחר בחירת נקודה; זהו סימון ידני שאינו אישור עירוני.'));
 const save=el('button','שמירת המיקום');save.id='save-position';save.disabled=true;
 save.onclick=()=>{const point=placementMarker.getLatLng();const saved={address:record.address,lat:point.lat,lng:point.lng,geocode_label:'מיקום שסומן ידנית · לא נבדק מול העירייה'};
 try{localStorage.setItem('nafa-map-locations',JSON.stringify({...overrides,[record.id]:saved}));overrides[record.id]=saved;}catch{document.querySelector('#status').textContent='לא ניתן לשמור בדפדפן. ניתן לייצא את המיקום בקובץ CSV.';}
 Object.assign(record,saved,{positioned:true});cancelPlacement();render();};
 const cancel=el('button','ביטול');cancel.className='secondary';cancel.onclick=cancelPlacement;panel.append(save,cancel);panel.hidden=false;
 map.flyTo(record.city==='בת ים'?[32.015,34.75]:record.city==='חולון'?[32.015,34.78]:[32.065,34.78],14);panel.scrollIntoView({block:'nearest'});
}
map.on('click',event=>{if(!placement)return;const {lat,lng}=event.latlng;if(lat<31.9||lat>32.2||lng<34.65||lng>34.95)return;
 if(placementMarker)placementMarker.setLatLng(event.latlng);else placementMarker=L.marker(event.latlng,{icon}).addTo(map);
 document.querySelector('#save-position').disabled=false;
});
document.querySelector('#export').onclick=()=>{
 const csv=Papa.unparse(records.map(({id,city,address,lat,lng,source_date,source_page,category,case_id,case_url,status_code,announcement_date,end_date,source_object_id,occupancy,treatment,section,case_opened,last_visit,treatment_since,preserved_marker,notes,geocode_label})=>({id,city,address,lat,lng,source_date,source_page,category,case_id,case_url,status_code,announcement_date,end_date,source_object_id,occupancy,treatment,section,case_opened,last_visit,treatment_since,preserved_marker,notes,geocode_label})),{escapeFormulae:true});
 const url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='municipal-buildings.csv';a.click();URL.revokeObjectURL(url);
};
