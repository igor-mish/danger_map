import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeRows,filterRecords} from './data.js';
test('reject unsupported cities and empty addresses',()=>{
 const r=normalizeRows([{city:'ירושלים',address:'בדיקה'},{city:'חולון',address:''}]);
 assert.equal(r.records.length,0);assert.equal(r.errors.length,2);
});
test('unlocated rows remain visible without invented coordinates',()=>{
 const r=normalizeRows([{city:'חולון',address:'בדיקה',lat:'',lng:''},{city:'תל אביב',address:'בדיקה',lat:'0',lng:'0'}]);
 assert.equal(r.records.length,2);assert.ok(r.records.every(x=>!x.positioned&&x.lat===null));
});
test('valid coordinates and source attribution survive filtering',()=>{
 const {records}=normalizeRows([{city:'תל אביב',address:'רחוב בדיקה 1',lat:'32.07',lng:'34.78'},{city:'חולון',address:'רחוב אחר 2'}]);
 const result=filterRecords(records,'תל אביב','בדיקה');
 assert.equal(result.length,1);assert.equal(result[0].lat,32.07);assert.match(result[0].source.url,/tel-aviv/);
 assert.equal(filterRecords(records,'חולון','בדיקה').length,0);
});

test('Bat Yam includes both raw status codes and attributes',()=>{
 const {records,errors}=normalizeRows(['פ','ל'].map((status_code,i)=>({id:`bat-yam-${i}`,city:'בת ים',address:'רחוב בדיקה 1',lat:32.01,lng:34.75,status_code,case_id:123})));
 assert.equal(errors.length,0);assert.equal(records.length,2);assert.ok(records.every(r=>r.positioned));assert.deepEqual(records.map(r=>r.status_code),['פ','ל']);assert.equal(filterRecords(records,'בת ים','').length,2);
});
