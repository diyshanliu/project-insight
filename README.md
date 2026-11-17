# Project Insight v1.1

**Project Insight** 是一个面向 Codex / Agent Skills 的项目代码库理解 Skill。它把“读懂一个陌生项目”变成可重复的工作流：先盘点文件，再还原架构和运行链路，提取核心算法与工程经验，最后生成项目文档、面试学习资料、思维导图，并按需给源码增加功能注释。

## 包含内容

```text
project-insight/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── analysis-workflow.md
│   ├── output-spec.md
│   ├── interview-extraction.md
│   ├── code-annotation.md
│   ├── robotics-domain-guide.md
│   └── safety-and-incremental.md
└── scripts/
    ├── scan_project.py
    ├── extract_symbols.py
    └── validate_docs.py
```

辅助脚本仅使用 Python 标准库，不要求安装第三方包。建议 Python 3.9 或更高版本。脚本用于确定性盘点和校验；真正的架构理解、函数语义分析和算法解释仍由 AI 阅读源码完成。

## 安装到 Codex 全局 Skill 目录

Codex 用户级 Skill 的目录为 `~/.agents/skills/`。请把整个 `project-insight` 文件夹放进去，不能只复制 `SKILL.md`。

### Ubuntu / WSL / Linux（bash）

假设 ZIP 已下载到 `~/Downloads`：

```bash
mkdir -p ~/.agents/skills
unzip ~/Downloads/project-insight-skill-v1.0.zip -d ~/.agents/skills
```

安装后应当存在：

```text
~/.agents/skills/project-insight/SKILL.md
```

### Windows PowerShell

```powershell
$SkillRoot = Join-Path $HOME ".agents\skills"
New-Item -ItemType Directory -Force -Path $SkillRoot | Out-Null
Expand-Archive `
    -Path "$HOME\Downloads\project-insight-skill-v1.0.zip" `
    -DestinationPath $SkillRoot `
    -Force
```

####手动安装
按键盘上的 Win + E，打开文件资源管理器。

然后按 Ctrl + L，在顶部地址栏粘贴：
%USERPROFILE%

按回车。
这里就是你的 Windows 用户目录，通常类似：
C:\Users\你的用户名\

在这个目录下，创建两个文件夹：
.agents

然后进入 .agents，再创建：
skills

最终得到这个目录：
C:\Users\你的用户名\.agents\skills\

这是 Codex 的用户级 Skill 安装目录。
#### WSL
如果 Codex 在 WSL 中运行，应安装到 WSL 用户自己的 `~/.agents/skills/`；如果 Codex 在 Windows 环境运行，则安装到 Windows 用户目录。Skill 必须放在实际运行 Codex 的环境能读取的位置。

安装后在 Codex 中输入 `/skills` 查看，或直接调用：

```text
$project-insight
```

如果新 Skill 没有立即出现，重新打开 Codex 会话或重启 Codex。

## 第一次使用

进入项目根目录后，在 Codex 中发送：

```text
$project-insight

请对当前仓库执行完整项目分析。先只读分析，不修改任何源代码。
输出中文项目文档，覆盖目录和文件功能、系统架构、程序入口、核心执行流程、数据流、核心算法、面试学习指南、知识总结、面试题、答案和 Mermaid 思维导图。
面试内容重点放在原理、设计思路、技术取舍、工程问题和排障经验。
```

默认文档输出到：

```text
<项目根目录>/docs/project-insight/
```

## 怎么给 Skill 下命令？

只需要记住：**每次都用 `$project-insight` 调用同一个 Skill，后面用普通中文说任务。** 不需要记特殊子命令，也不需要重复写一大段要求。

最简单的用法：

```text
$project-insight
```

这条命令默认执行完整项目分析（模式 A），不需要再补充其他要求。

### 四种内部工作模式

| 模式 | 什么时候用 | 示例 |
|---|---|---|
| A — 完整项目分析 | 第一次接触项目，想生成全套文档 | `$project-insight` |
| B — 面试学习 | 已有项目分析，只想学习面试知识、题目和答案 | `$project-insight 只做面试学习，更新知识点、面试题和答案` |
| C — 代码注释 | 想给源码增加功能分块注释或讲解 | `$project-insight 给 src/controller.cpp 添加功能分块注释` |
| D — 增量更新 | 代码变化后，更新已有项目文档 | `$project-insight 检查上次分析后的代码变化并更新文档` |

**注意：逐行讲解不是第五种模式。** 它是模式 C 的一种可选注释粒度，例如：

```text
$project-insight 对 PPO 核心实现做逐行讲解，先不要修改原始文件
```

### 可以附加的普通中文要求

你可以在调用后继续说明目标范围，例如“只分析 navigation 子目录”“重点分析 PPO 训练入口和奖励函数”“只注释这三个文件”“输出放到指定目录”。这些都是普通任务要求，不是额外的 Skill 命令。

除非你明确要求原地修改，否则代码注释模式默认先提供注释建议或独立讲解版本，不直接改动原始源码。

## 建议的使用边界

- 首次分析先只读；不要一上来就要求 AI 批量修改代码。
- 大型仓库先按子系统分批分析，再汇总全局架构。
- 第三方依赖、构建产物、数据集、模型权重和二进制文件可以列入清单，但不需要逐个读取内容。
- 如果项目依赖多个仓库，分别分析后再做跨仓库系统架构，不要假设它们属于同一个源码树。
- 如果要用于求职面试，应在提示词中指定目标岗位，例如机器人软件开发、SLAM、导航规划、运动控制、具身智能或仿真开发。

## 辅助脚本手动运行

在仓库根目录执行：

```bash
python3 ~/.agents/skills/project-insight/scripts/scan_project.py .
python3 ~/.agents/skills/project-insight/scripts/extract_symbols.py .
python3 ~/.agents/skills/project-insight/scripts/validate_docs.py docs/project-insight
```

扫描脚本默认把报告写入 `docs/project-insight/_analysis/`。符号提取只对 Python 和 C/C++ 做轻量索引，不等价于编译器级 AST。最终语义必须结合源码、构建配置和调用链确认。

## 兼容性说明

Skill 使用标准的 `SKILL.md` + 可选 `references/` + `scripts/` 结构。Codex 对本地仓库的访问取决于它实际运行的工作目录、权限和终端环境。其他支持 Agent Skills 的客户端也可以复用目录结构，但本地文件访问、脚本执行和 Skill 发现方式由各客户端决定。
