"""第 001 集實驗：rembg 四個模型（birefnet-general-lite 因記憶體不足被終止，已移除） × 三張授權乾淨的照片。

量測：模型檔大小、每張圖的推論時間（3 次取中位數，2 vCPU）、
以及每個模型的遮罩跟 isnet-general-use 的一致度（IoU，門檻 0.5）。
一致度不是「準確率」：沒有人工標註的正解，只是看各模型彼此差多少。

輸出：out/bench.json、out/<圖>-<模型>.png（去背結果）、out/<圖>-<模型>-mask.png
用法：python3 bench.py [輸出資料夾]
"""
import gc, json, os, platform, resource, statistics, sys, time
from pathlib import Path

import numpy as np
import onnxruntime
import rembg
import skimage
from PIL import Image
from rembg import new_session, remove
from skimage import data

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "out"); OUT.mkdir(parents=True, exist_ok=True)
MODELS = ["u2netp", "silueta", "u2net", "isnet-general-use"]
REF = "isnet-general-use"
# birefnet-general-lite（224 MB）在 8 GB RAM 的雲端機器上單獨推論一張圖就被 OOM 砍掉（RSS > 6 GB），所以沒列入
IMAGES = {  # 授權：scikit-image 文件
    "cat": (data.chelsea, "CC0（Stefan van der Walt 攝）"),
    "coffee": (data.coffee, "CC0（Rachel Michetti 攝）"),
    "rocket": (data.rocket, "公眾領域（SpaceX 釋出）"),
}

def model_file(session):
    home = Path(os.environ.get("REMBG_HOME", Path.home() / ".rembg")) / "models"
    files = list((home / session.model_name).glob("*.onnx")) if (home / session.model_name).exists() else []
    if not files:
        files = list(Path.home().glob(f".u2net/{session.model_name}*.onnx"))
    return files[0] if files else None

results = {"env": {"python": platform.python_version(), "rembg": rembg.__version__ if hasattr(rembg, "__version__") else "2.0.87",
                   "onnxruntime": onnxruntime.__version__, "scikit-image": skimage.__version__, "cpu": os.cpu_count(),
                   "date": time.strftime("%Y-%m-%d")},
           "notes": ["birefnet-general-lite（224 MB）在 8 GB RAM 機器上推論一張 600×400 的圖被 OOM 終止（RSS 超過 6 GB），未列入。",
                     "一致度 = 與 isnet-general-use 遮罩的 IoU（門檻 0.5），不是對人工標註的準確率。"],
           "images": {k: v[1] for k, v in IMAGES.items()}, "models": {}, "runs": []}
imgs = {k: Image.fromarray(f()) for k, (f, _) in IMAGES.items()}
for k, im in imgs.items():
    im.save(OUT / f"{k}.png")
    results["images"][k] = {"license": IMAGES[k][1], "size": list(im.size)}

masks = {}
for m in MODELS:
    t0 = time.perf_counter(); sess = new_session(m); load = time.perf_counter() - t0
    f = model_file(sess)
    results["models"][m] = {"sizeMB": round(f.stat().st_size / 2**20, 1) if f else None, "loadSec": round(load, 2)}
    for k, im in imgs.items():
        times = []
        for _ in range(3):
            t = time.perf_counter(); mask = remove(im, session=sess, only_mask=True); times.append(time.perf_counter() - t)
        cut = remove(im, session=sess)
        cut.save(OUT / f"{k}-{m}.png"); mask.save(OUT / f"{k}-{m}-mask.png")
        masks[(k, m)] = np.array(mask.convert("L")) >= 128
        fg = float(masks[(k, m)].mean())
        results["runs"].append({"image": k, "model": m, "medianSec": round(statistics.median(times), 3), "foreground": round(fg, 4)})
        print(f"{m:24s} {k:7s} {statistics.median(times):6.2f}s  前景 {fg:.1%}", flush=True)
    del sess; gc.collect()  # 一個模型跑完就釋放，避免 7GB RAM 不夠
    results["models"][m]["peakRssMB"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)

for r in results["runs"]:
    a, b = masks[(r["image"], r["model"])], masks[(r["image"], REF)]
    inter, union = np.logical_and(a, b).sum(), np.logical_or(a, b).sum()
    r["iouVsRef"] = round(float(inter / union), 4) if union else 1.0
(OUT / "bench.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), "utf-8")
print("寫入", OUT / "bench.json")
