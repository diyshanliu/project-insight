---
name: project-insight
description: Analyze an existing software or robotics codebase and turn it into a verified project knowledge base covering repository structure, file responsibilities, architecture, execution and data flows, core algorithms, Chinese interview-oriented learning guides and questions, Mermaid mind maps, optional source-code annotations, and standalone detailed guides explicitly requested for specific features or files. Use when a user asks to understand, document, onboard to, audit the structure of, prepare interviews from, annotate, or incrementally update an existing code repository.
---

# Project Insight

Use this skill to understand an existing repository before explaining or modifying it. The default output is a Chinese, evidence-grounded project handbook under `docs/project-insight/`. The skill is suitable for robotics and general software repositories, including C++, Python, CMake, ROS1/ROS2, simulation, perception, SLAM, planning, control, and embedded projects.

## Operating principles

1. **Understand before documenting.** Do not infer a file's purpose from its name alone. Read its contents and trace its callers, callees, data types, configuration, launch files, tests, and build integration.
2. **Evidence over confidence.** Support important claims with repository-relative paths and symbol names; add line numbers when available. Mark uncertain findings as `待确认`, not as facts.
3. **Separate fact from interpretation.** Distinguish what the code demonstrably does, what project documentation claims, and what is an engineering interpretation or recommendation.
4. **Prioritize understanding over exhaustive commentary.** Inventory relevant project files broadly, but deeply explain entry points, core modules, algorithms, interfaces, configuration, and runtime paths. Do not spend equal effort on generated files or trivial helpers.
5. **Read-only by default.** Full analysis and interview modes must not change source files. Code annotation is a separate, opt-in mode.
6. **Protect private repositories.** Do not upload, publish, or transmit source code, credentials, logs, datasets, or model files to external services. Do not print secret values. Use web research only when it is available, useful, and consistent with the user's request; search for public facts, never upload private source.
7. **Do not invent provenance.** Never label a generated question as a real company interview question unless an accessible source verifies it. Label original questions as `原创练习`.
8. **Keep the original project intact.** Never run destructive commands, mass-format code, rewrite build files, or alter algorithm behavior as part of documentation.

## Modes

Infer the mode from the user's request. If they ask generally to understand or document a project, use **A — Full analysis**.

- **A — Full analysis:** inventory the repository, reconstruct architecture and execution/data flows, analyze core algorithms, and generate the complete documentation set.
- **B — Interview learning:** use an existing analysis if it is current; otherwise perform enough repository analysis first. Generate or refresh the learning guide, knowledge summary, questions, answers, and mind map.
- **C — Code annotation:** add functional section comments and useful class/function comments. Line-by-line teaching comments are optional and should be limited to selected core files. Do not modify source unless the user explicitly asks for in-place edits; otherwise create a separate annotated copy or Markdown commentary.
- **D — Incremental update:** compare the current repository with the previous analysis, identify changed/deleted/added files, and update only affected documentation. Re-check any architecture or data-flow claim that may have become stale.
- **E — 生成详细功能说明:** Generate or refresh a standalone, code-rich Chinese guide only when the user explicitly asks for such a document about identifiable features or files. Resolve targets from context; if the request for a guide is clear but its subject is missing, ask for the subject. Only then read `references/detailed-feature-guide.md`. An ordinary question about code is answered in chat. A–D never create or refresh these guides on their own, even when a previous guide exists. For combined requests, apply E only to the named subjects.

If the repository root is ambiguous and cannot be inferred from the current working directory, ask one concise question for the root path. Do not ask for preferences already specified in the conversation.

## How the user invokes this skill

The user invokes the skill with the Codex skill name, then describes the task in ordinary language. There are no special subcommands, flags, or mandatory long prompts.

```text
$project-insight
```

This alone means **Mode A — Full analysis**.

For the other modes, the user still invokes the same skill and adds a short natural-language instruction:

| User request | Internal mode | Behavior |
|---|---|---|
| `$project-insight` | A — Full analysis | Run the complete read-only project analysis and generate all required Markdown documents. |
| `$project-insight 只做面试学习，基于现有分析生成知识点、题目和答案` | B — Interview learning | Reuse a current analysis where possible; otherwise inspect the relevant code first. |
| `$project-insight 给 src/controller.cpp 添加功能分块注释` | C — Code annotation | Add functional comments to the specified file. Do not edit in place unless the user explicitly requests it. |
| `$project-insight 对 PPO 核心实现做逐行讲解` | C — Code annotation (line-by-line subtask) | Use the optional line-by-line commentary level within Mode C. |
| `$project-insight 检查上次分析后的代码变化并更新文档` | D — Incremental update | Compare against the previous analysis and refresh affected documents. |
| `$project-insight 把日志从提交到写入文件的过程写成一篇带源码的详细教程` | E — 生成详细功能说明 | Trace the feature across files and write one standalone guide. |

The skill name is the only special invocation syntax. Everything after it is an ordinary-language task description. The user does not need to repeat the documentation format, analysis rules, interview priorities, or safety constraints because those are already defined in this skill.

If the user says only `$project-insight`, do not ask which mode they want: use Mode A. If they specify a task that clearly maps to B, C, D, or E, infer that mode. Ask a question only when an essential detail such as the target repository or target files cannot be determined.

## Full-analysis workflow

Read `references/analysis-workflow.md` before a full analysis. Read `references/output-spec.md` before generating documents. Load other references only when their mode or domain is relevant.

1. **Establish scope.** Identify the repository root, read applicable `AGENTS.md` and project instructions, inspect `README`, manifests, build files, CI, launch files, tests, and Git status. Do not overwrite existing user changes. If the repository is not a Git worktree, proceed without Git operations.
2. **Create a deterministic inventory.** Run `scripts/scan_project.py` from the repository root. Use its Markdown and JSON reports as an inventory aid, not as proof of file semantics. Run `scripts/extract_symbols.py` for Python/C++ symbol indexes when useful.
3. **Classify the repository.** Identify first-party source, public interfaces, configuration, scripts, tests, documentation, generated output, third-party dependencies, assets, datasets, and model weights. Respect existing ignore rules and local conventions.
4. **Find entry points.** Locate executable entry points, ROS nodes/components, launch files, CLI commands, service processes, training/evaluation/deployment entry points, and hardware interfaces as applicable.
5. **Trace actual behavior.** Follow initialization, configuration loading, data acquisition, transformations, core computation, state changes, outputs, error paths, and shutdown. Trace both directions where useful: who calls a component, and what the component calls.
6. **Build the architecture model.** Identify layers, modules, ownership, dependencies, interfaces, message/data types, coordinate frames, units, timing assumptions, concurrency boundaries, and external systems.
7. **Analyze core algorithms.** Explain the problem, inputs/outputs, assumptions, algorithm steps, important parameters, complexity where meaningful, alternatives, failure modes, and how the project validates results.
8. **Prioritize interview knowledge.** Read `references/interview-extraction.md`. Rank topics by relevance to the target role and actual project contribution. Emphasize principles, design choices, trade-offs, troubleshooting, verification, and engineering judgment—not memorizing every implementation detail.
9. **Generate documents.** Produce the required files listed in `references/output-spec.md`. Write in clear Chinese, with natural paragraphs as the default; use tables, diagrams, code snippets, and lists when they improve comprehension.
10. **Validate.** Run `scripts/validate_docs.py` against `docs/project-insight/`. Check internal links, Mermaid fences, coverage statements, and consistency between the architecture, learning guide, questions, and answers.
11. **Report limitations.** State what was inspected, what was excluded, which files or behaviors remain uncertain, and whether the source tree was modified. Do not claim complete coverage if files were skipped or not read.

## Code annotation workflow

Read `references/code-annotation.md` before editing code. Functional section comments are the default. Line-by-line comments are opt-in and should be used only for selected algorithmic or difficult files.

Before in-place annotation:
- inspect `git status --short` and the current diff;
- do not overwrite user modifications or files with unresolved conflicts;
- agree on the target files if the scope is broad;
- make only comment changes, unless separately authorized;
- preserve formatting, APIs, logic, and behavior;
- show a diff and verify that executable code is unchanged.

If a file is generated, vendored, third-party, minified, or machine-produced, do not annotate it. If a comment would merely restate the code, omit it.

## Incremental-update workflow

Read `references/safety-and-incremental.md`. Prefer Git diff against the previous analysis commit or a user-provided baseline. If no reliable baseline exists, compare the current file inventory and relevant content hashes where available. Re-read changed files and their callers/callees; do not assume a changed file is isolated. Mark stale documents and regenerate affected sections. Preserve manually edited explanations unless they contradict current source; explain conflicts rather than silently deleting user content.

## Output location

Default: `<repository-root>/docs/project-insight/`.

Keep analysis artifacts such as scanner reports in `docs/project-insight/_analysis/`. Do not place generated documentation inside source directories. If the user specifies another output directory, follow it.

## Required quality bar

A useful result must let a new engineer answer, without reopening every source file: what the project does; how it starts; how data moves; which modules own which responsibilities; where the core algorithms live; why important design choices were made; how to reproduce and verify behavior; what can fail and how to debug it; and what to explain in an interview.

Never substitute a generic architecture diagram for the actual one. Every diagram must be grounded in discovered modules and connections. If a relationship is inferred rather than directly established, label it as an inference.
