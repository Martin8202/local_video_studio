# 模型檔案來源紀錄

每下載一個模型、文字編碼器、VAE、LoRA 都記一列。廠商或底模是中國廠商者不得使用（SPEC C2）。
檔案存放在 `D:\ComfyUI\models\`（不在 OneDrive 內）。

| 檔名 | 用途 | 來源 | 廠商 | 大小 | 下載日期 |
|------|------|------|------|------|----------|
| `diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` | 主模型（蒸餾版 int8） | [Lightricks/LTX-2.5](https://huggingface.co/Lightricks/LTX-2.5) | Lightricks（以色列） | 21.5 GB | 2026-11-07 |
| `text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` | 文字編碼器 | Lightricks/LTX-2.5 | Lightricks（Gemma 4 為底） | 15.37 GB | 2026-11-07 |
| `text_encoders/gemma4_e2b_it_int8_convrot.safetensors` | 範本內的輔助文字編碼器 | [Comfy-Org/gemma-4](https://huggingface.co/Comfy-Org/gemma-4) | Comfy-Org（Gemma 4 e2b） | 5.2 GB | 2026-11-07 |
| `vae/ltx-2.5-video-vae-bf16.safetensors` | 影像 VAE | Lightricks/LTX-2.5 | Lightricks | 1.47 GB | 2026-11-07 |
| `vae/ltx-2.5-audio-vae-bf16.safetensors` | 音訊 VAE | Lightricks/LTX-2.5 | Lightricks | 0.36 GB | 2026-11-07 |
| `latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors` | 空間 upscaler | Lightricks/LTX-2.5 | Lightricks | 1.0 GB | 2026-11-07 |

檔名與網址取自 ComfyUI 內建範本 `video_ltx2_5_t2v.json`，大小取自 Hugging Face API。

## 已確認
- Gemma 4 12B 基底模型的廠商是 Google（授權 Apache 2.0），2026-11-07 查證，來源：[Wikipedia: Gemma (language model)](https://en.wikipedia.org/wiki/Gemma_(language_model))、[Jon Peddie Research](https://www.jonpeddie.com/news/google-fills-out-the-middle-with-the-gemma-4-12b/)、[FoneArena](https://www.fonearena.com/blog/?p=484210)。Lightricks 提供的是加上投影層、轉成 int8 的客製版，符合 C2。
- 以上為第三方報導與百科，沒有直接讀 Google 官方模型卡；發布日期各來源不一致（5/23 或 6/3），不影響廠商判斷。
