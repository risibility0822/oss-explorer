#!/usr/bin/env python3
"""開源探索誌 流程工具。

把流程中「可以寫死的部分」交給程式，讓 agent 專心在研究、Demo 與寫作。
每個子指令成功時 exit 0，失敗時 exit 1 並印出要修正的項目。

  preflight            環境與 repo 健康檢查（含推送權限、工具安裝）
  status               狀態摘要（SessionStart hook 會自動印出）
  plan [--force]       解析 feedback.md、決定本集編號/格式/層級/主鏡頭/領域排序，開始一次 run
  new <slug>           依骨架建立 ep-NNN-<slug>/
  check [ep]           結構、資料、連結、大小、禁用項驗證
  qa [ep]              Playwright：桌機/手機/深色截圖、console 錯誤、版面溢出、互動測試、無障礙、縮圖
  register [ep]        把 ep/meta.json 寫進 data/*.json（可重複執行，結果一樣）
  build                產生 feed.xml、sitemap.xml、README 總覽表
  finish               寫入執行紀錄 data/runs.json（狀態 ok）
  publish              commit + push（自動 rebase 與重試；失敗則推到 wip 分支）
  abort --reason ...   記錄失敗、保存半成品到 wip 分支
  gate                 判斷這次 run 是否真的完成（Stop hook 使用）
  lesson "..."         追加一條經驗到 ops/LESSONS.md
"""
from __future__ import annotations

import argparse, datetime as dt, functools, hashlib, html, http.server, json, os, re, shutil
import socketserver, subprocess, sys, threading, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "ops"
DATA = ROOT / "data"
RUN = ROOT / ".run"
CUR = RUN / "current.json"
TPE = ZoneInfo("Asia/Taipei")
SITE = "https://risibility0822.github.io/oss-explorer/"
REPO_URL = "https://github.com/risibility0822/oss-explorer"
DOMAINS = ["AI 模型與推論", "AI 應用與 Agent 框架", "開發者工具", "資料庫與後端基礎設施", "自架服務 self-hosted",
           "開放資料集", "前端・設計・UI・字體・圖示", "多媒體", "地圖與地理空間", "科學・數學・生醫・氣候",
           "隱私・安全・網路", "硬體・IoT・嵌入式・機器人", "生產力・知識管理・桌面 App", "好玩・怪奇・創意程式・藝術"]
FORMATS, TIERS, LENSES = ["單品", "組合技"], ["巨星", "寶石", "新星"], ["厲害", "好玩", "商業潛力"]
SECTIONS = ["header", "why", "how", "demo", "run", "start", "ideas", "cross", "limits", "more", "sources"]
MAX_EP_BYTES, MAX_FILE_BYTES = 20 * 1024 * 1024, 45 * 1024 * 1024


# ───────────────────────── 小工具 ─────────────────────────
def now() -> dt.datetime: return dt.datetime.now(TPE)
def today() -> str: return now().strftime("%Y-%m-%d")
def iso() -> str: return now().isoformat(timespec="seconds")
def load(p: Path, default=None):
    try: return json.loads(p.read_text("utf-8"))
    except FileNotFoundError: return default
def save(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp"); tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", "utf-8"); tmp.replace(p)
def sh(*cmd, cwd=ROOT, check=False, timeout=600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check, timeout=timeout)
def ok(m): print(f"  ✅ {m}")
def bad(m): print(f"  ❌ {m}")
def warn(m): print(f"  ⚠️  {m}")
def die(m, code=1): print(f"\n✖ {m}"); sys.exit(code)
def pad(n): return f"{int(n):03d}"
def cur() -> dict: return load(CUR, {}) or {}
def set_cur(**kw):
    c = cur(); c.update(kw); c["updatedAt"] = iso(); save(CUR, c); return c
def step(name, status, **kw):
    c = cur()
    if not c: return
    c.setdefault("steps", {})[name] = {"status": status, "at": iso(), **kw}; c["updatedAt"] = iso(); save(CUR, c)
def ep_dir(arg=None) -> Path:
    slug = arg or cur().get("slug")
    if not slug: die("沒有指定集數資料夾，也沒有進行中的 run。用法：oss.py <cmd> ep-NNN-slug")
    p = ROOT / slug.strip("/")
    if not p.is_dir(): die(f"找不到資料夾 {p}")
    return p
def data_files():
    return load(DATA / "episodes.json", []), load(DATA / "ideas.json", []), load(DATA / "state.json", {}), load(DATA / "runs.json", [])


# ───────────────────────── schema ─────────────────────────
def validate_schema(obj, name) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return [f"缺少 jsonschema 套件（pip install --break-system-packages jsonschema）"]
    schema = load(OPS / "schema" / f"{name}.schema.json")
    v = jsonschema.Draft202012Validator(schema)
    return [f"{name}: {'/'.join(map(str, e.absolute_path)) or '(root)'} → {e.message}" for e in sorted(v.iter_errors(obj), key=str)]


# ───────────────────────── preflight ─────────────────────────
def cmd_preflight(a):
    print("Preflight 環境檢查"); fatal = 0
    def need(cond, good, badmsg, is_fatal=True):
        nonlocal fatal
        if cond: ok(good)
        else: (bad if is_fatal else warn)(badmsg); fatal += 1 if is_fatal else 0
    need(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]}", "Python 需要 3.10+")
    for tool in ["git", "node", "npm"]:
        need(shutil.which(tool), f"{tool} 可用", f"找不到 {tool}")
    r = sh("git", "rev-parse", "--abbrev-ref", "HEAD"); need(r.stdout.strip() == "main", "在 main 分支", f"目前分支是 {r.stdout.strip()}，請切回 main")
    r = sh("git", "remote", "get-url", "origin"); need("risibility0822/oss-explorer" in r.stdout or os.environ.get("OSS_TEST_ORIGIN"), "origin 指向 risibility0822/oss-explorer", f"origin 不對：{r.stdout.strip()}")
    r = sh("git", "fetch", "--depth=20", "origin", "main", timeout=180)
    need(r.returncode == 0, "可以 fetch origin", f"fetch 失敗：{r.stderr.strip()[:200]}")
    if r.returncode == 0:
        behind = sh("git", "rev-list", "--count", "HEAD..origin/main").stdout.strip()
        if behind not in ("", "0"):
            m = sh("git", "merge", "--ff-only", "origin/main"); need(m.returncode == 0, f"已快轉到最新（落後 {behind} 個 commit）", f"無法快轉：{m.stderr.strip()[:200]}")
        else: ok("與 origin/main 同步")
    dirty = [l for l in sh("git", "status", "--porcelain").stdout.splitlines() if l and not l[3:].startswith(".run")]
    need(not dirty, "工作區乾淨", f"工作區有未提交變更：{dirty[:5]}（若是上次中斷的半成品，先決定保留或 git stash）", is_fatal=False)
    r = sh("git", "push", "--dry-run", "origin", "HEAD:main", timeout=120)
    need(r.returncode == 0, "推送權限 OK（dry-run）", f"推送權限檢查失敗：{(r.stderr or r.stdout).strip()[:300]}")
    for name in ["episodes", "ideas", "state", "runs"]:
        obj = load(DATA / f"{name}.json")
        if obj is None: bad(f"data/{name}.json 不存在或無法解析"); fatal += 1; continue
        errs = validate_schema(obj, name)
        need(not errs, f"data/{name}.json 格式正確", "；".join(errs[:3]))
    r = sh("git", "ls-remote", "https://github.com/octocat/Hello-World", "HEAD", timeout=60)
    need(r.returncode == 0, "可以從 GitHub clone", "無法連到 github.com（git）")
    r = sh("npm", "view", "esbuild", "version", timeout=60); need(r.returncode == 0, "npm registry 可用", "npm registry 連不到")
    r = sh(sys.executable, "-m", "pip", "download", "--no-deps", "-q", "-d", "/tmp/_pf", "six", timeout=120); need(r.returncode == 0, "PyPI 可用", "PyPI 連不到", is_fatal=False)
    if not (OPS / "node_modules" / "axe-core").exists():
        r = sh("npm", "ci", "--no-audit", "--no-fund", "--prefix", str(OPS), timeout=300)
        need(r.returncode == 0, "已安裝 ops 工具（axe-core、html-validate）", f"npm ci 失敗：{r.stderr.strip()[-300:]}", is_fatal=False)
    else: ok("ops 工具已安裝")
    try:
        import playwright  # noqa
        r = sh(sys.executable, "-c", "from playwright.sync_api import sync_playwright as s\nwith s() as p: b=p.chromium.launch(); b.close()", timeout=120)
        need(r.returncode == 0, "Playwright + Chromium 可啟動", f"Chromium 啟動失敗：{r.stderr.strip()[-300:]}", is_fatal=False)
    except ImportError: warn("沒有 Python playwright：qa 會失敗（pip install --break-system-packages playwright）")
    free = shutil.disk_usage(ROOT).free // 2**30; need(free >= 3, f"磁碟剩 {free} GB", f"磁碟只剩 {free} GB", is_fatal=False)
    RUN.mkdir(exist_ok=True); save(RUN / "preflight.json", {"at": iso(), "fatal": fatal})
    if fatal: die(f"Preflight 有 {fatal} 個致命問題。先處理；處理不了就 `oss.py abort --reason ...`")
    print("\n✔ Preflight 通過")


# ───────────────────────── feedback.md ─────────────────────────
def parse_feedback() -> dict:
    p = ROOT / "feedback.md"
    if not p.exists(): return {"wishes": [], "ratings": {}, "stars": []}
    sec, out = None, {"wishes": [], "ratings": {}, "stars": []}
    for raw in p.read_text("utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            t = line[3:]
            sec = "wishes" if t.startswith("許願") else "ratings" if t.startswith("評分") else "stars" if t.startswith("收藏") else "done" if t.startswith("已處理") else None
            continue
        if not line.startswith(("-", "*")) or sec in (None, "done"): continue
        item = line.lstrip("-* ").strip()
        if not item: continue
        if sec == "wishes": out["wishes"].append(item)
        elif sec == "stars": out["stars"].append(item)
        elif sec == "ratings":
            m = re.match(r"(ep-?\s*0*(\d+))\s*[：:]\s*(.*)", item, re.I)
            if not m: continue
            rest = m.group(3); rm = re.search(r"([1-5])\s*(分|/5)?", rest)
            if not rest.strip(): continue
            out["ratings"][f"ep-{pad(m.group(2))}"] = {"rating": int(rm.group(1)) if rm else None, "deeper": "想深入" in rest, "note": rest.strip()}
    return out

def wish_id(text): return "w-" + hashlib.sha1(text.strip().encode()).hexdigest()[:8]

def apply_feedback(state, ideas) -> dict:
    fb = parse_feedback(); known = {w["id"] for w in state.setdefault("wishes", [])}; added = []
    for t in fb["wishes"]:
        wid = wish_id(t)
        if wid not in known:
            state["wishes"].append({"id": wid, "text": t, "status": "open", "createdAt": iso()}); added.append(t); known.add(wid)
    state["feedback"] = fb["ratings"]
    starred = 0
    for idea in ideas:
        hit = any(s and (s in idea["title"] or idea["title"] in s or s == idea["id"]) for s in fb["stars"])
        if hit and not idea.get("starred"): starred += 1
        idea["starred"] = bool(hit) or bool(idea.get("starred") and idea.get("starredBy") == "manual")
    unmatched = [s for s in fb["stars"] if not any(s in i["title"] or i["title"] in s or s == i["id"] for i in ideas)]
    state["starNotes"] = unmatched
    return {"newWishes": added, "ratings": fb["ratings"], "newStars": starred, "unmatchedStars": unmatched}


# ───────────────────────── plan ─────────────────────────
def domain_ranking(episodes, state):
    counts = {d: 0 for d in DOMAINS}
    for e in episodes: counts[e["domain"]] = counts.get(e["domain"], 0) + 1
    recent = [e["domain"] for e in sorted(episodes, key=lambda e: e["no"])[-6:]]
    recent3 = recent[-3:]
    ratings = {}
    for epid, fb in (state.get("feedback") or {}).items():
        e = next((x for x in episodes if x["id"] == epid), None)
        if e and fb.get("rating"): ratings.setdefault(e["domain"], []).append(fb["rating"])
    deeper = {next((x["domain"] for x in episodes if x["id"] == k), None) for k, v in (state.get("feedback") or {}).items() if v.get("deeper")}
    rows = []
    for d in DOMAINS:
        avg = sum(ratings.get(d, [])) / len(ratings[d]) if ratings.get(d) else None
        liked = (avg is not None and avg >= 4) or d in deeper
        eligible = d not in (recent3 if liked else recent)
        score = counts[d] * 10 + (5 if avg is not None and avg <= 2 else 0) - (3 if liked else 0)
        why = []
        if not eligible: why.append("最近才去過")
        if liked: why.append("你評價高／想深入")
        if avg is not None and avg <= 2: why.append("評分偏低，往後排")
        rows.append({"domain": d, "count": counts[d], "eligible": eligible, "score": score, "avgRating": avg, "note": "、".join(why)})
    rows.sort(key=lambda r: (not r["eligible"], r["score"], DOMAINS.index(r["domain"])))
    return rows

def cmd_plan(a):
    episodes, ideas, state, runs = data_files()
    if cur().get("phase") not in (None, "published", "aborted") and not a.force:
        print(json.dumps(cur(), ensure_ascii=False, indent=1)); die("已有進行中的 run（上面）。接著做下一步，或用 --force 重新規劃。", 2)
    pf = load(RUN / "preflight.json", {})
    if not pf or pf.get("fatal"): die("請先成功執行 `oss.py preflight`")
    if any(e["date"] == today() for e in episodes) and not a.force:
        set_cur(phase="skipped", reason="今天已出刊"); print("今天已經出刊過了（data/episodes.json 有今天的集數）。最後訊息請寫「今天已出刊」。"); sys.exit(3)
    fb = apply_feedback(state, ideas)
    save(DATA / "state.json", state); save(DATA / "ideas.json", ideas)
    n = max([e["no"] for e in episodes], default=0) + 1
    fmt = "組合技" if n % 3 == 0 else "單品"
    tier = {1: "巨星", 2: "寶石", 0: "新星"}[n % 3]
    lens = {1: "厲害", 2: "好玩", 0: "商業潛力"}[n % 3]
    ranking = domain_ranking(episodes, state)
    wishes = [w for w in state.get("wishes", []) if w["status"] == "open"]
    starred = [{"id": i["id"], "title": i["title"]} for i in ideas if i.get("starred")]
    plan = {"runId": now().strftime("%Y%m%d-%H%M"), "startedAt": iso(), "phase": "planned", "no": n, "id": f"ep-{pad(n)}",
            "date": today(), "format": fmt, "tier": tier, "lens": lens,
            "wishFirst": wishes[0] if wishes else None, "openWishes": wishes,
            "domainTop": [r["domain"] for r in ranking if r["eligible"]][:4], "domainRanking": ranking,
            "covered": state.get("covered", []), "pool": state.get("pool", [])[:15], "starredIdeas": starred,
            "feedback": fb, "previous": [{"id": e["id"], "title": e["title"], "path": e["path"], "domain": e["domain"]} for e in episodes],
            "steps": {}}
    save(CUR, plan)
    print(f"本集：#{pad(n)}（{fmt}・{tier}・主鏡頭「{lens}」）")
    if plan["wishFirst"]: print(f"★ 許願優先：{plan['wishFirst']['text']}（id {plan['wishFirst']['id']}）")
    print("領域建議（依序）：" + " ＞ ".join(plan["domainTop"]))
    if starred: print("你收藏的點子：" + "；".join(s["title"] for s in starred))
    if fb["newWishes"]: print("新許願：" + "；".join(fb["newWishes"]))
    if fb["unmatchedStars"]: print("對不上的收藏：" + "；".join(fb["unmatchedStars"]))
    print(f"\n已寫入 {CUR.relative_to(ROOT)}。下一步：發掘候選 → 選定後 `oss.py new <slug>`")


# ───────────────────────── new ─────────────────────────
def cmd_new(a):
    c = cur()
    if c.get("phase") != "planned" and not a.force: die("請先 `oss.py plan`（或已經建立過了；加 --force 重建）")
    slug = a.slug.lower().strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", slug): die("slug 只能用英文小寫、數字與連字號，2–41 字")
    name = f"{c['id']}-{slug}"; dest = ROOT / name
    if dest.exists() and not a.force: die(f"{name} 已存在")
    tpl = OPS / "templates" / "episode"
    shutil.copytree(tpl, dest, dirs_exist_ok=True)
    for f in dest.rglob("*"):
        if f.is_file() and f.suffix in (".html", ".json", ".md", ".py"):
            t = f.read_text("utf-8").replace("{{NNN}}", pad(c["no"])).replace("{{NO}}", str(c["no"])).replace("{{ID}}", c["id"]) \
                .replace("{{SLUG}}", name).replace("{{DATE}}", c["date"]).replace("{{FORMAT}}", c["format"]).replace("{{TIER}}", c["tier"]) \
                .replace("{{LENS}}", c["lens"]).replace("{{SITE}}", SITE).replace("{{REPO}}", REPO_URL)
            f.write_text(t, "utf-8")
    set_cur(phase="building", slug=name)
    print(f"已建立 {name}/：index.html（骨架）、meta.json、lab/README.md、lab/qa_check.py\n下一步：研究 → 實作 Demo → 寫頁面 → `oss.py check` → `oss.py qa`")


# ───────────────────────── check ─────────────────────────
class _Collector:
    def __init__(self): self.sections, self.links, self.srcs, self.ids, self.meta, self.scripts = [], [], [], set(), {}, []

def parse_page(text):
    from html.parser import HTMLParser
    col = _Collector()
    class P(HTMLParser):
        def __init__(s): super().__init__(convert_charrefs=True); s.in_script = False; s.buf = []
        def handle_starttag(s, tag, attrs):
            d = dict(attrs)
            if "data-section" in d: col.sections.append(d["data-section"])
            if "id" in d: col.ids.add(d["id"])
            if tag == "a" and d.get("href"): col.links.append(d["href"])
            if tag in ("script", "img", "link", "source", "video", "audio", "iframe"):
                u = d.get("src") or (d.get("href") if tag == "link" else None)
                if u: col.srcs.append((tag, u))
            if tag == "meta":
                k = d.get("name") or d.get("property")
                if k: col.meta[k] = d.get("content", "")
            if tag == "script" and not d.get("src") and d.get("type", "text/javascript") in ("text/javascript", "module", ""): s.in_script = True; s.buf = []
        def handle_endtag(s, tag):
            if tag == "script" and s.in_script: col.scripts.append("".join(s.buf)); s.in_script = False
        def handle_data(s, data):
            if s.in_script: s.buf.append(data)
    P().feed(text)
    return col

def cmd_check(a):
    ep = ep_dir(a.ep); errs, warns = [], []
    page = ep / "index.html"; meta_p = ep / "meta.json"
    if not page.exists(): die("缺 index.html")
    text = page.read_text("utf-8"); col = parse_page(text)
    # 1. 骨架殘留
    for pat, why, fl in [(r"\{\{[^}\n]{1,80}\}\}", "骨架佔位符沒換掉", 0), (r"\bTODO\b|\bFIXME\b|待補|（待確認）", "還有 TODO／待補文字", 0), (r"lorem ipsum", "還有假文", re.I), (r"__[A-Z_]{3,}__", "還有 __PLACEHOLDER__", 0)]:
        m = re.search(pat, text, fl)
        if m: errs.append(f"{why}：「{m.group(0)}」")
    # 2. 必備區塊
    missing = [s for s in SECTIONS if s not in col.sections]
    if missing: errs.append(f"缺少區塊 data-section：{', '.join(missing)}")
    # 3. head
    if "viewport" not in col.meta: errs.append("缺 <meta name=viewport>")
    for k in ("og:title", "og:description", "og:image"):
        if not col.meta.get(k): errs.append(f"缺 {k}")
    if not re.search(r"prefers-color-scheme:\s*dark|light-dark\(", text): errs.append("沒有深色模式（prefers-color-scheme 或 light-dark()）")
    # 4. 連結與資源
    site_links = [l for l in col.links if not l.startswith(("http://", "https://", "#", "mailto:"))]
    for l in site_links:
        target = (ep / l.split("#")[0].split("?")[0]).resolve()
        if l.split("#")[0] and not (target.exists() or (target / "index.html").exists()):
            errs.append(f"站內連結指到不存在的檔案：{l}")
    for tag, u in col.srcs:
        if u.startswith("http://"): errs.append(f"不安全的 http 資源：{u}")
        elif u.startswith("https://"):
            if not re.match(r"https://fonts\.(googleapis|gstatic)\.com", u): warns.append(f"外部資源（網站上可用，但工作區測不到）：{u}")
        elif u in ("../feed.xml",): pass  # build 產生
        elif not (ep / u.split("?")[0]).exists(): errs.append(f"<{tag}> 指到不存在的檔案：{u}")
    if "../" not in col.links: errs.append("缺「回到首頁」連結 href=\"../\"")
    if not any("feedback.md" in l for l in col.links): errs.append("缺 feedback.md 評分連結")
    if not any(f"/tree/main/{ep.name}/lab" in l for l in col.links): errs.append(f"Demo 區缺 lab/ 連結（{REPO_URL}/tree/main/{ep.name}/lab）")
    ext = [l for l in col.links if l.startswith("https://")]
    if len(set(ext)) < 6: errs.append(f"外部連結太少（{len(set(ext))}），來源至少 5 個")
    for s in col.scripts:
        for m in re.finditer(r"fetch\(\s*['\"](https?://[^'\"]+)", s):
            warns.append(f"頁面在執行期抓外部資料（{m.group(1)}）：資料最好放進本集資料夾")
    # 5. JS 語法
    for i, s in enumerate(col.scripts):
        f = RUN / f"_check_{i}.js"; RUN.mkdir(exist_ok=True); f.write_text(s, "utf-8")
        r = sh("node", "--check", str(f))
        if r.returncode:
            lines = r.stderr.strip().splitlines(); msg = next((l for l in lines if "Error" in l), lines[-1] if lines else "")
            loc = next((l.rsplit(":", 1)[-1] for l in lines if str(f) in l), "")
            errs.append(f"第 {i+1} 段 <script> 語法錯誤（該段第 {loc} 行）：{msg.strip()}")
        f.unlink(missing_ok=True)
    # 6. html-validate（只取嚴重問題）
    hv = OPS / "node_modules" / ".bin" / "html-validate"
    if hv.exists():
        r = sh(str(hv), "--config", str(OPS / "htmlvalidate.json"), "--formatter", "json", str(page))
        try:
            for res in json.loads(r.stdout or "[]"):
                for msg in res.get("messages", []):
                    (errs if msg.get("severity") == 2 else warns).append(f"HTML（{msg.get('ruleId')}，第 {msg.get('line')} 行）：{msg.get('message')}")
        except json.JSONDecodeError: warns.append("html-validate 輸出無法解析")
    # 7. 大小
    total = 0
    for f in ep.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
            if f.stat().st_size > MAX_FILE_BYTES: errs.append(f"檔案太大（{f.stat().st_size//2**20} MB）：{f.relative_to(ROOT)}")
            if f.name in ("node_modules", ".env") or "node_modules" in f.parts: errs.append(f"不該提交：{f.relative_to(ROOT)}")
    if total > MAX_EP_BYTES: errs.append(f"整集 {total/2**20:.1f} MB，超過 20 MB")
    # 8. lab
    lab = ep / "lab"
    if not (lab / "README.md").exists(): errs.append("缺 lab/README.md")
    elif "{{" in (lab / "README.md").read_text("utf-8"): errs.append("lab/README.md 還是骨架")
    lab_files = [f for f in lab.rglob("*") if f.is_file() and f.name not in ("README.md", "qa_check.py")] if lab.exists() else []
    if not lab_files: errs.append("lab/ 沒有任何實驗腳本或輸出（Demo 必須真的跑過，腳本要留下）")
    qc = lab / "qa_check.py"
    if not qc.exists(): errs.append("缺 lab/qa_check.py（互動測試）")
    elif "TODO(本集)" in qc.read_text("utf-8"): errs.append("lab/qa_check.py 還是骨架：請寫真正操作 Demo 的測試")
    # 9. meta.json
    meta = load(meta_p)
    if meta is None: errs.append("meta.json 不存在或不是合法 JSON")
    else:
        errs += validate_schema(meta, "meta")
        c = cur()
        if c.get("id") and meta.get("id") != c["id"]: errs.append(f"meta.id={meta.get('id')}，但本次 run 是 {c['id']}")
        if meta.get("slug") != ep.name: errs.append(f"meta.slug 應為 {ep.name}")
        if c.get("format") and meta.get("format") != c["format"]: warns.append(f"meta.format={meta.get('format')}，規劃是 {c['format']}（若有理由請在頁面說明）")
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        if title and meta.get("title") and meta["title"].split("：")[0] not in title.group(1): warns.append("<title> 跟 meta.title 對不太起來")
        covered = set(load(DATA / "state.json", {}).get("covered", []))
        mains = [r["url"] for r in meta.get("resources", []) if r.get("role") == "main"]
        dup = [u for u in mains if u in covered and not (load(DATA / "episodes.json", []) and any(e["id"] == meta.get("id") for e in load(DATA / "episodes.json", [])))]
        if dup: errs.append(f"主角已經介紹過：{dup}")
        if len(re.findall(r'class="[^"]*\bidea\b', text)) < len(meta.get("ideas", [])):
            warns.append("頁面上的點子數量比 meta.ideas 少")
    # 結果
    for w in warns: warn(w)
    for e in errs: bad(e)
    step("check", "fail" if errs else "pass", errors=len(errs), warnings=len(warns))
    if errs: die(f"check 未通過：{len(errs)} 個錯誤")
    print(f"\n✔ check 通過（{len(warns)} 個提醒）")


# ───────────────────────── qa（Playwright）─────────────────────────
class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def serve():
    handler = functools.partial(_Quiet, directory=str(ROOT))
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler); srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"

def cmd_qa(a):
    home = a.ep in (".", "home")
    ep = ROOT if home else ep_dir(a.ep); label = "home" if home else ep.name
    out = RUN / "qa" / label; out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    srv, base = serve(); url = base if home else f"{base}{ep.name}/"; errs, warns, report = [], [], {}
    axe = OPS / "node_modules" / "axe-core" / "axe.min.js"
    views = [("desktop", {"width": 1280, "height": 900}, "light"), ("mobile", {"width": 375, "height": 812}, "light"), ("mobile-dark", {"width": 375, "height": 812}, "dark")]
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for name, vp, scheme in views:
                ctx = b.new_context(viewport=vp, color_scheme=scheme, device_scale_factor=1)
                pg = ctx.new_page(); perr, cerr, rfail = [], [], []
                pg.on("pageerror", lambda e: perr.append(str(e)))
                pg.on("console", lambda m: cerr.append(m.text) if m.type == "error" else None)
                pg.on("requestfailed", lambda r: rfail.append(r.url))
                t0 = time.time(); pg.goto(url, wait_until="load", timeout=45000); pg.wait_for_timeout(800)
                info = pg.evaluate("""() => {
                  const de=document.documentElement, over=de.scrollWidth-window.innerWidth;
                  const wide=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.right>window.innerWidth+2&&getComputedStyle(e).position!=='fixed'&&!e.closest('pre,.scroll,table,[data-allow-overflow]')}).slice(0,5).map(e=>e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'?'.'+e.className.split(' ')[0]:''));
                  const small=[...document.querySelectorAll('button,a.btn,[role=button],input[type=checkbox],select')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.height<32||r.width<32)}).length;
                  const sections=[...document.querySelectorAll('[data-section]')].map(e=>e.dataset.section);
                  const imgsBroken=[...document.images].filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src).slice(0,5);
                  return {over, wide, small, sections, imgsBroken, title:document.title, h1:document.querySelector('h1')?.textContent?.trim()};
                }""")
                pg.screenshot(path=str(out / f"{name}.png"), full_page=False)
                if name == "desktop":
                    pg.screenshot(path=str(out / "desktop-full.png"), full_page=True)
                    pg.set_viewport_size({"width": 1200, "height": 630}); pg.wait_for_timeout(300)
                    pg.screenshot(path=str(out / "og.png")); pg.set_viewport_size(vp)
                if axe.exists() and name == "desktop":
                    pg.add_script_tag(path=str(axe))
                    res = pg.evaluate("async()=>{const r=await axe.run(document,{runOnly:['wcag2a','wcag2aa']});return r.violations.map(v=>({id:v.id,impact:v.impact,n:v.nodes.length,help:v.help}))}")
                    report["axe"] = res
                    for v in res:
                        if v["impact"] in ("critical",): errs.append(f"無障礙嚴重問題：{v['id']}（{v['n']} 處）{v['help']}")
                        elif v["impact"] == "serious": warns.append(f"無障礙：{v['id']}（{v['n']} 處）{v['help']}")
                # 互動測試
                if name == "desktop" and (ep / "lab" / "qa_check.py").exists():
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("qa_check", ep / "lab" / "qa_check.py"); mod = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(mod)
                        if hasattr(mod, "check"):
                            pg.reload(wait_until="load"); pg.wait_for_timeout(500)
                            msgs = mod.check(pg) or []
                            report["interaction"] = msgs; print("  互動測試：" + ("；".join(map(str, msgs)) if msgs else "通過"))
                        else: errs.append("lab/qa_check.py 沒有 check(page) 函式")
                    except AssertionError as e: errs.append(f"互動測試失敗：{e}")
                    except Exception as e: errs.append(f"互動測試出錯：{type(e).__name__}: {e}")
                ext_fail = [u for u in rfail if not re.match(r"https://fonts\.(googleapis|gstatic)\.com/", u)]
                report[name] = {**info, "loadSec": round(time.time() - t0, 2), "pageErrors": perr, "consoleErrors": cerr, "failedRequests": ext_fail}
                if perr: errs.append(f"[{name}] JavaScript 錯誤：{perr[:2]}")
                cerr2 = [e for e in cerr if "fonts.g" not in e and "ERR_" not in e]
                if cerr2: errs.append(f"[{name}] console error：{cerr2[:2]}")
                local_fail = [u for u in ext_fail if u.startswith(base)]
                if local_fail: errs.append(f"[{name}] 檔案載入失敗：{local_fail[:3]}")
                elif ext_fail: warns.append(f"[{name}] 外部資源在工作區載入失敗（網站上可能正常）：{ext_fail[:3]}")
                if info["over"] > 2: errs.append(f"[{name}] 版面橫向溢出 {info['over']}px：{info['wide']}")
                if info["imgsBroken"]: errs.append(f"[{name}] 圖片壞掉：{info['imgsBroken']}")
                if name == "mobile" and info["small"] > 3: warns.append(f"[mobile] 有 {info['small']} 個按鈕/控制項小於 32px")
                ctx.close()
            b.close()
    finally:
        srv.shutdown()
    # 縮圖
    try:
        from PIL import Image
        im = Image.open(out / "og.png").convert("RGB"); im.save(ep / "og.jpg", quality=78, optimize=True, progressive=True)
        ok(f"已產生縮圖 {(ep/'og.jpg').relative_to(ROOT)}（{(ep/'og.jpg').stat().st_size//1024} KB）")
    except Exception as e: warns.append(f"縮圖產生失敗：{e}")
    save(out / "report.json", report)
    for w in warns: warn(w)
    for e in errs: bad(e)
    if not home: pass
    print(f"\n截圖：{out.relative_to(ROOT)}/desktop.png、mobile.png、mobile-dark.png、desktop-full.png（請用 Read 打開來看）")
    if not home: step("qa", "fail" if errs else "pass", errors=len(errs), warnings=len(warns))
    if errs: die(f"qa 未通過：{len(errs)} 個錯誤")
    print("✔ qa 通過")


# ───────────────────────── register / build ─────────────────────────
def cmd_register(a):
    ep = ep_dir(a.ep); meta = load(ep / "meta.json")
    if meta is None: die("meta.json 無法讀取")
    e = validate_schema(meta, "meta")
    if e: [bad(x) for x in e]; die("meta.json 格式不對")
    episodes, ideas, state, runs = data_files()
    entry = {k: meta[k] for k in ("no", "id", "date", "title", "oneliner", "domain", "format", "tier", "lens", "resources", "demo", "highlights", "tags")}
    entry.update(path=f"{ep.name}/", lab=f"{ep.name}/lab", thumb=f"{ep.name}/og.jpg" if (ep / "og.jpg").exists() else None,
                 createdAt=meta.get("createdAt") or iso())
    episodes = [x for x in episodes if x["id"] != meta["id"]] + [entry]; episodes.sort(key=lambda x: x["no"])
    ideas = [i for i in ideas if i["episode"] != meta["id"]]
    starred_titles = parse_feedback()["stars"]
    for k, it in enumerate(meta["ideas"], 1):
        iid = f"{meta['id']}-{k}"
        ideas.append({"id": iid, "episode": meta["id"], "no": meta["no"], "title": it["title"], "pitch": it["pitch"], "effort": it["effort"], "value": it["value"],
                      "starred": any(s and (s in it["title"] or it["title"] in s or s == iid) for s in starred_titles)})
    # 狀態一律從 episodes 推導（可重複執行）
    state["episodeCount"] = max(x["no"] for x in episodes)
    counts = {}
    for x in episodes: counts[x["domain"]] = counts.get(x["domain"], 0) + 1
    state["domainCounts"] = counts
    state["recentDomains"] = [x["domain"] for x in episodes[-6:]]
    cov = list(dict.fromkeys(state.get("covered", []) + [r["url"] for x in episodes for r in x["resources"] if r.get("role", "main") == "main"]))
    state["covered"] = cov
    pool = [p for p in state.get("pool", []) if p["url"] not in cov]
    for p in meta.get("poolAdd", []):
        if p["url"] not in cov and all(p["url"] != q["url"] for q in pool): pool.append(p)
    state["pool"] = pool[-40:]
    if meta.get("wish"):
        for w in state.get("wishes", []):
            if w["id"] == meta["wish"]["id"]: w.update(status=meta["wish"].get("status", "done"), reply=meta["wish"]["reply"], doneIn=meta["id"])
    for w in meta.get("wishUpdates", []):
        for x in state.get("wishes", []):
            if x["id"] == w["id"]: x.update({k: v for k, v in w.items() if k != "id"})
    state["lastRunAt"] = iso(); state["nextHint"] = meta.get("nextHint", state.get("nextHint", ""))
    for name, obj in (("episodes", episodes), ("ideas", ideas), ("state", state)):
        errs = validate_schema(obj, name)
        if errs: [bad(x) for x in errs]; die(f"寫入後的 data/{name}.json 不符合 schema，未儲存")
    save(DATA / "episodes.json", episodes); save(DATA / "ideas.json", ideas); save(DATA / "state.json", state)
    step("register", "pass")
    if cur(): set_cur(phase="registered")
    ok(f"已登錄 {meta['id']}：episodes {len(episodes)} 集、ideas {len(ideas)} 個、pool {len(state['pool'])} 筆")

def move_done_wishes(state):
    p = ROOT / "feedback.md"
    if not p.exists(): return
    lines = p.read_text("utf-8").splitlines(); done = {w["id"]: w for w in state.get("wishes", []) if w["status"] in ("done", "blocked")}
    keep, moved, sec = [], [], None
    for line in lines:
        s = line.strip()
        if s.startswith("## "): sec = s[3:]
        if sec and sec.startswith("許願") and s.startswith(("-", "*")) and s.lstrip("-* ").strip():
            w = done.get(wish_id(s.lstrip("-* ").strip()))
            if w: moved.append(f"- {s.lstrip('-* ').strip()}（→ {w.get('doneIn') or '做不到'}：{w.get('reply','')}）"); continue
        keep.append(line)
    if moved:
        text = "\n".join(keep).rstrip() + "\n" + "\n".join(moved) + "\n"
        p.write_text(text, "utf-8"); ok(f"feedback.md：{len(moved)} 則許願移到「已處理」")
    return bool(moved)

def cmd_build(a):
    episodes, ideas, state, runs = data_files()
    eps = sorted(episodes, key=lambda e: e["no"], reverse=True)
    def x(s): return html.escape(str(s or ""), quote=True)
    updated = (eps[0]["createdAt"] if eps else iso())
    entries = "".join(f"""
  <entry>
    <title>#{pad(e['no'])}｜{x(e['title'])}</title>
    <link href="{SITE}{x(e['path'])}"/>
    <id>{SITE}{x(e['path'])}</id>
    <updated>{x(e['createdAt'])}</updated>
    <category term="{x(e['domain'])}"/>
    <summary>{x(e['oneliner'])}</summary>
  </entry>""" for e in eps[:50])
    feed = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>開源探索誌</title>
  <subtitle>每週一、三、五自動出刊：認識一個開源資源，附可玩的 Demo。</subtitle>
  <link href="{SITE}"/>
  <link rel="self" href="{SITE}feed.xml"/>
  <id>{SITE}</id>
  <updated>{x(updated)}</updated>
  <author><name>開源探索誌</name></author>{entries}
</feed>
"""
    (ROOT / "feed.xml").write_text(feed, "utf-8")
    urls = [SITE] + [SITE + e["path"] for e in eps]
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{x(u)}</loc></url>\n" for u in urls) + "</urlset>\n", "utf-8")
    rd = ROOT / "README.md"; t = rd.read_text("utf-8") if rd.exists() else ""
    table = "| 集數 | 日期 | 主題 | 領域 |\n|---|---|---|---|\n" + "".join(f"| [{pad(e['no'])}]({e['path']}) | {e['date']} | {e['title']} | {e['domain']} |\n" for e in sorted(episodes, key=lambda e: e["no"]))
    block = f"<!-- EPISODES:START -->\n{table}<!-- EPISODES:END -->"
    t = re.sub(r"<!-- EPISODES:START -->.*?<!-- EPISODES:END -->", block, t, flags=re.S) if "EPISODES:START" in t else t.rstrip() + "\n\n" + block + "\n"
    rd.write_text(t, "utf-8")
    step("build", "pass"); ok(f"feed.xml（{len(eps)} 集）、sitemap.xml、README 總覽表已更新")


# ───────────────────────── runs / publish / gate ─────────────────────────
def record_run(status, note=""):
    runs = load(DATA / "runs.json", []); c = cur()
    rec = {"runId": c.get("runId") or now().strftime("%Y%m%d-%H%M"), "startedAt": c.get("startedAt") or iso(), "endedAt": iso(),
           "status": status, "episode": c.get("id") if status == "ok" else None, "note": note[:300],
           "steps": {k: v.get("status") for k, v in (c.get("steps") or {}).items()}}
    runs = [r for r in runs if r["runId"] != rec["runId"]] + [rec]
    save(DATA / "runs.json", runs[-60:])
    return rec

def cmd_finish(a):
    c = cur(); need = ["check", "qa", "register", "build"]
    missing = [s for s in need if (c.get("steps") or {}).get(s, {}).get("status") != "pass"]
    if a.review: step("review", "pass", note=a.review[:200])
    if (c.get("steps") or {}).get("review", {}).get("status") != "pass" and not a.review: missing.append("review（審查員通過後用 --review \"摘要\" 記錄）")
    if missing and not a.force: die("還有步驟沒通過：" + "、".join(missing))
    record_run("ok", a.note or ""); set_cur(phase="finished"); ok("已寫入 data/runs.json。下一步：`oss.py publish`")

def git_push(branch="main", attempts=3) -> tuple[bool, str]:
    last = ""
    for i in range(attempts):
        r = sh("git", "-c", "push.negotiate=true", "push", "origin", f"HEAD:{branch}", timeout=300)
        if r.returncode == 0: return True, ""
        last = (r.stderr or r.stdout).strip()
        if "rejected" in last or "fetch first" in last or "non-fast-forward" in last:
            sh("git", "fetch", "--depth=50", "origin", branch, timeout=180)
            rb = sh("git", "rebase", f"origin/{branch}")
            if rb.returncode:
                sh("git", "rebase", "--abort")
                return False, "rebase 衝突（通常是 feedback.md 被同時修改）：" + rb.stdout[-300:]
        elif "429" in last: time.sleep(5)
        else: time.sleep(3 * (i + 1))
    return False, last[-400:]

def cmd_publish(a):
    c = cur()
    if c.get("phase") not in ("finished", "published") and not a.force: die("請先 `oss.py finish`（或 abort）")
    # 主人可能同時在 GitHub 上改 feedback.md：本集的 commit 一律不碰它，避免衝突
    sh("git", "checkout", "--", "feedback.md")
    sh("git", "add", "-A"); sh("git", "reset", "-q", "--", "feedback.md")
    if sh("git", "diff", "--cached", "--quiet").returncode:
        title = f"第 {pad(c['no'])} 集：{(load(ROOT / c['slug'] / 'meta.json', {}) or {}).get('title', c.get('slug'))}" if c.get("slug") else "更新"
        r = sh("git", "commit", "-q", "-m", title, "-m", "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        if r.returncode: die(f"commit 失敗：{r.stderr}")
    okp, why = git_push("main")
    if not okp:
        wip = f"wip/{c.get('id','run')}-{c.get('runId','')}"; okw, _ = git_push(wip)
        step("publish", "fail", note=why)
        die(f"推送 main 失敗：{why}\n半成品{'已推到 ' + wip if okw else '也無法推到 wip 分支'}。可以再跑一次 publish；仍失敗就在最後訊息加 ⚠️ 說明。")
    head = sh("git", "rev-parse", "HEAD").stdout.strip(); remote = sh("git", "ls-remote", "origin", "refs/heads/main", timeout=60).stdout.split()[:1]
    if remote and remote[0] != head: die(f"推送後遠端 main={remote[0][:8]}，本地 HEAD={head[:8]}，不一致")
    step("publish", "pass", commit=head[:10]); set_cur(phase="published", commit=head)
    ok(f"已推送 {head[:10]}")
    # 已處理的許願：在最新的 feedback.md 上整理（主人的修改不會被覆蓋）
    state = load(DATA / "state.json", {})
    for attempt in range(3):
        sh("git", "fetch", "--depth=20", "origin", "main", timeout=180); sh("git", "merge", "--ff-only", "-q", "origin/main")
        if not move_done_wishes(state): break
        sh("git", "add", "feedback.md"); sh("git", "commit", "-q", "-m", "feedback.md：已處理的許願移到「已處理」", "-m", "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        if sh("git", "-c", "push.negotiate=true", "push", "origin", "HEAD:main", timeout=300).returncode == 0: break
        sh("git", "reset", "-q", "--hard", "HEAD~1")
    else: warn("feedback.md 整理三次都撞到主人同時修改，下次執行再整理")
    set_cur(commit=sh("git", "rev-parse", "HEAD").stdout.strip())
    url = f"{SITE}{c.get('slug','')}/"
    print(f"網站會在 1–3 分鐘內更新：{url}")
    print("下一步：等約 90 秒後用 WebFetch 打開上面網址確認（網址加 ?v=<runId> 避開快取）；然後寫最後訊息。")

def cmd_abort(a):
    c = cur(); record_run("failed", a.reason)
    slug = c.get("slug"); wip_msg = ""
    if slug and (ROOT / slug).exists():
        wip = f"wip/{c.get('id')}-{c.get('runId')}"
        sh("git", "stash", "push", "-u", "-q", "--", slug)
        tmpb = f"_wip_{c.get('runId')}"; sh("git", "checkout", "-q", "-b", tmpb)
        sh("git", "stash", "pop", "-q"); sh("git", "add", "-A", "--", slug)
        sh("git", "commit", "-q", "-m", f"WIP {slug}（未完成：{a.reason[:60]}）")
        okw, _ = git_push(wip); wip_msg = f"半成品{'已推到 ' + wip if okw else '推送失敗'}"
        sh("git", "checkout", "-q", "main"); sh("git", "branch", "-D", tmpb)
    sh("git", "add", "data/runs.json"); sh("git", "commit", "-q", "-m", f"執行紀錄：失敗（{a.reason[:60]}）", "-m", "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    okm, why = git_push("main")
    set_cur(phase="aborted", reason=a.reason)
    print(f"已記錄失敗。{wip_msg}。main {'已更新執行紀錄' if okm else '推送失敗：' + why}")

def gate_status() -> tuple[bool, str]:
    c = cur()
    if not c or c.get("phase") in ("skipped",): return True, "沒有進行中的 run"
    phase = c.get("phase")
    if phase == "aborted": return True, "本次 run 已記錄為失敗"
    if phase != "published":
        nxt = {"planned": "發掘候選 → `oss.py new <slug>`", "building": "完成頁面與 Demo → `oss.py check` → `oss.py qa` → 審查 → `oss.py register` → `oss.py build` → `oss.py finish` → `oss.py publish`",
               "registered": "`oss.py build` → `oss.py finish` → `oss.py publish`", "finished": "`oss.py publish`"}.get(phase, "依 CLAUDE.md 繼續")
        return False, f"本集 {c.get('id')} 還沒完成（目前階段：{phase}）。下一步：{nxt}。真的做不下去就 `oss.py abort --reason \"原因\"`。"
    if sh("git", "status", "--porcelain").stdout.strip().replace(".run", "").strip():
        st = [l for l in sh("git", "status", "--porcelain").stdout.splitlines() if ".run" not in l]
        if st: return False, f"已發布，但還有未提交的變更：{st[:5]}。再跑一次 `oss.py publish --force`。"
    return True, "已發布"

def cmd_gate(a):
    passed, msg = gate_status()
    print(("PASS：" if passed else "FAIL：") + msg); sys.exit(0 if passed else 1)

def cmd_status(a):
    episodes, ideas, state, runs = data_files(); c = cur()
    last = episodes[-1] if episodes else None; lr = runs[-1] if runs else None
    print("【開源探索誌 狀態】")
    print(f"- 已出刊 {len(episodes)} 集；最新：{('#'+pad(last['no'])+' '+last['title']+'（'+last['date']+'）') if last else '無'}")
    print(f"- 上次執行：{(lr['endedAt'][:16]+' '+lr['status']+('：'+lr['note'] if lr.get('note') else '')) if lr else '無紀錄'}")
    print(f"- 開放中的許願：{sum(1 for w in state.get('wishes', []) if w['status']=='open')}；收藏點子：{sum(1 for i in ideas if i.get('starred'))}；候選池：{len(state.get('pool', []))}")
    if state.get("nextHint"): print(f"- 上次預告：{state['nextHint']}")
    if c and c.get("phase") not in ("published", "aborted", "skipped"):
        print(f"- ⚠️ 有未完成的 run：{c.get('id')} 階段 {c.get('phase')}（{c.get('updatedAt','')[:16]}）→ 先 `python3 ops/bin/oss.py gate` 看下一步")
    print("- 出刊流程：讀 CLAUDE.md，使用 oss-episode skill。第一步 `python3 ops/bin/oss.py preflight`。")

def cmd_lesson(a):
    p = OPS / "LESSONS.md"; t = p.read_text("utf-8") if p.exists() else "# 經驗累積\n"
    line = f"- {today()}：{a.text.strip()}"
    if a.text.strip()[:30] in t: print("類似的經驗已經記過了"); return
    p.write_text(t.rstrip() + "\n" + line + "\n", "utf-8"); ok("已追加到 ops/LESSONS.md")


def main():
    ap = argparse.ArgumentParser(prog="oss.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("preflight").set_defaults(f=cmd_preflight)
    sp.add_parser("status").set_defaults(f=cmd_status)
    p = sp.add_parser("plan"); p.add_argument("--force", action="store_true"); p.set_defaults(f=cmd_plan)
    p = sp.add_parser("new"); p.add_argument("slug"); p.add_argument("--force", action="store_true"); p.set_defaults(f=cmd_new)
    for name, fn in (("check", cmd_check), ("qa", cmd_qa), ("register", cmd_register)):
        p = sp.add_parser(name); p.add_argument("ep", nargs="?"); p.set_defaults(f=fn)
    sp.add_parser("build").set_defaults(f=cmd_build)
    p = sp.add_parser("finish"); p.add_argument("--note"); p.add_argument("--review"); p.add_argument("--force", action="store_true"); p.set_defaults(f=cmd_finish)
    p = sp.add_parser("publish"); p.add_argument("--force", action="store_true"); p.set_defaults(f=cmd_publish)
    p = sp.add_parser("abort"); p.add_argument("--reason", required=True); p.set_defaults(f=cmd_abort)
    sp.add_parser("gate").set_defaults(f=cmd_gate)
    p = sp.add_parser("lesson"); p.add_argument("text"); p.set_defaults(f=cmd_lesson)
    a = ap.parse_args(); os.chdir(ROOT); a.f(a)

if __name__ == "__main__":
    main()
