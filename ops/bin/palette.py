"""SlideHelper 精選配色 → 每集的主題色（由 oss.py palette 呼叫）。2026-11-27 主人決定全面採用 SlideHelper。

設計師配好的組合不改色相。重點色、文字色、圖表色只調明度（OKLCH 的 L）來過對比；淡底、舞台、螢光筆是同色相的淡色（明度和彩度都會調）：
  --accent      重點色：對紙色 ≥ 4.5:1（上面可以放紙色的字，按鈕可用）
  --accent-ink  重點色當文字用：對紙色與淡底都 ≥ 4.8:1
  --accent-soft 重點色的淡底
  --stage       Demo 舞台底：組合裡另一個顏色的極淡版
  --pal-N       組合裡的第 N 色（圖表／標記用）：對紙色與舞台底都 ≥ 3:1
  --pal-N-ink   第 N 色當文字用：對紙色、舞台底、重點色淡底都 ≥ 4.6:1
  --pal-N-soft  第 N 色的淡底（區塊底）
  --pal-N-mark  第 N 色的螢光筆底：盡量保留原色的鮮豔，上面的墨色字仍 ≥ 7:1
亮色、暗色各算一次，用 light-dark() 輸出。
"""
from __future__ import annotations

import json, math, random
from pathlib import Path

PALS = Path(__file__).resolve().parents[1] / "palettes"
SOURCES = {
    "slidehelper": {"label": "SlideHelper 配色", "url": "https://slidehelper.com", "note": "主人精選 24 組", "sizes": (5,)},
}
DEFAULT_SOURCE = "slidehelper"   # 唯一來源（2026-11-27 主人決定）
BG = {"light": "#f8f8f6", "dark": "#1c1e22"}          # 與 assets/series.css 的 --bg 一致
INK = {"light": "#16181b", "dark": "#eceef1"}         # 與 assets/series.css 的 --ink 一致
HUES = {"red": 25, "orange": 55, "yellow": 95, "green": 140, "teal": 190, "blue": 250, "purple": 300, "pink": 350,
        "紅": 25, "橘": 55, "黃": 95, "綠": 140, "青": 190, "藍": 250, "紫": 300, "粉": 350}
TOKENS = ("--accent", "--accent-ink", "--accent-soft", "--stage")


# ── 色彩數學 ──
def hex2rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def rgb2hex(c): return "#" + "".join(f"{round(max(0, min(1, v)) * 255):02x}" for v in c)
def _lin(v): return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
def _gam(v): return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055


def rgb2oklch(c):
    r, g, b = (_lin(v) for v in c)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def oklch2rgb_raw(L, C, H):
    A, B = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3
    m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3
    s = (L - 0.0894841775 * A - 1.2914855480 * B) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return r, g, b


def oklch2hex(L, C, H):
    """超出 sRGB 就降彩度（色相、明度不變）。"""
    lo, hi = 0.0, C
    rgb = oklch2rgb_raw(L, C, H)
    if all(-1e-4 <= v <= 1 + 1e-4 for v in rgb): return rgb2hex(tuple(_gam(max(0, min(1, v))) for v in rgb))
    for _ in range(30):
        mid = (lo + hi) / 2; rgb = oklch2rgb_raw(L, mid, H)
        if all(-1e-4 <= v <= 1 + 1e-4 for v in rgb): lo = mid
        else: hi = mid
    return rgb2hex(tuple(_gam(max(0, min(1, v))) for v in oklch2rgb_raw(L, lo, H)))


def lum(h): r, g, b = (_lin(v) for v in hex2rgb(h)); return 0.2126 * r + 0.7152 * g + 0.0722 * b
def contrast(a, b): x, y = sorted((lum(a), lum(b)), reverse=True); return (x + 0.05) / (y + 0.05)


def fit(hexc, against, target, mode):
    """只動明度，找最接近原色、對 against 每個顏色都 ≥ target 的版本。"""
    L, C, H = rgb2oklch(hex2rgb(hexc))
    if all(contrast(hexc, b) >= target for b in against): return hexc
    end = 0.0 if mode == "light" else 1.0
    lo, hi = L, end            # lo：不夠；hi：夠（極端值）
    for _ in range(40):
        mid = (lo + hi) / 2; c = oklch2hex(mid, C, H)
        if all(contrast(c, b) >= target for b in against): hi = mid
        else: lo = mid
    return oklch2hex(hi, C, H)


def tint(hexc, mode, strength=1.0):
    L, C, H = rgb2oklch(hex2rgb(hexc))
    if mode == "light": return oklch2hex(0.955 - 0.015 * strength, min(C * 0.35, 0.035 * strength), H)
    return oklch2hex(0.27 + 0.02 * strength, min(C * 0.45, 0.045 * strength), H)


def mark(hexc, mode):
    """螢光筆：亮色模式往亮調、暗色模式往暗調，直到墨色字 ≥ 7:1。"""
    L, C, H = rgb2oklch(hex2rgb(hexc))
    if mode == "light": L, C = max(L, 0.92), C * 0.75          # 像螢光筆但不刺眼
    else: L, C = min(L, 0.42), min(C, 0.09)
    return fit(oklch2hex(L, C, H), [INK[mode]], 7.0, "dark" if mode == "light" else "light")


# ── 資料 ──
@__import__("functools").lru_cache(None)
def combos(source: str = DEFAULT_SOURCE) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {}
    if source == "slidehelper":
        for r in json.loads((PALS / "slidehelper" / "palettes.json").read_text("utf-8")):
            out[r["n"]] = [{"name": f"色{i}", "hex": h} for i, h in enumerate(r["colors"], 1)]
    else: raise ValueError(f"不認得的配色來源 {source}（{', '.join(SOURCES)}）")
    return dict(sorted(out.items()))


def default_accent(cols) -> int:
    """當重點色最不走樣的那一個（1 起算）：彩度高、而且為了過對比要改的明度少（黃色壓暗會變土黃，所以扣分）。"""
    def score(i):
        h = cols[i]["hex"]; L, C, H = rgb2oklch(hex2rgb(h))
        f = fit(h, [BG["light"]], 4.5, "light"); L2, C2, _ = rgb2oklch(hex2rgb(f))
        return C2 - 0.8 * abs(L - L2)
    return max(range(len(cols)), key=score) + 1


def default_stage(cols, accent) -> int:
    rest = [i for i in range(len(cols)) if i != accent - 1]
    return (max(rest, key=lambda i: rgb2oklch(hex2rgb(cols[i]["hex"]))[0]) + 1) if rest else accent


def hue_of(hexc): return rgb2oklch(hex2rgb(hexc))[2]
def chroma_of(hexc): return rgb2oklch(hex2rgb(hexc))[1]
def hue_dist(a, b): d = abs(a - b) % 360; return min(d, 360 - d)


def candidates(hue=None, avoid=(), seed="", k=10, source=DEFAULT_SOURCE):
    out = []
    for n, cols in combos(source).items():
        if len(cols) not in SOURCES[source]["sizes"]: continue
        a = default_accent(cols); ah = hue_of(cols[a - 1]["hex"]); ac = chroma_of(cols[a - 1]["hex"])
        if ac < 0.06: continue                                   # 全灰的組合當不了重點色
        if hue is not None and hue_dist(ah, hue) > 35: continue
        if any(hue_dist(ah, h) < 35 for h in avoid): continue   # 跟最近幾集撞色
        out.append({"combo": n, "colors": cols, "accent": a, "hue": round(ah), "source": source})
    random.Random(seed).shuffle(out)
    return out[:k]


def derive(combo: int, accent: int | None = None, stage: int | None = None, source: str = DEFAULT_SOURCE) -> dict:
    src = SOURCES[source]; cols = combos(source).get(combo)
    if not cols: raise ValueError(f"{src['label']}沒有第 {combo} 組（可用：{', '.join(map(str, combos(source)))}）")
    accent = accent or default_accent(cols); stage = stage or default_stage(cols, accent)
    if not (1 <= accent <= len(cols) and 1 <= stage <= len(cols)): raise ValueError(f"第 {combo} 組只有 {len(cols)} 色")
    a = cols[accent - 1]["hex"]; s = cols[stage - 1]["hex"]
    v = {}
    for mode in ("light", "dark"):
        bg = BG[mode]
        soft = tint(a, mode)
        st = tint(s, mode, 0.6)
        acc = fit(a, [bg], 4.5, mode)
        ink = fit(acc, [bg, soft], 4.8, mode)
        v[mode] = {"--accent": acc, "--accent-ink": ink, "--accent-soft": soft, "--stage": st}
        for i, c in enumerate(cols, 1):
            v[mode][f"--pal-{i}"] = fit(c["hex"], [bg, st], 3.0, mode)
            v[mode][f"--pal-{i}-ink"] = fit(c["hex"], [bg, st, soft], 4.6, mode)
            v[mode][f"--pal-{i}-soft"] = tint(c["hex"], mode)
            v[mode][f"--pal-{i}-mark"] = mark(c["hex"], mode)
    names = "、".join(f"{c['name']} {c['hex']}" for c in cols)
    lines = [f"/* palette:start — 由 oss.py palette 產生，不要手改 */",
             f"/* {src['label']}第 {combo} 組：{names}。重點色＝第 {accent} 色、舞台＝第 {stage} 色；文字與重點色只調明度過對比，底色用同色相的淡色。資料 {src['url']}（{src['note']}） */",
             ":root{"]
    for k in v["light"]: lines.append(f"  {k}:light-dark({v['light'][k]},{v['dark'][k]});")
    lines += ["}", "/* palette:end */"]
    return {"source": source, "label": src["label"], "url": src["url"], "combo": combo, "accent": accent, "stage": stage, "colors": [c["hex"] for c in cols], "names": [c["name"] for c in cols],
            "values": v, "css": "\n".join(lines)}


def preview_png(cands, path, current=None):
    """把候選畫成一張圖（亮色＋暗色），給 agent 用 Read 看。"""
    from PIL import Image, ImageDraw, ImageFont
    rows = len(cands); W, RH = 1180, 92
    img = Image.new("RGB", (W, RH * rows + 20), "#ffffff"); d = ImageDraw.Draw(img)
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15); fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except Exception: f = fb = ImageFont.load_default()
    for r, c in enumerate(cands):
        y = 10 + r * RH; p = derive(c["combo"], c.get("accent"), source=c.get("source", DEFAULT_SOURCE))
        d.text((12, y + 30), f"#{c['combo']}", fill="#111", font=fb)
        x = 90
        for col in c["colors"]:
            d.rectangle([x, y, x + 70, y + 70], fill=col["hex"]); x += 72
        x = max(x + 16, 400)
        for mode in ("light", "dark"):
            vv = p["values"][mode]; d.rectangle([x, y, x + 320, y + 70], fill=BG[mode])
            d.rectangle([x + 10, y + 10, x + 120, y + 60], fill=vv["--stage"])
            d.rectangle([x + 20, y + 18, x + 60, y + 52], fill=vv["--accent"])
            d.rectangle([x + 66, y + 18, x + 110, y + 52], fill=vv["--accent-soft"])
            d.text((x + 130, y + 12), "Accent text", fill=vv["--accent-ink"], font=fb)
            for i in range(len(c["colors"])): d.rectangle([x + 130 + i * 36, y + 44, x + 162 + i * 36, y + 62], fill=vv[f"--pal-{i + 1}"])
            x += 336
    img.save(path)
    return path
