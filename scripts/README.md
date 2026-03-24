# 站点维护（GitHub Pages / Docsify）

本站根目录即 **`3_技术文档`**。

- **侧栏**：由仓库根目录 **`_sidebar.md` 手工维护**（七章主线 + 项目总结）。`gen_sidebar.py` 已改为**不覆盖**该文件，仅提示说明；勿依赖 `regen_sidebar.sh` 生成全站侧栏。
- **正文版式**：篇名 div + `# N.` / `## N.M.` 等见 **`.cursor/rules/doc-heading-numbering.mdc`**。批量对齐执行：`python3 scripts/apply_doc_format.py`（勿再跑旧的 `normalize_headings.py` / `renumber_headings.py`）。
- **拉取上游镜像**：`fetch_github_docs.py` 同步 **CineMaker-AI-Platform** 与 **OpenClaw-Deployment-Issues** 的 Markdown 到 **`../归档/from_3_技术文档/projects/`**，并同步 CineMaker **`docs/guides/images/`**（截图与演示视频）到 **`docs/07_项目总结/guides/images/`** 与同路径归档。仅补图时可：`python3 scripts/fetch_github_docs.py --cinemaker-images-only`（含约 11MB 的 `episode-1_compressed.mov`，弱网易超时；可对该文件用 `curl -C -` 断点续传至 `docs/07_项目总结/guides/images/`）。Docsify 第七章正文在 **`docs/07_项目总结/7.1_CineMaker/`** 与 **`docs/07_项目总结/7.2_OpenClaw-Deployment-Issues/`**，需与归档或上游保持一致时自行对齐。

**从 GitHub 拉取镜像**（不克隆代码）：

```bash
python3 scripts/fetch_github_docs.py
```

新增或调整章节时，请**直接编辑 `_sidebar.md`** 与对应 `docs/` 下 `.md`，然后提交推送。

远程仓库：`git@github.com:chenweidu666/chenwei-tech-docs.git`  
线上阅读：<https://chenweidu666.github.io/chenwei-tech-docs/>
