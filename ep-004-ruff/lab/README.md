# ep-004 Ruff：lab

2026-11-27（台灣時間）在雲端工作區（4 核 CPU、Python 3.11.18、Node）實際執行。

| 檔案 | 用途 |
|---|---|
| `bench.py` | 速度實測：同一份 Django（f0e7bd9）跑 ruff check／flake8／pylint／ruff format／black，各 3 次取中位數，並比對 ruff format 與 black 的輸出 |
| `bench.json`、`bench.log` | bench.py 的原始輸出 |
| `ruff-rules.json` | `ruff rule --all --output-format json`：977 條規則（145 條預覽） |
| `select-all-settings.txt` | `ruff check --isolated --select ALL --show-settings` 的原始輸出：實際啟用 813 條（D203/D213 衝突被忽略） |
| `samples/` | Demo 的三個範例程式 |
| `entry.js`、`package.json` | 打包頁面用的 `ruff.bundle.js`（官方 wasm＋本集寫的「一鍵修好」） |
| `parity_node.cjs`、`parity.py`、`parity.json` | 用頁面同一份 bundle＋wasm 跑三個範例，跟 Ruff 命令列（`--fix --unsafe-fixes`、`format`）比對：全部一致 |
| `qa_check.py` | 真的操作 Demo 的互動測試（oss.py qa／live 會跑） |
| `requirements.txt` | Python 工具的版本 |

## 重跑

```bash
python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
git clone --depth=1 https://github.com/django/django /tmp/django
python3 bench.py /tmp/django bench.json      # 約 1 分鐘（pylint 佔大半）
python3 parity.py                              # 需要 node
```
