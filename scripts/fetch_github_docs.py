#!/usr/bin/env python3
"""
从 GitHub 仅拉取 Markdown 到归档目录 projects/（不克隆代码）。
镜像已迁出站点 docs/，默认写入 1_陈纬简历/归档/from_3_技术文档/projects/。
当前仅同步两个公开仓：
  - CineMaker-AI-Platform：根 README + docs/guides/（含 **docs/guides/images/** 资源）
  - OpenClaw-Deployment-Issues：根 README + docs/
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# 与侧栏七章主线分离：项目镜像归档到上级「归档」目录
OUT = ROOT.parent / "归档" / "from_3_技术文档" / "projects"
OWNER = "chenweidu666"
BRANCH = "main"
UA = "chenwei-tech-docs-fetch/1.0"


def http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def http_get_bytes(url: str, *, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def tree(owner: str, repo: str, branch: str = BRANCH) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    data = http_get_json(url)
    if data.get("truncated"):
        print(f"WARN: tree truncated for {repo}", file=sys.stderr)
    return data.get("tree", [])


def raw_url(repo: str, path: str, branch: str = BRANCH) -> str:
    from urllib.parse import quote

    parts = path.split("/")
    safe = "/".join(quote(p, safe="") for p in parts)
    return f"https://raw.githubusercontent.com/{OWNER}/{repo}/{branch}/{safe}"


def should_skip_path(path: str) -> bool:
    if path in ("CHANGELOG.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md"):
        return True
    return False


def _match_prefixes(path: str, prefixes: tuple[str, ...]) -> bool:
    for p in prefixes:
        pn = p.rstrip("/")
        if path == pn or path == p:
            return True
        if path.startswith(pn + "/"):
            return True
    return False


def sync_md_tree(
    repo: str,
    dest_name: str,
    *,
    path_prefixes: tuple[str, ...] | None = None,
) -> int:
    """下载仓库内 .md；path_prefixes 非空时只保留 README 或给定目录下文件。"""
    n = 0
    for item in tree(OWNER, repo):
        if item.get("type") != "blob":
            continue
        path = item["path"]
        if not path.endswith(".md"):
            continue
        if should_skip_path(path):
            continue
        if path_prefixes and not _match_prefixes(path, path_prefixes):
            continue
        url = raw_url(repo, path)
        target = OUT / dest_name / path
        target.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(3):
            try:
                body = http_get_bytes(url)
                note = (
                    f"<!-- 文档同步自 https://github.com/{OWNER}/{repo} 分支 {BRANCH} — 请勿手工与上游长期双轨编辑 -->\n\n"
                )
                text = body.decode("utf-8", errors="replace")
                if not text.lstrip().startswith("<!-- 文档同步自"):
                    text = note + text
                target.write_text(text, encoding="utf-8")
                print(f"OK {repo} {path} ({len(body)} B)")
                n += 1
                time.sleep(0.15)
                break
            except urllib.error.HTTPError as e:
                print(f"HTTP {e.code} {repo} {path}", file=sys.stderr)
                time.sleep(2 * (attempt + 1))
            except Exception as e:
                print(f"ERR {repo} {path}: {e}", file=sys.stderr)
                time.sleep(1)
    return n


def sync_cinemaker_guides() -> int:
    """CineMaker-AI-Platform：根 README + docs/guides/（与线上一致）。"""
    return sync_md_tree(
        "CineMaker-AI-Platform",
        "CineMaker-AI-Platform",
        path_prefixes=("README.md", "docs/guides"),
    )


def _github_contents_list(repo: str, content_path: str) -> list[dict]:
    url = f"https://api.github.com/repos/{OWNER}/{repo}/contents/{content_path}?ref={BRANCH}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.load(r)
    if not isinstance(data, list):
        return []
    return data


def sync_cinemaker_guide_images() -> int:
    """
    CineMaker docs/guides/images/* →
      1) docs/07_项目总结/guides/images/（与 7.1 下 md 中 ../guides/images/ 一致）
      2) 归档 projects/CineMaker-AI-Platform/docs/guides/images/
    """
    repo = "CineMaker-AI-Platform"
    remote_dir = "docs/guides/images"
    items = _github_contents_list(repo, remote_dir)
    dests = [
        ROOT / "docs" / "07_项目总结" / "guides" / "images",
        OUT / "CineMaker-AI-Platform" / "docs" / "guides" / "images",
    ]
    n = 0
    for item in items:
        if item.get("type") != "file":
            continue
        name = item.get("name") or ""
        dl = item.get("download_url")
        if not name or not dl:
            continue
        body = http_get_bytes(dl, timeout=600)
        for d in dests:
            d.mkdir(parents=True, exist_ok=True)
            (d / name).write_bytes(body)
        print(f"OK {repo} {remote_dir}/{name} ({len(body)} B)", flush=True)
        n += 1
        time.sleep(0.12)
    return n


def sync_openclaw() -> int:
    """OpenClaw-Deployment-Issues：README + docs/*.md"""
    return sync_md_tree(
        "OpenClaw-Deployment-Issues",
        "OpenClaw-Deployment-Issues",
        path_prefixes=("README.md", "docs"),
    )


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="从 GitHub 拉取 CineMaker / OpenClaw 文档与 CineMaker 配图")
    ap.add_argument(
        "--cinemaker-images-only",
        action="store_true",
        help="仅下载 CineMaker docs/guides/images/* 到 docs/07_项目总结/guides/images/ 与归档（不拉 md）",
    )
    args = ap.parse_args()
    if args.cinemaker_images_only:
        n = sync_cinemaker_guide_images()
        print(f"\nCineMaker guides/images：{n} 个文件。")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    total += sync_cinemaker_guides()
    total += sync_cinemaker_guide_images()
    total += sync_openclaw()
    print(f"\nMarkdown + CineMaker 图片合计处理约 {total} 个文件（含覆盖）。")


if __name__ == "__main__":
    main()
