#!/usr/bin/env python3
"""Build a lightweight Python and C/C++ symbol index using the standard library.

Python is parsed with ast. C/C++ extraction is regex-based and intentionally
heuristic; use clangd, clang tooling, or ctags for compiler-accurate indexing.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "build", "dist", "install", "devel", "log", "target", "vendor", "third_party",
}
SUPPORTED = {".py", ".pyi", ".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".cu", ".cuh"}
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]')
NAMESPACE_RE = re.compile(r'^\s*namespace\s+([A-Za-z_]\w*)')
CLASS_RE = re.compile(r'^\s*(?:template\s*<[^;{}]+>\s*)?(?:class|struct)\s+([A-Za-z_]\w*)')
FUNCTION_RE = re.compile(
    r'^\s*(?:template\s*<[^;{}]+>\s*)?'
    r'(?:[\w:\<\>\~\*&,\[\]\s]+?\s+)?'
    r'([A-Za-z_~]\w*(?:::\w+)?|operator[^\s(]+)\s*'
    r'\([^;{}]*\)\s*(?:const\s*)?(?:noexcept(?:\([^)]*\))?\s*)?'
    r'(?:override\s*)?(?:final\s*)?(?:->\s*[\w:\<\>\*&\s]+)?\s*(?:\{|;)\s*$'
)
CONTROL_WORDS = {"if", "for", "while", "switch", "catch", "return", "sizeof", "alignof"}


def python_symbols(path: Path, rel: str) -> list[dict]:
    result = []
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=rel)
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        return [{"file": rel, "kind": "parse_error", "name": str(exc), "line": 0}]

    def visit(nodes, parents):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                result.append({
                    "file": rel, "kind": "class",
                    "name": ".".join(parents + [node.name]),
                    "line": node.lineno,
                })
                visit(node.body, parents + [node.name])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                try:
                    args = ast.unparse(node.args)
                except Exception:
                    args = "..."
                prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
                result.append({
                    "file": rel, "kind": "function",
                    "name": ".".join(parents + [node.name]),
                    "signature": f"{prefix}{node.name}({args})",
                    "line": node.lineno,
                })
                visit(node.body, parents + [node.name])

    visit(tree.body, [])
    return result


def cpp_symbols(path: Path, rel: str) -> list[dict]:
    result = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return [{"file": rel, "kind": "read_error", "name": str(exc), "line": 0}]

    for number, line in enumerate(lines, start=1):
        match = INCLUDE_RE.match(line)
        if match:
            result.append({"file": rel, "kind": "include", "name": match.group(1), "line": number})
            continue
        match = NAMESPACE_RE.match(line)
        if match:
            result.append({"file": rel, "kind": "namespace", "name": match.group(1), "line": number})
            continue
        match = CLASS_RE.match(line)
        if match:
            result.append({"file": rel, "kind": "class_or_struct", "name": match.group(1), "line": number})
            continue
        match = FUNCTION_RE.match(line)
        if match:
            name = match.group(1)
            if name not in CONTROL_WORDS:
                result.append({"file": rel, "kind": "function_candidate", "name": name, "signature_line": line.strip(), "line": number})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a lightweight Python/C++ symbol index.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--out", default=None, help="Markdown report path")
    parser.add_argument("--json-out", default=None, help="JSON report path")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"Not a directory: {root}")
    out_md = Path(args.out).expanduser().resolve() if args.out else root / "docs/project-insight/_analysis/symbols.md"
    out_json = Path(args.json_out).expanduser().resolve() if args.json_out else out_md.with_suffix(".json")
    symbols = []
    scanned = 0

    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_dirs = []
        for dirname in sorted(dirs):
            child_rel = (current_path / dirname).relative_to(root).as_posix()
            if dirname in EXCLUDED_DIRS or child_rel == "docs/project-insight":
                continue
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs
        for name in sorted(names):
            path = Path(current) / name
            if path.suffix.lower() not in SUPPORTED:
                continue
            if path.name == ".env" or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
                continue
            try:
                if path.stat().st_size > 2 * 1024 * 1024:
                    continue
            except OSError:
                continue
            rel = path.relative_to(root).as_posix()
            scanned += 1
            if path.suffix.lower() in {".py", ".pyi"}:
                symbols.extend(python_symbols(path, rel))
            else:
                symbols.extend(cpp_symbols(path, rel))

    lines = [
        "# Python / C++ 符号索引",
        "",
        f"- 项目根目录：`{root}`",
        f"- 扫描文件数：{scanned}",
        f"- 提取符号/候选项：{len(symbols)}",
        "- Python 使用标准库 AST；C/C++ 使用单行正则启发式，可能漏掉多行声明、宏和复杂模板。",
        "- 本索引只用于定位，不代表已理解函数语义；请回到源码核对。",
        "",
        "| 文件 | 类型 | 符号/名称 | 行号 |",
        "|---|---|---|---:|",
    ]
    for item in symbols:
        file_name = item.get("file", "").replace("|", r"\|")
        kind = item.get("kind", "")
        name = item.get("signature") or item.get("name", "")
        name = str(name).replace("|", r"\|").replace("`", r"\`")
        line_no = item.get("line", "")
        lines.append(f"| `{file_name}` | {kind} | `{name}` | {line_no} |")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps({"root": str(root), "scanned_files": scanned, "symbols": symbols}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Symbol index written:\n- {out_md}\n- {out_json}")
    print(f"Scanned files: {scanned} | Symbols/candidates: {len(symbols)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
