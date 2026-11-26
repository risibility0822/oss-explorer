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
- 2026-11-25：WebFetch 在新環境也受網路允許清單限制（news.ycombinator.com、hn.algolia.com、joelgrus.com 都 ENOTFOUND），api.github.com/repos/<owner>/<repo> 對未掛載的 repo 會回『not enabled for this session』，但 search/repositories?q=repo:owner/name 拿得到星數與授權。
- 2026-11-25：系統的 python3 PIL 壞掉（cannot import _imaging），qa 縮圖會失敗；先 python3 -m pip install --user --force-reinstall --no-deps pillow 就好。手機上寬的 inline SVG 圖會把字縮到 5px，設 min-width 並包在 .scroll 裡。
- 2026-11-25：解釋用圖（visual-explainer 原則）：主線要有一張「畫機制」的圖（資料怎麼流、箭頭寫動詞），流程用步驟圖（上一步／下一步，從第 1 步開始；2026-11-25 起改成由兩格長大，見下面的 eli5 條目），圖上的數字最好接 Demo 的真實計算（ep-002 用 HW.run 的中間值）。每張圖的 figcaption 寫結論；figcaption 必須是 figure 的直接子元素（html-validate 會擋）。手機上 SVG 小字至少 16 單位。
- 2026-11-25：系列骨架 assets/series.css 統一字型、版面、元件與圖說編號；每集只設 --accent/--accent-ink/--accent-soft/--stage、Demo（#demo 或 .demo-* 選擇器）與 2–3 個主題小細節，check 會擋覆寫骨架的選擇器。機制圖專屬元素用 #mechSvg 開頭，不要用 .mech（會被擋）。
- 2026-11-25：讀者什麼都不懂（eli5-method）：dek 寫答案句；30 秒看懂第一格是「先說背景」；名詞第一次出現用 <dfn>…</dfn><span class="gloss">（白話）</span>；機制圖第 1 步只有輸入→黑盒子→答案（用 data-only="1" 的群組只在第 1 步顯示「？」），之後每步打開一點。
- 2026-11-25：series.css 是全站骨架，改它會影響所有集數；改完要對已出刊、有用骨架的集數重跑 qa。機制圖預設從第 1 步開始，.st.off 要完全隱藏（opacity 0），不能留淡影。
- 2026-11-25：頁面上的指令範例一定要在乾淨環境真的跑過才能寫「實測」：rembg[cpu] 不含命令列依賴，要 rembg[cpu,cli]（ep-001 重做時審查員抓到）。倍數比較要用同一個單位的原始數字算（1,024,331,469 ÷ 4,574,861 bytes ≈ 224，不是 1024 MB ÷ 4.4 MB）。
- 2026-11-25：推送後 GitHub Pages 偶爾不會開始部署（ep-001 重做時 3eddbbb 推了 10 分鐘都沒有 workflow run）。用 gh api repos/<repo>/actions/runs 查得到部署狀態；沒有就推一個空 commit 重新觸發，不要只看線上頁面是不是舊的就以為是快取。
- 2026-11-25：2026-11-25 系列骨架改成雜誌版面（參考《大誌》）：刊頭＋期數、書背標語、目錄、章節頭 01–05、folio、紙色 #f8f8f6；字型加 Bodoni Moda（斜體數字與英文欄名）與 Archivo 900（刊頭）。impeccable 會把「字貼著底線」判成 cramped padding，章節頭的底線要留 padding-bottom:8px。
- 2026-11-25：首頁也改用 assets/series.css（刊頭顯示最新一期期數、封面是最新一集、目錄、章節頭 01–05、過刊列表）；每集刊頭的 OSS EXPLORER 和「回首頁」都連回 ../。縮圖 og.jpg 改拍 Demo 本身（作品就是封面照），不再是頁面頂端，避免首頁出現「頁面裡的頁面」。meta.json 的 oneliner、demo 會直接顯示在首頁，也要用白話寫。
- 2026-11-26：llama.cpp v1.0.0 起 tag 改名、Releases 網頁 403 抓不到預編譯檔；自己 cmake 編譯要加 -DLLAMA_BUILD_HTML=OFF，且 llama-server 會去下載網頁介面檔而失敗，只編 llama-completion／llama-tokenize（4 核約 5 分鐘）。Qwen2.5-1.5B Q4 在 4 執行緒 CPU 讀 2 萬 token 約 230 秒，跑實驗要放背景並預留 20 分鐘。
- 2026-11-26：工作區連不到 tiktoken 編碼檔（openaipublic.blob.core.windows.net），用到 tiktoken 的套件會退回估算，token 數要用目標模型自己的分詞器（llama-tokenize）重數。Demo 元素若用 display:grid/flex，[hidden] 會失效，要加 #demo [hidden]{display:none!important}（qa_check 只看 .hidden 屬性抓不到，設計審查員抓到）。
- 2026-11-26：2026-11-26 主人反映第 3 集看不出介紹的是哪個工具：標題寫結論＋星數收進深入區，結果第一屏沒有名字、連結、星數。新增「本集主角」卡（oss.py card 從 meta.json 產生，check 比對一致、必須在 Demo 之前），主線字數不算卡片。標題可以寫結論，但第一屏一定要有『介紹的是誰、在哪裡、多少星、什麼授權』。
- 2026-11-26：機制圖的步驟說明是 sticky（往下捲會跟著走），它所在的欄不能再放別的東西：圖說原本放右欄，捲到一半會被上一步／下一步按鈕蓋住（主人截圖回報）。現在圖說在圖的正下方。改 series.css 後用 /tmp/stick.py 這類腳本捲動量重疊，不要只看靜態截圖。
