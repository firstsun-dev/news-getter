# TASKS：來源分級與收斂門禁

只有程式碼、測試與實跑證據齊備後才勾選。

## 1. 規格

- [x] 核對現有 `fetch.py`/`summarizer.py`/`build_site.py`/`feeds.yaml` 行為與問題
- [x] 定義 tier/role 分類、`news.db` schema、打分公式與輸出 Schema
- [x] 寫 PRD/SYSTEM/TEST 文件

## 2. Phase 1 — 來源分級

- [ ] `feeds.yaml` 全部 ~40 個來源標註 `tier`/`role`
- [ ] `fetch.py` 把 `tier`/`role` 帶進 article dict 與 `raw_data.json`

## 3. Phase 2 — 持久化與去重

- [ ] 新增 `store.py`（`upsert_story`/`stories_since`），`news.db` 加入 `.gitignore`
- [ ] `fetch.py` 改用 `store.upsert_story()`，拿掉「無新文章即刪除 `raw_data.json`」邏輯

## 4. Phase 3 — 確定性打分

- [ ] 新增 `scoring.py`（`score_story`），單元測試涵蓋 tier/独立來源/seen_count 對分數的影響
- [ ] `summarizer.py` 依分數門檻分流「深度分析」與「速報清單」

## 5. Phase 4 — AI 收斂 Schema 校驗

- [ ] `requirements.txt` 加入 `pydantic`
- [ ] `summarizer.py` 定義 `StoryDigest`，改寫 prompt 要求純 JSON 輸出，校驗失敗即丟棄並記錄
- [ ] `build_site.py` 改為從 `StoryDigest` 渲染事實/判斷雙區塊 + confidence/heat 標籤

## 6. 驗證

- [ ] 單元測試（`test_fetch.py`/`test_store.py`/`test_scoring.py`/`test_summarizer_schema.py`）全過
- [ ] 本地完整跑 `./run_pipeline.sh`，人工檢查輸出符合 PRD 驗收標準
- [ ] 確認 `news.db` 不進入 git 追蹤
- [ ] 更新 `CLAUDE.md`／`README.md` 反映新的 pipeline 行為
