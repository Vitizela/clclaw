# ADR-002: Python 渐进式迁移与数据分析增强方案

**状态**: 已批准 (Approved)

**日期**: 2026-02-11

**决策者**: 项目负责人

**修订历史**:
- 2026-02-11: 初始版本，定义完整迁移方案

---

## 目录

- [1. 背景与动机](#1-背景与动机)
- [2. 核心决策](#2-核心决策)
- [3. 迁移路线图](#3-迁移路线图)
- [4. 技术架构设计](#4-技术架构设计)
- [5. Phase 详细规划](#5-phase-详细规划)
- [6. 数据分析功能设计](#6-数据分析功能设计)
- [7. 验收标准](#7-验收标准)
- [8. 风险与缓解](#8-风险与缓解)
- [9. 附录](#9-附录)

---

## 1. 背景与动机

### 1.1 现状问题

基于 ADR-001 实现的 Node.js 系统存在以下局限：

1. **交互性不足**
   - 命令行参数模式对用户不友好
   - 需要记忆多个脚本名称和参数格式
   - 缺少操作引导和状态反馈

2. **缺少数据分析能力**
   - 无法统计作者发帖趋势
   - 无法进行内容文本分析
   - 无法生成可视化报告

3. **技术栈限制**
   - Node.js 在数据分析领域生态不成熟
   - 中文分词、词云等功能缺少成熟库
   - 数据处理能力弱于 Python

### 1.2 新需求

用户提出以下增强需求：

1. **菜单式交互**: 提供友好的交互式菜单，降低使用门槛
2. **保留命令行模式**: 支持脚本化调用和高级用户
3. **数据分析功能**:
   - 作者帖子/图片/视频数量统计
   - 发帖时间分析
   - 内容词云生成
   - 发帖趋势可视化
4. **配置管理**: 使用 YAML 格式，支持配置向导

### 1.3 语言选择分析

| 评估维度 | Node.js | Python | 优势方 |
|---------|---------|--------|--------|
| 网页爬取 | ✅ Playwright 原生 | ✅ Playwright 官方支持 | 平手 |
| 菜单交互 | ✅ inquirer, prompts | ✅ questionary, rich | **Python** |
| 中文分词 | ⚠️ nodejieba (移植) | ✅ **jieba** (原生) | **Python** |
| 数据处理 | ⚠️ danfojs (不成熟) | ✅ **pandas** (工业标准) | **Python** |
| 可视化 | ⚠️ chart.js (有限) | ✅ **matplotlib/plotly** | **Python** |
| 词云生成 | ❌ 基本无成熟方案 | ✅ **wordcloud** | **Python** |
| 统计分析 | ⚠️ simple-statistics | ✅ **numpy/scipy** | **Python** |
| 现有代码 | ✅ 无需改动 | ⚠️ 需要迁移 | Node.js |
| 异步处理 | ✅ 原生优秀 | ⚠️ asyncio 较复杂 | Node.js |

**结论**: 数据分析需求使 Python 成为更优选择，但需通过渐进式迁移降低风险。

---

## 2. 核心决策

### 2.1 技术决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| **迁移策略** | 渐进式迁移（方案A） | 降低风险，保持系统可用性 |
| **目标语言** | Python 3.11+ | 数据分析生态成熟 |
| **配置格式** | YAML | 可读性强，支持注释 |
| **命令行模式** | 混合模式 | 菜单 + CLI 并存 |
| **数据存储** | SQLite | 轻量级，无需独立服务 |
| **Web 界面** | 不实现 | 降低复杂度 |

### 2.2 迁移策略

**方案A：渐进式迁移**（已选择）

```
Phase 1: Python 基础框架 + 菜单系统（桥接 Node.js）
    ↓
Phase 2: Python 爬虫核心（替换 Node.js）
    ↓
Phase 3: 数据库 + 基础统计
    ↓
Phase 4: 数据分析 + 可视化
    ↓
Phase 5: 完善与优化
```

**关键原则**:
- 每个 Phase 保持系统可用
- 向后兼容，支持回滚
- 充分测试后再进入下一 Phase

### 2.3 命令行接口设计

```bash
# 无参数 → 菜单模式
python main.py

# 有参数 → 命令行模式
python main.py follow --url "https://..."
python main.py update [--author "name"]
python main.py list
python main.py unfollow --author "name"
python main.py stats
python main.py analyze wordcloud --author "name"
python main.py analyze trend [--author "name"]
```

---

## 3. 迁移路线图

### 3.1 时间线总览

```
┌─────────────────────────────────────────────────────────────┐
│                  当前状态 (Node.js)                          │
│  ✓ 基本功能完整  ✗ 无数据分析  ✗ 交互性差                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: 基础框架 (Week 1)                                  │
│  ✓ Python 项目结构  ✓ YAML 配置  ✓ 菜单系统                 │
│  ⚠️ 桥接模式调用 Node.js 脚本                                │
│  验收: 菜单可用，功能与现有系统一致                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Python 爬虫 (Week 2-3)                             │
│  ✓ Playwright 爬虫  ✓ 归档逻辑  ✓ 媒体下载                  │
│  验收: Python 版本与 Node.js 功能对等                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: 数据层 (Week 4)                                    │
│  ✓ SQLite 数据库  ✓ 数据同步  ✓ 基础统计                    │
│  验收: 历史数据导入成功，统计准确                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 4: 数据分析 (Week 5-6)                                │
│  ✓ 时间分析  ✓ 词云  ✓ 趋势图  ✓ 报告生成                   │
│  验收: 所有分析功能正常，图表清晰                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 5: 完善优化 (Week 7)                                  │
│  ✓ 命令行完善  ✓ 日志  ✓ 错误处理  ✓ 文档                   │
│  验收: 系统稳定，文档齐全                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ✅ 迁移完成
```

### 3.2 工作量估算

| Phase | 主要任务 | 预计时间 | 关键里程碑 |
|-------|---------|---------|-----------|
| Phase 1 | 菜单系统、配置管理、桥接 | 2-3 天 | 菜单可用 |
| Phase 2 | Python 爬虫、媒体下载 | 5-7 天 | 功能对等 |
| Phase 3 | 数据库、数据导入、统计 | 3-4 天 | 统计可用 |
| Phase 4 | 分词、可视化、报告 | 5-7 天 | 分析完整 |
| Phase 5 | CLI、日志、优化、文档 | 2-3 天 | 文档齐全 |
| **总计** | | **17-24 天** | **完整系统** |

---

## 4. 技术架构设计

### 4.1 项目结构

```
gemini-t66y/
├── [现有 Node.js 文件]         # Phase 2 前保持不变
│   ├── archive_posts.js
│   ├── follow_author.js
│   ├── run_scheduled_update.js
│   ├── discover_authors.js
│   ├── discover_authors_v2.js
│   ├── config.json             # Phase 1 后逐步废弃
│   └── package.json
│
├── python/                     # 新建：Python 代码目录
│   ├── main.py                # 主入口
│   ├── requirements.txt       # 依赖清单
│   ├── config.yaml            # 新配置文件
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   │
│   │   ├── config/            # 配置管理模块
│   │   │   ├── __init__.py
│   │   │   ├── manager.py     # 配置读写
│   │   │   └── wizard.py      # 配置向导
│   │   │
│   │   ├── menu/              # 菜单模块
│   │   │   ├── __init__.py
│   │   │   ├── main_menu.py   # 主菜单
│   │   │   ├── follow_menu.py # 关注管理
│   │   │   ├── analysis_menu.py  # 分析菜单
│   │   │   └── settings_menu.py  # 设置菜单
│   │   │
│   │   ├── cli/               # 命令行模块
│   │   │   ├── __init__.py
│   │   │   └── commands.py    # CLI 命令定义
│   │   │
│   │   ├── bridge/            # 桥接模块（Phase 2 后删除）
│   │   │   ├── __init__.py
│   │   │   └── nodejs_bridge.py  # 调用 Node.js 脚本
│   │   │
│   │   ├── scraper/           # 爬虫模块（Phase 2）
│   │   │   ├── __init__.py
│   │   │   ├── archiver.py    # 归档器
│   │   │   ├── extractor.py   # 内容提取
│   │   │   ├── downloader.py  # 媒体下载
│   │   │   └── follower.py    # 关注作者
│   │   │
│   │   ├── database/          # 数据库模块（Phase 3）
│   │   │   ├── __init__.py
│   │   │   ├── schema.sql     # 数据库结构
│   │   │   ├── models.py      # 数据模型
│   │   │   ├── query.py       # 查询工具
│   │   │   └── migrate.py     # 历史数据导入
│   │   │
│   │   ├── analysis/          # 分析模块（Phase 4）
│   │   │   ├── __init__.py
│   │   │   ├── statistics.py  # 统计分析
│   │   │   ├── text_analysis.py  # 文本分析
│   │   │   ├── visualization.py  # 可视化
│   │   │   └── reporter.py    # 报告生成
│   │   │
│   │   └── utils/             # 工具模块
│   │       ├── __init__.py
│   │       ├── display.py     # 界面显示
│   │       ├── validator.py   # 输入验证
│   │       └── logger.py      # 日志工具
│   │
│   └── data/                  # 数据目录
│       ├── forum_data.db      # SQLite 数据库
│       └── stopwords.txt      # 停用词表
│
├── 论坛存档/                  # 归档目录（现有）
├── 分析报告/                  # 报告目录（Phase 4 新增）
└── logs/                      # 日志目录
```

### 4.2 配置文件设计

#### config.yaml 完整结构

```yaml
# ==================== 元信息 ====================
version: "2.0"
migrated_from_json: true  # 标记是否从 JSON 迁移
created_at: "2026-02-11 16:50:00"
last_updated: "2026-02-11 16:50:00"

# ==================== 基本设置 ====================
forum:
  section_url: "https://t66y.com/thread0806.php?fid=7"
  timeout: 60  # 页面加载超时（秒）
  max_retries: 3  # 失败重试次数

# ==================== 关注列表 ====================
followed_authors:
  - name: "独醉笑清风"
    added_date: "2026-02-11"
    last_update: "2026-02-11 16:47:00"
    total_posts: 45
    total_images: 120
    total_videos: 8
    tags: ["原创", "高产"]  # 可选标签
    notes: ""  # 可选备注

# ==================== 存储设置 ====================
storage:
  archive_path: "./论坛存档"
  analysis_path: "./分析报告"
  database_path: "./python/data/forum_data.db"

  download:
    images: true
    videos: true
    max_file_size_mb: 100

  organization:
    structure: "author/year/month/title"
    filename_max_length: 100

# ==================== 数据分析设置 ====================
analysis:
  enabled: true

  jieba:
    enabled: true
    dict_path: null  # 自定义词典路径
    stop_words_file: "./python/data/stopwords.txt"

  statistics:
    - author_ranking
    - posting_frequency
    - content_length
    - media_usage

  visualization:
    wordcloud:
      enabled: true
      font_path: "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
      width: 1920
      height: 1080
      background_color: "white"
      max_words: 200

    charts:
      - posting_trend
      - hourly_heatmap
      - content_length_distribution

# ==================== 定时任务 ====================
schedule:
  enabled: false
  frequency: "daily"
  time: "03:00"
  cron_expression: "0 3 * * *"

# ==================== 日志设置 ====================
logging:
  level: "INFO"
  file: "./logs/scraper.log"
  max_size_mb: 50
  backup_count: 5

# ==================== 高级设置 ====================
advanced:
  parallel_downloads: 5
  browser_headless: true
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  proxy: null

# ==================== 实验性功能 ====================
experimental:
  use_python_scraper: false  # Phase 2: 切换为 true
  enable_database: false     # Phase 3: 切换为 true

# ==================== 兼容性设置 ====================
legacy:
  keep_nodejs_scripts: true  # 保留 Node.js 脚本
  nodejs_path: "../"         # Node.js 脚本路径
```

### 4.3 数据库设计

#### Schema 定义 (database/schema.sql)

```sql
-- ==================== Authors 表 ====================
CREATE TABLE IF NOT EXISTS authors (
    name TEXT PRIMARY KEY,
    total_posts INTEGER DEFAULT 0,
    total_images INTEGER DEFAULT 0,
    total_videos INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    first_post_date DATE,
    last_post_date DATE,
    followed_at DATE NOT NULL,
    last_update_at DATETIME,
    tags TEXT,  -- JSON 数组
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==================== Posts 表 ====================
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    content_clean TEXT,  -- 清理后的纯文本
    publish_date DATETIME,
    word_count INTEGER,
    image_count INTEGER DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    file_path TEXT UNIQUE NOT NULL,  -- 文件系统路径
    post_url TEXT,  -- 原始帖子 URL
    archived_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author) REFERENCES authors(name) ON DELETE CASCADE
);

-- ==================== Media 表 ====================
CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    type TEXT CHECK(type IN ('image', 'video')) NOT NULL,
    filename TEXT NOT NULL,
    file_size INTEGER,  -- 字节
    file_path TEXT NOT NULL,
    source_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- ==================== Statistics 表（缓存） ====================
CREATE TABLE IF NOT EXISTS statistics_cache (
    key TEXT PRIMARY KEY,
    value TEXT,  -- JSON
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 索引 ====================
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author);
CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(publish_date);
CREATE INDEX IF NOT EXISTS idx_posts_archived ON posts(archived_at);
CREATE INDEX IF NOT EXISTS idx_media_post ON media(post_id);
CREATE INDEX IF NOT EXISTS idx_media_type ON media(type);

-- ==================== 触发器：自动更新作者统计 ====================
CREATE TRIGGER IF NOT EXISTS update_author_stats_insert
AFTER INSERT ON posts
BEGIN
    UPDATE authors SET
        total_posts = total_posts + 1,
        total_images = total_images + NEW.image_count,
        total_videos = total_videos + NEW.video_count,
        total_words = total_words + NEW.word_count,
        last_post_date = MAX(last_post_date, NEW.publish_date),
        last_update_at = CURRENT_TIMESTAMP
    WHERE name = NEW.author;

    -- 如果是第一篇帖子
    UPDATE authors SET
        first_post_date = NEW.publish_date
    WHERE name = NEW.author AND first_post_date IS NULL;
END;

CREATE TRIGGER IF NOT EXISTS update_author_stats_delete
AFTER DELETE ON posts
BEGIN
    UPDATE authors SET
        total_posts = total_posts - 1,
        total_images = total_images - OLD.image_count,
        total_videos = total_videos - OLD.video_count,
        total_words = total_words - OLD.word_count,
        last_update_at = CURRENT_TIMESTAMP
    WHERE name = OLD.author;
END;
```

### 4.4 依赖清单

#### requirements.txt 分阶段版本

##### Phase 1: 基础框架
```txt
# Phase 1: 基础框架与菜单
PyYAML==6.0.1              # 配置文件
questionary==2.0.1         # 交互菜单
rich==13.7.0               # 终端美化
click==8.1.7               # 命令行框架
python-dateutil==2.8.2     # 日期处理
```

##### Phase 2: 爬虫功能
```txt
# Phase 1 + Phase 2
playwright==1.42.0         # 网页自动化
aiohttp==3.9.1             # 异步 HTTP
beautifulsoup4==4.12.3     # HTML 解析
tqdm==4.66.1               # 进度条
requests==2.31.0           # HTTP 请求（备用）
```

##### Phase 3: 数据库
```txt
# Phase 1 + Phase 2 + Phase 3
# SQLite 是 Python 内置，无需额外依赖
```

##### Phase 4: 数据分析
```txt
# Phase 1-3 + Phase 4
pandas==2.2.0              # 数据处理
numpy==1.26.3              # 数值计算
matplotlib==3.8.2          # 可视化
seaborn==0.13.1            # 高级可视化
jieba==0.42.1              # 中文分词
wordcloud==1.9.3           # 词云生成
Pillow==10.2.0             # 图像处理
jinja2==3.1.3              # HTML 模板
markdown==3.5.2            # Markdown 处理
```

---

## 5. Phase 详细规划

### 5.1 Phase 1: 基础框架（2-3 天）

#### 5.1.1 目标
建立 Python 项目基础，实现菜单系统，通过桥接模式调用现有 Node.js 脚本，确保不破坏任何现有功能。

#### 5.1.2 任务清单

```
□ 环境搭建
  □ 创建 python/ 目录结构
  □ 编写 requirements.txt (Phase 1 版本)
  □ 创建虚拟环境
  □ 安装依赖

□ 配置管理
  □ 实现 ConfigManager 类 (src/config/manager.py)
  □ 实现 ConfigWizard 类 (src/config/wizard.py)
  □ config.json → config.yaml 转换工具
  □ 配置验证器

□ 菜单系统
  □ 主菜单框架 (src/menu/main_menu.py)
  □ 关注管理菜单 (src/menu/follow_menu.py)
  □ 设置菜单 (src/menu/settings_menu.py)
  □ 菜单工具类 (src/menu/utils.py)

□ 桥接模块
  □ NodeJSBridge 类 (src/bridge/nodejs_bridge.py)
  □ 实现 follow_author 调用
  □ 实现 archive_posts 调用
  □ 实现 run_update 调用
  □ 实时输出显示

□ 工具模块
  □ Display 类 (src/utils/display.py)
  □ Validator 类 (src/utils/validator.py)

□ 主入口
  □ main.py 入口逻辑
  □ 命令行参数解析（简单版）
  □ 菜单/CLI 模式分发

□ 测试
  □ 配置向导测试
  □ 配置迁移测试
  □ 菜单导航测试
  □ 桥接调用测试
  □ 所有功能与 Node.js 版本对比
```

#### 5.1.3 核心代码示例

##### main.py
```python
#!/usr/bin/env python3
"""
论坛作者订阅归档系统 - 主入口
支持菜单模式和命令行模式
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config.manager import ConfigManager
from config.wizard import ConfigWizard
from menu.main_menu import MainMenu
from cli.commands import CLI

def main():
    """主入口"""
    # 检查配置文件
    config_manager = ConfigManager()

    if not config_manager.config_exists():
        print("检测到首次运行，启动配置向导...")
        wizard = ConfigWizard()
        wizard.run()

    # 加载配置
    config = config_manager.load()

    # 判断模式
    if len(sys.argv) > 1:
        # 命令行模式
        cli = CLI(config)
        cli.run()
    else:
        # 菜单模式
        menu = MainMenu(config)
        menu.run()

if __name__ == '__main__':
    main()
```

##### src/config/manager.py
```python
"""配置管理器"""
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class ConfigManager:
    """配置文件管理器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(__file__).parent.parent.parent / config_path
        self.legacy_json_path = self.config_path.parent.parent / "config.json"

    def config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.config_path.exists()

    def load(self) -> Dict[str, Any]:
        """加载配置"""
        if not self.config_exists():
            # 尝试从 JSON 迁移
            if self.legacy_json_path.exists():
                return self._migrate_from_json()
            else:
                raise FileNotFoundError("配置文件不存在，请运行配置向导")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def save(self, config: Dict[str, Any]):
        """保存配置"""
        config['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    def _migrate_from_json(self) -> Dict[str, Any]:
        """从旧 config.json 迁移"""
        print("检测到旧配置文件，正在迁移...")

        with open(self.legacy_json_path, 'r', encoding='utf-8') as f:
            old_config = json.load(f)

        # 转换为新格式
        new_config = {
            'version': '2.0',
            'migrated_from_json': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'forum': {
                'section_url': old_config.get('forumSectionUrl', ''),
                'timeout': 60,
                'max_retries': 3
            },
            'followed_authors': [
                {
                    'name': author,
                    'added_date': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'migrated'
                }
                for author in old_config.get('followedAuthors', [])
            ],
            'storage': {
                'archive_path': './论坛存档',
                'analysis_path': './分析报告',
                'download': {
                    'images': True,
                    'videos': True
                }
            },
            'analysis': {
                'enabled': False  # Phase 4 后启用
            },
            'legacy': {
                'keep_nodejs_scripts': True,
                'nodejs_path': '../'
            }
        }

        # 保存新配置
        self.save(new_config)
        print(f"✓ 配置已迁移至 {self.config_path}")

        return new_config
```

##### src/bridge/nodejs_bridge.py
```python
"""Node.js 脚本桥接器（临时方案）"""
import subprocess
import os
from pathlib import Path
from typing import List, Tuple

class NodeJSBridge:
    """桥接器：调用现有 Node.js 脚本"""

    def __init__(self, nodejs_dir: str = "../"):
        self.nodejs_dir = Path(__file__).parent.parent.parent.parent / nodejs_dir

        if not self.nodejs_dir.exists():
            raise FileNotFoundError(f"Node.js 目录不存在: {self.nodejs_dir}")

    def follow_author(self, post_url: str) -> Tuple[str, str]:
        """调用 follow_author.js"""
        return self._run_script("follow_author.js", [post_url])

    def archive_posts(self, authors: List[str]) -> Tuple[str, str]:
        """调用 archive_posts.js"""
        return self._run_script("archive_posts.js", authors)

    def run_update(self) -> Tuple[str, str]:
        """调用 run_scheduled_update.js"""
        return self._run_script("run_scheduled_update.js", [])

    def _run_script(self, script_name: str, args: List[str]) -> Tuple[str, str]:
        """执行 Node.js 脚本"""
        script_path = self.nodejs_dir / script_name

        if not script_path.exists():
            raise FileNotFoundError(f"脚本不存在: {script_path}")

        cmd = ["node", str(script_path)] + args

        print(f"执行: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # 实时显示输出
        stdout_lines = []
        stderr_lines = []

        for line in process.stdout:
            print(line, end='')
            stdout_lines.append(line)

        for line in process.stderr:
            print(line, end='', file=sys.stderr)
            stderr_lines.append(line)

        process.wait()

        return ''.join(stdout_lines), ''.join(stderr_lines)
```

#### 5.1.4 验收标准

- [ ] 运行 `python main.py` 显示完整菜单
- [ ] 配置向导在首次运行时正确触发
- [ ] config.json 正确迁移到 config.yaml
- [ ] 所有菜单选项功能正常
- [ ] 桥接调用 Node.js 脚本成功
- [ ] 实时输出显示正常
- [ ] 配置修改（添加/删除作者）正确保存
- [ ] 无任何功能退化

---

### 5.2 Phase 2: Python 爬虫核心（5-7 天）

#### 5.2.1 目标
用 Python + Playwright 重写所有爬虫逻辑，实现与 Node.js 版本功能对等，逐步替换桥接调用。

#### 5.2.2 任务清单

```
□ 爬虫核心
  □ Archiver 类 (src/scraper/archiver.py)
  □ Extractor 类 (src/scraper/extractor.py)
  □ Downloader 类 (src/scraper/downloader.py)
  □ Follower 类 (src/scraper/follower.py)

□ 功能实现
  □ 论坛页面导航
  □ 帖子链接收集
  □ 帖子内容提取
  □ 图片下载
  □ 视频下载
  □ Markdown 生成
  □ 增量检查逻辑

□ 测试验证
  □ 单元测试
  □ 与 Node.js 版本对比测试
  □ 边界情况测试
  □ 性能测试

□ 集成
  □ 菜单集成 Python 爬虫
  □ 配置开关 (experimental.use_python_scraper)
  □ 双版本并行运行测试
  □ 完全切换到 Python 版本
```

#### 5.2.3 核心代码示例

##### src/scraper/archiver.py（部分）
```python
"""归档器核心逻辑"""
from playwright.async_api import async_playwright
from pathlib import Path
from typing import List
import asyncio

class Archiver:
    """帖子归档器"""

    def __init__(self, config: dict):
        self.config = config
        self.forum_url = config['forum']['section_url']
        self.timeout = config['forum']['timeout'] * 1000
        self.archive_path = Path(config['storage']['archive_path'])

    async def archive_authors(self, authors: List[str]):
        """归档指定作者的所有帖子"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # 1. 收集帖子链接
            post_urls = await self._collect_posts(page, authors)

            # 2. 逐一归档
            new_count = 0
            for i, post_info in enumerate(post_urls):
                if await self._archive_post(page, post_info):
                    new_count += 1

            await browser.close()

            return new_count

    async def _collect_posts(self, page, authors):
        """收集所有相关帖子链接"""
        # 实现逻辑...
        pass

    async def _archive_post(self, page, post_info):
        """归档单个帖子"""
        # 实现逻辑...
        pass
```

#### 5.2.4 验收标准

- [ ] Python 版本归档结果与 Node.js 一致
- [ ] 所有图片/视频正确下载
- [ ] Markdown 格式正确
- [ ] 增量逻辑正常工作
- [ ] 性能不低于 Node.js 版本
- [ ] 错误处理健壮
- [ ] 通过所有对比测试

---

### 5.3 Phase 3: 数据库 + 基础统计（3-4 天）

#### 5.3.1 目标
建立数据持久化层，归档时同步写入数据库，支持快速统计查询。

#### 5.3.2 任务清单

```
□ 数据库设计
  □ schema.sql 设计
  □ 索引设计
  □ 触发器设计

□ 数据模型
  □ Database 类 (src/database/models.py)
  □ Query 工具 (src/database/query.py)

□ 数据同步
  □ 归档时自动写入数据库
  □ 历史数据导入工具 (src/database/migrate.py)
  □ 数据一致性检查

□ 基础统计
  □ 总体统计
  □ 作者排行
  □ 时间分布统计
  □ 媒体使用统计

□ 菜单集成
  □ 统计信息查看
  □ 数据导入工具入口
```

#### 5.3.3 验收标准

- [ ] 数据库正确创建
- [ ] 历史数据成功导入
- [ ] 统计数字准确无误
- [ ] 查询响应 < 1秒
- [ ] 数据与文件系统一致

---

### 5.4 Phase 4: 数据分析 + 可视化（5-7 天）

#### 5.4.1 目标
实现核心分析功能：数量统计、时间分析、词云、趋势图。

#### 5.4.2 任务清单

```
□ 文本分析
  □ 中文分词集成
  □ 停用词过滤
  □ 词频统计
  □ 词云生成

□ 时间分析
  □ 发帖频率分析
  □ 小时分布
  □ 星期分布
  □ 月度趋势

□ 可视化
  □ 趋势图生成
  □ 热力图生成
  □ 分布图生成

□ 报告生成
  □ HTML 报告模板
  □ Markdown 报告
  □ 图表嵌入

□ 菜单集成
  □ 分析菜单
  □ 报告查看
```

#### 5.4.3 验收标准

- [ ] 词云图片清晰
- [ ] 中文字体正确显示
- [ ] 趋势图数据准确
- [ ] 报告包含所有分析内容
- [ ] 图表美观清晰

---

### 5.5 Phase 5: 完善与优化（2-3 天）

#### 5.5.1 目标
完善系统，优化性能，清理冗余代码。

#### 5.5.2 任务清单

```
□ 命令行完善
  □ 所有子命令实现
  □ 帮助文档
  □ 参数验证

□ 日志系统
  □ 日志配置
  □ 日志轮转
  □ 错误追踪

□ 错误处理
  □ 网络失败重试
  □ 断点续传
  □ 优雅降级

□ 性能优化
  □ 并发下载
  □ 数据库查询优化
  □ 缓存机制

□ 文档
  □ README.md
  □ 用户手册
  □ API 文档

□ 清理
  □ 删除桥接模块
  □ 可选：删除 Node.js 脚本
  □ 代码重构
```

#### 5.5.3 验收标准

- [ ] 命令行所有功能正常
- [ ] 日志完整记录
- [ ] 错误处理健壮
- [ ] 性能达标
- [ ] 文档齐全

---

## 6. 数据分析功能设计

### 6.1 分析模块架构

```python
src/analysis/
├── statistics.py          # 统计分析
├── text_analysis.py       # 文本分析
├── visualization.py       # 可视化
└── reporter.py            # 报告生成
```

### 6.2 核心分析功能

#### 6.2.1 数量统计

**功能**: 统计作者的帖子、图片、视频数量

**实现**:
```python
def get_author_stats(author_name: str) -> dict:
    """获取作者统计信息"""
    return {
        'total_posts': count_posts(author_name),
        'total_images': count_images(author_name),
        'total_videos': count_videos(author_name),
        'total_words': sum_word_count(author_name),
        'avg_post_length': avg_word_count(author_name),
        'avg_images_per_post': avg_images(author_name),
        'avg_videos_per_post': avg_videos(author_name),
        'date_range': get_date_range(author_name)
    }
```

**输出示例**:
```
作者: 独醉笑清风
────────────────────────────
总帖子数: 45
总图片数: 120
总视频数: 8
总字数: 105,678
平均帖子长度: 2,348 字
平均图片/帖: 2.7
平均视频/帖: 0.2
发帖时间跨度: 2025-01-15 ~ 2026-02-10
```

#### 6.2.2 时间分析

**功能**: 分析发帖时间模式

**实现**:
```python
def analyze_posting_time(author_name: str) -> dict:
    """分析发帖时间"""
    posts = get_posts_by_author(author_name)

    return {
        'hourly_distribution': posts.groupby('hour').size(),
        'weekday_distribution': posts.groupby('weekday').size(),
        'monthly_trend': posts.groupby('month').size(),
        'peak_hour': posts['hour'].mode()[0],
        'peak_weekday': posts['weekday'].mode()[0]
    }
```

**可视化**: 热力图（星期 x 小时）

#### 6.2.3 词云生成

**功能**: 生成作者内容词云

**实现**:
```python
def generate_wordcloud(author_name: str, output_path: str):
    """生成词云"""
    # 1. 获取所有内容
    posts = get_posts_by_author(author_name)
    text = ' '.join(posts['content_clean'])

    # 2. 分词
    words = jieba.cut(text)
    stopwords = load_stopwords()
    filtered = [w for w in words if len(w) > 1 and w not in stopwords]

    # 3. 生成词云
    wc = WordCloud(
        font_path=get_font_path(),
        width=1920,
        height=1080,
        background_color='white',
        max_words=200
    ).generate(' '.join(filtered))

    # 4. 保存
    wc.to_file(output_path)
```

#### 6.2.4 趋势分析

**功能**: 发帖趋势可视化

**实现**:
```python
def plot_posting_trend(author_name: str, output_path: str):
    """绘制发帖趋势图"""
    posts = get_posts_by_author(author_name)
    monthly = posts.groupby(posts['publish_date'].dt.to_period('M')).size()

    plt.figure(figsize=(12, 6))
    plt.plot(monthly.index.astype(str), monthly.values,
             marker='o', linewidth=2)
    plt.title(f'{author_name} 发帖趋势')
    plt.xlabel('月份')
    plt.ylabel('帖子数')
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path, dpi=300)
```

### 6.3 分析菜单设计

```
📈 数据分析
────────────────────────────────
选择作者:
  [1] 独醉笑清风
  [2] 作者B
  [3] 所有作者
  [4] 返回

选择分析类型:
  [1] 📊 统计总览
  [2] 📈 发帖趋势图
  [3] ☁️  内容词云
  [4] 🔥 时间热力图
  [5] 📊 数量对比
  [6] 📑 生成完整报告
  [0] 返回
```

---

## 7. 验收标准

### 7.1 各 Phase 验收标准

见各 Phase 详细规划章节。

### 7.2 整体系统验收

#### 功能完整性
- [ ] 所有原有功能正常工作
- [ ] 菜单模式完全可用
- [ ] 命令行模式完全可用
- [ ] 数据分析功能完整

#### 性能指标
- [ ] 归档速度不低于 Node.js 版本
- [ ] 数据库查询 < 1秒
- [ ] 图表生成 < 5秒
- [ ] 内存占用合理

#### 稳定性
- [ ] 24小时连续运行无崩溃
- [ ] 网络异常自动恢复
- [ ] 数据一致性保证

#### 可用性
- [ ] 菜单导航清晰直观
- [ ] 错误提示友好
- [ ] 文档完整易懂

---

## 8. 风险与缓解

### 8.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| Python 爬虫性能低于 Node.js | 高 | 中 | 使用异步+并发，性能测试对比 |
| 数据库设计不合理 | 中 | 低 | Phase 3 前充分评审 |
| 中文分词效果差 | 中 | 低 | 使用成熟的 jieba 库，自定义词典 |
| 可视化字体问题 | 低 | 中 | 提前验证字体路径，提供配置 |

### 8.2 迁移风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 功能退化 | 高 | 中 | 每个 Phase 充分测试，保留回滚能力 |
| 数据丢失 | 高 | 低 | 数据备份，双写验证 |
| 配置迁移失败 | 中 | 低 | 自动迁移+人工验证 |
| 用户适应困难 | 中 | 中 | 菜单引导，文档完善 |

### 8.3 回滚策略

1. **Phase 1**: 删除 python/ 目录，继续使用 Node.js
2. **Phase 2**: 通过配置开关切回 Node.js 脚本
3. **Phase 3**: 可选启用数据库
4. **Phase 4**: 分析功能独立，不影响核心功能

**关键**: 每个 Phase 保持向后兼容，保留 Node.js 脚本作为备份。

---

## 9. 附录

### 9.1 术语表

| 术语 | 定义 |
|------|------|
| 渐进式迁移 | 分阶段逐步迁移，每个阶段保持系统可用 |
| 桥接模式 | 通过适配器调用旧系统，平滑过渡 |
| 增量归档 | 只下载新增内容，跳过已存在内容 |
| 词云 | 文本可视化，词频越高字体越大 |
| 热力图 | 二维数据的颜色编码可视化 |

### 9.2 参考资料

- Playwright Python 文档: https://playwright.dev/python/
- pandas 文档: https://pandas.pydata.org/
- jieba 中文分词: https://github.com/fxsjy/jieba
- WordCloud: https://github.com/amueller/word_cloud
- Rich 终端美化: https://rich.readthedocs.io/

### 9.3 变更日志

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-02-11 | 1.0 | 初始版本，完整迁移方案 |

---

**文档结束**

**下一步**: 开始实施 Phase 1 - 基础框架搭建
