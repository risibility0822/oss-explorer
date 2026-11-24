# 第 001 集實驗室：Yjs

這些是製作第 001 集時，在雲端工作區實際執行的腳本與輸出（2026-11-24，Node v22.23.5、yjs 13.6.33、pycrdt 0.14.13、@hocuspocus/server 4.9.0）。

```bash
npm install
pip install pycrdt        # 只有 interop 需要
npm run bench             # 兩台離線各做 N 次編輯後合併 → 輸出同 bench.json
npm run seq               # 依序打 10,000 個中文字的文件大小 → seq.json
npm run interop           # JS 寫 → Python 改 → JS 讀回
npm run hocuspocus        # 本機起 Hocuspocus，兩個客戶端透過 WebSocket 同步
npm run bundle            # 重新打包頁面用的 yjs.bundle.js
```

| 檔案 | 用途 |
|---|---|
| bench.mjs / bench.json | 離線合併 benchmark 與當次結果 |
| seq.mjs / seq.json | 一般打字情境的文件大小 |
| interop.mjs / interop.py / interop2.mjs | 跨語言互通測試 |
| hp.mjs | Hocuspocus 伺服器＋兩個 provider |
| entry.js | 打包成瀏覽器用 IIFE 的入口 |
