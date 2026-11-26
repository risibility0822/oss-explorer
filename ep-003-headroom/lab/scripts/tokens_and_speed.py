"""只算 token 與壓縮耗時（不跑模型）：原文與 Headroom 壓縮後，用 Qwen2.5 的分詞器（llama-tokenize）數 token。
用法：SAVE_DIR=<資料夾> python -I tokens_and_speed.py <檔案…>，會把原文與壓縮後存成 <名稱>.raw.txt／.compressed.txt"""
import json, os, subprocess, sys, time, statistics
os.environ["HEADROOM_OFFLINE"] = "1"
from headroom import compress
W="/home/claude/work/ep-003"; BIN=f"{W}/src/llama.cpp/build/bin"; MODEL=f"{W}/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
def ntok(text):
    p="/tmp/_tok.txt"; open(p,"w").write(text)
    o=subprocess.run([f"{BIN}/llama-tokenize","-m",MODEL,"-f",p,"--ids","--log-disable"],capture_output=True,text=True).stdout
    return len(json.loads(o.strip().splitlines()[-1]))
def msgs(c): return [{"role":"user","content":"Analyse the tool output and answer."},{"role":"assistant","content":None,"tool_calls":[{"id":"c1","type":"function","function":{"name":"query_logs","arguments":"{}"}}]},{"role":"tool","tool_call_id":"c1","content":c}]
SAVE=os.environ.get("SAVE_DIR")
out=[]
for f in sys.argv[1:]:
    raw=open(f).read()
    times=[]
    for i in range(6):
        t=time.perf_counter(); r=compress(msgs(raw),model="gpt-4o"); times.append((time.perf_counter()-t)*1000)
    c=r.messages[-1]["content"]
    row={"file":os.path.basename(f),"raw_chars":len(raw),"qwen_raw":ntok(raw),"qwen_compressed":ntok(c),
         "headroom_est_before":r.tokens_before,"headroom_est_after":r.tokens_after,"transforms":r.transforms_applied,
         "compress_ms_first":round(times[0],1),"compress_ms_median_next5":round(statistics.median(times[1:]),1)}
    if SAVE:
        n=os.path.basename(f).rsplit(".",1)[0].replace("cmake_fail","cmake")
        open(f"{SAVE}/{n}.raw.txt","w").write(raw); open(f"{SAVE}/{n}.compressed.txt","w").write(c)
    print(json.dumps(row,ensure_ascii=False)); out.append(row)
