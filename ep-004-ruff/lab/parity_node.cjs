// 用頁面上同一個 ruff.bundle.js＋wasm，在 Node 跑「一鍵修好」與「排版」，輸出 JSON
const fs = require('fs'), path = require('path');
globalThis.window = globalThis;
eval(fs.readFileSync(path.join(__dirname, '..', 'ruff.bundle.js'), 'utf8'));
(async () => {
  const api = window.RuffDemo;
  const ver = await api.load(fs.readFileSync(path.join(__dirname, '..', 'ruff_wasm_bg.wasm')));
  const select = process.argv[2].split(',');
  const ws = api.make(select);
  const out = {version: ver, select, files: {}};
  for (const f of process.argv.slice(3)) {
    const src = fs.readFileSync(f, 'utf8');
    const t0 = performance.now(); const diags = ws.check(src); const t1 = performance.now();
    const fixed = api.fixAll(ws, src);
    out.files[path.basename(f)] = {diagnostics: diags.map(d => d.code), checkMs: t1 - t0, fixed: fixed.src, applied: fixed.applied,
      remaining: ws.check(fixed.src).map(d => d.code), formatted: ws.format(src)};
  }
  process.stdout.write(JSON.stringify(out));
})();
