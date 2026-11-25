# 來源與用法

取自 [nicobailon/visual-explainer](https://github.com/nicobailon/visual-explainer)（MIT，授權見 LICENSE），commit 9d5f880（2026-11-04），2026-11-25 複製。只複製了原則文件：`SKILL.md`、`references/diagrams.md`、`references/style-guide.md`、`references/motion.md`。

## 在開源探索誌怎麼用

- **用它的「解釋原則」**：Show, don't tell 九條、圖的選擇表、Words 一節、style-guide 的版面與圖表規則、diagrams 的機制圖畫法、motion 的步驟圖與 live figure。
- **不用它的工具**：本 repo 沒有它的 kit（`kit.css`、`<ve-bars>`、`<ve-flow>` 等元件）、render 指令、MCP、`~/.agent/diagrams/` 輸出路徑。文件裡提到這些的地方，一律改成**手寫 inline SVG／HTML／CSS** 做出同樣效果；檢查交給 `oss.py qa`、impeccable 與設計審查員。
- **衝突時的優先順序**：版型結構（區塊、字數上限、收合）以 `oss-episode/design.md` 為準；品味以 `frontend-design` 為準；「怎麼把一件事解釋清楚」以這份為準。
