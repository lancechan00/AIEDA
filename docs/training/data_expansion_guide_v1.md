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

1. 用 `scripts/github_kicad_discovery.py` 扩展白名单，增加更多项目；或按 5.5 手动追加。
2. 运行扩数脚本一键执行下载、解析、构建：`.\scripts\run_board_expansion.ps1`
3. 或手动：`github_kicad_download.py` → `apps/data_cli.py parse` → `apps/data_cli.py build`
4. 构建后审计 `dataset_summary.json` 的 split 分布与 label 分布；运行 `scripts/audit_local_route_choice_dataset.py`。
5. 将本轮 board 数、样本数、test acc 记录到 [expansion_log.md](expansion_log.md)，跟踪收益曲线。

## 5. 数据源参考（快速扩数）

### 5.1 KiCad 官方示例（GitLab）

- **位置**：<https://gitlab.com/kicad/code/kicad/-/tree/master/demos>
- **获取**：`git clone --depth 1 https://gitlab.com/kicad/code/kicad.git`，取 `kicad/demos/` 下各子目录（如 `pic_programmer`、`jetson-agx-thor-baseboard`、`tiny_tapeout` 等）
- **说明**：非 GitHub 格式，需单独解析后并入 `data/embedding/parsed`，或写脚本转为与 GitHub 相同结构

### 5.2 公开 Open Hardware 精选（GitHub）

| 来源 | 说明 |
|------|------|
| [aeonSolutions/PCB-Prototyping-Catalogue](https://github.com/aeonSolutions/PCB-Prototyping-Catalogue) | 78 个 KiCad 项目，多为智能设备/AI 硬件 |
| [synthetos/KicadExample](https://github.com/synthetos/KicadExample) | 入门示例板 |
| [aspro648/KiCad-Hello-World](https://github.com/aspro648/KiCad-Hello-World) | 1 小时快速 PCB 示例 |
| [sparkfun](https://github.com/sparkfun) | 搜索含 `kicad` 的仓库 |
| [splitflap](https://github.com/scottbez1/splitflap) | DIY 翻牌显示，含 KiCad PCB |

### 5.3 已知能解析出 track 的仓库（当前在用）

`data/local_route_choice_lite_github/dataset_summary.json` 中的 `boards` 即为已验证可解析的板子。白名单中已包含的例如：

- `StuckAtPrototype/Racer`
- `atopile/atopile`
- `yaqwsx/KiKit`、`yaqwsx/PcbDraw`
- `fossasia/pslab-hardware`
- `soulscircuit/pilet`
- `Nicholas-L-Johnson/flip-card`
- `skuep/AIOC`、`yaqwsx/PcbDraw/examples/resources` 等

可在此基础上，从 5.2 中挑选新仓库，加入 `data/embedding/github_whitelist_extra.json`，再合并进主白名单。

### 5.4 手动下载（无需写进白名单）

**你手动下载的 KiCad 官方示例 / Open Hardware 精选**：

1. 放进 `data/embedding/raw/`，每个工程一个子目录，目录内需含 `.kicad_pcb` 文件
2. 执行 parse：`python apps/data_cli.py parse --source-dir data/embedding/raw --output-dir data/embedding/parsed --parallel 4`
3. 执行 build：`python apps/data_cli.py build --parsed-dir data/embedding/parsed --output-dir data/local_route_choice_lite_github`

**白名单 (github_whitelist.json) 仅用于 GitHub 自动下载**：名单由脚本维护，手动下载的工程**不需要**加入白名单。

### 5.5 手动追加 GitHub 白名单（可选）

在 `data/embedding/github_whitelist.json` 的 `included_repositories` 中加入条目，格式：

```json
{
  "full_name": "owner/repo",
  "html_url": "https://github.com/owner/repo",
  "default_branch": "main",
  "license_spdx": "MIT"
}
```

然后运行 `github_kicad_download.py` 拉取，`parse` 解析，`build` 构建 LocalRouteChoice。

## 6. 参考

- `docs/data/kicad_dataset_plan.md`：数据管道整体设计
- `docs/training/local_route_choice_runbook_v1.md`：训练与评估口径
