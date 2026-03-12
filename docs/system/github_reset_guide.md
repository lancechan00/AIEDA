# GitHub 重置提交指南（清除历史中的敏感信息）

若仓库历史中曾提交过含个人路径或 token 的文件，需要重写历史并强制推送，确保 GitHub 仓库不再包含任何个人信息。

## 方案一：软重置 + 强制推送

适用于：敏感文件已从工作区删除，.gitignore 已更新，仅需提交当前状态并覆盖远端。

```powershell
git add .
git status   # 确认无 .env、data/embedding/、outputs/ 等
git commit -m "chore: 脱敏，更新 gitignore"
git push --force-with-lease origin main
```

`--force-with-lease` 比 `--force` 更安全，会检查远端是否有他人新提交。

---

## 方案二：BFG Repo-Cleaner 清除历史

适用于：历史中已提交过 `.env`、含路径的 JSON 等，需从所有提交中删除。

1. **安装 BFG**：https://rtyley.github.io/bfg-repo-cleaner/

2. **备份并克隆裸仓库**
   ```powershell
   cd <项目父目录>
   cp -r AIEDA AIEDA_backup
   cd AIEDA
   git clone --mirror . ../AIEDA-mirror
   cd ../AIEDA-mirror
   ```

3. **删除敏感文件**
   ```powershell
   bfg --delete-files .env
   ```

4. **执行 gc 并推回**
   ```powershell
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   cd ..
   cd AIEDA
   git remote set-url origin <你的GitHub仓库URL>
   git push --force origin main
   ```

---

## 方案三：全新初始化（丢失历史）

若不在意提交历史，可完全重置：

```powershell
cd <项目根目录>

Remove-Item -Recurse -Force .git
git init
git add .
git commit -m "chore: 开源版本，脱敏"
git remote add origin https://github.com/<你的用户名>/AIEDA.git
git branch -M main
git push -u origin main --force
```

---

## 推送前检查

- [ ] `.env` 未提交
- [ ] `data/embedding/raw/`、`parsed/`、`graph_text_pairs/` 未提交
- [ ] `outputs/` 未提交
- [ ] 无 token 字符串（`ghp_`、`github_pat_` 等）
- [ ] 无个人路径（用 `git grep` 搜索你的用户名、盘符等关键词）
