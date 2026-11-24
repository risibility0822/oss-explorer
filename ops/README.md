# 流程架構（給人看的說明）

## 一次出刊怎麼跑

1. 排程（Claude 帳號裡的「開源探索誌 每週一三五出刊」）在週一、三、五 07:23（台北）啟動一個雲端 session。
2. session 取得這個 repo，讀 `CLAUDE.md`（營運手冊），用 `oss-episode` skill（`.claude/skills/oss-episode/SKILL.md`）一步一步做。
3. 能寫死的步驟都交給 `ops/bin/oss.py`：
   - `preflight`：環境、網路、推送權限、資料格式
   - `plan`：解析 `feedback.md`，算出這集的編號、格式、層級、主鏡頭、領域順序
   - `new`：建立本集骨架
   - `check`：結構、連結、大小、HTML、JS 語法、資料格式
   - `qa`：真實 Chromium 的桌機／手機／深色截圖、錯誤、溢出、互動測試、無障礙、縮圖
   - `register`、`build`：寫入資料、產生 RSS 與總覽
   - `finish`、`publish`：寫執行紀錄、推送（失敗推到 wip 分支）
   - `abort`：記錄失敗
   - `gate`：判斷是否完成
4. 發布前有獨立審查員（`.claude/agents/oss-reviewer.md`）查核事實、看截圖、依 `ops/rubric.md` 評分，不過就修。
5. `.claude/settings.json` 的 hooks：
   - session 一開始自動印出目前狀態
   - 本集還沒發布（或記錄失敗）前，擋住 session 結束（最多擋 4 次）
6. 每次學到的事寫進 `ops/LESSONS.md`，下次開工先讀。

## 防呆設計

| 可能出錯的地方 | 怎麼防 |
|---|---|
| 忘了某個步驟、提早說「做完了」 | `.run/current.json` 進度檔＋`gate`＋Stop hook |
| 選題邏輯算錯、重複介紹 | `plan` 用程式算；`check` 擋重複主角 |
| 資料檔被改壞 | 只透過 `register` 寫入，寫入前驗證 schema；狀態從各集資料推導，可重複執行 |
| 拿到舊資料 | 查詢帶日期範圍或 `?v=`；候選一律用 git 驗證最近 commit |
| 頁面壞掉、手機破版、Demo 不能動 | `check`＋`qa`（真實瀏覽器）＋互動測試＋人眼看截圖 |
| 事實錯誤、自我感覺良好 | 獨立審查員＋評分門檻 |
| 主人同時改 feedback.md 造成推送衝突 | `publish` 自動 rebase 與重試 |
| 推送失敗、做到一半 | 半成品推到 `wip/` 分支；`runs.json` 記錄失敗，首頁看得到 |
| 同一天被觸發兩次 | `plan` 偵測到今天已出刊就停 |

## 手動操作

想自己加一集：在 Claude Code 裡打開這個 repo，說「出一集」。
想看流程工具：`python3 ops/bin/oss.py --help`。
