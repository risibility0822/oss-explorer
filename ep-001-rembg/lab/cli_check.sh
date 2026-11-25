#!/usr/bin/env bash
# 驗證「五分鐘上手」的命令列寫法真的能跑（2026-11-25 補做）
set -euo pipefail
python3 -m venv v && ./v/bin/pip install -q "rembg[cpu,cli]==2.0.87"
export U2NET_HOME="$PWD/models"
time ./v/bin/rembg i -m u2netp ../img/coffee.jpg out.png
./v/bin/python -I -c "from PIL import Image;im=Image.open('out.png');a=list(im.getchannel('A').getdata());print(im.mode,im.size,'透明',round(sum(v<16 for v in a)/len(a),3),'不透明',round(sum(v>240 for v in a)/len(a),3))"
