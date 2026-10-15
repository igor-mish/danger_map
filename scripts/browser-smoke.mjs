import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { chromium, request } from 'playwright';

const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||(existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),args:['--no-sandbox']});
let verifiedNetwork,page;
try {
 page=await browser.newPage({viewport:{width:1440,height:900}});
 // Forward real map/font responses through the platform-trusted Node HTTPS client.
 // This adapts cloud proxy trust for testing; never disable certificate verification.
 if(process.env.HTTPS_PROXY){
  verifiedNetwork=await request.newContext({proxy:{server:process.env.HTTPS_PROXY}});
  if(process.env.APP_URL?.startsWith('https://')){
   const origin=new URL(process.env.APP_URL).origin;
   await page.route(`${origin}/**`,async route=>{
    const response=await verifiedNetwork.get(route.request().url(),{headers:await route.request().allHeaders()});
    assert.equal(response.status(),200);try{await route.fulfill({response});}catch(e){if(!e.message.includes('Route is already handled'))throw e;}
   });
  }
  await page.route(/^https:\/\/(?:[abc]\.tile\.openstreetmap\.org|fonts\.googleapis\.com|fonts\.gstatic\.com)\//,async route=>{
   const response=await verifiedNetwork.get(route.request().url(),{headers:await route.request().allHeaders()});
   assert.equal(response.status(),200);assert.equal(response.headers()['x-blocked'],undefined);try{await route.fulfill({response});}catch(e){if(!e.message.includes('Route is already handled'))throw e;}
  });
 }
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.APP_URL||'http://localhost:5173/');
 await page.waitForFunction(()=>document.querySelector('#total').textContent==='890');
 await page.locator('#city').selectOption('בת ים');
 assert.equal(await page.locator('.card').count(),205);assert.equal(await page.locator('.building-marker').count(),205);
 assert.equal(await page.locator('.card .record-details dd').filter({hasText:/^פ$/}).count(),198);
 assert.equal(await page.locator('.card .record-details dd').filter({hasText:/^ל$/}).count(),7);
 await page.locator('.card').first().getByRole('button',{name:'הצגה במפה'}).click();
 await page.waitForFunction(()=>document.querySelectorAll('.leaflet-popup').length===1);await page.locator('.leaflet-popup').waitFor();assert.match(await page.locator('.leaflet-popup').innerText(),/קוד סטטוס במקור/);
 const caseLink=page.locator('.leaflet-popup').getByRole('link',{name:'פתיחת תיק הפיקוח'});
 assert.match(await caseLink.getAttribute('href'),/^https:\/\/handasi\.complot\.co\.il\//);
 assert.equal(await caseLink.getAttribute('target'),'_blank');
 await page.locator('#city').selectOption('תל אביב');await page.locator('#search').fill('אבן גבירול, רחוב 160');
 assert.equal(await page.locator('.card').count(),1);await page.locator('.card').getByRole('button',{name:'הצגה במפה'}).click();
 await page.waitForFunction(()=>document.querySelectorAll('.leaflet-popup').length===1);await page.locator('.leaflet-popup').waitFor();const details=await page.locator('.leaflet-popup').innerText();
 assert.match(details,/מאוכלס/);assert.match(details,/המתנה לאישורי מסירה/);assert.match(details,/06\/09\/2026/);assert.match(details,/26\/08\/2026/);assert.match(details,/15\/09\/2026/);
 const gisDetails=page.locator('.leaflet-popup .gis-details');await gisDetails.getByRole('heading',{name:'ממצאים ותיאור צו'}).waitFor();assert.match(await gisDetails.innerText(),/התאמה לפי כתובת/);assert.match(await gisDetails.innerText(),/11\/10\/2026/);
 await page.locator('#search').fill('אהרונסון, רחוב 28');assert.equal(await page.locator('.card').count(),1);assert.equal(await page.locator('.building-marker').count(),1);await page.locator('.card').getByRole('button',{name:'הצגה במפה'}).click();await page.waitForFunction(()=>document.querySelectorAll('.leaflet-popup').length===1);await page.locator('.leaflet-popup').waitFor();assert.match(await page.locator('.leaflet-popup').innerText(),/מיקום מה־GIS העירוני/);
 await page.locator('#search').fill('');
 await page.locator('#city').selectOption('חולון');
 assert.equal(await page.locator('.card').count(),70);
 assert.equal(await page.locator('#mapped').innerText(),'70');assert.match(await page.locator('#coverage').innerText(),/0 ללא מיקום/);
 assert.equal(await page.locator('.building-marker, .parcel-marker').count(),75);
 await page.locator('#search').fill('ראש פינה');assert.equal(await page.locator('.card').count(),1);assert.equal(await page.locator('.building-marker').count(),2);assert.equal(await page.locator('.card button').count(),2);
 await page.locator('#search').fill('וולפסון 26');assert.equal(await page.locator('.parcel-marker').count(),1);
 await page.locator('.card').getByRole('button',{name:'הצגה במפה'}).click();await page.waitForFunction(()=>document.querySelectorAll('.leaflet-popup').length===1);await page.locator('.leaflet-popup').waitFor();
 assert.match(await page.locator('.leaflet-popup').innerText(),/אינו מיקום מדויק/);assert.match(await page.locator('.leaflet-popup').getByRole('link',{name:'הצגת החלקה ב־GovMap'}).getAttribute('href'),/^https:\/\/www\.govmap\.gov\.il\//);
 await page.locator('#search').fill('');
 await page.locator('#pal-kal').check();assert.equal(await page.locator('.card').count(),87);
 await page.locator('#search').fill('וולפסון');assert.equal(await page.locator('.card').count(),2);
 await page.locator('summary').click();
 await page.locator('#upload').setInputFiles({name:'fixture.csv',mimeType:'text/csv',buffer:Buffer.from('city,address,lat,lng\nתל אביב,כתובת בדיקה בלבד,32.07,34.78\nחולון,בדיקה ללא מיקום,,\n')});
 await page.locator('#city').selectOption('');await page.locator('#search').fill('');
 assert.equal(await page.locator('.card').count(),2);
 assert.equal(await page.locator('.building-marker').count(),1);
 await page.getByRole('button',{name:'הצגה במפה',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.leaflet-popup').length===1);await page.locator('.leaflet-popup').waitFor();
 await page.getByRole('button',{name:'סימון מיקום ידני',exact:true}).click();
 assert.equal(await page.locator('#save-position').isDisabled(),true);
 await page.locator('#map').click({position:{x:300,y:400}});
 assert.equal(await page.locator('#save-position').isDisabled(),false);
 await page.getByRole('button',{name:'ביטול',exact:true}).click();assert.equal(await page.locator('#placement').isHidden(),true);
 await page.getByRole('button',{name:'סימון מיקום ידני',exact:true}).click();await page.locator('#map').click({position:{x:300,y:400}});
 await page.locator('#save-position').click();assert.equal(await page.locator('.building-marker').count(),2);
 assert.match(await page.evaluate(()=>localStorage.getItem('nafa-map-locations')),/בדיקה ללא מיקום/);
 const download=page.waitForEvent('download');await page.locator('#export').click();assert.equal((await download).suggestedFilename(),'municipal-buildings.csv');
 await page.locator('#upload').setInputFiles({name:'bad.csv',mimeType:'text/csv',buffer:Buffer.from('city,address\nירושלים,בדיקה\n')});
 assert.equal(await page.locator('.card').count(),2);await page.getByText('לא נמצאו רשומות תקינות בקובץ. הנתונים הקודמים נשמרו.',{exact:true}).waitFor();
 await page.reload();await page.waitForFunction(()=>document.querySelector('#total').textContent==='890');
 await page.waitForFunction(()=>[...document.querySelectorAll('.leaflet-tile')].some(i=>i.complete&&i.naturalWidth>=256));
 if(process.env.SCREENSHOT_PATH)await page.screenshot({path:process.env.SCREENSHOT_PATH});
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);
 console.log('PASS: real records, city/search/category filters, CSV import, marker/popup, manual location confirmation/cancel/storage, export, invalid CSV preservation, reload, real map tiles, mobile width; no JS errors.');
} catch(error) {console.error(error);throw error;} finally {await page?.unrouteAll({behavior:'ignoreErrors'});await browser.close();await verifiedNetwork?.dispose();}
