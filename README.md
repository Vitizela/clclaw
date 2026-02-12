# 论坛作者订阅归档系统

> **版本**: v1.0-phase1
> **状态**: Phase 1 完成 ✅
> **最后更新**: 2026-02-11

一个基于 Python 的自动化工具，用于订阅和归档论坛作者的帖子内容，支持全量归档、增量更新和数据分析。

---

## 🎯 项目特性

- 🔍 **智能订阅**: 通过帖子链接一键关注作者
- 📦 **自动归档**: 全量下载历史帖子，增量更新新内容
- 🎨 **友好交互**: 菜单式界面，无需记忆命令
- 📊 **数据分析**: 发帖趋势、词云、时间分析（Phase 4）
- ⏰ **定时任务**: 无人值守自动更新
- 🔄 **平滑迁移**: 自动从旧配置迁移

---

## 📸 界面预览

```
╔════════════════════════════════════════╗
║   论坛作者订阅归档系统 v1.0            ║
╠════════════════════════════════════════╣
║  当前关注: 3 位作者                    ║
║  最后更新: 2026-02-11 16:47           ║
╠════════════════════════════════════════╣
║  [1] 关注新作者 (通过帖子链接)         ║
║  [2] 查看关注列表                      ║
║  [3] 立即更新所有作者                  ║
║  [4] 取消关注作者                      ║
║  [5] 系统设置                          ║
║  [6] 查看统计（开发中）                ║
║  [7] 数据分析（开发中）                ║
║  [0] 退出                              ║
╚════════════════════════════════════════╝
```

---

## 🚀 快速开始

### 前置要求

- **Python**: 3.10+
- **Node.js**: v25.6.0+ (Phase 2 前需要)

### 安装步骤

```bash
# 1. 克隆仓库（如果从远程获取）
git clone <仓库地址>
cd gemini-t66y

# 2. 创建 Python 虚拟环境
cd python
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 安装 Node.js 依赖（Phase 2 前需要）
cd ..
npm install

# 5. 运行系统
cd python
python main.py
```

首次运行会启动配置向导，按提示完成配置。

---

## 📚 文档导航

### 快速入门
- **[README.md](./README.md)** - 本文档
- **[SETUP.md](./SETUP.md)** - 环境配置指南
- **[python/README.md](./python/README.md)** - Python 版本使用说明

### 项目设计
- **[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)** - 项目总览
- **[ADR-001](./ADR-001_Phase1_Forum_Scraping_Plan.md)** - 初始架构（Node.js）
- **[ADR-002](./ADR-002_Python_Migration_Plan.md)** - Python 迁移方案

### 开发指南
- **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - 迁移实施指南
- **[MIGRATION_PROGRESS.md](./MIGRATION_PROGRESS.md)** - 进度追踪
- **[GIT_GUIDE.md](./GIT_GUIDE.md)** - Git 使用指南

### 测试与质量
- **[PHASE1_TESTING.md](./PHASE1_TESTING.md)** - Phase 1 测试指南
- **[PHASE1_COMPLETED.md](./PHASE1_COMPLETED.md)** - Phase 1 完成总结
- **[PHASE1_BUGS_FIXED.md](./PHASE1_BUGS_FIXED.md)** - Bug 修复记录

---

## 📊 项目进度

| Phase | 功能 | 状态 | 进度 |
|-------|------|------|------|
| **Phase 1** | 基础框架与菜单 | ✅ 完成 | 100% |
| **Phase 2** | Python 爬虫核心 | 🔴 未开始 | 0% |
| **Phase 3** | 数据库与统计 | 🔴 未开始 | 0% |
| **Phase 4** | 数据分析可视化 | 🔴 未开始 | 0% |
| **Phase 5** | 完善与优化 | 🔴 未开始 | 0% |

**总体进度**: 20% (Phase 1/5)

---

## 🛠️ 技术栈

### Python 版本（当前）
- **Python 3.10+** - 主要语言
- **Playwright** - 网页自动化
- **Rich** - 终端美化
- **Questionary** - 交互菜单
- **PyYAML** - 配置管理
- **pandas** - 数据分析（Phase 4）
- **matplotlib** - 可视化（Phase 4）

### Node.js 版本（Phase 2 前临时桥接）
- **Node.js v25.6.0**
- **Playwright**

---

## 📖 使用示例

### 关注新作者

```bash
python main.py
# 选择 [1] 关注新作者
# 输入帖子 URL: https://...
# ✓ 成功关注作者: xxx
```

### 查看关注列表

```bash
# 选择 [2] 查看关注列表
┌────┬──────────────┬──────────┬────────┐
│ ID │ 作者名       │ 帖子数   │ 最后更新│
├────┼──────────────┼──────────┼────────┤
│ 1  │ 独醉笑清风   │ 45       │ 今天   │
│ 2  │ 清风皓月     │ 23       │ 昨天   │
└────┴──────────────┴──────────┴────────┘
```

### 立即更新

```bash
# 选择 [3] 立即更新所有作者
# 确认? [Y/n]: y
# 正在更新...
# ✓ 更新完成！新增 5 篇帖子
```

---

## 🗂️ 项目结构

```
gemini-t66y/
├── python/                  # Python 版本（主要）
│   ├── main.py             # 主入口
│   ├── requirements.txt    # Python 依赖
│   ├── config.yaml         # 配置文件
│   └── src/                # 源代码
│       ├── config/         # 配置管理
│       ├── menu/           # 菜单系统
│       ├── bridge/         # Node.js 桥接（临时）
│       ├── scraper/        # 爬虫（Phase 2）
│       ├── database/       # 数据库（Phase 3）
│       └── analysis/       # 分析（Phase 4）
│
├── [Node.js 脚本]          # Phase 2 前使用
│   ├── follow_author.js
│   ├── archive_posts.js
│   └── run_scheduled_update.js
│
├── 论坛存档/               # 归档内容（.gitignore）
├── 分析报告/               # 分析结果（.gitignore）
├── logs/                   # 日志（.gitignore）
│
└── [文档]
    ├── README.md           # 本文档
    ├── ADR-002*.md         # 架构决策
    ├── MIGRATION_*.md      # 迁移指南
    ├── PHASE1_*.md         # Phase 1 文档
    └── GIT_GUIDE.md        # Git 指南
```

---

## 🤝 参与开发

### 分支策略

- **main**: 稳定版本，每个 Phase 完成后合并
- **dev**: 开发分支，日常开发在此进行

### 开发流程

```bash
# 1. 切换到开发分支
git checkout dev

# 2. 开始开发
# 编辑代码...

# 3. 提交变更
git add .
git commit -m "feat: 描述你的变更"

# 4. Phase 完成后合并到 main
git checkout main
git merge dev --no-ff
git tag -a v1.0-phaseX -m "Phase X 完成"
```

详见 [GIT_GUIDE.md](./GIT_GUIDE.md)

---

## 🐛 已知问题

Phase 1 测试中发现并修复的问题：

- ✅ **Bug #1**: 路径计算错误 - 已修复
- ✅ **Bug #2**: Node.js 依赖缺失 - 已修复
- ✅ **Bug #3**: 配置文件不同步 - 已修复
- ✅ **Bug #4**: Python 版本要求不清晰 - 已修复

详见 [PHASE1_BUGS_FIXED.md](./PHASE1_BUGS_FIXED.md)

---

## 📝 变更日志

### v1.0-phase1 (2026-02-11)

**新增功能**:
- ✅ 配置管理系统（YAML 格式）
- ✅ 交互式菜单系统
- ✅ 配置向导（首次运行）
- ✅ 关注/取消关注作者
- ✅ 系统设置管理
- ✅ Node.js 脚本桥接

**文档**:
- ✅ 完整的 ADR 文档
- ✅ 详细的迁移指南
- ✅ 完整的测试文档

**代码统计**:
- Python 代码: ~1,103 行
- 文档: ~8,500 行
- 提交: 2 次

---

## 📄 许可证

本项目仅供学习研究使用。

---

## 🔗 相关链接

- **Git 仓库**: 本地仓库
- **问题反馈**: 见 [PHASE1_TESTING.md](./PHASE1_TESTING.md)
- **文档索引**: [DOCS_INDEX.md](./DOCS_INDEX.md)

---

## 🙏 致谢

感谢 Claude Sonnet 4.5 协助开发和文档编写。

---

**最后更新**: 2026-02-11
**当前版本**: v1.0-phase1
**下一目标**: Phase 2 - Python 爬虫核心
