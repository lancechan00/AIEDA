# LocalRouteChoice-Lite 数据扩充指南 (v1)

## 1. 优先原则

扩数时优先：**板级多样性 > 标签质量 > 样本数量**。

同一块板上切出更多窗口，对泛化帮助有限；增加不同板子的样本，才能提升跨板泛化。

## 2. 板级多样性 (Board Diversity)

- **优先增加 board 数量**，而非同一板上更多 segment。
- 保持 `board-level split`：同一块板子的样本不能跨 train/val/test。
- 扩充时尽量覆盖：不同层数 (2/4)、不同密度、不同设计风格、不同领域（消费/工控/开源）。

## 3. 标签与样本质量

- **审计类别分布**：对 `up / down / left / right / stop` 做统计，检查偏斜。
- **弱标注质量**：确认“真实下一段方向”能被局部窗口充分决定，避免模糊样本。
- **窗口构造**：检查起点 marker、目标 marker、同 net 上下文的正确性。

## 4. 扩充流程建议

1. 用 `scripts/github_kicad_discovery.py` 扩展白名单，增加更多项目。
2. 用 `scripts/github_kicad_download.py` 或 `run_kicad_github_pipeline.ps1` 拉取。
3. 用 `apps/data_cli.py build` 重新构建 LocalRouteChoice-Lite，保持 `--seed` 一致以便复现。
4. 构建后审计 `dataset_summary.json` 的 split 分布与 label 分布。

## 5. 参考

- `docs/data/kicad_dataset_plan.md`：数据管道整体设计
- `docs/training/local_route_choice_runbook_v1.md`：训练与评估口径
