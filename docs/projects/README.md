# 开源文档镜像（本站仅二仓）

本目录由 `scripts/fetch_github_docs.py` 从 GitHub **仅同步 .md**，无业务代码；**正文以上游为准**。

| 目录 | 仓库 | 同步范围 |
|------|------|----------|
| [CineMaker-AI-Platform](./CineMaker-AI-Platform/README.md) | [CineMaker-AI-Platform](https://github.com/chenweidu666/CineMaker-AI-Platform) | 根 `README.md` + [`docs/guides/`](https://github.com/chenweidu666/CineMaker-AI-Platform/tree/main/docs/guides) |
| [OpenClaw-Deployment-Issues](./OpenClaw-Deployment-Issues/README.md) | [OpenClaw-Deployment-Issues](https://github.com/chenweidu666/OpenClaw-Deployment-Issues) | 根 `README.md` + `docs/*.md` |

更新命令（在 `3_技术文档` 根目录）：

```bash
python3 scripts/fetch_github_docs.py
bash scripts/regen_sidebar.sh
```
