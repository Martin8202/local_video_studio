# Local Video Studio

用 **Claude Code + ComfyUI + LTX-2** 在家用電腦上完全本機生成帶聲音的 AI 短片。個人測試專案。

- 🖥️ 完全本機推論（RTX 5060 Ti 16 GB）
- 🚫 不使用中國廠商模型（排除 MiniMax H3、Wan、HunyuanVideo、CogVideoX）
- 🎬 影像與音訊一次生成（LTX-2，Lightricks）
- 🤖 Claude Code 負責寫 prompt、組 workflow、呼叫 ComfyUI API

完整設計見 [`SPEC.md`](SPEC.md)。

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

## 進度

- [ ] M0 環境建置
- [ ] M1 手動跑通第一支影片
- [ ] M2 Claude Code 自動化
- [ ] M3 多鏡頭合成

## 授權備註

LTX-2 可免費用於學術用途，以及年營收低於 1,000 萬美元的公司商用。本專案僅供個人測試。
