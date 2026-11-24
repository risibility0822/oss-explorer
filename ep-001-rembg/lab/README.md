# 第 001 集實驗室：rembg

製作本集時在雲端工作區（2 vCPU、8 GB RAM）實際執行的腳本與原始輸出，日期 2026-11-24。
版本：Python 3.13、rembg 2.0.87、onnxruntime 1.29.0、scikit-image 0.26.0、onnxruntime-web 1.31.1、Playwright 1.63（Chromium）。

## 怎麼重跑

```bash
pip install -r requirements.txt
python3 bench.py out                      # 四個模型 × 三張照片：速度、記憶體、與 isnet 的一致度（第一次會下載約 390 MB 模型）
cd ../.. && python3 ep-001-rembg/lab/parity.py   # 瀏覽器版 vs Python 版（需要 Playwright 的 Chromium）
```

## 檔案

| 檔案 | 用途 |
|---|---|
| `bench.py` | 用 rembg 跑 u2netp、silueta、u2net、isnet-general-use，量測時間與記憶體，存去背結果 |
| `out/bench.json` | 上面的原始輸出（頁面上的表格就是讀這份） |
| `out/*-u2netp-mask.png` | Python 版 u2netp 在 scikit-image 原圖上的遮罩（parity.py 的對照組） |
| `parity.py` | 用 Playwright 開本集頁面讓瀏覽器算遮罩，跟 rembg Python 版在同一張網頁 JPEG 上的遮罩比對 IoU 與每像素差異；另外量「原圖 vs JPEG」的差異當對照組 |
| `out/parity.json` | 上面的原始輸出 |
| `qa_check.py` | `oss.py qa` 用的互動測試 |
| `requirements.txt` | 鎖定版本 |

## 備註

- `bench.py` 的記憶體欄位是同一個 Python 行程依序跑模型時的 RSS 峰值（累計），只能看趨勢。
- birefnet-general-lite（224 MB）在 8 GB RAM 的機器上推論一張圖就超過 6 GB 記憶體被系統終止，所以沒有列入比較。
- 範例照片取自 scikit-image 內建資料（貓、咖啡杯為 CC0；火箭為 SpaceX 釋出的公眾領域照片）。
- 頁面上的 `u2netp.onnx` 與 rembg Release 的檔案 MD5 相同（`8e83ca70e441ab06c318d82300c84806`）。
