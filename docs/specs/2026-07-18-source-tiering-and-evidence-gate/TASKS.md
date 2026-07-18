# TASKS：來源分級與收斂門禁

只有程式碼、測試與實跑證據齊備後才勾選。

## 1. 規格

- [x] 核對現有 `fetch.py`/`summarizer.py`/`build_site.py`/`feeds.yaml` 行為與問題
- [x] 定義 tier/role 分類、`news.db` schema、打分公式與輸出 Schema
- [x] 寫 PRD/SYSTEM/TEST 文件

## 2. Phase 1 — 來源分級

- [x] `feeds.yaml` 全部 ~40 個來源標註 `tier`/`role`
- [x] `fetch.py` 把 `tier`/`role` 帶進 article dict 與 `raw_data.json`

## 3. Phase 2 — 持久化與去重

- [x] 新增 `store.py`（`upsert_story`/`stories_since`），`news.db` 加入 `.gitignore`
- [x] `fetch.py` 改用 `store.upsert_story()`，拿掉「無新文章即刪除 `raw_data.json`」邏輯

## 4. Phase 3 — 確定性打分

- [x] 新增 `scoring.py`（`score_story`），單元測試涵蓋 tier/独立來源/seen_count 對分數的影響
- [x] `summarizer.py` 依分數門檻分流「深度分析」與「速報清單」

## 5. Phase 4 — AI 收斂 Schema 校驗

- [x] `requirements.txt` 加入 `pydantic`
- [x] `summarizer.py` 定義 `StoryDigest`，改寫 prompt 要求純 JSON 輸出，校驗失敗即丟棄並記錄
- [x] `build_site.py` 改為從 `StoryDigest` 渲染事實/判斷雙區塊 + confidence/heat 標籤

## 6. 驗證

- [x] 單元測試（`test_fetch.py`/`test_store.py`/`test_scoring.py`/`test_summarizer_schema.py`）全過（12 tests, 2026-07-18）
- [ ] 本地完整跑 `./run_pipeline.sh`（含真實 Gemini 呼叫）— **未完成**：本機 Gemini CLI 帳號配額已耗盡（429 rate limit），無法跑通真實 Gemini 深度分析呼叫。已用以下方式驗證邏輯正確性：
  - `fetch.py` 實跑兩次（真實網路抓取 186→226 篇文章），確認 `news.db` 去重累積、`seen_count` 遞增、relative link 正確解析為絕對網址
  - `summarizer.py`/`build_site.py` 用 mock 掉的 `run_gemini()`（回傳固定合法 JSON）實跑，確認：分數門檻分流、Pydantic schema 校驗（含 relative URL 校驗失敗案例）、全分類未達標時跳過 Gemini 並顯示「本次無達標深度分析」、`index.html`/history 頁面正確渲染事實/判斷區塊與 confidence/heat 標籤
  - 待 Gemini 配額恢復後，需再跑一次含真實 Gemini 呼叫的完整 `./run_pipeline.sh` 補齊此項驗證
- [x] 確認 `news.db` 不進入 git 追蹤
- [x] 更新 `CLAUDE.md`／`README.md` 反映新的 pipeline 行為
