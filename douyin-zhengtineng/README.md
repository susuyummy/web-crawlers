# 正体能影片下載與分類合輯

本專案依使用者要求，把作者公開作品建立清單、下載原片，並依主題合併成附章節的長片。

## 來源與涵蓋範圍

- 核對日期：2026-10-19。
- 作者：正体能；抖音號：2067846244。
- 作者首頁：https://www.douyin.com/user/MS4wLjABAAAAM1_p0rl5_KWjzfP8cs60YEcJxfmTdcnGPA0lIQzjFn4
- 首頁顯示939則作品。正常捲動至作品回應的 `has_more=0` 後，實際取得937個不重複作品ID。
- 其中744支影片、193則圖文。差額2則未由頁面提供，原因未知；不能宣稱已取得全部939則。
- 影片總片長約9.51小時。193則圖文保留清單，未混入影片合輯。

## 儲存位置

使用者指定外接磁碟「未命名3」。檔案放在：

```text
/Volumes/未命名3/正体能影片整理/
├── 開始觀看.html
├── 原始影片/
├── 分類合輯/
│   ├── 主題_01.mp4
│   └── 主題_01.txt
└── 處理紀錄/
    ├── 作品清單.json
    ├── download-state.json
    ├── merge-state.json
    ├── processing-status.json
    ├── pipeline-result.json（流程結束後產生）
    └── pipeline.log
```

GitHub 保存程式、公開作品清單、分類依據與進度摘要。大型媒體保留在指定外接磁碟；登入狀態、Cookie、簽名下載網址與私有暫存不進入儲存庫。

## 處理方式

1. 透過獨立已登入的瀏覽器正常載入作者作品頁，讀取頁面實際回應；依作品ID去重。
2. 六部並行下載，可中斷後續傳；完成紀錄會略過已成功的原片。
3. 檢查HTTP內容類型、檔案長度、實際片長及開頭解碼，成功才改為正式檔名。
4. 依原標題與標籤分類，**尚未逐支觀看內容或查核作者的訓練、健康主張**。這是主題合輯，不是精華摘要或處方。
5. 同主題依發布時間排列，完整保留每支影片的講解。每部合輯約45分鐘；單支超過45分鐘時保留完整單支。
6. 統一為720×1280、30fps、H.264/AAC；保留畫面比例，必要時補留白。使用VideoToolbox硬體編碼。
7. 加入MP4章節及同名文字索引，記錄每段開始時間與原始連結。
8. 合輯完成後核對片長，做完整音畫解碼檢查，再列為完成。
9. 外接磁碟未掛載或剩餘空間低於10GB時停止新增媒體，避免寫入內建磁碟或耗盡空間。

## 執行

此版本使用本機既有工具：Python 3、`agent-browser` 與BlueStacks附帶的FFmpeg。工具路徑位於 `scripts/archive.py`，可依環境調整。抖音登入只用於作品頁讀取；不會上傳登入憑證。

```sh
python3 scripts/archive.py collect
python3 scripts/archive.py download --workers 6
python3 scripts/archive.py merge
python3 scripts/library.py
python3 scripts/archive.py status
```

`collect` 需要先在獨立的 `zhengtineng-archive` 瀏覽器工作階段開啟該作者頁面。下載網址暫存在被忽略的 `.local/`，可能過期；過期需重新載入作品頁。

下載及自動重試、合併：

```sh
python3 scripts/finish_pipeline.py
```

僅在沒有其他下載程序執行時使用。若已有本專案下載程序，可透過 `--wait-pid 程序編號` 等它結束後接續，避免同時寫入相同檔案。

## 進度與驗證

目前進度見 [data/processing-status.json](data/processing-status.json)。

已實測：三支原片的下載與片長、音訊檢查；14支營養主題原片合併成1.4分鐘影片、章節與來源索引、完整解碼。已抽查輸出畫面，文字保留，未裁切。

大量下載與其餘合輯仍以實際進度報告為準，不能因程式已啟動就宣稱全部完成。
