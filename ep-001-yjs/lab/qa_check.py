"""第 001 集互動測試：播放「離線衝突劇本」，確認三台最後完全一致、沒有遺失任何修改。"""


def check(page):
    log = []
    assert page.evaluate("typeof window.Y") == "object", "Yjs 函式庫沒有載入"
    assert page.text_content("#badge").startswith("三台內容一致"), "初始狀態三台就不一致"
    page.select_option("#lat", "80")
    page.click("#play")
    page.wait_for_function("document.getElementById('narr').textContent.startsWith('⑤')", timeout=20000)
    texts = [page.input_value(f"#ta{k}") for k in "ABC"]
    assert texts[0] == texts[1] == texts[2], f"劇本結束後三台文字不同：{texts}"
    for frag in ["Amy：客戶說改下週一", "Ben：會議室訂好了", "Jack：記得錄影"]:
        assert frag in texts[0], f"合併後少了「{frag}」"
    todos = page.locator("#tdA li span").all_text_contents()
    assert "準備 demo 機" in todos and "寫週報" not in todos, f"待辦合併結果不對：{todos}"
    log.append("離線衝突劇本：三台一致，三人的修改都保留")
    # 手動輸入：A 打字後 B 會收到
    page.fill("#taA", page.input_value("#taA") + "!")
    page.dispatch_event("#taA", "input")
    page.wait_for_function("document.getElementById('taB').value.endsWith('!')", timeout=5000)
    log.append("A 輸入後 B 即時同步")
    return log
