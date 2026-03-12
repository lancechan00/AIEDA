# LocalRouteChoice-Lite 阶段决策清单

在基线稳定后，决定是否进入下一阶段（patch 生成闭环、多模态后端验证）时使用本清单。

## 基线门槛（需满足才进入下一阶段）

- [ ] **3 seeds** 下 test accuracy 波动可接受（如标准差 &lt; 10%），均值在预期范围
- [ ] **top_3** 稳定高于 85%
- [ ] 类别分布无明显塌陷，错误样本中非大量脏标注
- [ ] 新增板子后指标仍有提升空间，或扩数边际已明显变小

## 下一阶段选项

### A. Patch 生成闭环

- 将 LocalRouteChoice-Lite 作为已验证任务，接入 patch 生成 + Mock PatchFeedbackBridge
- 参考 [training_strategy_v1.md](training_strategy_v1.md) 第二阶段

### B. 多模态后端验证

- 接入 DeepSeek-VL / Janus 做同任务推理，验证技术栈适配性
- 在数据规模与基线稳定后再投入

### C. 继续扩数

- 若扩数仍有边际收益，优先继续板级多样性扩数
- 参考 [data_expansion_guide_v1.md](data_expansion_guide_v1.md)、[expansion_log.md](expansion_log.md)

## 当前状态（2026-03-12）

- 126 板基线：test acc 46.9%–65.6%（3 seeds），top_3 87.5%–92.2%
- 类别分布：train 中 right 偏高（约 48%），val/test 由单板决定
- **建议**：先做一轮扩数，观察收益曲线；若 top_3 稳定 &gt; 88%、acc 均值 &gt; 55%，再考虑进入 patch 闭环或多模态验证。
