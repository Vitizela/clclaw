# 文档索引

> 本文档提供项目所有文档的导航和说明

---

## 📚 文档分类

### 🎯 快速入门

| 文档 | 说明 | 适用对象 |
|------|------|---------|
| **[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)** | 项目总览，快速了解项目 | 所有人（首次阅读） |
| **[SETUP.md](./SETUP.md)** | 环境安装配置指南 | 首次使用者 |
| **README.md** | 项目简介（待创建） | 外部访问者 |

### 📋 架构决策记录（ADR）

| 文档 | 说明 | 决策日期 | 状态 |
|------|------|---------|------|
| **[ADR-001_Phase1_Forum_Scraping_Plan.md](./ADR-001_Phase1_Forum_Scraping_Plan.md)** | 初始架构决策（Node.js 版本） | 2026-02-11 | 已修订 |
| **[ADR-002_Python_Migration_Plan.md](./ADR-002_Python_Migration_Plan.md)** | Python 迁移方案 | 2026-02-11 | ✅ 当前 |

**ADR 说明**: 架构决策记录是项目重大技术决策的正式文档，具有可审计性。

### 🛠️ 实施指南

| 文档 | 说明 | 适用阶段 |
|------|------|---------|
| **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** | Python 迁移详细实施步骤 | Phase 1-5 |
| **[MIGRATION_PROGRESS.md](./MIGRATION_PROGRESS.md)** | 迁移进度追踪清单 | Phase 1-5 |

### 📖 用户文档（待创建）

| 文档 | 说明 | 状态 |
|------|------|------|
| **USER_MANUAL.md** | 用户使用手册 | Phase 5 |
| **FAQ.md** | 常见问题 | Phase 5 |
| **TROUBLESHOOTING.md** | 故障排除指南 | Phase 5 |

### 👨‍💻 开发文档（可选）

| 文档 | 说明 | 状态 |
|------|------|------|
| **API.md** | API 接口文档 | 按需 |
| **CONTRIBUTING.md** | 贡献指南 | 按需 |
| **CODE_STYLE.md** | 代码规范 | 按需 |

---

## 📖 阅读路径

### 路径1：快速了解项目

```
1. PROJECT_OVERVIEW.md  （10分钟）
   ↓
2. ADR-002 第1-2节      （5分钟）
   ↓
3. SETUP.md            （5分钟）
```

**适用**: 想快速了解项目的人

### 路径2：参与迁移开发

```
1. PROJECT_OVERVIEW.md       （10分钟）
   ↓
2. ADR-002 完整阅读          （30分钟）
   ↓
3. MIGRATION_GUIDE.md        （20分钟）
   ↓
4. MIGRATION_PROGRESS.md     （5分钟，查看待办）
   ↓
5. 开始实施 Phase 1
```

**适用**: 工程师、AI 编程助手

### 路径3：理解架构演进

```
1. ADR-001                   （15分钟）
   ↓
2. ADR-002                   （30分钟）
   ↓
3. 对比两个 ADR 的差异
```

**适用**: 架构师、技术决策者

### 路径4：使用系统（Phase 1 完成后）

```
1. SETUP.md                  （安装环境）
   ↓
2. USER_MANUAL.md            （学习使用）
   ↓
3. FAQ.md                    （遇到问题时）
```

**适用**: 最终用户

---

## 📊 文档关系图

```
PROJECT_OVERVIEW.md (入口)
    │
    ├─→ ADR-001 (历史背景)
    │
    ├─→ ADR-002 (当前方案) ←── 核心文档
    │       │
    │       └─→ MIGRATION_GUIDE.md (实施细节)
    │               │
    │               └─→ MIGRATION_PROGRESS.md (任务清单)
    │
    └─→ SETUP.md (环境配置)
```

---

## 🔍 文档内容摘要

### PROJECT_OVERVIEW.md
- **内容**: 项目简介、架构、功能、快速开始
- **长度**: ~500 行
- **关键信息**:
  - 迁移进度: Phase 1
  - 技术栈: Python 3.11+, Playwright, Rich
  - 核心功能: 订阅、归档、分析

### ADR-002_Python_Migration_Plan.md
- **内容**: 完整迁移方案设计
- **长度**: ~1000 行
- **关键信息**:
  - 5 个 Phase 详细规划
  - 技术架构设计
  - 配置文件设计（YAML）
  - 数据库 Schema
  - 数据分析功能设计
  - 验收标准
  - 风险缓解

### MIGRATION_GUIDE.md
- **内容**: 逐步实施指南
- **长度**: ~800 行
- **关键信息**:
  - Phase 1 详细操作步骤
  - 完整代码示例
  - 验证命令
  - 故障排除

### MIGRATION_PROGRESS.md
- **内容**: 任务清单和进度追踪
- **长度**: ~400 行
- **关键信息**:
  - 145 个细分任务
  - 当前进度: 0%
  - 验收标准

### SETUP.md
- **内容**: 环境配置指南
- **长度**: ~150 行
- **关键信息**:
  - Node.js + Python 双环境
  - 依赖安装
  - 中文字体配置

---

## 📝 文档维护

### 更新频率

| 文档 | 更新频率 |
|------|---------|
| MIGRATION_PROGRESS.md | 每日（实施期间） |
| MIGRATION_GUIDE.md | 每 Phase |
| ADR-002 | 重大变更时 |
| PROJECT_OVERVIEW.md | 每 Phase |
| SETUP.md | 依赖变更时 |

### 维护责任

| 文档类型 | 负责人 |
|---------|--------|
| ADR | 架构师/技术负责人 |
| 实施指南 | 工程师 |
| 用户文档 | 产品/工程师 |
| 进度追踪 | 项目经理/工程师 |

---

## 🎯 文档质量标准

### 可审计性

所有架构决策和实施步骤都有完整记录：
- ✅ 决策日期
- ✅ 决策理由
- ✅ 替代方案对比
- ✅ 验收标准
- ✅ 变更历史

### AI 编程可实现性

所有技术文档包含：
- ✅ 详细的代码结构
- ✅ 完整的代码示例
- ✅ 明确的依赖关系
- ✅ 具体的验证命令
- ✅ 清晰的接口定义

### 可追溯性

- ✅ 每个决策可追溯到具体 ADR
- ✅ 每个任务可追溯到 MIGRATION_PROGRESS
- ✅ 每个实施步骤可追溯到 MIGRATION_GUIDE
- ✅ 每个配置可追溯到 ADR-002

---

## 📚 外部参考

### 技术文档

- [Playwright Python 文档](https://playwright.dev/python/)
- [Rich 文档](https://rich.readthedocs.io/)
- [Questionary 文档](https://questionary.readthedocs.io/)
- [pandas 文档](https://pandas.pydata.org/)
- [jieba 文档](https://github.com/fxsjy/jieba)

### ADR 规范

- [ADR 最佳实践](https://adr.github.io/)
- [架构决策记录模板](https://github.com/joelparkerhenderson/architecture-decision-record)

---

## 🔖 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-02-11 | 初始版本，完整文档体系 |

---

**文档索引结束**

**下一步**: 阅读 [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) 开始了解项目
