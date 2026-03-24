#!/usr/bin/env python3
"""生成 Docsify 侧栏：仅包含 CineMaker（guides）与 OpenClaw 两仓镜像。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SIDEBAR = ROOT / "_sidebar.md"

# 与 fetch_github_docs.py 范围一致；站内不展示 docs/01_～05_ 等本地笔记
CINEMAKER_PREFIX = "docs/projects/CineMaker-AI-Platform/"
OPENCLAW_PREFIX = "docs/projects/OpenClaw-Deployment-Issues/"


def include_rel(rel: Path) -> bool:
    s = rel.as_posix()
    if s == f"{CINEMAKER_PREFIX}README.md":
        return True
    if s.startswith(f"{CINEMAKER_PREFIX}docs/guides/") and s.endswith(".md"):
        return True
    if s == f"{OPENCLAW_PREFIX}README.md":
        return True
    if s.startswith(f"{OPENCLAW_PREFIX}docs/") and s.endswith(".md"):
        return True
    return False


def bucket_key(rel: Path) -> str:
    s = rel.as_posix()
    if s.startswith(CINEMAKER_PREFIX):
        return "cinemaker"
    if s.startswith(OPENCLAW_PREFIX):
        return "openclaw"
    return ""


def sort_md_paths(items: list[Path]) -> list[Path]:
    def key(p: Path) -> tuple:
        name = p.name.lower()
        readme_first = 0 if name == "readme.md" else 1
        return (readme_first, p.as_posix())

    return sorted(items, key=key)


def main() -> None:
    if not DOCS.is_dir():
        raise SystemExit(f"缺少目录: {DOCS}")

    md_files: list[Path] = []
    for p in sorted(DOCS.rglob("*.md")):
        rel = p.relative_to(ROOT)
        if not include_rel(rel):
            continue
        md_files.append(rel)

    labels = {
        "cinemaker": "CineMaker-AI-Platform · 产品指南（docs/guides）",
        "openclaw": "OpenClaw-Deployment-Issues · 部署文库",
    }

    lines: list[str] = ["* [首页](/)", ""]

    buckets: dict[str, list[Path]] = {}
    for rel in md_files:
        key = bucket_key(rel)
        if key:
            buckets.setdefault(key, []).append(rel)

    for key in ("cinemaker", "openclaw"):
        items = buckets.get(key, [])
        if not items:
            continue
        lines.append(f"* **{labels[key]}**")
        for rel in sort_md_paths(items):
            title = rel.stem
            lines.append(f"  * [{title}]({rel.as_posix()})")
        lines.append("")

    SIDEBAR.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
