"""互動測試：`python3 ops/bin/oss.py qa` 會用 Playwright 打開本集頁面後呼叫 check(page)。

- page 是 Playwright 的 sync Page，已載入本集 index.html。
- 用 assert 檢查 Demo 真的能動；失敗時 assert 訊息要說清楚哪裡壞了。
- 回傳字串清單當作測試紀錄。
"""


def check(page):
    log = []
    # 範例：確認 Demo 區有東西
    assert page.locator("[data-section=demo]").count() == 1, "找不到 Demo 區塊"
    # TODO(本集)：操作 Demo（點按鈕、輸入文字），斷言結果正確
    log.append("Demo 區塊存在")
    return log
