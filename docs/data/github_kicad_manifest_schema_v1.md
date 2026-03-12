# GitHub KiCad Manifest 格式（v1）

## 1. discovery manifest

由 `scripts/github_kicad_discovery.py` 生成，核心字段：

- `policy`: 本次筛选策略（license 白名单、排除关键词、查询语句）
- `stats`: 检索统计（examined / included / excluded）
- `included_repositories`: 通过筛选的仓库清单
- `excluded_repositories`: 未通过筛选的仓库及原因

`included_repositories` 单项字段：

- `full_name`: `owner/repo`
- `html_url`: 仓库地址
- `default_branch`
- `license_spdx`
- `has_kicad_pcb`
- `has_kicad_sch`
- `has_net`
- `is_library_like`
- `is_permissive_license`
- `include_reason`

## 2. download summary

由 `scripts/github_kicad_download.py` 生成，输出到 `raw/download_summary.json`。

核心字段（路径均为相对路径，便于开源可移植）：

- `manifest`: 使用的 discovery manifest 路径（相对于 output_dir）
- `output_dir`: 固定为 `"."`（summary 位于 raw 目录内）
- `selected_repositories`: 选中仓库数
- `downloaded_projects`: 实际落盘项目数
- `repositories`: 每个仓库对应的项目目录清单

## 3. 推荐命令

```powershell
python .\scripts\github_kicad_discovery.py --output-file .\data\embedding\github_whitelist.json --target-count 30 --max-pages 3 --per-page 20
python .\scripts\github_kicad_download.py --manifest .\data\embedding\github_whitelist.json --output-dir .\data\embedding\raw --limit 30
```

如果你设置了 `GITHUB_TOKEN`，脚本会自动使用 token 以提升 API 额度。
