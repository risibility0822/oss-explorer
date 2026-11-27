import init, {Workspace, PositionEncoding} from '@astral-sh/ruff-wasm-web';
// 把 (row, column)（1 起算、UTF-16）換成字串位置
function offsets(src){ const o=[0]; for(let i=0;i<src.length;i++) if(src[i]==='\n') o.push(i+1); return o; }
function pos(o, loc){ return o[loc.row-1] + loc.column - 1; }
// 套用一輪修正：照位置從後往前，跳過互相重疊的修正（Ruff 命令列也是重疊就留到下一輪）
function applyOnce(src, diags){
  const o=offsets(src), fixes=[];
  for(const d of diags){ if(!d.fix||!d.fix.edits.length) continue;
    const ed=d.fix.edits.map(e=>({s:pos(o,e.location),e:pos(o,e.end_location),t:e.content??''})).sort((a,b)=>a.s-b.s);
    fixes.push({code:d.code, ed, s:ed[0].s, e:Math.max(...ed.map(x=>x.e))}); }
  fixes.sort((a,b)=>a.s-b.s);
  const chosen=[]; let last=-1;
  for(const f of fixes){ if(f.s>last || (f.s===last && f.e===f.s)){ chosen.push(f); last=Math.max(f.e, f.s); } }
  if(!chosen.length) return {src, codes:[]};
  const edits=chosen.flatMap(f=>f.ed).sort((a,b)=>b.s-a.s||b.e-a.e);
  let out=src; for(const x of edits) out=out.slice(0,x.s)+x.t+out.slice(x.e);
  return {src:out, codes:chosen.map(f=>f.code)};
}
function fixAll(ws, src){
  const applied=[];
  for(let pass=0; pass<10; pass++){
    const r=applyOnce(src, ws.check(src)); if(!r.codes.length) break;
    applied.push(...r.codes); src=r.src;
  }
  return {src, applied};
}
const api = {
  async load(wasm){ await init({module_or_path: wasm}); return Workspace.version(); },
  make(select, lineLength){
    const s = Workspace.defaultSettings();
    return new Workspace({...s, 'line-length': lineLength || 88, lint:{select}}, PositionEncoding.Utf16);
  },
  fixAll, offsets
};
if (typeof window !== 'undefined') window.RuffDemo = api;
export default api;
