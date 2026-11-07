# Demo：新聞 → 25 秒本機生成短片

![5 個鏡頭的縮圖](news-1107-contact-sheet.jpg)

**成品**：[`news-1107.mp4`](news-1107.mp4)（25 秒、1920×1024、24 fps、含音軌，約 31 MB）
**輸入**：[`news-1107-source.md`](news-1107-source.md)（5 則新聞）
**分鏡**：[`../shots/news-1107.yaml`](../shots/news-1107.yaml)

## 這個 demo 做了什麼

使用者貼上 5 則財經新聞，要求做成一支影片。整個流程中，只有 Claude Code 連網；影片生成完全在本機 GPU 上跑，沒有呼叫任何雲端影片 API。

```
 白話步驟                              對應位置
 ──────────────────────────────────   ─────────────────────────────────
 1 使用者貼 5 則新聞                   → 對話
        ▼
 2 Claude 為每則新聞挑一個主題，        → skills/ltx-prompt/SKILL.md 規則
   編一個英文鏡頭描述                     shots/news-1107.yaml
        ▼
 3 把 prompt、解析度、秒數填進          → scripts/build_workflow.py
   ComfyUI 工作流程                       workflows/templates/ltx2_5_t2v_*.json
        ▼
 4 逐一送給本機 ComfyUI 生成            → scripts/run_comfy.py
   （16 GB 一次只跑一個鏡頭）               ComfyUI + LTX-2.5（127.0.0.1:8188）
        ▼
 5 下載 5 個 mp4，ffmpeg 合併成片       → scripts/concat.py
```

## 5 個鏡頭與對應新聞

| # | 新聞主題 | Claude 編的畫面（象徵性） |
|---|----------|--------------------------|
| 1 | 台股重挫、外資匯出 | 黃昏的交易室，螢幕上紅色下跌走勢圖，人群站著看盤 |
| 2 | 鴻海營收創高 | 明亮的工廠，機械手臂組裝發光的伺服器機櫃 |
| 3 | 美股晶片、AI 股遭拋售 | 資料中心走道，機櫃的燈一盞盞熄滅，光線由藍轉紅 |
| 4 | Airbnb、Cloudflare 財報優於預期 | 客廳裡有人看著地圖、闔上行李箱 |
| 5 | 豐田財測上調 | 一排白色油電車駛出展間，開上街頭 |

## 技術設定

| 項目 | 內容 |
|------|------|
| 模型 | LTX-2.5 22B distilled（int8-convrot），Lightricks |
| 文字編碼器 | Gemma 4 12B（Lightricks 客製版） |
| 介面 | ComfyUI 0.44.0，以 API 方式由腳本呼叫，沒有開介面操作 |
| 硬體 | RTX 5060 Ti 16 GB、系統記憶體 31 GB |
| 每鏡頭 | 5 秒、24 fps、1920×1024、約 390–406 秒 |
| VRAM 峰值 | 約 15.9 GB |
| 來源紀錄 | [`../docs/MODELS.md`](../docs/MODELS.md) |

## 限制與注意事項

- **畫面是 Claude 的詮釋，不是新聞的忠實呈現。** 影片沒有字幕或旁白，新聞裡的數字（跌幅、營收、財報）都沒有出現；鏡頭 3 只用「機櫃熄滅」表達，政治背景完全沒有表現。
- 為避免模型生成亂碼文字與假 logo，prompt 排除了文字、品牌與真實人物，所以看不出是哪家公司。鏡頭 4 的人物是模型隨機生成的。
- 實際解析度是 1920×1024，不是 1920×1080：流程先用一半尺寸生成再升頻 2 倍，一半的高度必須是 32 的倍數。要標準 1080p 可設 1088 後用 ffmpeg 裁切（未驗證）。
- 1440p 沒有成功驗證。
- 1080p 生成時系統剩餘記憶體最低約 0.9 GB。在 Claude Code 背景啟動 ComfyUI 時，系統兩次因記憶體不足自動停掉背景程式；建議在自己的終端機啟動。
- 音軌由模型同步生成，品質未經正式評估。

## 重現方式

```
# 1. 啟動 ComfyUI（需已依 README 裝好環境與模型）
# 2. 產生每個鏡頭的 workflow
python scripts/build_workflow.py shots/news-1107.yaml
# 3. 逐一生成（每個約 6–7 分鐘）
python scripts/run_comfy.py workflows/out/news-1107_shot_01.json --dest output/news-1107
# ...對 02–05 重複
# 4. 合併
python scripts/concat.py final/news-1107.mp4 output/news-1107/*.mp4
```

注意：`output/news-1107/*.mp4` 的順序要和鏡頭編號一致（ComfyUI 的輸出檔名編號是全域遞增）。
