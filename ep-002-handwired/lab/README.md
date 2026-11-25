# 第 002 集 lab：handwired 的 FizzBuzz 網路

2026-11-25 在雲端工作區（2 CPU、無 GPU、Node v22.23.5、esbuild 0.25.12）實際執行。

## 檔案

| 檔案 | 用途 |
|---|---|
| `src/fizzbuzz.ts` | FizzBuzz 數值程式（建構程式）：333＋200 次比較器呼叫（15 的倍數 66 個共用，實際 467 個 ≥ 比較器）、餘數、AND，輸出四個 0/1 |
| `src/noise.ts` | 「解凍權重」：每個係數與偏差乘上 (1 + σ·N(0,1))，固定亂數種子（mulberry32） |
| `src/entry.ts` | 瀏覽器 Demo 的進入點，打包成 `../handwired-fizzbuzz.bundle.js` |
| `src/lab_run.ts` → `out/exact.json` | 1..1000 全部跑一次，跟普通 JS 比對；統計運算數、層數、係數數 |
| `src/lab_noise.ts` → `out/noise.json` | σ 從 1e-7 到 0.3，每個 σ 跑 10 組種子，記錄 1..100 答對題數 |
| `src/lab_speed.ts` → `out/speed.jsonl` | 每次執行的時間：handwired tensor evaluator 對普通 JS（跑 3 輪） |
| `src/minimal.js` → `out/minimal.txt` | 頁面「五分鐘上手」的程式碼，實際執行輸出 |
| `out/joelgrus_notebook_wrong.txt` | joelgrus/fizz-buzz-tensorflow（commit d14b8b5）notebook 存下的答錯清單 |
| `qa_check.py` | Playwright 互動測試：輸入數字、按 ±、點答案板、切換雜訊、重抽 |

## 重跑

```bash
git clone https://github.com/chenglou/handwired && git -C handwired checkout ade1a75
cd lab/src && ln -s <handwired 路徑>/src/runtime runtime
npm install --ignore-scripts esbuild@0.25.12
for f in lab_run lab_noise lab_speed; do npx esbuild $f.ts --bundle --platform=node --format=esm --outfile=$f.mjs && node $f.mjs; done
# 瀏覽器 bundle
npx esbuild entry.ts --bundle --minify --format=iife --outfile=../../handwired-fizzbuzz.bundle.js
```

速度數字會隨機器變動；正確性與雜訊實驗（固定種子）每次結果相同。

## 2026-11-25 重做呈現

機制圖第 4、5 步要顯示網路的實際值，所以 `src/fizzbuzz.ts` 把「餘數＝0？」的輸出存成 `probe.d3`／`probe.d5`，`src/entry.ts` 的 `run()` 多回傳 `d3`、`d5`，並用同樣指令重新打包 `../handwired-fizzbuzz.bundle.js`（運算數仍是 1,416，1–1000 仍全對）。
