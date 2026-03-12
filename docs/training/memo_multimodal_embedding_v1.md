# 备忘录：原生多模态向量化模型（Gemini Embedding 2 等）考量

**日期**：2026-03-12  
**状态**：待评估

---

## 1. 背景

当前 AIEDA 的 embedding 栈基于 **Qwen3-Embedding-0.6B**（文本塔），与自研 GraphFeatureEncoder 对齐，用于 graph-text 检索。LocalRouteChoice 任务同时使用 geometry 与 image 模态，但二者是分开编码的。若引入**原生多模态 embedding 模型**，可统一多模态表示，减少拼接/投影开销，并复用云厂商在跨模态对齐上的预训练成果。

---

## 2. Gemini Embedding 2 概览

### 2.1 能力

| 特性 | 说明 |
|------|------|
| 模态 | 文本、图像、视频、音频、文档 统一到单一 embedding 空间 |
| 文本长度 | 最高 8,192 tokens |
| 图像 | 每请求最多 6 张（PNG/JPEG） |
| 视频 | 最长 120 秒（MP4/MOV） |
| 音频 | 原生输入，无需 ASR |
| 文档 | PDF 最多 6 页 |
| 语言 | 100+ 语言 |
| 向量维度 | 默认 3,072，支持 MRL 压缩以控制存储成本 |

### 2.2 可用性

- **API**：Gemini API（`gemini-embedding-2-preview`）、Vertex AI
- **部署**：公有云 API，**无本地离线部署**
- **定价**：按用量计费（需关注图像/视频的 token 计费）

---

## 3. 与本项目的关联

### 3.1 与当前架构的差异

| 维度 | 当前（Qwen + Graph Encoder） | Gemini Embedding 2 |
|------|-----------------------------|---------------------|
| 文本 | 本地 Qwen3-Embedding-0.6B | API 文本 embedding |
| 图像 | 独立 image 模态编码 | 原生 image 输入，直接产出向量 |
| PCB 图 | 自研 GraphFeatureEncoder | **不支持**，需投影或替代表示 |
| 部署 | 全本地，可离线 | 依赖 Google Cloud / Gemini API |
| 微调 | 可训练 graph 塔对齐 Qwen | 不可微调，仅推理 |

### 3.2 潜在收益

1. **image 模态**：PCB 渲染图、截图可直接喂入，无需额外 image encoder，省去多塔拼接
2. **跨模态检索**：文本查询 PCB 图、图查图等，可利用其预训练跨模态能力
3. **统一空间**：文本 + 图像共空间，有助于 RAG、相似度检索

### 3.3 主要限制

1. **PCB graph 无法原生支持**：Gemini Embedding 2 是 text/image/video/audio/document，**没有 graph 模态**。PCB 需继续通过：
   - 方案 A：GraphEncoder → 投影到 Gemini 空间（需自研对齐）
   - 方案 B：仅用 image 代替 graph（丢失拓扑/电气语义）
2. **无离线能力**：必须联网、走 API，本地训练/评估需稳定网络与配额
3. **成本**：大规模 embedding 调用会产生费用，需评估预算

---

## 4. 国内主流模型（10 个）

| # | 模型 | 厂商 | 模态 | 核心关键 | 部署 |
|---|------|------|------|----------|------|
| 1 | **Qwen3-VL-Embedding-2B/8B** | 阿里通义 | text+image+video+doc | MMEB-V2 第一；与现有 Qwen 栈同源；2048 维 MRL；Apache 2.0；**推荐 PoC** | 本地 |
| 2 | **RzenEmbed-v2-7B** | 360 奇虎 | text+image+video+doc | MMEB-V2 总分 71.61 领先；统一多模态；视频/视觉文档检索强 | 开源 |
| 3 | **Ops-MM-embedding-v1-7B** | 阿里云 | text+image+video | 3584 维；与 OpenSearch 深度集成；MMEB 67.61 | API |
| 4 | **seed-1.6-embedding** | Seed（字节？） | 多模态 | MMEB-Image 77.78 最高 | 待确认 |
| 5 | **UniME-LLaVA-OneVision-7B** | 深度赋智 | text+image | MMEB 曾第一；336×336 即可；AAAI 2026 | 开源 |
| 6 | **BGE M3-Embedding** | 智源 BAAI | 仅文本 | 密集+稀疏+多向量三合一；8192 token；100+ 语言 | 本地 |
| 7 | **BriVL** | 智源 BAAI | text+image | 中文图文预训练鼻祖；图文检索强 | 开源 |
| 8 | **EVA-CLIP 系列** | 智源 BAAI | text+image | 18B 零样本 80.7%；最强开源 CLIP；支持视频/3D | 开源 |
| 9 | **Kimi-VL / K2** | 月之暗面 | 多模态 VLM | 16B MoE / K2 万亿级；text+image+doc；**无专用 embedding API**；若后续推出可关注 | API（对话） |
| 10 | **百川 Embedding** | 百川智能 | 仅文本 | 1024 维；C-MTEB 中文第一 | API |

---

## 5. 国外主流模型（10 个）

| # | 模型 | 厂商 | 模态 | 核心关键 | 部署 |
|---|------|------|------|----------|------|
| 1 | **Gemini Embedding 2** | Google | text+image+video+audio+doc | 原生多模态；3072 维 MRL；8K token；100+ 语言 | API only |
| 2 | **Voyage multimodal-3.5** | Voyage AI | text+image+video | 统一 Transformer；视频检索优于 Cohere/Google；无 modality gap | API |
| 3 | **Cohere Embed v4** | Cohere | text+image | 企业级；多语言；检索优化变体；压缩选项 | API only |
| 4 | **OpenAI text-embedding-3** | OpenAI | 仅文本 | large 3072 维；MTEB 64.6%；dimensions 可缩短 | API |
| 5 | **CLIP (ViT-L/14)** | OpenAI | text+image | 400M 图文对；零样本强；开源可微调 | 本地 |
| 6 | **SigLIP** | Google | text+image | Sigmoid 损失优于对比；细粒度视觉理解强 | 开源 |
| 7 | **ImageBind** | Meta | 6 模态 | text/image/audio/视频/深度/热力；统一空间 | 开源 |
| 8 | **Google Multimodal Embedding 001** | Google | text+image | 旧版多模态；Vertex AI | API |
| 9 | **Nomic Embed** | Nomic | 文本 | 开源；MTEB 强；可微调 | 本地 |
| 10 | **E5-mistral-7b** | 微软/社区 | 仅文本 | 多语言检索基准；7B 参数 | 开源 |

---

## 6. 与本项目的关联与建议

### 6.1 核心结论

- **PCB graph**：所有模型均无原生支持，需保留 GraphEncoder 做投影对齐。
- **与现有栈最顺滑**：Qwen3-VL-Embedding-2B（同源、本地、多模态）。
- **云端多模态**：Gemini、Voyage、Cohere 适合 RAG/检索 PoC，需评估成本与网络依赖。

### 6.2 短期（维持当前路线）

1. 继续以 **Qwen3-Embedding + GraphEncoder** 为主，geometry-only 已形成 126 板基线
2. 暂不引入云端多模态 API，避免依赖与成本

### 6.3 中期（试验性评估）

1. **优先 PoC**：Qwen3-VL-Embedding-2B，对 PCB 渲染图做 image embedding，与 graph-text 检索对比
2. **可选**：Gemini Embedding 2 / Voyage 小规模调用，评估云端多模态效果与成本

### 6.4 长期（视需求而定）

1. 若 RAG / 跨模态检索成为核心：评估 Qwen3-VL-Embedding + GraphEncoder 投影的混合方案
2. 若强调离线：优先 **CLIP/SigLIP + 自研 GraphEncoder** 本地多模态

---

## 7. 参考

- [Gemini Embedding 2](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-embedding-2/)
- [Qwen3-VL-Embedding](https://huggingface.co/Qwen/Qwen3-VL-Embedding-2B)
- [MMEB 排行榜](https://huggingface.co/spaces/TIGER-Lab/MMEB-Leaderboard)
- [Voyage multimodal-3.5](https://blog.voyageai.com/2026/01/15/voyage-multimodal-3-5/)
- 本项目：`docs/training/qwen_embedding_runbook_v1.md`、`docs/training/experiment_results_260312.md`
