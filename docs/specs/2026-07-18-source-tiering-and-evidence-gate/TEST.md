# TEST：來源分級與收斂門禁

## 1. 單元測試（`unittest`，不新增測試框架）

- `test_fetch.py`：`fetch_feeds()` 產出的每篇文章帶有 `tier`/`role`，且與對應 `feeds.yaml` 項目一致。
- `test_store.py`：
  - 同一篇文章（相同 canonical_url）連續 `upsert_story()` 兩次，`seen_count` 從 1 變 2，`sources_json` 不重複累加同一來源。
  - 同一則新聞被兩個不同 feed 命中（相同標題指紋、不同來源），`sources_json` 累積兩個獨立來源。
- `test_scoring.py`：
  - tier1 + 2 個獨立來源的 story，`confidence` 高於 tier4 + 1 個來源的 story。
  - `seen_count` 越高，`heat` 分數越高（在封頂前）；封頂後不再上升。
- `test_summarizer_schema.py`：
  - 合法 JSON（`used_source_urls` ⊆ 輸入 URL 集合、長度在範圍內）通過 `StoryDigest` 校驗。
  - `used_source_urls` 含輸入之外的網址 → 校驗失敗，story 被丟棄且不寫檔。
  - `fact_summary`/`judgment` 命中占位詞正則 → 校驗失敗。
  - 欄位長度超出/低於邊界 → 校驗失敗。

## 2. 本地端到端驗證

```bash
cd news-getter
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 fetch.py    # 檢查 raw_data.json 含 tier/role/seen_count/sources
python3 fetch.py    # 再跑一次，確認 news.db 中重複命中的 story seen_count 遞增
python3 summarizer.py
python3 build_site.py
```

檢查項：

- `news.db` 用 `sqlite3 news.db "select fingerprint, seen_count, sources_json from stories order by seen_count desc limit 5;"` 確認去重與累積正確。
- `summary.md`／`index.html` 裡每個深度分析要點可見「事實」與「判斷」兩個獨立區塊，且每個判斷至少附一個輸入來源連結。
- 分數低於門檻的 story 只出現在速報清單，不進入深度分析區塊。
- 手動修改一次 `run_gemini()` 回傳值，注入一個不在輸入 URL 集合內的連結，確認該 story 被丟棄（檢查 log 訊息與 `summary.md` 內容）。

## 3. 回歸檢查

- `./run_pipeline.sh` 完整跑一次不報錯，`git status` 顯示只有預期的檔案變更（`index.html`/`rss.xml`/`summary.md`/`history/`），`news.db` 不出現在 `git status`（已加入 `.gitignore`）。
- `.github/workflows/daily-news.yml` 不需改動即可沿用（沒有新增環境變數需求，`pydantic` 已在 `requirements.txt`，`run_pipeline.sh` 的 `pip install -r requirements.txt` 會自動裝上）。
