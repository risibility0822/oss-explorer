"""互動測試：`oss.py qa` / `oss.py live` 會呼叫 check(page)。真的操作 Demo 並檢查結果。"""


def _count(page):
    return int(page.locator("#demoCount").get_attribute("data-n"))


def check(page):
    log = []
    page.wait_for_function("document.documentElement.dataset.ruff", timeout=60000)
    log.append("Ruff wasm 載入：" + page.evaluate("document.documentElement.dataset.ruff"))
    page.wait_for_selector("#demoCount")
    n0 = _count(page)
    assert n0 == 16, f"FastAPI 範例（多開 7 組）應找到 16 個問題（跟命令列一致），實際 {n0}"
    assert page.locator("#demoView .demo-ln.has").count() > 5, "作業紙上沒有標出有問題的行"
    log.append(f"FastAPI 範例：{n0} 個問題")
    # 點清單第一項：會跳到那一行並加框
    page.locator("#demoList button").first.click()
    assert page.locator("#demoView .demo-ln.flash").count() == 1, "點問題清單沒有標出那一行"
    # 一鍵修好：剩 2 個（E722、B904），跟 ruff check --fix --unsafe-fixes 一致
    page.click("#demoFix")
    n1 = _count(page)
    assert n1 == 2, f"一鍵修好後應剩 2 個問題，實際 {n1}"
    assert page.locator("#demoView .demo-ln.fixed").count() > 3, "修好的行沒有螢光標記"
    v = page.input_value("#demoSrc")
    assert "status is None" in v and "import os" not in v, "修正內容不對"
    log.append(f"一鍵修好後剩 {n1} 個；改過的行有標記")
    # 規則切到預設：問題變少
    page.click("[data-rules=basic]")
    page.click("[data-sample='1']")
    nb = _count(page)
    page.click("[data-rules=more]")
    nm = _count(page)
    assert nm == 8 and nb < nm, f"資料整理範例：預設 {nb} 個、多開 7 組應 8 個（實際 {nm}）"
    log.append(f"資料整理範例：預設規則 {nb} 個、多開 7 組 {nm} 個")
    # 排整齊
    page.click("[data-sample='2']")
    page.click("#demoFmt")
    v = page.input_value("#demoSrc")
    assert "def price_with_tax(price, rate=0.05):" in v and "items = [120, 350, 980]" in v, "排版結果不對：\n" + v
    log.append("排整齊：結果符合 ruff format")
    # 自己輸入：寫一行有問題的程式
    page.fill("#demoSrc", "import os\nx == None\n")
    page.wait_for_timeout(400)
    assert _count(page) >= 2, "輸入自己的程式後沒有重新檢查"
    ms = float(page.locator("#demoMs").inner_text())
    assert ms < 50, f"檢查兩行花了 {ms} 毫秒，太慢"
    log.append(f"自己輸入兩行：{_count(page)} 個問題、{ms} 毫秒")
    # 還原
    page.click("#demoReset")
    assert "x == None" not in page.input_value("#demoSrc"), "還原範例沒作用"
    return log
