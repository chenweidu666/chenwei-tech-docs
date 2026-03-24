#!/usr/bin/env python3
"""
将 docs/**/*.md 正文标题改为「# 篇号.」「## 篇号.节.」「### 篇号.节.小节.」形式。
- 跳过围栏代码块内行。
- 遇到「## 附录」「## 📎」视为附录入口：仅将该行纳入篇号，其后原文不改。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"

CN = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}

FILENAME_RE = re.compile(r"^(\d+\.\d+)_.+\.md$")
APPENDIX_RE = re.compile(r"^##\s*(附录[：:]|📎)")
H2_CN_RE = re.compile(r"^##\s*([一二三四五六七八九十]+)[、,]\s*(.*)$")
H3_NUM_RE = re.compile(r"^###\s*(\d+)\.(\d+)\s+(.*)$")
H4_NUM3_RE = re.compile(r"^####\s*(\d+)\.(\d+)\.(\d+)\s+(.*)$")
H1_RE = re.compile(r"^#\s+(\d+\.\d+)\.?\s+(.+)$")


def process_markdown(text: str, doc_id: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_code = False
    appendix = False
    current_h2 = 0
    last_h3_p = 0
    last_h3_q = 0
    h4_counter = 0

    def flush_line(raw: str) -> None:
        out.append(raw)

    for line in lines:
        s = line.rstrip("\n\r")
        st = s.strip()

        if st.startswith("```"):
            in_code = not in_code
            flush_line(line)
            continue
        if in_code:
            flush_line(line)
            continue

        if appendix:
            flush_line(line)
            continue

        if APPENDIX_RE.match(s):
            appendix = True
            current_h2 += 1
            tit = re.sub(r"^##\s*", "", s).strip()
            ending = "\n" if line.endswith("\n") else ""
            flush_line(f"## {doc_id}.{current_h2}. {tit}{ending}")
            continue

        # H1
        if s.startswith("# ") and not s.startswith("##"):
            m = H1_RE.match(s)
            if m:
                title = m.group(2).strip()
                flush_line(f"# {doc_id}. {title}\n")
            else:
                flush_line(line)
            continue

        m2 = H2_CN_RE.match(s)
        if m2:
            ch = m2.group(1)
            title = m2.group(2).strip()
            current_h2 = CN[ch]
            h4_counter = 0
            last_h3_p = 0
            last_h3_q = 0
            flush_line(f"## {doc_id}.{current_h2}. {title}\n")
            continue

        m3 = H3_NUM_RE.match(s)
        if m3:
            p, q, title = int(m3.group(1)), int(m3.group(2)), m3.group(3).strip()
            last_h3_p, last_h3_q = p, q
            h4_counter = 0
            flush_line(f"### {doc_id}.{p}.{q}. {title}\n")
            continue

        m4 = H4_NUM3_RE.match(s)
        if m4:
            a, b, c, title = int(m4.group(1)), int(m4.group(2)), int(m4.group(3)), m4.group(4).strip()
            flush_line(f"#### {doc_id}.{a}.{b}.{c}. {title}\n")
            continue

        if s.startswith("#### ") and not s.startswith("#####"):
            h4_counter += 1
            inner = s[5:].strip()
            if last_h3_p and last_h3_q:
                flush_line(
                    f"#### {doc_id}.{last_h3_p}.{last_h3_q}.{h4_counter}. {inner}\n"
                )
            else:
                flush_line(line)
            continue

        flush_line(line)

    return "".join(out)


def process_readme(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines:
        return text
    first = lines[0].rstrip("\n\r")
    if first.startswith("# ") and not first.startswith("# 1."):
        rest = first[2:].strip()
        lines[0] = f"# 1. {rest}\n"
    return "".join(lines)


def main() -> int:
    changed = 0
    for path in sorted(DOCS.rglob("*.md")):
        if path.name == "README.md":
            raw = path.read_text(encoding="utf-8")
            new = process_readme(raw)
            if new != raw:
                path.write_text(new, encoding="utf-8")
                print(f"OK README {path.relative_to(DOCS)}")
                changed += 1
            continue

        m = FILENAME_RE.match(path.name)
        if not m:
            continue
        doc_id = m.group(1)
        raw = path.read_text(encoding="utf-8")
        new = process_markdown(raw, doc_id)
        if new != raw:
            path.write_text(new, encoding="utf-8")
            print(f"OK {path.relative_to(DOCS)}")
            changed += 1
    print(f"Done. Updated {changed} files.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
