# 技术文档站（CineMaker + OpenClaw）

本站 GitHub Pages / Docsify **仅展示**两个公开仓的文档镜像：

- [CineMaker-AI-Platform · `docs/guides`](https://github.com/chenweidu666/CineMaker-AI-Platform/tree/main/docs/guides)
- [OpenClaw-Deployment-Issues](https://github.com/chenweidu666/OpenClaw-Deployment-Issues)

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-0366d6?logo=github)](https://chenweidu666.github.io/chenwei-tech-docs/#/)

## 入口

| 说明 | 链接 |
|------|------|
| 文档首页（目录表） | [docs/README.md](./docs/README.md) |
| 在线阅读 | <https://chenweidu666.github.io/chenwei-tech-docs/#/> |
| 镜像目录说明 | [docs/projects/README.md](./docs/projects/README.md) |

## 仓库结构

```
├── docs/
│   ├── README.md                 # 站点首页（仅两仓导航）
│   ├── projects/                 # 上游 .md 镜像（仅 CineMaker guides + OpenClaw）
│   └── 01_～05_*                 # 历史笔记：保留在仓库，不进入侧栏
├── scripts/                      # fetch_github_docs.py · gen_sidebar.py
├── index.html                    # Docsify
├── _sidebar.md                   # 由脚本生成
└── README.md                     # 本文件
```

## 同步上游

```bash
python3 scripts/fetch_github_docs.py
bash scripts/regen_sidebar.sh
```

## 联系

- 📧 [514351508@qq.com](mailto:514351508@qq.com)
- 💼 <https://chenweidu666.github.io/Resume-Site/>
- 🌐 [github.com/chenweidu666](https://github.com/chenweidu666)
