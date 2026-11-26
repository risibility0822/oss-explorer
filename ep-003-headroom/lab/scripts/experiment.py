"""開源探索誌 ep-003 組合技實驗：Headroom 壓縮工具輸出 → llama.cpp 在 CPU 上跑 Qwen2.5-1.5B 回答。
每個情境跑兩次（原文／壓縮後），記錄：Qwen 分詞器算的 token 數、讀入提示的時間、回答、記憶體峰值。
用法：python experiment.py <輸出目錄>
"""
import json, os, re, subprocess, sys, time, resource
os.environ["HEADROOM_OFFLINE"] = "1"
import headroom
from headroom import compress

W = "/home/claude/work/ep-003"
BIN = f"{W}/src/llama.cpp/build/bin"
MODEL = f"{W}/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

def hr(content):
    msgs = [{"role": "user", "content": "Analyse the tool output and answer."},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "query_logs", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "c1", "content": content}]
    t = time.perf_counter(); r = compress(msgs, model="gpt-4o"); dt = time.perf_counter() - t
    return r.messages[-1]["content"], {"headroom_tokens_before": r.tokens_before, "headroom_tokens_after": r.tokens_after,
            "transforms": r.transforms_applied, "compress_ms": round(dt * 1000, 2)}

def prompt(tool_out, q):
    return ("<|im_start|>system\nYou are an SRE assistant. Answer only from the tool output.<|im_end|>\n"
            "<|im_start|>user\nTool output from query_logs:\n" + tool_out +
            f"\n\nQuestion: {q} Answer in one short line.<|im_end|>\n<|im_start|>assistant\n")

def ntok(path):
    p = subprocess.run([f"{BIN}/llama-tokenize", "-m", MODEL, "-f", path, "--ids", "--log-disable"], capture_output=True, text=True)
    return len(json.loads(p.stdout.strip().splitlines()[-1]))

def ask(tool_out, q, tag):
    pf = f"{OUT}/{tag}.prompt.txt"; open(pf, "w").write(prompt(tool_out, q))
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    t = time.perf_counter()
    p = subprocess.run([f"{BIN}/llama-completion", "-m", MODEL, "-f", pf, "-n", "60", "--temp", "0", "-t", "4",
                        "-c", "32768", "-no-cnv", "--no-display-prompt", "--no-warmup"], capture_output=True, text=True)
    wall = time.perf_counter() - t
    open(f"{OUT}/{tag}.log", "w").write(p.stderr)
    ans = p.stdout.strip()
    m = re.search(r"prompt eval time =\s*([\d.]+) ms /\s*(\d+) tokens", p.stderr)
    return {"answer": ans, "prompt_tokens": ntok(pf), "prompt_eval_s": round(float(m.group(1)) / 1000, 2) if m else None,
            "wall_s": round(wall, 2), "returncode": p.returncode}

SCEN = json.load(open(f"{W}/scripts/scenarios.json"))
res = {"headroom": "0.45.0", "llama.cpp": "v1.0.0 (b1b770d)", "model": "Qwen2.5-1.5B-Instruct Q4_K_M", "threads": 4,
       "date": time.strftime("%Y-%m-%d"), "runs": []}
for s in SCEN:
    raw = open(f"{W}/{s['file']}").read()
    comp, info = hr(raw)
    open(f"{OUT}/{s['id']}.compressed.txt", "w").write(comp)
    for q in s["questions"]:
        row = {"scenario": s["id"], "question": q["q"], "expect": q["expect"], **info,
               "raw_chars": len(raw), "compressed_chars": len(comp)}
        for ver, txt in (("raw", raw), ("compressed", comp)):
            r = ask(txt, q["q"], f"{s['id']}-{q['id']}-{ver}")
            a = re.sub(r"req-\d+", "", r["answer"].lower())  # 去掉題目裡的 request_id，避免數字誤判
            r["correct"] = all(re.search(r"\b" + re.escape(e.lower()) + r"\b", a) for e in q["expect"])
            row[ver] = r
            print(s["id"], q["id"], ver, r, flush=True)
        res["runs"].append(row)
        json.dump(res, open(f"{OUT}/results.json", "w"), ensure_ascii=False, indent=1)
