# SYSTEM：來源分級與收斂門禁

## 1. 當前與目標差異

```text
當前：feeds.yaml（無分級）-> fetch.py 拋棄式抓取 -> raw_data.json（無累積）
      -> summarizer.py 全量塞給 Gemini -> 自由格式長文 -> 原樣寫入 summary.md/history/

目標：feeds.yaml（tier/role）-> fetch.py 抓取 -> store.py 去重累積 -> news.db（seen_count/sources）
      -> scoring.py 算 confidence/heat -> 只把達門檻 story 送進 Gemini
      -> Gemini 輸出結構化 JSON -> Pydantic 校驗（Schema/占位詞/引用子集）
      -> 通過才寫入 summary.md/history/，build_site.py 拆事實/判斷兩區塊呈現
```

## 2. 資料模型

### `feeds.yaml` 新欄位

```yaml
feeds:
  - name: "OpenAI News"
    url: "https://openai.com/news/rss.xml"
    category: "AI"
    tier: 1
    role: "primary"
```

`tier`：1（官方一手）/ 2（專業媒體）/ 3（專家/個人 newsletter）/ 4（社群熱度或聚合）。
`role`：`primary` / `professional` / `expert` / `aggregator` / `heat`。所有 `Google News: *` 搜尋型來源固定 `tier: 4, role: aggregator`，不分它掛在哪個 `category` 下。

### `news.db`（SQLite，`store.py` 管理）

```sql
CREATE TABLE stories (
  fingerprint    TEXT PRIMARY KEY,  -- sha256(canonical_url 或 normalize(title))
  title          TEXT NOT NULL,
  canonical_url  TEXT NOT NULL,
  category       TEXT NOT NULL,
  first_seen_at  TEXT NOT NULL,     -- ISO-8601 UTC
  last_seen_at   TEXT NOT NULL,
  seen_count     INTEGER NOT NULL DEFAULT 1,
  sources_json   TEXT NOT NULL      -- JSON array of {name, tier, role}，去重後
);
```

`store.upsert_story(article)`：以 fingerprint 查找，不存在則新建（`seen_count=1`）；存在則 `seen_count += 1`、`last_seen_at` 更新、`sources_json` 合併去重（依 `name` 去重，同名來源不重複累加）。

## 3. 邊界

### 送進 Gemini 的輸入 allowlist

- story 的 `title`、`canonical_url`、`category`；
- 本次抓取到的原文清理後文字（沿用現有 `clean_html` + 1200 字截斷）；
- 累積後的 `tier`（取最小值，即最高權威）、`seen_count`、獨立來源數與名稱列表。

不送整個 `news.db`、不送其他分類的 story、不送任何本機路徑或 feed 設定以外的中繼資料。

### 輸出 Schema（Pydantic）

```python
class StoryDigest(BaseModel):
    fact_summary: str = Field(min_length=20, max_length=400)
    judgment: str = Field(min_length=20, max_length=600)
    used_source_urls: list[HttpUrl] = Field(min_length=1, max_length=3)
```

`used_source_urls` 必須是輸入 story 本身（含其累積來源）canonical_url 的子集；`fact_summary`/`judgment` 兩個欄位都要跑占位詞正則（`待補充|TBD|TODO|placeholder`），命中即拒絕。

## 4. 打分公式（`scoring.py`）

```python
def clamp(v: float) -> int:
    return max(0, min(100, round(v)))

def score_story(tiers: list[int], seen_count: int, distinct_sources: int) -> dict:
    authority = 100 - (min(tiers) - 1) * 25       # tier1→100, tier2→75, tier3→50, tier4→25
    confidence = clamp(authority * 0.7 + min(distinct_sources, 4) * 7.5)
    heat = clamp(min(seen_count, 6) * 12 + min(distinct_sources, 4) * 10)
    return {"confidence": confidence, "heat": heat}
```

只有 `confidence >= 60` 或 `heat >= 60` 的 story 送進 `prompt_deep`；其餘留在 `raw_data.json`/`news.db` 但不進入 Gemini 深度分析，於首頁精簡摘要標記為「觀察中」而非展開分析。分數不由 Gemini 產生或覆寫。

## 5. 失敗與回滾

- 單一 story 的 Gemini 輸出解析/校驗失敗：記錄 `logging.warning`，跳過該 story，不中斷同分類其他 story 的處理。
- 全分類都沒有達到打分門檻的 story：該分類只輸出來源清單（標題+連結+tier），不呼叫 Gemini，`summary.md` 明確標示「本次無達標深度分析」而非留空白或報錯。
- `news.db` 若不存在，`store.py` 啟動時自動建表；不影響既有 `history/`、`summary.md`、`index.html` 的手動回滾（直接 `git revert` 即可，與資料庫狀態無關，資料庫本身不進版控）。
- `news.db` 加入 `.gitignore`，不提交進 repo（比照 agent-pulse 的本機資料庫不進版控原則）。

## 6. Pipeline

```text
fetch.py
  讀 feeds.yaml（含 tier/role）
  抓取 -> store.upsert_story() 去重累積
  寫 raw_data.json（本次新增/更新的 story，含 seen_count/sources/tier）
        │
        ▼
scoring.py（被 summarizer.py 呼叫）
  對每個 story 算 confidence/heat
  分流：達門檻 -> 深度 prompt；未達門檻 -> 僅速報清單
        │
        ▼
summarizer.py
  Gemini 回傳 JSON -> Pydantic 校驗 -> 通過寫 history/*.md；失敗丟棄並記錄
        │
        ▼
build_site.py
  從驗證過的 StoryDigest 渲染事實/判斷分區塊 + confidence/heat 標籤
  -> index.html / rss.xml
```
