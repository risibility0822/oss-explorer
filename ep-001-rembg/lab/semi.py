"""貓的毛邊：各模型縮圖（img/cat-*.webp）裡半透明點（16 ≤ alpha ≤ 240）的比例。用 python3 -I lab/semi.py 重跑。"""
from pathlib import Path
from PIL import Image
img = Path(__file__).resolve().parent.parent / "img"
for m in ["u2netp", "silueta", "u2net", "isnet-general-use"]:
    a = list(Image.open(img / f"cat-{m}.webp").getchannel("A").getdata())
    print(m, round(sum(16 <= v <= 240 for v in a) / len(a), 3))
