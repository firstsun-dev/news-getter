# PRD：來源分級與收斂門禁

## 1. 問題

`feeds.yaml` 混合了官方一手來源（OpenAI News、ArXiv）、專業媒體（BBC、WSJ、iThome）、個人 newsletter（Ben's Bites）、社群熱度（Reddit、PTT）與聚合轉載（`Google News: *` 搜尋型 RSS）共約 40 個來源，但 `summarizer.py` 把它們同等看待餵給 Gemini。Gemini 輸出是不限篇幅的自由文字，沒有機制要求「引用連結必須來自輸入文章」，也沒有事實與判斷分離。`fetch.py` 每次抓取即拋棄（`raw_data.json` 沒新文章就整個刪除），`history/<timestamp>/` 之間互不關聯，同一則新聞在不同時段的抓取會被當成新事件重複寫深度分析，也無法回答「這則消息有幾個獨立來源」。

## 2. 目標

1. 每個 `feeds.yaml` 來源標註 `tier`（1-4）與 `role`（primary/professional/expert/aggregator/heat），`fetch.py` 把這兩個欄位帶進每篇文章紀錄。
2. 抓取結果持久化到本機 SQLite（`news.db`），用 URL/標題指紋去重，累積同一則新聞的 `seen_count` 與獨立來源列表，取代目前拋棄式的 `raw_data.json`。
3. 用累積後的 tier、獨立來源數、`seen_count` 算出確定性的 `confidence`/`heat` 分數，只把達到門檻的 story 送進 Gemini 深度分析，其餘保留但不深度處理。
4. Gemini 輸出改為結構化 JSON（`fact_summary`/`judgment`/`used_source_urls`），本機用 Pydantic 校驗：`used_source_urls` 必須是輸入文章連結的子集、長度與占位詞檢查未過就整條丟棄，不寫進 `summary.md`/`history/`。
5. `build_site.py` 呈現時把「事實」與「判斷」拆成兩個視覺區塊，並顯示 confidence/heat 分數。

## 3. 非目標

- 不做多語言語意聚類或跨來源實體對齊；去重只做同一則新聞的 URL/標題指紋比對。
- 不引入外部資料庫服務；仍用本機 SQLite 檔案，不改變 self-hosted runner 的部署模式。
- 不讓 Gemini 決定 tier、分級規則或分數公式；這些永遠是本機確定性程式碼。
- 不承諾每次執行都有通過門檻的深度分析內容；未達標時只出速報清單。
- 不處理 `Google News` 搜尋源背後實際轉載媒體的身份解析（維持整體標記為 `aggregator`，不做到 Agent Pulse 那種「必須解析回原始發布方」的程度）。

## 4. 用戶價值

- 使用者能分辨「單一來源速報」與「多來源交叉驗證」的新聞，不再被 PTT 八卦和官方公告用同樣篇幅呈現。
- 深度分析裡的每個判斷都附著至少一個輸入來源連結，降低 Gemini 編造細節但查無來源的風險。
- 同一則新聞不會在每次抓取後被當成新事件重複寫一次深度分析，`history/` 增長速度與雜訊下降。

## 5. 驗收

- `python3 fetch.py` 後，`raw_data.json` 每篇文章都有 `tier`/`role`，數值與 `feeds.yaml` 一致。
- 連續兩次抓到同一則新聞（不同 feed 或不同時間），`news.db` 對應 story 的 `seen_count` 遞增、`sources_json` 累積多個來源，而非產生兩筆獨立紀錄。
- `scoring.py` 對 tier1+多來源 story 給出的分數高於 tier4 單一來源 story（有對應單元測試）。
- 手動構造一筆「引用輸入之外連結」的假 Gemini 回應，`summarizer.py` 會丟棄它，不寫進 `summary.md`。
- 完整跑一次 `./run_pipeline.sh`，`summary.md`/`index.html` 裡每個要點可見「事實」與「判斷」兩個獨立區塊，且顯示 confidence/heat 分數。
