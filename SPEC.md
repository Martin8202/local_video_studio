# Local Video Studio 規格書

> 版本：v0.1（2026-11-07）｜擁有者：Martin｜用途：個人測試

---

## 1. 目標與範圍

### 1.1 目標
在家用電腦上**完全本機**執行 AI 影片生成：由 Claude Code 負責寫 prompt、組 workflow、呼叫 ComfyUI，由 ComfyUI 執行開放權重的影片模型，產出帶聲音的短片。

### 1.2 硬性限制
| # | 限制 | 說明 |
|---|------|------|
| C1 | 完全本機推論 | 影片生成不呼叫任何雲端 API；只有安裝階段需要下載模型 |
| C2 | 不使用中國廠商模型 | 主模型、文字編碼器、VAE、LoRA 都適用 |
| C3 | 硬體上限 | RTX 5060 Ti 16 GB VRAM |
| C4 | 個人測試用途 | 不涉及公司資料與商業用途 |

> 備註：Claude Code 本身是雲端 LLM，它只負責**寫 prompt 與控制流程**，不會碰到影片運算。若連這部分也要離線，需另外評估本機 LLM（不在本版範圍內）。
>
> 網路政策：只有 Claude Code 可以聯網。Claude 檢查成品時（例如抽幀確認）可以讀取影片抽出的圖片，這些圖片會送到雲端，已獲使用者同意（2026-11-07）。

### 1.3 不在範圍內
- 長片（超過 20 秒的單段）、即時生成
- 模型微調／LoRA 訓練（列為未來選項）
- 公司部署與商業授權

---

## 2. 模型選型

### 2.1 選定：LTX-2 / LTX-2.3（Lightricks，以色列）
| 項目 | 內容 |
|------|------|
| 類型 | DiT 架構，影像與音訊在同一次生成中同步產出 |
| 規格上限 | 最長約 20 秒、原生 4K、最高 50 fps（以官方公告為準） |
| 權重版本 | `19b-dev`（bf16）、`fp8`、`fp4`（NVFP4）、`distilled`（8 步、CFG=1）、空間／時間 upscaler |
| ComfyUI | 官方節點 `ComfyUI-LTXVideo`，也有 ComfyUI 內建支援 |
| 授權 | 學術用途免費；年營收低於 1,000 萬美元的公司可商用（個人測試沒有問題） |
| 語言 | 模型卡標示為英文；中文 prompt 和中文語音的效果需要實測 |

### 2.2 排除名單（違反 C2）
| 模型 | 廠商 | 排除原因 |
|------|------|----------|
| MiniMax H3 | MiniMax（中國） | 主模型是中國廠商；文字編碼器使用 Qwen3-VL |
| Wan 2.x | 阿里巴巴 | 中國廠商 |
| HunyuanVideo | 騰訊 | 中國廠商 |
| CogVideoX | 智譜 | 中國廠商 |
| SkyReels | 崑崙萬維 | 中國廠商 |

### 2.3 待驗證
- [ ] LTX-2 搭配的**文字編碼器**來源（預期是 Google Gemma 系列，安裝時要確認檔名，不能是 Qwen/T5 的中國衍生版）
- [ ] 所有從 Civitai 或 Hugging Face 下載的 LoRA 都要確認作者和底模，不能用到 C2 排除的模型

---

## 3. 系統架構

```
┌──────────┐  自然語言需求  ┌───────────────────────┐
│   你     │ ────────────► │ Claude Code           │
└──────────┘               │  ├ skill: ltx-prompt  │  寫分鏡、寫 prompt
                           │  └ scripts/*.py       │  組 JSON、呼叫 API
                           └──────────┬────────────┘
                                      │ HTTP（localhost:8188）
                    POST /prompt  ▼   ▲  GET /history、/view
                           ┌──────────┴────────────┐
                           │ ComfyUI（headless）    │
                           │  ├ ComfyUI-LTXVideo   │
                           │  ├ LTX-2 權重（fp4/8）  │
                           │  ├ 文字編碼器          │
                           │  └ 影像／音訊 VAE       │
                           └──────────┬────────────┘
                                      ▼
                           output/*.mp4（含音軌）
                                      │
                                      ▼
                           ffmpeg 合併 → final/*.mp4
```

### 3.1 元件責任
| 元件 | 責任 | 不負責 |
|------|------|--------|
| Claude Code | 拆分鏡、寫 prompt、修改參數、執行腳本、判斷是否重跑 | 影片運算 |
| `ltx-prompt` skill | LTX-2 的 prompt 寫法規則（鏡頭、動作、聲音描述） | — |
| `build_workflow.py` | 把 prompt 和參數填進 workflow 範本 | 送出任務 |
| `run_comfy.py` | 送出任務、輪詢進度、下載成品 | 組 JSON |
| `concat.py` | 用 ffmpeg 合併多段影片 | — |
| ComfyUI | 載入模型、執行推論 | 業務邏輯 |

---

## 4. 主流程

```
 步驟（白話）                       對應檔案／函式
 ─────────────────────────────    ──────────────────────────────────
 1 輸入需求（主題、長度、風格）   → 你 → Claude Code
        │
        ▼
 2 拆成 N 個鏡頭、各寫 prompt     → skills/ltx-prompt/SKILL.md
        │                           產出 shots.yaml
        ▼
 3 每個鏡頭填入 workflow 範本     → scripts/build_workflow.py
        │                           build(shot) → workflows/out/shot_XX.json
        ▼
 4 依序送出（16 GB 一次只跑一個）  → scripts/run_comfy.py
        │                           submit() → POST /prompt
        ▼
 5 輪詢直到完成                   → run_comfy.py  poll() → GET /history/{id}
        │
        ├─ 失敗（OOM／節點錯誤）──► 降解析度或秒數，或改用蒸餾版 → 回到 3
        ▼
 6 下載 mp4                       → run_comfy.py  download() → GET /view
        │
        ▼
 7 檢查結果，不滿意就調 prompt     → Claude Code（必要時抽幀確認）→ 回到 2
        │
        ▼
 8 多段合併成片                   → scripts/concat.py（ffmpeg concat）
```

不涵蓋：字幕、背景音樂替換、調色。

---

## 5. 元件規格

### 5.1 `shots.yaml`（分鏡格式）
```yaml
project: demo-01
defaults:
  width: 768
  height: 512
  seconds: 5
  fps: 24
  seed: -1          # -1 = 隨機
shots:
  - id: 01
    prompt: "A golden retriever runs across a beach at sunset, waves crashing, gentle wind sound"
    negative: "blurry, distorted, low quality"
  - id: 02
    prompt: "..."
```

### 5.2 `build_workflow.py`
- 輸入：`shots.yaml`、`workflows/templates/ltx2_t2v_api.json`
- 範本是在 ComfyUI 介面中用「Export (API)」匯出的 API 格式 JSON
- 用 **node id 對照表**（`workflows/templates/ltx2_t2v_map.json`）指定 prompt、寬高、幀數、seed 各自填進哪個節點的哪個欄位，避免把 node id 寫死在程式碼裡
- 啟動時呼叫 `GET /object_info` 驗證節點存在，不存在就報錯並列出缺少的節點

### 5.3 `run_comfy.py`
| 函式 | 行為 |
|------|------|
| `submit(workflow)` | POST `/prompt`，回傳 `prompt_id` |
| `poll(prompt_id, timeout=1800)` | 每 5 秒查詢 `/history/{id}`，逾時就丟出例外 |
| `download(prompt_id, dest)` | 從 history 找到輸出檔，透過 `/view` 下載 |
| 錯誤處理 | 遇到 OOM 時記錄錯誤並回傳特定代碼，讓 Claude Code 判斷要不要降規重跑 |

### 5.4 `concat.py`
- 用 `ffmpeg -f concat -c copy` 合併；如果各段解析度不一致，就改成重新編碼（H.264，`-preset veryfast`）

### 5.5 `skills/ltx-prompt/SKILL.md`
- 用英文寫 prompt，結構：**主體 → 動作 → 鏡頭運動 → 場景光線 → 聲音**
- 一定要描述聲音（模型卡指出沒有語音時音質可能比較差）
- 一個鏡頭只放一個主要動作

---

## 6. 硬體與量化選擇（RTX 5060 Ti 16 GB）

5060 Ti 是 Blackwell 架構，硬體支援 **NVFP4**，所以優先嘗試 fp4 版本。

| 優先順序 | 權重 | 預期 | 用途 |
|----------|------|------|------|
| 1 | `distilled`（8 步）+ fp4/fp8 | 最快，畫質稍差 | 調 prompt、快速迭代 |
| 2 | `fp4`（NVFP4） | 畫質和速度平衡 | 正式產出 |
| 3 | `fp8` | 需要靠 ComfyUI 把部分權重卸載到 RAM | 想要更好畫質時 |
| ✗ | `bf16 dev` | 16 GB 不夠用 | 不採用 |

**起始參數（M1）**：768×512、5 秒、24 fps、蒸餾版。跑通之後再往上加。

**其他建議**
- 系統記憶體：建議 32 GB 以上（offload 會用到），64 GB 更穩（待實測）
- 磁碟：預留 80 GB 以上給模型（主模型、文字編碼器、VAE、upscaler）
- 開啟 ComfyUI 的動態 VRAM 管理；OOM 時再加 `--lowvram`

> 以上 VRAM 和速度預估是 M1 之前寫的，實測結果見下。

**M1 實測（2026-11-07，LTX-2.5 22B distilled int8-convrot，ComfyUI 0.44.0，RTX 5060 Ti 16 GB，系統記憶體 31 GB）**
| 項目 | 結果 |
|------|------|
| 模型 | `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot`（使用者選 LTX-2.5，取代原定的 LTX-2 / 2.3） |
| 768×512、5 秒、24 fps | 約 101 秒（含首次載入）；VRAM 峰值 15.7 GB |
| 1920×1080 設定、5 秒、24 fps | 每鏡頭約 390–406 秒；VRAM 峰值 15.9 GB；實際輸出 **1920×1024** |
| 系統記憶體 | 1080p 時剩餘最低約 0.9 GB；從背景程式啟動 ComfyUI 時，Claude Code 兩次因記憶體不足自動停掉背景程式 |
| 尺寸限制 | 流程先以一半尺寸生成再升頻 2 倍，高度需讓「一半」為 32 的倍數，1080 會被捨去成 1024；要標準 1080p 可設 1088 後用 ffmpeg 裁切 |
| 1440p | 未成功驗證（試跑時被中止） |
| 結論 | 16 GB VRAM 可跑；31 GB 系統記憶體是瓶頸，1080p 建議在自己的終端機啟動 ComfyUI 並關閉其他程式 |

---

## 7. 里程碑

| 里程碑 | 內容 | 完成標準 |
|--------|------|----------|
| **M0 環境** | 安裝 ComfyUI、LTXVideo 節點、下載權重、確認文字編碼器來源 | ComfyUI 介面可以載入 LTX-2 範本 |
| **M1 跑通** | 在介面中手動跑出第一支 5 秒影片 | 有影像也有聲音的 mp4；記錄 VRAM 峰值與耗時 |
| **M2 自動化** | 完成 `build_workflow.py` 和 `run_comfy.py`；Claude Code 能從一句話產出影片 | 不打開 ComfyUI 介面就能出片 |
| **M3 多鏡頭** | `shots.yaml` 支援多鏡頭，加上 `concat.py` | 3 個鏡頭合成 15 秒短片 |
| M4（選配） | 圖生影片、首尾幀控制、upscaler | — |

---

## 8. 風險與待決事項

| # | 風險／問題 | 對策 |
|---|-----------|------|
| R1 | 16 GB 不夠導致 OOM | 先用蒸餾版和低解析度；改 fp4；加 `--lowvram` |
| R2 | 中文 prompt 或中文語音效果差 | prompt 一律用英文；中文對白在 M1 實測 |
| R3 | 社群 LoRA／workflow 混用了中國模型 | 下載前確認底模；在 `docs/MODELS.md` 記錄每個檔案的來源 |
| R4 | ComfyUI 或節點更新後，workflow 的 node id 改變 | 用對照表加 `/object_info` 驗證；鎖定版本 |
| R5 | 生成時間太長 | 調 prompt 時用蒸餾版，定稿後才用完整版 |

**待決**
- [ ] 系統記憶體容量（影響 fp8 能否順跑）
- [ ] 要不要做圖生影片（M4）
