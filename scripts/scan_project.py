#!/usr/bin/env python3
"""Create a deterministic, privacy-conscious repository file inventory.

Uses only the Python standard library. It inventories paths and metadata; it does
not read source contents. Sensitive files are omitted from the report.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    ".idea", ".vscode", ".cache", "build", "dist", "install", "devel",
    "log", "logs", "target", "bazel-bin", "bazel-out", "bazel-testlogs",
}
DEFAULT_EXCLUDED_RELATIVE = {"docs/project-insight"}
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff",
    ".pdf", ".zip", ".7z", ".rar", ".gz", ".bz2", ".xz", ".tar",
    ".so", ".dll", ".dylib", ".a", ".lib", ".o", ".obj", ".exe",
    ".bin", ".elf", ".hex", ".uf2", ".bag", ".db3", ".mcap",
    ".pcd", ".ply", ".stl", ".dae", ".fbx", ".onnx", ".pt", ".pth",
    ".engine", ".tflite", ".pb", ".safetensors", ".mp4", ".mov",
    ".wav", ".mp3", ".sqlite", ".db",
}
LANGUAGE_BY_SUFFIX = {
    ".c": "C", ".h": "C/C++ header", ".cc": "C++", ".cpp": "C++",
    ".cxx": "C++", ".hh": "C++ header", ".hpp": "C++ header",
    ".hxx": "C++ header", ".cu": "CUDA", ".cuh": "CUDA header",
    ".py": "Python", ".pyi": "Python stub", ".sh": "Shell",
    ".bash": "Shell", ".ps1": "PowerShell", ".cmake": "CMake",
    ".xml": "XML", ".launch": "ROS launch/XML", ".msg": "ROS message",
    ".srv": "ROS service", ".action": "ROS action", ".yaml": "YAML",
    ".yml": "YAML", ".json": "JSON", ".toml": "TOML", ".ini": "INI",
    ".md": "Markdown", ".rst": "reStructuredText", ".txt": "Text",
    ".urdf": "URDF/XML", ".xacro": "Xacro/XML", ".mjcf": "MJCF/XML",
    ".world": "Simulation world", ".sdf": "SDF/XML",
    ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript JSX",
    ".jsx": "JavaScript JSX", ".rs": "Rust", ".go": "Go",
    ".java": "Java", ".html": "HTML", ".css": "CSS",
}
SENSITIVE_NAMES = {
    "id_rsa", "id_ed25519", "id_ecdsa", "credentials.json",
    "secrets.json", "secrets.yaml", "secrets.yml",
}
SENSITIVE_SUFFIXES = {".pem", ".p12", ".pfx", ".key", ".keystore"}


def is_sensitive(path: Path) -> bool:
    name = path.name.lower()
    if name == ".env" or name.startswith(".env."):
        return True
    if name in SENSITIVE_NAMES or path.suffix.lower() in SENSITIVE_SUFFIXES:
        return True
    return False


def classify(path: Path) -> str:
    if path.name in {"CMakeLists.txt", "Makefile", "justfile"}:
        return "构建/工程配置"
    if path.name.startswith("Dockerfile"):
        return "容器配置"
    suffix = path.suffix.lower()
    if suffix in BINARY_SUFFIXES:
        return "二进制/资源"
    if suffix in LANGUAGE_BY_SUFFIX:
        return LANGUAGE_BY_SUFFIX[suffix]
    if path.name in {".gitignore", ".gitattributes", ".editorconfig"}:
        return "工程配置"
    return "其他/待识别"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory a project without reading source contents.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--out", default=None, help="Markdown report path")
    parser.add_argument("--json-out", default=None, help="JSON report path")
    parser.add_argument("--exclude-dir", action="append", default=[], help="Additional directory name to exclude; repeatable")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"Not a directory: {root}")

    out_md = Path(args.out).expanduser().resolve() if args.out else root / "docs/project-insight/_analysis/project_scan.md"
    out_json = Path(args.json_out).expanduser().resolve() if args.json_out else out_md.with_suffix(".json")
    excluded_names = DEFAULT_EXCLUDED_DIRS | set(args.exclude_dir)
    excluded_files = {out_md, out_json}
    files = []
    directories = []
    skipped_sensitive = 0
    skipped_dirs = Counter()

    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        rel_current = current_path.relative_to(root).as_posix()
        kept_dirs = []
        for dirname in sorted(dirnames):
            child = current_path / dirname
            rel = child.relative_to(root).as_posix()
            if dirname in excluded_names or rel in DEFAULT_EXCLUDED_RELATIVE:
                skipped_dirs[dirname] += 1
                continue
            if child.is_symlink():
                files.append({
                    "path": rel + "/",
                    "kind": "symlink-directory",
                    "language": "symlink",
                    "bytes": 0,
                    "suffix": "",
                })
                continue
            directories.append(rel + "/")
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in sorted(filenames):
            path = current_path / filename
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                continue
            if is_sensitive(path):
                skipped_sensitive += 1
                continue
            if path.resolve() in excluded_files:
                continue
            try:
                size = path.lstat().st_size
                is_link = path.is_symlink()
            except OSError:
                size = -1
                is_link = False
            files.append({
                "path": rel,
                "kind": "symlink" if is_link else ("binary/asset" if path.suffix.lower() in BINARY_SUFFIXES else "file"),
                "language": classify(path),
                "bytes": size,
                "suffix": path.suffix.lower(),
            })

    files.sort(key=lambda item: item["path"].lower())
    directories.sort(key=str.lower)
    lang_counts = Counter(item["language"] for item in files)
    suffix_counts = Counter(item["suffix"] or "[无扩展名]" for item in files)

    lines = [
        "# 项目文件扫描报告",
        "",
        f"- 项目根目录：`{root}`",
        f"- 生成时间（UTC）：`{datetime.now(timezone.utc).isoformat(timespec='seconds')}`",
        f"- 目录数：{len(directories)}",
        f"- 文件/链接数：{len(files)}",
        f"- 因敏感文件名而跳过的文件数：{skipped_sensitive}",
        "- 本脚本只读取路径和文件元数据，不读取源代码正文。",
        "",
        "## 文件类型统计",
        "",
        "| 类型 | 数量 |",
        "|---|---:|",
    ]
    for name, count in sorted(lang_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {name} | {count} |")
    lines += ["", "## 扩展名统计", "", "| 扩展名 | 数量 |", "|---|---:|"]
    for name, count in sorted(suffix_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{name}` | {count} |")

    lines += ["", "## 目录树与文件清单", "", "```text", root.name + "/"]
    all_entries = [(p, "dir") for p in directories] + [(item["path"], item["kind"]) for item in files]
    all_entries.sort(key=lambda entry: (entry[0].lower(), entry[1]))
    for rel, kind in all_entries:
        clean = rel.rstrip("/")
        depth = len(Path(clean).parts)
        name = Path(clean).name + ("/" if kind == "dir" or kind == "symlink-directory" else "")
        marker = "  " * depth + name
        lines.append(marker)
    lines += ["```", "", "## 逐文件索引", "", "| 路径 | 类型 | 大小（字节） |", "|---|---|---:|"]
    for item in files:
        safe_path = item["path"].replace("|", r"\|")
        lines.append(f"| `{safe_path}` | {item['language']} | {item['bytes']} |")

    if skipped_dirs:
        lines += ["", "## 默认排除目录统计", "", "| 目录名 | 排除次数 |", "|---|---:|"]
        for name, count in sorted(skipped_dirs.items()):
            lines.append(f"| `{name}` | {count} |")
    lines += [
        "",
        "## 使用说明",
        "",
        "此报告只提供文件盘点，不代表每个文件已经完成语义分析。请结合 README、构建配置、入口、调用链和实际源码继续分析。敏感文件仅统计跳过数量，不输出路径或内容。",
        "",
    ]

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    payload = {
        "root": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "directory_count": len(directories),
        "file_count": len(files),
        "skipped_sensitive_count": skipped_sensitive,
        "excluded_directory_counts": dict(skipped_dirs),
        "files": files,
        "directories": directories,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Inventory written:\n- {out_md}\n- {out_json}")
    print(f"Directories: {len(directories)} | Files/links: {len(files)} | Sensitive files skipped: {skipped_sensitive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
