---
name: oss-episode
description: 出刊一集開源探索誌（選題、研究、實際跑 Demo、寫頁面、審查、發布到 GitHub Pages）。排程觸發或主人說「出一集／加一集」時使用。
---

# 出刊一集

照順序做。每一階段後面的「⏱」是時間上限，超過就照備案處理。每完成一階段就用 TaskCreate／TaskUpdate 勾掉，主人回來看得到進度。

## 0. 準備 ⏱ 5 分

```bash
cd <repo 根目錄>                    # 通常是 /home/claude/oss-explorer
python3 ops/bin/oss.py preflight    # 環境與推送權限；有致命問題就停
cat ops/LESSONS.md                  # 過去的教訓，一定要讀
python3 ops/bin/oss.py plan         # 解析 feedback.md，決定本集編號／格式／層級／主鏡頭／領域排序
```

- `plan` 回傳 exit 3：今天已出刊。最後訊息寫「今天已出刊」，結束。
- `plan` 回傳 exit 2：有上次沒做完的 run。先 `oss.py gate` 看卡在哪；能接著做就接著做，不能就 `oss.py plan --force` 重新開始（上次的半成品已在 wip 分支或工作區）。
- 讀 `.run/current.json`：`wishFirst`（許願優先）、`domainTop`、`starredIdeas`、`previous`（做跨集組合用）、`pool`。

## 1. 發掘與選題 ⏱ 15 分

**先跑趨勢雷達**：`python3 ops/bin/oss.py radar`（約 1 分鐘）。它抓 Google Trends 台灣與美國的每日熱搜、Bluesky 公開的熱門話題（大眾＋社群）、GitHub 近 30 天新專案與主題標籤、Hacker News 首頁、Hugging Face 熱門模型（開發者圈），寫進 `data/trends.json`，首頁「趨勢雷達」會顯示。shell 連不到 Google Trends 時，用 WebFetch 讀 `https://trends.google.com/trending/rss?geo=TW&v=<runId>`，把結果存成每行「關鍵字 | 搜尋量 | 日期」的檔案，再跑 `oss.py radar --gtrends-tw <檔案>`（美國用 `--gtrends-us`）；還是不行就照常選題，最後訊息加 ⚠️。

**熱門話題日（plan 印出 `trendDay: true`，每週一、四，或許願提到熱門／趨勢）**：主題一定要接上雷達，meta.json 的 `trend` 必填（kind、topic、source、url、date、traffic、why）：
- **大眾話題**（kind=public）：從 Google Trends 台灣的熱搜挑一個（台股代號除外；台灣沒有合適的才用美國或 Bluesky 熱門話題），找一個能幫人看懂、查詢或處理這件事的開源工具或開放資料。例：颱風 → 氣象資料或災害地圖工具；演唱會搶票 → 排隊或爬蟲防護；選舉 → 開票資料視覺化。`why` 用一句白話寫「為什麼這集跟這個熱門話題有關」（≤60 字），例如「颱風假熱搜第一：用開源氣象資料看風雨怎麼走」。
- **開發者圈**（kind=dev）：雷達上的主題標籤或星數漲最快的新專案。
- 兩種都找不到能做 Demo 的題目，就回到一般選題，在 meta 的 trend 寫 kind=dev 並在 why 寫明「本週熱門話題找不到能在這台機器跑的 Demo，改選…」。
**其他天**：雷達上的熱門關鍵字只當加分（同分時優先），不用填 trend；有接上的話也可以填，卡片會多一行「為什麼是現在」。


**規則（依序套用）**
1. **許願優先**：`wishFirst` 不是 null 就做它。做不到（需要 GPU、資料拿不到）時，在 meta.json 的 `wishUpdates` 填 `{"id":…, "status":"blocked", "reply":"原因＋替代方案"}`，然後照一般規則選題；替代方案夠接近就直接做替代方案（meta.json 的 `wish` 填它）。
2. **領域**：從 `domainTop` 的第一個開始，找不到好題目才換下一個。
3. **格式／層級／主鏡頭**：照 plan 給的。巨星＝>10k ★ 或該領域代表作；寶石＝<3k ★ 但品質好、活躍、點子獨特；新星＝近 12 個月誕生或爆紅。組合技＝2–5 個資源真的串起來（A 的輸出餵給 B）。
4. **不重複**：`covered` 裡的不能當主角（可當組合技配角，註明「第 NNN 集介紹過」）。

**來源**（每集至少 3 個不同來源、5–10 個候選）。**資料新鮮度很重要：WebFetch 會給舊快取。**
- GitHub 搜尋 API（網址帶日期，會拿到新資料）：`https://api.github.com/search/repositories?q=created:>YYYY-MM-DD+stars:>200+topic:<主題>&sort=stars&order=desc&per_page=20`；也可以用 `pushed:>`、`language:`、`topic:` 組合。
- Hacker News Show HN（帶時間範圍）：`https://hn.algolia.com/api/v1/search?tags=show_hn&numericFilters=created_at_i>UNIX秒,points>50&hitsPerPage=30`。2026-11-25 起排程環境連不到 HN（WebFetch 回 ENOTFOUND）：連不到就改用 WebSearch 搜「Show HN <本週主題>」，不要卡在這裡。
- 其他：trendshift.io、ossinsight.io、awesome-* 清單（awesome-selfhosted、Awesome Public Datasets）、selfh.st、console.dev、Changelog、Hugging Face Trending Papers（https://huggingface.co/papers/trending ，Papers with Code 已在 2025 年 7 月關閉）、data.gov.tw、WebSearch。
- **不要用** `github.com/trending` 的 WebFetch 結果（實測會拿到好幾年前的快取）。
- 其他網址加 `?v=<runId>` 避開快取。

**每個候選都要驗證**：`git ls-remote` 或 `git clone --filter=blob:none --depth=50` 確認最近 commit 日期；讀 LICENSE 原文。把候選寫進 `.run/candidates.json`：`[{name,url,domain,stars,lastCommit,license,demoPlan,score:{wow,fun,biz,ownerFit,demoFeasible},why}]`。

**Demo 可行性是硬門檻**。排程跑在專屬雲端環境 `oss-explorer`，網路允許：
- GitHub（clone、Releases 下載、raw、api.github.com）、PyPI、npm 等套件管理工具。
- Hugging Face（huggingface.co、*.hf.co：可以下載小模型權重）、cdn.jsdelivr.net、unpkg.com、data.gov.tw。
- 本站 risibility0822.github.io（只用於發布後的 `oss.py live` 線上檢查）。
- 其他網站從 shell 連不到（WebFetch／WebSearch 不受影響）。不確定時先用 `curl -sI <url>` 實測；被擋就換資料來源，並在最後訊息寫 ⚠️，請主人把網域加進環境的允許清單。
- 2 CPU、約 7GB RAM、沒有 GPU（AI 模型只選小的，CPU 能在幾分鐘內跑完）；有 Chromium（Playwright）。
- 資料集題目：資料檔放進本集資料夾（單檔 < 45 MB），頁面不要在執行期去外部抓。

選定後：`python3 ops/bin/oss.py new <slug>`（slug 用英文小寫，例如 `tldraw`）。沒選上的好候選寫進 meta.json 的 `poolAdd`。

## 2. 研究 ⏱ 15 分

clone 到 `/home/claude/work/<id>/src/<name>/`（新的空目錄）。收集：
- 真實數據：最後 commit、近 12 個月 commit 數、作者數、版本 tag、LICENSE 原文。
- 星數與授權：`https://api.github.com/search/repositories?q=repo:<owner>/<repo>&v=<runId>`（排程環境裡 `/repos/<owner>/<repo>` 對沒掛在任務上的 repo 會回「not enabled for this session」，search 拿得到），標明「截至 YYYY-MM-DD」。授權最後仍以 clone 下來的 LICENSE 原文為準。
- 它是什麼、誰做的、解決什麼問題、核心原理、生態系（誰在用、周邊套件、靠它賺錢的公司）、替代品、授權對商用的影響（AGPL、SSPL、BSL、CC-BY-NC、CC-BY-ND 要特別講）、成熟度與坑。
- 每個要寫上頁面的事實都記下來源網址（之後放進 meta.json 的 `sources` 與頁尾）。

## 3. Demo 與 lab ⏱ 30 分

**優先順序**
1. **瀏覽器裡能玩的 Demo**：`npm install`（加 `--ignore-scripts`）後用 esbuild 打包：`npx esbuild entry.js --bundle --minify --format=iife --outfile=<本集>/xxx.bundle.js`。wasm、模型、資料檔也放本集資料夾，頁面用相對路徑載入，執行期不要依賴外部網站。
   - **共用執行引擎放 `vendor/`**：已經有 `vendor/onnxruntime-web-1.31.1/`（ONNX 模型的瀏覽器推論，wasm 單執行緒），直接用 `<script src="../vendor/onnxruntime-web-1.31.1/ort.wasm.min.js">`，`wasmPaths` 要寫成 `new URL('../vendor/onnxruntime-web-1.31.1/', location.href).href`。新的共用引擎同樣放 `vendor/<名稱-版本>/` 並附 LICENSE。範例：`ep-001-rembg/`。
   - **重寫了原專案的前後處理**，就寫 `lab/parity.py` 跟原專案的輸出比對，數字放上頁面。
2. **工作區實跑紀錄**：真實輸出（文字、數據、產生的圖片、benchmark）嵌進頁面，附指令、版本、日期。
3. 兩者結合最好：工作區跑出結果，頁面提供互動瀏覽。

**備案**：20 分鐘內瀏覽器 Demo 做不起來，就改成「工作區實跑＋互動結果瀏覽器」；連實跑都不行就換題（回到第 1 步，時間還夠的話）。

**lab/ 必須有**：本集實際執行過的所有腳本、原始輸出（json／txt／圖片）、鎖定版本的 `package.json` 或 `requirements.txt`、`README.md`（每個檔案的用途、怎麼重跑），以及 `qa_check.py`。`qa_check.py` 要真的操作 Demo（點按鈕、輸入文字）並用 assert 檢查結果，參考 `ep-001-rembg/lab/qa_check.py`。不要放 node_modules、第三方 repo 的副本、超過 20 MB 的檔案。

有文字輸入框的 Demo 要處理中文輸入法：選字期間（compositionstart → compositionend）不送出。

## 4. 頁面與 meta.json ⏱ 20 分

`new` 已經建好骨架：`index.html`（每個 `data-section` 都要保留）、`meta.json`、`lab/`。

**先讀四份設計文件**：`.claude/skills/frontend-design/SKILL.md`（品味）、`.claude/skills/visual-explainer/SKILL.md` 與它的 `references/`（怎麼用圖解釋）、`.claude/skills/eli5-method/`（怎麼對完全外行的人解釋）、同資料夾的 `design.md`（版型與系列骨架 `assets/series.css`）。工具部分都不用，見各自的 NOTICE.md。在 `<style>` 開頭寫五行設計計畫，對照 AI 預設特徵檢查過再動工。

**內容**（版型照骨架，細節見 design.md）
- **主線**（讀者 2 分鐘看完，可見文字 ≤ 1500 字，Demo 不計）：`header` 標題寫結論 → `demo` 第一屏 → `tldr` 30 秒看懂（四句話）→ `how` 一張機制圖（畫機制不畫名詞，流程用步驟圖）→ `findings` 實測後的三個發現（每個是一張 figure，圖說寫結論）→ `ideas` 3–5 個點子（一句話＋工作量；至少一個貼近主人背景：macOS app、Python/FastAPI、台灣市場；主人有收藏的點子時，至少一個延伸那個方向）。
- **深入**（全部收在 `<details>`，預設收合）：`run` 實測紀錄與 lab 連結、`start` 實測過的最小程式碼、`limits` 授權陷阱與替代品比較表、`more` 延伸資源與跨集組合（第 2 集起至少一個 `../ep-XXX-slug/`）、`sources` 至少 5 個來源。
- 寫完把每一句主線讀一遍：拿掉它，Jack 會少知道什麼？答不出來就刪。

**設計**：每集的視覺從主題本身取材，不要長得一樣；第 001 集是版型的範例，不是視覺的範本。

**meta.json**：填完全部欄位（schema 在 `ops/schema/meta.schema.json`）。`ideas` 必須跟頁面一致；`nextHint` 寫下一集預告。`resources` 的主角（role 為 main）要寫完整的 owner/repo、網址、授權、星數（附查詢日期）、語言，再加三個給卡片用的欄位：`title`（顯示名，例如 Headroom）、`what`（一句白話：它是什麼，≤30 字）、`commercial`（能不能商用的結論，授權不單純時一定要填，例如「程式可免費商用，模型另計」）；配角也填 `what`（一句它做什麼）。`meta.title` 結尾要加上主角名（例如「…（Headroom）」），首頁、推播、分享預覽只看得到標題，check 會擋。

**本集主角卡**：meta.json 填好後跑 `python3 ops/bin/oss.py card`，它會在標題下方產生卡片（名字、連結、星數、授權、語言、搭配的工具）。不要手改卡片；meta 改了就再跑一次，check 會比對兩者一致。讀者一定要在第一屏看得到這集介紹的是誰、在哪裡。

## 5. 驗證與審查 ⏱ 15 分

```bash
python3 ops/bin/oss.py palette   # 主題色：列出和田三造《配色事典》的候選（--hue 縮小範圍，預覽圖 .run/palettes.png）
python3 ops/bin/oss.py palette --pick N --why "…"   # 套用：產生配色區塊並寫入 meta.palette（不要手改）
python3 ops/bin/oss.py card      # 從 meta.json 產生「本集主角」卡
python3 ops/bin/oss.py check     # 結構、連結、大小、殘留骨架、HTML、JS 語法、meta schema
python3 ops/bin/oss.py qa        # 真實 Chromium：桌機／手機／深色、JS 錯誤、溢出、互動測試、無障礙、主線字數（≤1500）、收合、impeccable 設計偵測、縮圖
```

1. 修到兩個都通過。
2. **用 Read 打開截圖親眼看**：`.run/qa/<slug>/desktop.png`、`mobile.png`、`mobile-dark.png`、`desktop-full.png`。看有沒有破版、字太小、對比不足、空白太多、內容重疊。
3. **獨立審查**：用 Agent 工具啟動 `oss-reviewer` subagent（沒有的話用 general-purpose，並把 `.claude/agents/oss-reviewer.md` 的內容當作指示），告訴它本集資料夾名稱。它不會改檔案，會回傳 JSON 判定。
4. **設計審查**（跟第 3 步同時啟動，兩個 subagent 平行跑）：用 Agent 工具啟動 `oss-design-reviewer`（沒有的話用 general-purpose，並把 `.claude/agents/oss-design-reviewer.md` 的內容當作指示）。它只看讀起來與看起來怎樣：3 秒抓重點、主線是不是太長、像不像模板、手機好不好用。
5. 兩份審查的 `must_fix` 全部修掉，重跑 check／qa；`verdict` 是 `revise` 時修完再審一次，最多兩輪。第二輪還沒過，就把剩下的問題寫進頁面的 limits 區，並在最後訊息加 ⚠️。
6. 把兩份審查的摘要分別用 `finish --review "…" --design "…"` 記錄。

## 6. 發布與線上檢查 ⏱ 20 分

### 6a. 發布

```bash
python3 ops/bin/oss.py register                   # meta.json → data/*.json（可重複執行）
python3 ops/bin/oss.py build                      # feed.xml、sitemap、README 總覽表
python3 ops/bin/oss.py finish --review "內容審查：pass，正確性 5／Demo 4…" --design "設計審查：pass，一眼抓重點 4／…"
python3 ops/bin/oss.py publish                    # commit + push（自動 rebase、重試，失敗推到 wip 分支）
```

### 6b. 到線上網址親自檢查、親手玩（必做，gate 會擋）⏱ 10 分

自動測試只會驗證你想得到的事；讀者打開網址的那一刻才是真的考試。ep-001 就是這樣抓到「圖上的把手看起來能拖、其實拖不動」。

1. `python3 ops/bin/oss.py live`：等 GitHub Pages 部署到跟 HEAD 一模一樣（最多 10 分鐘），再用真的 Chromium 打開**線上網址**：
   - 桌機、手機、手機深色三種畫面截圖，抓 JavaScript 錯誤、網站自己的檔案載入失敗、版面溢出；
   - 在線上跑本集的 `lab/qa_check.py`；
   - **探索**：自動點 Demo 區的每個按鈕、調每個滑桿和選單、拖每個游標暗示能拖的東西（grab、ew-resize…），沒有任何反應的列為「可疑」；
   - 確認首頁有這一集的連結和縮圖、feed.xml 有這一集。
   有錯誤 → 修正 → `oss.py publish --force` → 再跑 `oss.py live`。
2. 用 Read **打開 `.run/live/<slug>/` 的每一張截圖**（含 `*-after-play.png`），逐一處理每個「可疑」項目：真的壞了就修；是誤判就在 `--played` 裡說明為什麼。
3. **親手玩**，就像第一次來的讀者：
   - 有瀏覽器工具（Claude in Chrome、內建瀏覽器）就用它打開線上網址；沒有就寫一支短的 Playwright 腳本（放 `.run/live/play.py`，啟動時 `proxy={"server": os.environ["HTTPS_PROXY"]}`）對線上網址操作並截圖來看。
   - 至少做到：桌機和手機各完整操作一次 Demo（每個範例、每個選項、上傳或輸入自己的東西、下載）；**畫面上看起來能點、能拖的東西都試一次**；把整頁捲完，看表格、圖、程式碼區塊有沒有斷行或擠壓；從首頁點進來一次。
   - 問自己：第一次來的人知道要做什麼嗎？操作完能馬上看到結果嗎（手機上不用捲回去）？有沒有哪段讀起來太擠？
4. 發現的問題修掉（`publish --force` → `live`），然後記錄：`python3 ops/bin/oss.py live --played "桌機：…；手機：…；發現並修正：…"`（至少 40 字）。
5. **網路連不到網站時**（工作區允許清單沒有 `risibility0822.github.io`），`live` 會自動降級成用本機檔案跑同樣的檢查。這時另外用 WebFetch 打開線上網址（加 `?v=<runId>`）確認標題出現，照樣親手玩本機版並記錄 `--played`，最後訊息加一行 `⚠️ 線上檢查降級（連不到網站）`。

### 6c. 收尾

1. `python3 ops/bin/oss.py lesson "…"`：這次學到、下次用得上的事（例如某個主機被擋、某個套件的坑），一到三條，沒有就不寫。寫了要再 `publish --force` 一次。
2. `python3 ops/bin/oss.py gate` → PASS。
3. 照 CLAUDE.md 的格式寫最後訊息。

## 失敗處理

- 任何一步卡死、而且時間不夠重來：`python3 ops/bin/oss.py abort --reason "哪一步、為什麼"`。最後訊息寫 ⚠️ 和原因。
- `publish` 推送失敗：工具會自動推到 `wip/…` 分支並告訴你。在最後訊息寫 ⚠️。
- 不要把內容存到 Claude 帳號，也不要假裝已發布。
