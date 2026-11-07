# Local Video Studio

用 **Claude Code + ComfyUI + LTX-2** 在家用電腦上完全本機生成帶聲音的 AI 短片。個人測試專案。

- 🖥️ 完全本機推論（RTX 5060 Ti 16 GB）
- 🚫 不使用中國廠商模型（排除 MiniMax H3、Wan、HunyuanVideo、CogVideoX）
- 🎬 影像與音訊一次生成（LTX-2，Lightricks）
- 🤖 Claude Code 負責寫 prompt、組 workflow、呼叫 ComfyUI API

完整設計見 [`SPEC.md`](SPEC.md)。

## Demo

用 5 則財經新聞生成 25 秒短片，全程本機生成：[`demo/`](demo/README.md)（成品 [`news-1107.mp4`](demo/news-1107.mp4)）

![demo 縮圖](demo/news-1107-contact-sheet.jpg)

## 運作方式

```
你 ──► Claude Code ──► ComfyUI (localhost:8188) ──► LTX-2 ──► mp4 ──► ffmpeg 合併
       寫分鏡/prompt     headless API                 影像+音訊
```

## 目錄結構（規劃）

```
local-video-studio/
├── README.md
├── docs/
│   ├── SPEC.md              規格書
│   └── MODELS.md            模型檔案來源紀錄（待建立）
├── skills/
│   └── ltx-prompt/SKILL.md  LTX-2 prompt 寫法（待建立）
├── workflows/
│   ├── templates/           ComfyUI 匯出的 API 格式 JSON 與 node 對照表
│   └── out/                 每個鏡頭產生的 workflow
├── scripts/
│   ├── build_workflow.py    填範本
│   ├── run_comfy.py         送出、輪詢、下載
│   └── concat.py            合併多段影片
├── shots/                   分鏡 yaml
└── output/                  成品（不進 git）
```

## 快速開始（M0–M1）

1. 安裝最新版 [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
2. 從 ComfyUI Manager 安裝 `ComfyUI-LTXVideo` 節點
3. 從 [Lightricks/LTX-2](https://huggingface.co/Lightricks/LTX-2) 下載權重（建議先用蒸餾版和 fp4 版）
4. 確認文字編碼器來源不是中國廠商模型，並記錄在 `docs/MODELS.md`
5. 在介面中載入 LTX-2 範本，以 768×512、5 秒的設定跑第一支影片
6. 記錄 VRAM 峰值與耗時，回填到 `SPEC.md` 第 6 節

## 啟動 ComfyUI 並用網頁開啟

在自己的 PowerShell 視窗執行（路徑 `D:\ComfyUI` 是作者這台電腦的安裝位置，換電腦請自行修改）：

```
cd D:\ComfyUI
.\.venv\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188
```

視窗出現 `To see the GUI go to: http://127.0.0.1:8188` 後，用瀏覽器開啟 <http://127.0.0.1:8188>，左側選 Templates 載入 LTX-2.5 Text to Video（本機版，名稱不含 API）。關閉時在該視窗按 `Ctrl+C`。

- `--listen 127.0.0.1` 代表只有本機能連線，手機與其他電腦打不開。
- 請在自己的終端機啟動，不要由 Claude Code 背景啟動：1080p 時系統記憶體會吃滿，背景程式可能被系統自動停掉（見 `SPEC.md` 第 6 節）。
- 用腳本生成（`scripts/run_comfy.py`）時，也要先照上面啟動 ComfyUI，不需要開網頁。

## 進度

- [x] M0 環境建置
- [x] M1 跑通第一支影片（改由腳本送出，未使用介面）
- [x] M2 Claude Code 自動化
- [x] M3 多鏡頭合成（5 鏡頭、25 秒，1920×1024）

## 授權備註

LTX-2 可免費用於學術用途，以及年營收低於 1,000 萬美元的公司商用。本專案僅供個人測試。
