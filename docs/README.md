# 技术文档站（精简入口）

本站 **仅公开展示** 下列两个 GitHub 仓库的 Markdown 镜像（由脚本从上游拉取）。  
`docs/` 下 `01_`～`05_` 等历史个人笔记仍保留在仓库中，**不进入侧栏与本文导航**，如需请直接在仓库内打开文件。

---

## CineMaker-AI-Platform · 产品指南

**上游**：[github.com/chenweidu666/CineMaker-AI-Platform](https://github.com/chenweidu666/CineMaker-AI-Platform) · 目录 [`docs/guides`](https://github.com/chenweidu666/CineMaker-AI-Platform/tree/main/docs/guides)

| 文档 | 本站路径 |
|------|----------|
| 仓库说明 | [projects/CineMaker-AI-Platform/README.md](./projects/CineMaker-AI-Platform/README.md) |
| 产品工作流 | [projects/CineMaker-AI-Platform/docs/guides/1_产品工作流.md](./projects/CineMaker-AI-Platform/docs/guides/1_产品工作流.md) |
| 技术架构 | [projects/CineMaker-AI-Platform/docs/guides/2_技术架构.md](./projects/CineMaker-AI-Platform/docs/guides/2_技术架构.md) |
| 提示词指南 | [projects/CineMaker-AI-Platform/docs/guides/3_提示词指南.md](./projects/CineMaker-AI-Platform/docs/guides/3_提示词指南.md) |
| 火山引擎 API 申请 | [projects/CineMaker-AI-Platform/docs/guides/4_火山引擎API申请指南.md](./projects/CineMaker-AI-Platform/docs/guides/4_火山引擎API申请指南.md) |

---

## OpenClaw-Deployment-Issues · 部署文库

**上游**：[github.com/chenweidu666/OpenClaw-Deployment-Issues](https://github.com/chenweidu666/OpenClaw-Deployment-Issues)

| 文档 | 本站路径 |
|------|----------|
| 仓库首页 README | [projects/OpenClaw-Deployment-Issues/README.md](./projects/OpenClaw-Deployment-Issues/README.md) |
| 环境构建与 API 配置 | [projects/OpenClaw-Deployment-Issues/docs/1_OpenClaw_Deploy_Guide.md](./projects/OpenClaw-Deployment-Issues/docs/1_OpenClaw_Deploy_Guide.md) |
| 踩坑记录与实践 | [projects/OpenClaw-Deployment-Issues/docs/2_OpenClaw_Pitfalls_and_Practices.md](./projects/OpenClaw-Deployment-Issues/docs/2_OpenClaw_Pitfalls_and_Practices.md) |
| Nginx / WebUI | [projects/OpenClaw-Deployment-Issues/docs/3_OpenClaw_Nginx_WebUI.md](./projects/OpenClaw-Deployment-Issues/docs/3_OpenClaw_Nginx_WebUI.md) |
| Workspace | [projects/OpenClaw-Deployment-Issues/docs/4_OpenClaw_Workspace.md](./projects/OpenClaw-Deployment-Issues/docs/4_OpenClaw_Workspace.md) |
| Skills | [projects/OpenClaw-Deployment-Issues/docs/5_OpenClaw_Skills.md](./projects/OpenClaw-Deployment-Issues/docs/5_OpenClaw_Skills.md) |
| 原生工具插件 | [projects/OpenClaw-Deployment-Issues/docs/6_OpenClaw_Native_Tools_Plugin.md](./projects/OpenClaw-Deployment-Issues/docs/6_OpenClaw_Native_Tools_Plugin.md) |
| 安全加固与复盘 | [projects/OpenClaw-Deployment-Issues/docs/7_OpenClaw_Security_and_Retrospective.md](./projects/OpenClaw-Deployment-Issues/docs/7_OpenClaw_Security_and_Retrospective.md) |

---

## 更新本站镜像

在仓库**根目录**（`3_技术文档`）执行：

```bash
python3 scripts/fetch_github_docs.py
bash scripts/regen_sidebar.sh
```

---

## 在线阅读

- **Docsify**：<https://chenweidu666.github.io/chenwei-tech-docs/#/>

---

## 联系

- 📧 [514351508@qq.com](mailto:514351508@qq.com)
- 💼 简历：<https://chenweidu666.github.io/Resume-Site/>
- 🌐 GitHub：[github.com/chenweidu666](https://github.com/chenweidu666)

---

## 许可证

本文档站聚合内容以**各上游仓库许可**为准；本站说明文字沿用 **CC BY-NC-SA 4.0**（署名 - 非商业性使用 - 相同方式共享）。
