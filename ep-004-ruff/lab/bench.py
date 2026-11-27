"""ep-004 Ruff 實測：同一份 Django 原始碼，Ruff vs flake8 / pylint / black。
用法：python3 bench.py <django repo 路徑> <輸出 json>
每個指令跑 3 次取中位數；Ruff 一律 --no-cache，black 用全新的快取目錄。"""
import json, os, shutil, statistics, subprocess, sys, tempfile, time, filecmp, platform

repo, out = sys.argv[1], sys.argv[2]
target = os.path.join(repo, "django")
sub = os.path.join(repo, "django", "db")   # pylint 太慢，只跑 django/db 這個子資料夾
REPS = 3

def run(cmd, env=None, cwd=None):
    t = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd)
    return time.perf_counter() - t, p

def bench(name, cmd_fn, reps=REPS):
    times, last = [], None
    for i in range(reps):
        cmd, env = cmd_fn(i)
        dt, p = run(cmd, env=env)
        times.append(dt); last = p
    lines = [l for l in last.stdout.splitlines() if l.strip()]
    print(f"{name}: {[round(t,3) for t in times]} exit={last.returncode} lines={len(lines)}", flush=True)
    return {"name": name, "cmd": " ".join(cmd), "times": times, "median": statistics.median(times),
            "exit": last.returncode, "outputLines": len(lines), "stdoutHead": last.stdout[:1500], "stderrTail": last.stderr[-800:]}

def count_files(d):
    return sum(1 for r, _, fs in os.walk(d) for f in fs if f.endswith(".py"))

def count_lines(d):
    n = 0
    for r, _, fs in os.walk(d):
        for f in fs:
            if f.endswith(".py"):
                with open(os.path.join(r, f), "rb") as fh: n += fh.read().count(b"\n")
    return n

def ver(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip().splitlines()[0]

res = {"date": time.strftime("%Y-%m-%d"), "machine": {"cpus": os.cpu_count(), "python": platform.python_version(), "platform": platform.platform()},
       "versions": {"ruff": ver(["ruff", "--version"]), "flake8": ver(["flake8", "--version"]), "black": ver(["black", "--version"]), "pylint": ver(["pylint", "--version"])},
       "target": {"path": "django/", "files": count_files(target), "lines": count_lines(target)},
       "subTarget": {"path": "django/db/", "files": count_files(sub), "lines": count_lines(sub)}, "lint": [], "lintSub": [], "format": []}

E = dict(os.environ)
# 1) lint 全部 django/：規則對齊 flake8 預設（E、F、W、C90 中 Ruff 有的 E/F/W）
res["lint"].append(bench("ruff check（E,F,W）", lambda i: (["ruff", "check", "--no-cache", "--isolated", "--select", "E,F,W", "--output-format", "concise", target], E)))
res["lint"].append(bench("flake8（預設規則）", lambda i: (["flake8", "--isolated", target], E)))
# 2) django/db：加上 pylint
res["lintSub"].append(bench("ruff check（E,F,W）", lambda i: (["ruff", "check", "--no-cache", "--isolated", "--select", "E,F,W", "--output-format", "concise", sub], E)))
res["lintSub"].append(bench("ruff check（ALL 全部規則）", lambda i: (["ruff", "check", "--no-cache", "--isolated", "--select", "ALL", "--output-format", "concise", sub], E)))
res["lintSub"].append(bench("flake8（預設規則）", lambda i: (["flake8", "--isolated", sub], E)))
res["lintSub"].append(bench("pylint（預設規則）", lambda i: (["pylint", "--rcfile=/dev/null", "--jobs=0", "--persistent=n", sub], E), reps=1))
# 3) 格式化：各自在全新副本上真的改寫檔案，再比較兩邊結果
tmp = tempfile.mkdtemp()
def fresh(tag, i):
    d = os.path.join(tmp, f"{tag}{i}")
    shutil.copytree(target, d)
    return d
def ruff_fmt(i):
    return (["ruff", "format", "--no-cache", "--isolated", "--quiet", fresh("ruff", i)], E)
def black_fmt(i):
    env = dict(E); env["BLACK_CACHE_DIR"] = tempfile.mkdtemp()
    return (["black", "--quiet", fresh("black", i)], env)
res["format"].append(bench("ruff format", ruff_fmt))
res["format"].append(bench("black", black_fmt))
# 比較最後一次兩邊格式化的結果
same = diff = changed = 0; diffs = []
a, b = os.path.join(tmp, f"ruff{REPS-1}"), os.path.join(tmp, f"black{REPS-1}")
for r, _, fs in os.walk(target):
    for f in fs:
        if not f.endswith(".py"): continue
        rel = os.path.relpath(os.path.join(r, f), target)
        orig = os.path.join(target, rel)
        if not filecmp.cmp(os.path.join(a, rel), orig, shallow=False) or not filecmp.cmp(os.path.join(b, rel), orig, shallow=False):
            changed += 1
        if filecmp.cmp(os.path.join(a, rel), os.path.join(b, rel), shallow=False): same += 1
        else: diff += 1; diffs.append(rel)
res["formatCompare"] = {"identical": same, "different": diff, "changedByEither": changed, "differentFiles": diffs[:40]}
# 保存一個差異範例
if diffs:
    p = subprocess.run(["diff", "-u", os.path.join(b, diffs[0]), os.path.join(a, diffs[0])], capture_output=True, text=True)
    res["formatCompare"]["sampleDiff"] = {"file": diffs[0], "diff": p.stdout[:3000]}
shutil.rmtree(tmp, ignore_errors=True)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
print(json.dumps(res["formatCompare"], ensure_ascii=False)[:600])
