# 第 003 集 lab：Headroom 壓縮工具輸出 → llama.cpp 在 CPU 跑 Qwen2.5-1.5B

2026-11-26（台灣時間）在雲端工作區實際執行：4 執行緒 CPU、無 GPU、約 16 GB RAM、Python 3.11。

- Headroom：`headroom-ai==0.45.0`（PyPI），原始碼 commit `d2014cb`（2026-11-26 台灣時間）。全程 `HEADROOM_OFFLINE=1`（不連網、關掉預設開啟的匿名統計）。
- llama.cpp：tag `v1.0.0`（commit `b1b770d`，2026-11-13），自行編譯 `llama-completion` 與 `llama-tokenize`（GitHub Releases 網頁 403，`llama-server` 需要下載網頁介面檔也失敗，所以只編這兩個）。
- 模型：Qwen2.5-1.5B-Instruct Q4_K_M GGUF（Qwen 官方，Apache-2.0），`-c 32768 --temp 0 -t 4 -n 60`。

## 檔案

| 檔案 | 用途 |
|---|---|
| `scripts/make_logs.py` | 產生**合成**的服務 log（JSON 陣列，固定亂數種子 20261126）：每筆 6 個欄位，第 62% 那筆是 payments 的 ERROR |
| `scripts/scenarios.json` | 每份 log 要問的問題與正確答案（從 JSON 原文查出來的） |
| `scripts/experiment.py` → `out/results.json`、`out/*.answer`、`out/*.log` | 主實驗：每題「原樣」與「Headroom 壓縮後」各問一次，記錄 Qwen 分詞器算的 token 數、讀入提示秒數（llama.cpp 的 prompt eval time）、整題秒數、回答、對錯 |
| `scripts/tokens_and_speed.py` → `out/tokens.jsonl` | 只算 token 與壓縮耗時（每份壓 6 次：第 1 次與後 5 次的中位數），並把原樣／壓縮後內容存成 `../data/*.txt` |
| `scripts/build_demo_data.py` → `../data/results.json` | 把上面兩份原始輸出合併成頁面 Demo 讀的檔案（只搬運，不改數字） |
| `scripts/minimal.py` → `out/minimal.txt` | 頁面「五分鐘上手」的程式碼，實跑輸出 |
| `out/proof_table.txt` | 重跑 Headroom 官方 `benchmarks/index_proof_table.py --seed 20260902` 的輸出 |
| `qa_check.py` | Playwright 互動測試：切換情境、原樣／壓縮後、問題、重播、機制圖 |

`../data/cmake.raw.txt` 是本集第一次編譯 llama.cpp `llama-server` 時真的失敗的 cmake 輸出（下載網頁介面檔被擋）。

## 重跑

```bash
python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
# 照 requirements.txt 的註解編譯 llama.cpp、下載模型；腳本裡的路徑 W=/home/claude/work/ep-003 改成你的
python3 scripts/make_logs.py 100 > data/logs100.json   # 300、2000 同理
python -I scripts/experiment.py out
SAVE_DIR=../data python -I scripts/tokens_and_speed.py data/logs100.json data/logs300.json data/logs2000.json data/cmake_fail.log > out/tokens.jsonl
python3 scripts/build_demo_data.py out/results.json out/tokens.jsonl scripts/scenarios.json ../data/results.json
```

## 注意

- 對錯是程式判斷：回答裡去掉 `req-xxxxx` 後，要出現正確數字（整個字）或「payments」＋「timeout」。
- Headroom 的 `tokens_before/after` 是它自己估的：工作區連不到 tiktoken 的編碼檔（openaipublic.blob.core.windows.net 被擋），它退回「估算」，所以跟 OpenAI 實際 token 數可能不同。頁面主要用 Qwen 自己的分詞器數。
- 讀入秒數會受機器負載影響；同一題重跑幾秒內的差異是正常的。
