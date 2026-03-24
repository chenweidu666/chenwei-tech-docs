# 站点维护（GitHub Pages / Docsify）

本站根目录即 **`3_技术文档`**。

- **拉取**：`fetch_github_docs.py` 仅同步 **CineMaker-AI-Platform**（`README` + `docs/guides`）与 **OpenClaw-Deployment-Issues**（`README` + `docs/`），写入 `docs/projects/`。
- **侧栏**：`gen_sidebar.py` 仅将上述路径写入 `_sidebar.md`；`docs/01_`～`05_` 等不参与侧栏。

**从 GitHub 拉取镜像**（不克隆代码）：

```bash
python3 scripts/fetch_github_docs.py
bash scripts/regen_sidebar.sh
```

新增或重命名 `.md` 后，刷新左侧导航：

```bash
cd /path/to/3_技术文档
bash scripts/regen_sidebar.sh
git add _sidebar.md && git commit -m "chore: 更新侧栏" && git push
```

远程仓库：`git@github.com:chenweidu666/chenwei-tech-docs.git`  
线上阅读：<https://chenweidu666.github.io/chenwei-tech-docs/>
