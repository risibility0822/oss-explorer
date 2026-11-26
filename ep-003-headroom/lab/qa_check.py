"""第 003 集互動測試：Demo 讀得到實測資料、切換情境／原樣與壓縮後／問題都會更新畫面，數字跟 lab 一致。"""


def _s(page):
    return page.evaluate("""() => ({
      nr: document.getElementById('demoNR').textContent,
      nc: document.getElementById('demoNC').textContent,
      saved: document.getElementById('demoSaved').textContent,
      text: document.getElementById('demoText').textContent.slice(0, 200),
      hit: (document.querySelector('#demoText .demo-hit')||{}).textContent || '',
      qs: document.querySelectorAll('#demoQs button').length,
      lineR: document.getElementById('demoLineR').textContent,
      lineC: document.getElementById('demoLineC').textContent,
      ansHidden: document.getElementById('demoAns').hidden,
      overR: document.getElementById('demoColR').classList.contains('over'),
      overC: document.getElementById('demoColC').classList.contains('over'),
    })""")


def check(page):
    log = []
    page.wait_for_function("window.__demoData && document.getElementById('demoText').textContent.startsWith('[300]')", timeout=20000)
    d = page.evaluate("window.__demoData")
    t = d["tokens"]["logs300"]
    s = _s(page)
    assert s["nr"].replace(",", "") == str(t["qwen_raw"]) and s["nc"].replace(",", "") == str(t["qwen_compressed"]), f"300 筆 token 數跟資料不一致：{s}"
    assert "ERROR" in s["hit"], f"預設問題（出錯）應框出 ERROR 那一行：{s['hit']!r}"
    assert "答對" in s["lineR"] and "答對" in s["lineC"], f"300 筆出錯題兩邊都應答對：{s}"
    log.append(f"300 筆：{s['nr']} → {s['nc']} token，{s['saved']}；出錯題兩邊答對")
    # 原樣 tab
    page.click(".demo-tabs button[data-v=raw]")
    page.wait_for_function("document.getElementById('demoText').textContent.startsWith('{')")
    assert '"level":"ERROR"' in _s(page)["hit"], "原樣檢視應框出 ERROR 那筆 JSON"
    log.append("原樣（JSON）檢視正常，框出 ERROR")
    # 換問題：查 req-10042
    page.click("#demoQs button[data-q=lookup42]")
    page.wait_for_function("(document.querySelector('#demoText .demo-hit')||{}).textContent?.includes('req-10042')")
    page.wait_for_function("/答/.test(document.getElementById('demoLineC').textContent) && /答/.test(document.getElementById('demoLineR').textContent)", timeout=60000)
    run = next(r for r in d["runs"] if r["scenario"] == "logs300" and r["qid"] == "lookup42")
    s = _s(page)
    for k, v in (("lineR", run["raw"]), ("lineC", run["compressed"])):
        assert ("答對" if v["correct"] else "答錯") in s[k], f"{k} 對錯標示跟資料不一致：{s[k]} vs {v['correct']}"
    log.append(f"查 req-10042：原樣 {'對' if run['raw']['correct'] else '錯'}、壓縮後 {'對' if run['compressed']['correct'] else '錯'}（與 lab 一致）")
    # 2,000 筆：破頂、沒有問題可問
    page.click("#demoScen button[data-s=logs2000]")
    page.wait_for_function("document.getElementById('demoText').textContent.length > 1000")
    s = _s(page)
    assert s["overR"] and s["overC"] and s["ansHidden"], f"2,000 筆兩根柱子都應破頂、不能問：{s}"
    log.append("2,000 筆：兩邊都破 32,768 天花板，問答區隱藏")
    # 建置 log：0%
    page.click("#demoScen button[data-s=cmake]")
    page.wait_for_function("document.getElementById('demoSaved').textContent.includes('0%')")
    s = _s(page)
    assert s["nr"] == s["nc"], f"建置 log 應原封不動：{s}"
    log.append("建置 log：Headroom 沒壓（0%）")
    # 100 筆＋重播
    page.click("#demoScen button[data-s=logs100]")
    page.wait_for_function("document.querySelectorAll('#demoQs button').length === 4")
    page.click("#demoPlay")
    page.wait_for_function("/答/.test(document.getElementById('demoLineR').textContent)", timeout=30000)
    log.append("100 筆：4 個問題、重播按鈕正常")
    # 機制圖
    assert page.text_content("#mPos").strip() == "1 / 4", "機制圖應從第 1 步開始"
    page.click("#mNext"); page.click("#mNext"); page.click("#mNext")
    assert page.text_content("#mPos").strip() == "4 / 4", "機制圖應能走到第 4 步"
    log.append("機制圖 1→4 步正常")
    return log
