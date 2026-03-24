#!/usr/bin/env python3
"""
将 docs 下 Markdown 标题改为文档内层级编号（与文件名篇号无关）：
  # 1. 标题
  ## 1.1. 标题
  ### 1.1.1. 标题
  #### 1.1.1.1. 标题
- 按标题层级（# 数量）维护计数；跳过围栏代码块。
- 自动剥除标题上已有的「数字.」前缀或「一、」等旧编号后再套新编号。
- 全篇仅保留**第一个** ATX H1（`# `）；其后出现的 `# ` 一律先降为 `## `，再参与编号（避免附录里出现与篇首平级的 `# 2.`）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def demote_extra_h1(text: str) -> str:
    """第一个 `# 标题` 保留；之后所有 `# 标题` 改为 `## 标题`（不在代码围栏内）。"""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_code = False
    first_h1 = False
    for line in lines:
        st = line.rstrip("\n\r").strip()
        if st.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue
        raw = line.rstrip("\n\r")
        if raw.startswith("# ") and not raw.startswith("##"):
            ending = "\n" if line.endswith("\n") else ""
            if first_h1:
                out.append(f"## {raw[2:]}{ending}")
            else:
                first_h1 = True
                out.append(line)
            continue
        out.append(line)
    return "".join(out)


def strip_leading_numbering(title: str) -> str:
    t = title.strip()
    while True:
        m = re.match(r"^(\d+\.)+\s*", t)
        if not m:
            break
        t = t[m.end() :].strip()
    t = re.sub(r"^[一二三四五六七八九十]+[、,]\s*", "", t)
    return t.strip()


def heading_level(line: str) -> int:
    m = HEADING_RE.match(line.rstrip("\n\r"))
    return len(m.group(1)) if m else 0


def number_for_level(h: list[int], level: int) -> str:
    parts = [str(h[i]) for i in range(level)]
    return ".".join(parts) + "."


def process_markdown(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_code = False
    h = [0, 0, 0, 0, 0, 0]  # h[0]=h1 .. h[5]=h6

    for line in lines:
        st = line.rstrip("\n\r").strip()
        if st.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue

        raw = line.rstrip("\n\r")
        level = heading_level(raw)
        if level == 0:
            out.append(line)
            continue

        m = HEADING_RE.match(raw)
        assert m
        hashes = m.group(1)
        body = m.group(2)
        title = strip_leading_numbering(body)
        idx = level - 1

        # 补齐缺失的上级（例如文首直接从 ## 开始）
        for j in range(idx):
            if h[j] == 0:
                h[j] = 1

        h[idx] += 1
        for j in range(idx + 1, 6):
            h[j] = 0

        num = number_for_level(h, level)
        ending = "\n" if line.endswith("\n") else ""
        out.append(f"{hashes} {num} {title}{ending}")

    return "".join(out)


def main() -> int:
    changed = 0
    for path in sorted(DOCS.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        new = process_markdown(demote_extra_h1(raw))
        if new != raw:
            path.write_text(new, encoding="utf-8")
            print(f"OK {path.relative_to(DOCS)}")
            changed += 1
    print(f"Done. Updated {changed} files.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
