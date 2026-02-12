# 项目总览 - 论坛作者订阅归档系统

> **最后更新**: 2026-02-11
> **当前版本**: 2.0-dev (Python 迁移中)
> **项目状态**: 🟡 迁移中 (Phase 1)

---

## 📖 项目简介

论坛作者订阅归档系统是一个自动化工具，用于订阅和归档论坛作者的帖子内容。系统支持：

- 🔍 **订阅管理**: 通过帖子链接关注作者
- 📦 **自动归档**: 全量下载历史帖子，增量更新新帖
- 📊 **数据分析**: 发帖趋势、词云、时间分析（开发中）
- 🎨 **友好交互**: 菜单式界面 + 命令行模式
- ⏰ **定时任务**: 无人值守自动更新

---

## 🗂️ 文档导航

### 核心文档

| 文档 | 说明 | 适用对象 |
|------|------|---------|
| [ADR-001](./ADR-001_Phase1_Forum_Scraping_Plan.md) | 初始架构决策（Node.js 版本） | 了解项目起源 |
| [ADR-002](./ADR-002_Python_Migration_Plan.md) | Python 迁移方案（当前） | **必读** - 完整技术方案 |
| [MIGRATION_GUIDE](./MIGRATION_GUIDE.md) | 迁移实施指南 | **工程师必读** - 详细操作步骤 |
| [SETUP](./SETUP.md) | 环境配置指南 | 首次使用者 |
| [PROJECT_OVERVIEW](./PROJECT_OVERVIEW.md) | 本文档 | 快速了解项目 |

### 用户文档（Phase 5 创建）

- **用户手册**: 如何使用系统（待编写）
- **FAQ**: 常见问题（待编写）

### 开发文档

- **API 文档**: 代码接口文档（按需）
- **测试文档**: 测试用例和报告（按需）

---

## 🏗️ 项目架构

### 当前状态

```
gemini-t66y/
├── [Node.js 版本]          # Phase 1-2 保留，之后可选删除
│   ├── archive_posts.js
│   ├── follow_author.js
│   ├── run_scheduled_update.js
│   └── config.json
│
├── python/                 # 新系统（推荐使用）
│   ├── main.py            # 主入口
│   ├── requirements.txt   # Python 依赖
│   ├── config.yaml        # 配置文件
│   └── src/               # 源代码
│       ├── config/        # 配置管理
│       ├── menu/          # 菜单系统
│       ├── cli/           # 命令行接口
│       ├── bridge/        # Node.js 桥接（临时）
│       ├── scraper/       # 爬虫模块（Phase 2）
│       ├── database/      # 数据库（Phase 3）
│       ├── analysis/      # 数据分析（Phase 4）
│       └── utils/         # 工具模块
│
├── 论坛存档/               # 归档内容
├── 分析报告/               # 分析结果（Phase 4）
└── logs/                  # 日志
```

### 技术栈

**当前系统（Node.js）**:
- Node.js 25.6.0
- Playwright (网页自动化)

**新系统（Python - 推荐）**:
- Python 3.10+
- Playwright (网页自动化)
- Rich + Questionary (交互界面)
- pandas + matplotlib (数据分析)
- jieba + wordcloud (中文分析)
- SQLite (数据存储)

---

## 🚀 快速开始

### 方式1: Python 版本（推荐）

```bash
# 1. 进入 Python 目录
cd python

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行（首次会启动配置向导）
python main.py
```

### 方式2: Node.js 版本（旧版）

```bash
# 1. 安装依赖
npm install

# 2. 关注作者
node follow_author.js "https://帖子URL"

# 3. 更新所有
node run_scheduled_update.js
```

---

## 📊 迁移进度

### 总体进度: 15% (Phase 1 进行中)

| Phase | 状态 | 进度 | 预计完成 |
|-------|------|------|---------|
| **Phase 1: 基础框架** | 🟡 进行中 | 0% | Week 1 |
| Phase 2: Python 爬虫 | ⚪ 未开始 | 0% | Week 2-3 |
| Phase 3: 数据库 | ⚪ 未开始 | 0% | Week 4 |
| Phase 4: 数据分析 | ⚪ 未开始 | 0% | Week 5-6 |
| Phase 5: 完善优化 | ⚪ 未开始 | 0% | Week 7 |

详见 [MIGRATION_PROGRESS.md](./MIGRATION_PROGRESS.md)

---

## 🎯 核心功能

### 已实现（Node.js 版本）

- ✅ 通过帖子链接关注作者
- ✅ 自动提取作者信息
- ✅ 全量归档历史帖子
- ✅ 增量更新（跳过已存在）
- ✅ 图片/视频下载
- ✅ Markdown 格式保存
- ✅ 定时任务支持

### 开发中（Python 版本）

- 🟡 **Phase 1**: 菜单交互系统
- ⚪ **Phase 2**: Python 爬虫核心
- ⚪ **Phase 3**: 数据库与统计
- ⚪ **Phase 4**: 数据分析
  - 发帖趋势分析
  - 内容词云生成
  - 时间分布热力图
  - 数量统计排行
  - HTML 报告生成

### 计划功能

- 📋 多作者对比分析
- 📋 内容分类（AI 辅助）
- 📋 敏感词过滤
- 📋 导出功能（PDF/Excel）

---

## 📚 使用示例

### 关注新作者（Python 菜单模式）

```bash
cd python
python main.py

# 在菜单中选择
[1] 关注新作者
输入帖子 URL: https://...
✓ 成功关注作者: xxx
是否立即归档? [Y/n]: y
```

### 查看统计（Phase 3 后）

```bash
python main.py

# 选择
[6] 查看统计

# 显示
总关注作者: 3
总帖子数: 80
总图片数: 1,245
总视频数: 67
```

### 生成词云（Phase 4 后）

```bash
# 命令行模式
python main.py analyze wordcloud --author "独醉笑清风"

# 或菜单模式
[7] 数据分析 → [3] 生成词云
```

---

## 🔧 配置说明

### 配置文件位置

- **Node.js**: `config.json`（根目录）
- **Python**: `python/config.yaml`（自动从 JSON 迁移）

### 主要配置项

```yaml
forum:
  section_url: "论坛版块URL"
  timeout: 60

followed_authors:
  - name: "作者名"
    added_date: "2026-02-11"
    total_posts: 45

storage:
  archive_path: "./论坛存档"
  download:
    images: true
    videos: true

analysis:
  enabled: true  # Phase 4 启用
```

完整配置说明见 `ADR-002` 第 4.2 节。

---

## 🐛 故障排除

### Python 导入错误

```bash
# 确保在 python/ 目录下运行
cd python
python main.py
```

### Node.js 脚本找不到

```bash
# 检查配置
cat python/config.yaml | grep nodejs_path

# 应该是: nodejs_path: "../"
```

### 中文字体问题（词云生成）

```bash
# Linux
sudo apt-get install fonts-wqy-microhei

# 然后在 config.yaml 中设置字体路径
```

更多问题见 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) 故障排除章节。

---

## 📈 数据分析功能预览（Phase 4）

### 统计面板

```
╔════════════════════════════════════════╗
║         作者统计总览                   ║
╠════════════════════════════════════════╣
║  总关注作者: 3                         ║
║  总归档帖子: 80                        ║
║  总下载图片: 1,245                     ║
║  总下载视频: 67                        ║
║  占用空间: 2.3 GB                      ║
╚════════════════════════════════════════╝
```

### 词云示例

![词云示例](./docs/images/wordcloud_example.png)
> 自动生成作者常用词汇可视化

### 趋势图示例

![趋势图示例](./docs/images/trend_example.png)
> 发帖频率随时间变化

---

## 🤝 贡献指南

### 参与迁移

当前处于 Phase 1，欢迎贡献：

1. 阅读 `ADR-002` 和 `MIGRATION_GUIDE`
2. 查看 `MIGRATION_PROGRESS.md` 找到未完成任务
3. Fork 项目，创建分支
4. 提交 PR

### 代码规范

- **Python**: PEP 8
- **文档**: Markdown
- **提交**: 清晰的 commit message

---

## 📋 待办事项（下一步）

### Phase 1 - 本周

- [ ] 创建 Python 项目结构
- [ ] 实现配置管理器
- [ ] 实现配置向导
- [ ] 实现主菜单系统
- [ ] 实现 Node.js 桥接器
- [ ] 测试所有功能

详见 [MIGRATION_PROGRESS.md](./MIGRATION_PROGRESS.md)

---

## 📄 许可证

本项目仅供学习研究使用。

---

## 📞 联系方式

- **问题反馈**: 提交 Issue
- **技术讨论**: 见文档评论

---

## 🔖 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-02-11 | Node.js 版本（ADR-001） |
| 2.0-dev | 2026-02-11 | Python 迁移开始（ADR-002） |

---

**项目文档结束**
