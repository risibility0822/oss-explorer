"""第 001 集互動測試：Demo 真的能去背、能換背景、能切換範例、能對照、能上傳自己的照片、能下載 PNG。"""
from pathlib import Path

IMG = Path(__file__).resolve().parent.parent / "img"


def _alpha_stats(page):
    return page.evaluate("""() => {
      const c=document.getElementById('outCanvas'), g=c.getContext('2d'), d=g.getImageData(0,0,c.width,c.height).data;
      let clear=0, solid=0; for(let i=3;i<d.length;i+=4){ if(d[i]<16) clear++; else if(d[i]>240) solid++; }
      const n=d.length/4; return {w:c.width,h:c.height,clear:clear/n,solid:solid/n,
        corner:d[3], center:d[((Math.floor(c.height/2)*c.width+Math.floor(c.width/2))*4)+3]};
    }""")


def check(page):
    log = []
    page.wait_for_function("document.getElementById('sInfer').textContent.includes('秒')", timeout=60000)
    s = _alpha_stats(page)
    assert (s["w"], s["h"]) == (600, 400), f"咖啡杯輸出尺寸不對：{s}"
    assert s["clear"] > 0.3 and s["solid"] > 0.3, f"去背結果不像去背（透明 {s['clear']:.0%}、不透明 {s['solid']:.0%}）"
    assert s["corner"] < 16 and s["center"] > 240, f"角落應透明、中央（杯子）應不透明：{s}"
    log.append(f"咖啡杯去背：透明 {s['clear']:.0%}、不透明 {s['solid']:.0%}，推論 {page.text_content('#sInfer')}")
    # 機制圖：從第 1 步開始，小圖是 Demo 的真實中間結果
    assert page.text_content("#mPos").strip() == "1 / 5", "機制圖應從第 1 步開始"
    st = page.evaluate("""() => ({off:[...document.querySelectorAll('#mechSvg .st.off')].length,
        q:getComputedStyle(document.querySelector('#mechSvg .only1')).opacity,
        href:['mIn','mSmall','mProb','mMask','mOut'].map(i=>(document.getElementById(i).getAttribute('href')||'').slice(0,22)),
        ms:document.getElementById('mMs').textContent})""")
    assert st["off"] == 4 and st["q"] == "1", f"第 1 步應只有照片、黑盒子、結果：{st}"
    assert all(h.startswith("data:image/png") for h in st["href"]), f"機制圖小圖沒有接上 Demo：{st['href']}"
    assert "秒" in st["ms"], f"機制圖數字沒有更新：{st}"
    page.click("#mNext"); page.click("#mNext"); page.wait_for_timeout(450)
    assert page.text_content("#mPos").strip() == "3 / 5"
    assert page.evaluate("getComputedStyle(document.querySelector('#mechSvg .only1')).opacity") == "0", "第 2 步之後黑盒子的？要消失"
    page.evaluate("window.__mech.go(5)")
    assert page.evaluate("document.querySelectorAll('#mechSvg .st.off').length") == 0
    log.append(f"機制圖：1/5 起始、小圖接上 Demo（{st['ms']}）、步驟按鈕正常")
    # 切換到貓
    page.click("[data-sample=cat]")
    page.wait_for_function("document.getElementById('sSize').textContent==='451×300'", timeout=30000)
    s2 = _alpha_stats(page)
    assert s2["solid"] > 0.3, f"貓的去背結果異常：{s2}"
    log.append("切換範例（貓）正常")
    # 換背景：白底 → 背景畫布應該是白色
    page.click("[data-bg='#ffffff']")
    px = page.evaluate("Array.from(document.getElementById('bgCanvas').getContext('2d').getImageData(2,2,1,1).data)")
    assert px[:3] == [255, 255, 255], f"白底沒有套用：{px}"
    log.append("換白底正常")
    # 對照滑桿
    page.fill("#split", "75")
    page.dispatch_event("#split", "input")
    assert page.evaluate("getComputedStyle(document.getElementById('stage')).getPropertyValue('--split').trim()") == "75%", "對照滑桿沒有作用"
    log.append("對照滑桿正常")
    # 直接在圖上拖（看起來能拖的把手就要能拖）
    box = page.locator("#stage").bounding_box()
    y = box["y"] + box["height"] / 2
    page.mouse.move(box["x"] + box["width"] * 0.5, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * 0.2, y, steps=5)
    page.mouse.up()
    v = float(page.evaluate("getComputedStyle(document.getElementById('stage')).getPropertyValue('--split')").strip().rstrip("%"))
    assert 15 <= v <= 25, f"在圖上拖動後對照位置應約 20%，實際 {v}%"
    assert page.input_value("#split") == str(int(v)), "拖動後下方滑桿沒有同步"
    log.append(f"在圖上直接拖動正常（{v:.0f}%）")
    # 上傳自己的照片（用火箭照片模擬）
    page.set_input_files("#file", str(IMG / "rocket.jpg"))
    page.wait_for_function("document.getElementById('sSize').textContent==='640×427'", timeout=30000)
    s3 = _alpha_stats(page)
    assert s3["clear"] > 0.5, f"上傳照片的去背結果異常：{s3}"
    log.append(f"上傳照片去背正常（透明 {s3['clear']:.0%}）")
    # 下載 PNG
    assert not page.is_disabled("#download"), "下載按鈕沒有啟用"
    with page.expect_download(timeout=15000) as d:
        page.click("#download")
    head = Path(d.value.path()).read_bytes()[:8]
    assert head == b"\x89PNG\r\n\x1a\n", f"下載的不是 PNG：{head!r}"
    log.append(f"下載 PNG 正常（{d.value.suggested_filename}）")
    return log
