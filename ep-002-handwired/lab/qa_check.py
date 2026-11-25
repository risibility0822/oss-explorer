"""第 002 集互動測試：FizzBuzz 網路真的在瀏覽器跑、答案正確、雜訊會讓它答錯、答案板可以點。"""


def _state(page):
    return page.evaluate("""() => ({
      word: document.getElementById('word').textContent,
      label: document.getElementById('word').dataset.l,
      verdict: document.getElementById('verdict').textContent,
      n: document.getElementById('n').value,
      lit3: document.querySelectorAll('#led3 i.on').length,
      lit5: document.querySelectorAll('#led5 i.on').length,
      score: Number(document.getElementById('score').firstChild.textContent),
      wrong: document.querySelectorAll('#grid button.wrong').length,
    })""")


def check(page):
    log = []
    page.wait_for_function("window.HW && document.querySelectorAll('#grid button').length===100", timeout=20000)
    s = _state(page)
    assert s["word"] == "FizzBuzz" and s["lit3"] == 5 and s["lit5"] == 3, f"初始 15 應是 FizzBuzz、亮 5+3 顆：{s}"
    assert s["score"] == 100 and s["wrong"] == 0, f"原廠權重應 100 題全對：{s}"
    assert page.evaluate("HW.stats.operations") == 1416, "運算數應為 1416（與 lab 一致）"
    log.append("初始 15 → FizzBuzz，原廠權重 100/100")
    # 輸入框
    page.fill("#n", "999")
    page.press("#n", "Enter")
    s = _state(page)
    assert s["word"] == "Fizz" and s["lit3"] == 333 and s["lit5"] == 199, f"999 應是 Fizz、亮 333+199 顆：{s}"
    log.append("輸入 999 → Fizz，LED 333/199")
    # ± 按鈕
    page.click("#plus")
    s = _state(page)
    assert s["n"] == "1000" and s["word"] == "Buzz", f"+1 後應是 1000 Buzz：{s}"
    page.click("#minus"); page.click("#minus")
    s = _state(page)
    assert s["n"] == "998" and s["word"] == "998" and s["label"] == "number", f"998 應顯示數字：{s}"
    log.append("± 按鈕正常（1000 Buzz、998）")
    # 滑桿
    page.fill("#nRange", "45")
    page.dispatch_event("#nRange", "input")
    assert _state(page)["word"] == "FizzBuzz", "滑桿到 45 應是 FizzBuzz"
    log.append("滑桿正常（45 FizzBuzz）")
    # 點答案板
    page.click("#grid button[data-n='10']")
    s = _state(page)
    assert s["n"] == "10" and s["word"] == "Buzz", f"點 10 應變成 Buzz：{s}"
    log.append("點答案板正常")
    # 1% 雜訊：應該答錯不少題，與 lab（種子 1 → 61 題）一致
    page.click(".demo-sig button[data-s='0.01']")
    s = _state(page)
    assert s["score"] == 61 and s["wrong"] == 39, f"1% 雜訊種子 1 應答對 61 題（lab/out/noise.json）：{s}"
    assert not page.is_disabled("#reseed"), "有雜訊時應可重抽"
    page.click("#reseed")
    s2 = _state(page)
    assert s2["score"] == 46, f"重抽（種子 2）應答對 46 題（lab）：{s2}"
    log.append(f"雜訊 1%：61 → 重抽 46 題，跟 lab 一致")
    # 回到原廠
    page.click(".demo-sig button[data-s='0']")
    s = _state(page)
    assert s["score"] == 100 and page.is_disabled("#reseed"), f"回原廠應 100 題且不能重抽：{s}"
    log.append("回原廠權重 100/100")
    # 機制圖：跟著 Demo 的數字更新（用網路實際算出的中間值），步驟按鈕可用
    page.fill("#n", "9"); page.press("#n", "Enter"); page.wait_for_timeout(200)
    t = page.evaluate("({n:document.getElementById('mN').textContent, q3:document.getElementById('mQ3').textContent, z5:document.getElementById('mZ5').textContent, ans:document.getElementById('mAns').textContent, out:document.getElementById('mOut').textContent})")
    assert t["n"] == "你輸入 9" and t["q3"] == "有 3 個 3" and t["z5"] == "不整除（0）" and t["ans"] == "答案：Fizz" and t["out"] == "輸出 Fizz", f"機制圖沒跟 Demo 同步：{t}"
    assert page.text_content("#mPos").strip() == "1 / 6", "機制圖應從第 1 步（兩格）開始"
    page.evaluate("window.__mech.go(6)")
    for _ in range(5): page.click("#mPrev")
    assert page.text_content("#mPos").strip() == "1 / 6" and page.is_disabled("#mPrev"), "上一步按到底應停在 1 / 6"
    s1 = page.evaluate("({off:document.querySelectorAll('#mechSvg .st.off').length, box:!document.querySelector('#mechSvg .only1').classList.contains('hide')})")
    assert s1["off"] == 5 and s1["box"], f"第 1 步應只有輸入、黑盒子與答案：{s1}"
    page.click("#mNext")
    assert page.text_content("#mPos").strip() == "2 / 6" and page.evaluate("document.querySelector('#mechSvg .only1').classList.contains('hide')"), "第 2 步應打開黑盒子"
    page.evaluate("window.__mech.go(6)")
    log.append("機制圖跟 Demo 同步（9 → Fizz）、步驟按鈕正常")
    # 加雜訊時，機制圖必須顯示網路的實際值，跟輸出一致（內容審查抓到的矛盾）
    page.fill("#n", "15"); page.press("#n", "Enter")
    page.click(".demo-sig button[data-s='0.01']"); page.click("#reseed"); page.wait_for_timeout(200)
    m = page.evaluate("({a:document.getElementById('mA').textContent, fb:window.HW.run(15).vals[3], label:window.HW.run(15).label, lit:[...document.querySelectorAll('#mOuts rect.on')].length, word:document.getElementById('word').textContent})")
    assert m["a"].endswith(f"{m['fb']:.2f}"), f"「兩邊都整除？」應顯示網路的 fizzbuzz 值：{m}"
    assert m["lit"] == 1, f"四顆輸出燈應只亮一顆：{m}"
    log.append(f"雜訊下機制圖與網路一致（{m['a']} → {m['word']}）")
    page.click(".demo-sig button[data-s='0']")
    return log
