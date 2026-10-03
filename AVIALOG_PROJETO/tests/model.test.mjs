import assert from 'node:assert/strict';
import {createWorkspace,simulate,nightLoad,parseRoutes,validateWorkspace,validateConfig} from '../lib/model.ts';
const w=createWorkspace();
const r=simulate(w.config,w.routes,w.trucks);
assert(r.trips.length>0);assert(r.delivered<=r.requested);assert(r.peak<=r.active);
for(const truck of w.trucks){const t=r.trips.filter(t=>t.truck===truck.id).sort((a,b)=>a.start-b.start);for(let i=1;i<t.length;i++)assert(t[i].start>=t[i-1].end-1e-6,'Caminhão sobreposto');}
for(const p of ['ave','real']){const t=r.trips.filter(t=>t.plant===p).sort((a,b)=>a.dock-b.dock);for(let i=1;i<t.length;i++)assert(t[i].dock>=t[i-1].dock+w.config.unloadMin-1e-6,'Doca sobreposta');for(const x of t)assert(x.dock+w.config.unloadMin<=w.config[p==='ave'?'aveClose':'realClose']+.01);}
for(const route of w.routes){assert(r.trips.filter(t=>t.routeId===route.id).reduce((s,t)=>s+t.birds,0)<=route.birds);}
for(const t of r.trips){assert(t.birds>0&&t.birds<=w.config.boxes*w.config.density);assert(t.start<=t.loadStart&&t.loadStart<t.loadedStart&&t.loadedStart<=t.arrival&&t.arrival<=t.dock&&t.dock<t.end);}
assert.equal(simulate({...w.config,unavailable:22},w.routes,w.trucks).trips.length,0);
assert.equal(simulate(w.config,[],w.trucks).trips.length,0);
assert.equal(simulate({...w.config,date:'2026-10-04'},w.routes,w.trucks).requested,0);
const horizon=simulate({...w.config,days:45},w.routes,w.trucks);assert(horizon.delivered<=w.routes.reduce((s,x)=>s+x.birds,0));assert.equal(horizon.days.length,45);
const blocked=w.routes.map(x=>({...x,blockedUntil:'2026-12-31'}));assert.equal(simulate(w.config,blocked,w.trucks).delivered,0);
const missing=w.routes.map(x=>({...x,aveMin:null,realMin:null}));assert.equal(simulate(w.config,missing,w.trucks).delivered,0);
const night=simulate({...w.config,nightOnly:true},w.routes,w.trucks);for(const t of night.trips){const m=((t.loadStart%1440)+1440)%1440;assert(m>=1140||m+90<=360);}
assert(nightLoad(23*60,500,1140,360)>=23*60);assert.equal(nightLoad(5*60+45,90,1140,360),1140);
const csv='granja;galpao;cidade;aves;vazio_min;ave_nova_min;real_min;destino\n"Granja;Sul";731B;Teste;8000;90;180;;ave\n';const parsed=parseRoutes(csv);assert.equal(parsed.errors.length,0);assert.equal(parsed.routes[0].shed,'731B');assert.equal(parsed.routes[0].realMin,null);assert.equal(parseRoutes(csv+csv.split('\n')[1]).errors.length,1);
assert.throws(()=>validateConfig({...w.config,residenceMin:10}));assert.throws(()=>validateWorkspace({...w,routes:[w.routes[0],w.routes[0]]}));
const fixed={...w.config,date:'2026-10-05',aveTarget:8000,realTarget:0,unavailable:0,aveClose:1380};const partial=simulate(fixed,[{...w.routes[0],birds:8000,emptyMin:1,aveMin:1}],w.trucks);assert.equal(partial.delivered,8000);assert.equal(partial.trips.length,3);assert.equal(partial.trips.at(-1).birds,476);
console.log(JSON.stringify({status:'passed',checks:'invariantes de frota, doca, estoque, janelas, horizonte, faltantes, noturno, CSV e sobras',base:{trips:r.trips.length,delivered:r.delivered,requested:r.requested,peak:r.peak,active:r.active},horizon:{trips:horizon.trips.length,delivered:horizon.delivered}},null,2));
