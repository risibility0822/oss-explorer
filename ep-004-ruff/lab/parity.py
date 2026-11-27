"""比對：頁面 Demo（瀏覽器同一份 wasm＋本集自己寫的「套用修正」程式）vs Ruff 命令列。
用法：python3 parity.py   （需要 node、ruff 0.17.6 在 PATH）→ 寫 parity.json"""
import json, os, shutil, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
SELECT = "E,F,W,I,UP,B,SIM,C4,FAST"
files = [os.path.join(HERE, "samples", f) for f in ("fastapi_app.py", "clean_data.py", "messy_format.py")]
web = json.loads(subprocess.run(["node", os.path.join(HERE, "parity_node.cjs"), SELECT, *files], capture_output=True, text=True, check=True).stdout)
res = {"select": SELECT, "wasmVersion": web["version"], "cli": subprocess.run(["ruff", "--version"], capture_output=True, text=True).stdout.strip(), "files": {}}
for f in files:
    name = os.path.basename(f); w = web["files"][name]
    d = tempfile.mkdtemp(); p = os.path.join(d, name); shutil.copy(f, p)
    diag = subprocess.run(["ruff", "check", "--isolated", "--no-cache", "--select", SELECT, "--output-format", "json", p], capture_output=True, text=True)
    cli_codes = [x["code"] for x in json.loads(diag.stdout)]
    subprocess.run(["ruff", "check", "--isolated", "--no-cache", "--select", SELECT, "--fix", "--unsafe-fixes", "--quiet", p], capture_output=True, text=True)
    cli_fixed = open(p, encoding="utf-8").read()
    rem = subprocess.run(["ruff", "check", "--isolated", "--no-cache", "--select", SELECT, "--output-format", "json", p], capture_output=True, text=True)
    shutil.copy(f, p); subprocess.run(["ruff", "format", "--isolated", "--no-cache", "--quiet", p])
    cli_fmt = open(p, encoding="utf-8").read()
    res["files"][name] = {
        "diagnosticsSame": sorted(cli_codes) == sorted(w["diagnostics"]), "cliDiagnostics": sorted(cli_codes), "webDiagnostics": sorted(w["diagnostics"]),
        "fixSame": cli_fixed == w["fixed"], "cliRemaining": sorted(x["code"] for x in json.loads(rem.stdout)), "webRemaining": sorted(w["remaining"]),
        "formatSame": cli_fmt == w["formatted"], "webCheckMsNode": round(w["checkMs"], 3),
        "cliFixed": cli_fixed, "webFixed": w["fixed"]}
    print(name, {k: v for k, v in res["files"][name].items() if k.endswith("Same") or k.endswith("Remaining")})
json.dump(res, open(os.path.join(HERE, "parity.json"), "w"), ensure_ascii=False, indent=1)
