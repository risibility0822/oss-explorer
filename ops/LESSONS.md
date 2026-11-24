# 經驗累積

每次出刊前讀一遍；學到新的事用 `python3 ops/bin/oss.py lesson "…"` 追加。過時的條目可以刪掉。

## 環境與網路
- 2026-11-24（舊環境，僅供參考）：工作區 shell 只連得到 github.com（clone、Releases）、raw.githubusercontent.com、PyPI、npm registry。連不到：Hugging Face、Kaggle、jsdelivr／unpkg、HN、ecosyste.ms、api.github.com、github.io、多數政府網站。
- 2026-11-24：WebFetch 對同一個網址會給舊快取（實測 GitHub 搜尋 API 和 HN 晚了約 7 週，github.com/trending 甚至是好幾年前的資料）。網址帶日期範圍或加 `?v=<runId>` 就會拿到新資料。
- 2026-11-24：工作區有 Chromium 和 Python／Node 的 Playwright（PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers），可以做真實瀏覽器測試與截圖。jsdom 只能當備案。
- 2026-11-24：工作區連不到 Google Fonts，所以 qa 截圖裡的字型是系統備用字型（網站上正常），不算錯。
- 2026-11-24：2 CPU、7GB RAM、沒有 GPU。

## 研究
- 2026-11-24：第三方彙整網站（libhunt 等）的授權資訊可能錯（把 MIT 的 y-crdt 標成 GPL）。一律回 repo 讀 LICENSE 原文。
- 2026-11-24：Papers with Code 已在 2025 年 7 月關閉，改看 Hugging Face Trending Papers。
- 2026-11-24：npm 下載量 API（api.npmjs.org）從 shell 連不到；需要的話用 WebFetch 或引用官方文件。

## Demo 與頁面
- 2026-11-24：瀏覽器 Demo 最穩的做法：npm 安裝後用 esbuild 打包成 IIFE，跟頁面放同一個資料夾，用相對路徑載入。
- 2026-11-24：textarea 類 Demo 要處理中文輸入法：選字期間不送出，結束後若同時有遠端修改要用相對位置合併（見 ep-001 的做法）。
- 2026-11-24：check 的 TODO 規則會比對單字邊界，變數名稱像 `todos` 不會被誤判。
- 2026-11-24：星數要用 GitHub API 的 stargazers_count 換算並正確四捨五入（23,108 → 23.1k），forks 也一樣；不要沿用研究初期看到的舊數字。
- 2026-11-24：benchmark 要可重現：固定 Y.Doc 的 clientID 等隨機來源，否則位元組數每次會差 1；頁面說「隨機」時要確認程式真的用了隨機。
- 2026-11-24：旁白與說明要跟程式實際做的事一致（例如「三個人改同一行」其實只有兩人），審查員會逐句對照。
- 2026-11-24：排程改為 Claude Code 雲端任務（repo 掛在任務上、專屬環境 oss-explorer）。環境允許：GitHub 各下載網域、Hugging Face、jsdelivr、unpkg、data.gov.tw、Playwright 下載點、本站 risibility0822.github.io（2026-11-24 加入，給 live 線上檢查用），加上套件管理工具。若某個網域被擋，回報在最後訊息，請主人加到環境的允許清單。
- 2026-11-24：瀏覽器 AI Demo 的執行引擎放在共用的 vendor/（例如 vendor/onnxruntime-web-1.31.1/），各集不要重複放 15 MB 的 wasm。onnxruntime-web 的 wasmPaths 相對路徑是以函式庫檔所在位置解析（會變成 vendor/vendor/…），一定要寫成 new URL('../vendor/…/', location.href).href。
- 2026-11-24：模型授權和程式授權是兩回事：rembg 程式是 MIT，但 2.0.87 的預設模型 BRIA RMBG-2.0 商用要付費。介紹 AI 工具時要逐一列出模型權重的授權，範例程式一律明確指定可商用的模型。
- 2026-11-24：8 GB RAM 的工作區跑大型 ONNX 模型容易 OOM（birefnet-general-lite 單張就超過 6 GB）。benchmark 要每個模型 del session + gc.collect()，並用 /usr/bin/time -v 或 resource 記錄記憶體峰值；被終止本身就是值得寫進頁面的發現。
- 2026-11-24：瀏覽器 Demo 若重寫了原專案的前後處理，要寫 lab/parity.py 用 Playwright 跑真 Chromium，跟原專案的輸出比對（IoU／平均差異），把數字放上頁面；這一步在 ep-001 抓到 wasm 路徑錯誤。
- 2026-11-24：發布後要用真的瀏覽器親手玩一次線上版（不只看自動截圖）。ep-001 這樣抓到：圖上的對照把手看起來能拖卻拖不動、手機上換背景要捲回去才看得到結果、表格第一欄斷行、首頁對非 GitHub 資源顯示「★—」。自動測試只驗證你想到的事，親手玩才會發現沒想到的。
- 2026-11-24：頁面要讓人 2 分鐘看完：主線（30 秒看懂、三個發現、點子）≤1500 字，其餘收進 <details>。舊版第 1 集 5,754 字、約 14 分鐘，主人說「塞滿八成會跳過的文字」。數字比較畫成長條、對照用並排圖，不要用段落講。
- 2026-11-24：impeccable 偵測器在 jsdom 裡讀不懂混了 var() 的 font 簡寫和 padding-block，會誤報「字級階層太平」「內距擠」：字型與內距請寫成分開的屬性（font-size、padding-top…）。另外 .wrap 用 padding 簡寫會蓋掉 section 的上下留白（CSS 權重陷阱），左右留白請用 padding-left/right。
