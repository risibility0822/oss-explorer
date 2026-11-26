"""把 experiment.py 的 results.json 與 tokens_and_speed.py 的 tokens.jsonl 合成頁面 Demo 用的 data/results.json（只搬運，不改數字）。
用法：python3 build_demo_data.py <results.json> <tokens.jsonl> <scenarios.json> <輸出檔>"""
import json, re, sys
res = json.load(open(sys.argv[1])); scen = json.load(open(sys.argv[3]))
qid = {(s["id"], q["q"]): q["id"] for s in scen for q in s["questions"]}
tokens = {}
for line in open(sys.argv[2]):
    r = json.loads(line); n = r["file"].rsplit(".", 1)[0].replace("cmake_fail", "cmake")
    r["compressed_chars"] = None; tokens[n] = r
runs = []
for r in res["runs"]:
    m = re.search(r"req-\d+", r["question"])
    runs.append({"scenario": r["scenario"], "qid": qid[(r["scenario"], r["question"])], "question": r["question"],
                 "expect": r["expect"], "target": m.group(0) if m else "ERROR",
                 "raw": r["raw"], "compressed": r["compressed"]})
for n, t in tokens.items():
    t["compressed_chars"] = len(open(f"{sys.argv[4].rsplit('/',1)[0]}/{n}.compressed.txt").read())
out = {k: res[k] for k in ("headroom", "llama.cpp", "model", "threads", "date")}
out.update({"ceiling": 32768, "tokens": tokens, "runs": runs})
json.dump(out, open(sys.argv[4], "w"), ensure_ascii=False, indent=1)
print("runs", len(runs), "tokens", list(tokens))
