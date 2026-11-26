# 合成測試資料：模擬 agent 呼叫「查詢 log」工具拿回來的 JSON（固定亂數種子）
import json, random, sys
random.seed(20261126)
N=int(sys.argv[1]) if len(sys.argv)>1 else 300
svcs=["api-gateway","auth","orders","payments","inventory"]
msgs={"api-gateway":"request completed","auth":"token validated","orders":"order fetched","payments":"charge authorized","inventory":"stock checked"}
rows=[]
for i in range(N):
    s=random.choice(svcs)
    rows.append({"ts":f"2026-11-25T03:{i//60%60:02d}:{i%60:02d}Z","level":"INFO","service":s,"request_id":f"req-{10000+i}","latency_ms":random.randint(8,90),"message":msgs[s]})
k=int(N*0.62)
rows[k]={"ts":rows[k]["ts"],"level":"ERROR","service":"payments","request_id":rows[k]["request_id"],"latency_ms":30012,"message":"upstream timeout: card-processor did not respond in 30s (pool exhausted, 64/64 connections busy)"}
json.dump(rows,sys.stdout,ensure_ascii=False)
