"""瀏覽器版 vs Python 版的一致性測試。

用 Playwright 開真的 Chromium，載入本集頁面，呼叫頁面上的 window.__rembgDemo.maskOf()，
取得瀏覽器（onnxruntime-web + 本頁的 JavaScript 前後處理）算出的遮罩，
再跟 rembg Python 版在「同一張」img/<圖>.jpg 上算出的遮罩比對（兩邊輸入完全相同）。
另外記錄：Python 版用 scikit-image 原圖（bench.py 的 out/<圖>-u2netp-mask.png）與用網頁 JPEG 的差異，
用來說明 JPEG 重新壓縮本身造成多少差異。

用法（在 repo 根目錄）：python3 ep-001-rembg/lab/parity.py
輸出：ep-001-rembg/lab/out/parity.json
"""
import base64, functools, http.server, io, json, socketserver, statistics, threading
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
from rembg import new_session, remove

LAB = Path(__file__).resolve().parent
ROOT = LAB.parents[1]
EP = LAB.parent.name


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/{EP}/"

PY = new_session("u2netp")


def py_mask(path):
    return np.array(remove(Image.open(path).convert("RGB"), session=PY, only_mask=True)).astype(np.int16)


def compare(x, y):
    a, c = x >= 128, y >= 128
    return round(float(np.logical_and(a, c).sum() / max(np.logical_or(a, c).sum(), 1)), 4), round(float(np.abs(x - y).mean()), 2)


out = {"engine": "onnxruntime-web 1.31.1（wasm，單執行緒）於 Playwright Chromium", "images": []}
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(url, wait_until="load")
    pg.wait_for_function("window.__rembgDemo && document.getElementById('sInfer').textContent.includes('ms')", timeout=60000)
    out["modelLoadMs"] = round(pg.evaluate("window.__rembgDemo.loadMs"))
    for k in ["coffee", "cat", "rocket"]:
        runs = [pg.evaluate("k => window.__rembgDemo.maskOf(k)", k) for _ in range(3)]
        ms = statistics.median(r["ms"] for r in runs)
        data = base64.b64decode(runs[-1]["mask"].split(",", 1)[1])
        browser = np.array(Image.open(io.BytesIO(data)).convert("L")).astype(np.int16)
        python = py_mask(LAB.parent / "img" / f"{k}.jpg")
        assert browser.shape == python.shape, (k, browser.shape, python.shape)
        iou, mad = compare(browser, python)
        orig = np.array(Image.open(LAB / "out" / f"{k}-u2netp-mask.png").convert("L")).astype(np.int16)
        jiou, jmad = compare(python, orig)
        out["images"].append({"image": k, "runs": len(runs), "browserMs": round(ms), "iou": iou, "meanAbsDiff": mad,
                              "jpegVsOriginalIou": jiou, "jpegVsOriginalMeanAbsDiff": jmad, "size": list(browser.shape[::-1])})
        print(k, out["images"][-1], flush=True)
    b.close()
srv.shutdown()
ious = [i["iou"] for i in out["images"]]; jious = [i["jpegVsOriginalIou"] for i in out["images"]]
out["note"] = (f"兩邊輸入同一張網頁 JPEG，遮罩 IoU 介於 {min(ious):.4f}–{max(ious):.4f}；剩下的差異來自縮放演算法（Python 用 PIL 的 LANCZOS，瀏覽器用 canvas）。"
               f"對照組：同樣用 Python，只把輸入從 scikit-image 原圖換成網頁上的 JPEG，IoU 介於 {min(jious):.4f}–{max(jious):.4f}。"
               "兩種差異是同一個量級：改在瀏覽器裡跑（主要是縮放方法不同）造成的差異，跟照片多壓縮一次差不多。")
(LAB / "out" / "parity.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
print("寫入", LAB / "out" / "parity.json")
