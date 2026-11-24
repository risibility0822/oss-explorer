#!/usr/bin/env python3
"""Stop hook：本集還沒真正發布（或記錄失敗）前，不讓 session 結束。

- 沒有進行中的 run → 放行（一般對話不受影響）
- 有 run 但沒完成 → 擋下，告訴 Claude 下一步是什麼
- 最多擋 4 次，避免無限迴圈；第 5 次放行並留紀錄（之後由 runs.json / 推播看得到）
"""
import json, os, subprocess, sys
from pathlib import Path

root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
run_dir = root / ".run"
try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}
if not (run_dir / "current.json").exists():
    sys.exit(0)
counter = run_dir / "stop_blocks"
n = int(counter.read_text() or 0) if counter.exists() else 0
r = subprocess.run([sys.executable, str(root / "ops/bin/oss.py"), "gate"], cwd=root, capture_output=True, text=True, timeout=100)
msg = (r.stdout or r.stderr).strip()
if r.returncode == 0:
    counter.unlink(missing_ok=True)
    sys.exit(0)
if n >= 4:
    (run_dir / "stop_gate_gave_up").write_text(msg, "utf-8")
    sys.exit(0)
counter.write_text(str(n + 1))
print(json.dumps({"decision": "block",
                  "reason": f"[完成閘門 {n+1}/4] {msg} 完成後在最後訊息照 CLAUDE.md 的格式回報。"}, ensure_ascii=False))
sys.exit(0)
