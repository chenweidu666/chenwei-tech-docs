# 参与与编辑说明

- **站内可见内容**：侧栏与 [docs/README.md](./docs/README.md) 仅收录 **CineMaker-AI-Platform（`README` + `docs/guides`）** 与 **OpenClaw-Deployment-Issues（`README` + `docs/`）**，由 [scripts/gen_sidebar.py](./scripts/gen_sidebar.py) 白名单控制。
- **上游镜像**：勿长期手工改 `docs/projects/` 下同步文件；在源仓库修改后执行根目录 `python3 scripts/fetch_github_docs.py`，再 `bash scripts/regen_sidebar.sh`。
- **历史笔记**：`docs/01_`～`05_` 等目录保留在仓库但**不参与**侧栏；若需纳入站点，须改 `gen_sidebar.py` 白名单并更新首页说明。
- **Docsify 首页**：`index.html` 中 `homepage: docs/README.md`。
