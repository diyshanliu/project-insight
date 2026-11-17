#!/usr/bin/env python3
"""Validate the expected Project Insight Markdown deliverables."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

EXPECTED = [
    "README.md",
    "00_项目总览.md",
    "01_目录结构与文件功能索引.md",
    "02_系统架构与模块关系.md",
    "03_核心执行流程与数据流.md",
    "04_核心算法与技术原理.md",
    "05_项目快速学习指南.md",
    "06_面试知识点总结.md",
    "07_项目面试题.md",
    "08_项目面试题答案.md",
    "09_项目思维导图.md",
    "10_分析覆盖与待确认项.md",
]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Project Insight documentation completeness.")
    parser.add_argument("docs_dir", nargs="?", default="docs/project-insight")
    parser.add_argument("--strict", action="store_true", help="Treat broken relative links as errors")
    args = parser.parse_args()
    docs = Path(args.docs_dir).expanduser().resolve()
    if not docs.is_dir():
        print(f"ERROR: documentation directory does not exist: {docs}")
        return 2

    errors = []
    warnings = []
    for name in EXPECTED:
        path = docs / name
        if not path.is_file():
            errors.append(f"Missing required file: {name}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text.strip()) < 80:
            errors.append(f"File is empty or too short: {name}")
        fence_count = sum(1 for line in text.splitlines() if line.strip().startswith("```"))
        if fence_count % 2:
            errors.append(f"Unclosed Markdown code fence: {name}")
        if "```mermaid" in text and "```" not in text:
            errors.append(f"Mermaid block may be malformed: {name}")
        for target in LINK_RE.findall(text):
            target = target.strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local_target = target.split("#", 1)[0]
            if not local_target:
                continue
            resolved = (path.parent / local_target).resolve()
            if not resolved.exists():
                warnings.append(f"Broken relative link in {name}: {target}")

    if (docs / "09_项目思维导图.md").is_file():
        mindmap = (docs / "09_项目思维导图.md").read_text(encoding="utf-8", errors="replace")
        if "mindmap" not in mindmap and "flowchart" not in mindmap:
            warnings.append("Mind map document contains no Mermaid mindmap/flowchart block.")

    print(f"Documentation directory: {docs}")
    print(f"Required documents: {len(EXPECTED)}")
    for message in errors:
        print("ERROR:", message)
    for message in warnings:
        print("WARNING:", message)
    if not errors and not (args.strict and warnings):
        print("Validation passed.")
        return 0
    print("Validation failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
