# 來源分級與收斂門禁

- 狀態：草案
- 日期：2026-07-18
- 目標版本：Unreleased
- 前置規格：無（本專案第一份規格文件）

`news-getter` 目前把 `feeds.yaml` 裡所有來源（官方部落格、專業媒體、個人 newsletter、Reddit、PTT、Google News 搜尋聚合）不分權重地餵給本機 Gemini CLI，Gemini 自由發揮寫長文，沒有事實與判斷分離、沒有引用來源校驗，且每次抓取即拋棄，同一則新聞會被重複當成新事件深度分析。

本規格參考 `agent-pulse` 的來源分級、確定性打分、AI 收斂 Schema 校驗與 Event 去重模型，訂出 news-getter 可執行的落地版本：來源加 tier/role → 抓取結果持久化去重 → 用累積證據算分 → AI 只能在輸入證據範圍內寫結構化 JSON，未通過 Schema/占位詞/引用校驗一律丟棄。

## 文件

- [PRD](PRD.md)：問題、目標、非目標與驗收
- [SYSTEM](SYSTEM.md)：資料模型、邊界、打分公式、失敗與回滾
- [TEST](TEST.md)：單元與端到端驗證
- [TASKS](TASKS.md)：實施與驗收清單

## 核心原則

```text
Tier 決定證據夠不夠；AI 只能在證據允許的範圍內寫判斷；Schema 校驗失敗就整條丟棄，不寫進任何輸出。
```

沒有合格 story 時，當次輸出可以只有速報、沒有深度分析，但必須留下可觀察的候選數、丟棄原因與分數依據。
