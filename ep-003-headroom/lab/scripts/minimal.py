"""頁面「五分鐘上手」的程式碼，原樣實跑過。用法：python -I minimal.py <工具輸出檔>"""
import os, sys
os.environ["HEADROOM_OFFLINE"] = "1"          # 不連網、也關掉預設開啟的匿名統計
from headroom import compress

tool_output = open(sys.argv[1]).read()        # 工具吐回來的 JSON（這裡用 300 筆 log）
messages = [
    {"role": "user", "content": "哪個服務出錯？"},
    {"role": "assistant", "content": None, "tool_calls": [
        {"id": "c1", "type": "function", "function": {"name": "query_logs", "arguments": "{}"}}]},
    {"role": "tool", "tool_call_id": "c1", "content": tool_output},
]
result = compress(messages, model="gpt-4o")
print(result.tokens_before, "→", result.tokens_after, result.transforms_applied)
print(result.messages[-1]["content"][:160])
# 接著把 result.messages 照常送給任何相容 OpenAI 格式的模型（本集用 llama.cpp 跑 Qwen2.5-1.5B）
