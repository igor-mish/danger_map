import test from 'node:test';
import assert from 'node:assert/strict';
import {searchAddresses} from './geocoder.js';
test('address lookup constrains geography, distinguishes street precision, and caches searches',async()=>{
 let calls=0;
 const fetcher=async url=>{calls++;const u=new URL(url);assert.equal(u.hostname,'nominatim.openstreetmap.org');assert.equal(u.searchParams.get('countrycodes'),'il');assert.equal(u.searchParams.get('bounded'),'1');return {ok:true,json:async()=>[
 {display_name:'סוקולוב 28 חולון',lat:'32.0227',lon:'34.7726',address:{town:'חולון',house_number:'28'}},
 {display_name:'רחוב בת ים',lat:'32.01',lon:'34.75',address:{city:'בת ים'}},
 {display_name:'ראשון לציון',lat:'32.00',lon:'34.79',address:{city:'ראשון לציון'}},
 {display_name:'bad coordinates',lat:'NaN',lon:'34.78',address:{city:'חולון'}}]};};
 const results=await searchAddresses('כתובת ניסוי חולון',fetcher);assert.equal(results.length,2);assert.match(results[1].precision,/ללא התאמה למספר בית/);
 assert.deepEqual(await searchAddresses('כתובת ניסוי חולון',fetcher),results);assert.equal(calls,1);
});
