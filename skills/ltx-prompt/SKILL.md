---
name: ltx-prompt
description: 寫 LTX-2 影片生成的英文 prompt 與 shots.yaml 分鏡。使用者要用 local_video_studio 生成影片、拆分鏡、改 prompt 時使用。
---

# LTX-2 prompt 規則

## 結構（依序，一段英文話）
主體 → 動作 → 鏡頭運動 → 場景光線 → 聲音

範例：
`A golden retriever runs across a beach, slow tracking shot from the side, warm golden-hour light, waves crashing and gentle wind`

## 規則
- 一律用英文；使用者給中文需求時，先翻成英文再寫進 `shots.yaml`。
- 一個鏡頭只放一個主要動作。要兩個動作就拆成兩個鏡頭。
- 一定要描述聲音（環境音、動作音、對白）。沒有聲音描述時音質可能較差。
- 具體描述可見的東西：外觀、動作、鏡頭、光線；不要寫抽象情緒或劇情背景。
- 預設 `seconds: 5`、768×512、24 fps（SPEC 第 6 節起始參數）。
- `negative` 預設：`blurry, distorted, low quality`。

## 流程
1. 把需求拆成 N 個鏡頭，寫成 `shots/<project>.yaml`（格式見 SPEC 5.1）。
2. `python scripts/build_workflow.py shots/<project>.yaml`
3. 逐一 `python scripts/run_comfy.py workflows/out/<project>_shot_XX.json --dest output/<project>`（16 GB 一次只跑一個）。
3b. 檢查成品：可以用 ffmpeg 抽幀（例如每秒一張、縮小尺寸）再讀取判斷；圖片會上傳雲端，使用者已同意。
4. 結束碼 2 = OOM：降解析度或秒數，或改蒸餾版，回到步驟 2。結束碼 3 = 逾時。
5. 不滿意就改 prompt 重跑；滿意後 `python scripts/concat.py final/<project>.mp4 output/<project>/*.mp4`。

## 限制
- 不使用中國廠商的模型或 LoRA（SPEC C2）；新增任何模型檔都要記錄到 `docs/MODELS.md`。
