# KiCad 数据采集规范（v1）

## 目标

为 `Qwen3-Embedding-0.6B` 的第一阶段训练建立稳定数据入口：

- 可追溯：每个样本都能追溯到具体工程目录和源文件。
- 可扩展：支持从 30 个项目平滑扩展到 100+ 项目。
- 可审核：避免 license 和质量不达标数据混入训练集。

## 目录结构

推荐目录采用三层：

```text
data/
  embedding/
    raw/                    # 原始 KiCad 工程
      <project_name>/
        *.kicad_pcb
        *.kicad_sch
        *.net (optional)
    parsed/                 # parse 后的 board json
      <project_name>.json
    graph_text_pairs/       # build-pairs 后的训练样本
      train/
      val/
      test/
```

## 数据源筛选标准

最小必需条件：

1. 项目目录内至少包含一个 `.kicad_pcb`。
2. 允许没有 `.net`，但优先保留有 netlist 的工程。
3. 工程可被 `apps/data_cli.py parse` 正常解析。

建议加分条件：

- 同时含 `.kicad_sch` 和 `.kicad_pcb`。
- 覆盖不同板型（电源、控制、传感、接口）。
- 有清晰的网络命名（例如 GND/VCC/SCL/SDA）。

### GitHub 采集附加规则（试点 20-30）

1. 仅采公开仓库。
2. 许可证优先：`MIT / Apache-2.0 / BSD* / CERN-OHL-P-2.0`。
3. 排除纯库仓和模板仓（如 `library / footprint / symbol / template`）。
4. 必须命中 `.kicad_pcb`。
5. 最终以白名单 manifest 落盘，不直接全量抓取。

## 审计流程

在采集后先执行：

```powershell
python .\apps\data_cli.py audit-sources --source-dir .\data\embedding\raw --output-file .\data\embedding\raw_manifest.json
```

GitHub 发现与下载流程：

```powershell
python .\scripts\github_kicad_discovery.py --output-file .\data\embedding\github_whitelist.json --target-count 30 --max-pages 3 --per-page 20
python .\scripts\github_kicad_download.py --manifest .\data\embedding\github_whitelist.json --output-dir .\data\embedding\raw --limit 30
python .\apps\data_cli.py audit-sources --source-dir .\data\embedding\raw --output-file .\data\embedding\raw_manifest.json
```

产物 `raw_manifest.json` 用于记录：

- 可用项目总量
- 每个项目的 `pcb/sch/net` 文件路径
- 项目是否满足最小训练条件

## 版本化建议

- 每次新增数据源时保留 manifest 快照（例如 `raw_manifest_2026-03-12.json`）。
- 同时保留 `github_whitelist_YYYYMMDD.json` 与 `download_summary.json`，用于许可证追溯。
- 如果后续引入远端训练，优先将 `parsed/` 和 `graph_text_pairs/` 打包同步，避免远端重复 parse。
