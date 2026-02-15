# 项目安装与环境配置 (SETUP.md)

> **版本**: v1.4-phase4
> **更新日期**: 2026-02-15
> **状态**: Phase 4 完成 ✅

---

## 📋 目录

1. [系统要求](#1-系统要求)
2. [快速安装](#2-快速安装)
3. [详细安装步骤](#3-详细安装步骤)
4. [中文字体配置](#4-中文字体配置)
5. [数据库配置](#5-数据库配置)
6. [验证安装](#6-验证安装)
7. [常见问题](#7-常见问题)
8. [进阶配置](#8-进阶配置)

---

## 1. 系统要求

### 1.1 核心依赖

| 组件 | 版本要求 | 验证命令 | 说明 |
|------|----------|----------|------|
| **Python** | 3.10+ | `python --version` | 主要运行环境 |
| **pip** | 最新版 | `pip --version` | Python 包管理器 |
| **Node.js** | v25.6.0+ | `node --version` | Phase 2 前临时需要 |
| **npm** | 11.8.0+ | `npm --version` | Node.js 包管理器 |

### 1.2 操作系统

- ✅ **Linux** (Ubuntu 20.04+, Debian 10+, CentOS 8+)
- ✅ **macOS** (10.15+)
- ✅ **Windows** (10/11)

### 1.3 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| **CPU** | 双核 2.0GHz | 四核 2.5GHz+ |
| **内存** | 4GB | 8GB+ |
| **硬盘** | 10GB 可用空间 | 50GB+ SSD |
| **网络** | 稳定的互联网连接 | 10Mbps+ |

---

## 2. 快速安装

### 2.1 一键安装脚本（推荐）

```bash
# 克隆项目
git clone <仓库地址>
cd gemini-t66y

# 运行安装脚本
bash install.sh
```

### 2.2 手动安装（5 分钟）

```bash
# 1. 进入 Python 目录
cd gemini-t66y/python

# 2. 创建虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 4. 安装依赖
pip install -r requirements.txt

# 5. 安装 Playwright 浏览器
playwright install chromium

# 6. 安装中文字体（Linux）
sudo apt install fonts-wqy-zenhei  # Ubuntu/Debian

# 7. 启动系统
python main.py
```

首次运行会启动配置向导，按提示完成配置即可。

---

## 3. 详细安装步骤

### 3.1 准备工作

#### 3.1.1 安装 Python

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**macOS**:
```bash
# 使用 Homebrew
brew install python@3.11
```

**Windows**:
1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.10+ 安装包
3. 安装时勾选 "Add Python to PATH"

#### 3.1.2 安装 Node.js（临时需要）

**Linux (Ubuntu/Debian)**:
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS**:
```bash
brew install node
```

**Windows**:
访问 https://nodejs.org/ 下载安装包

### 3.2 获取项目代码

```bash
# 如果从 Git 仓库克隆
git clone <仓库地址>
cd gemini-t66y

# 或者直接下载并解压
```

### 3.3 创建 Python 虚拟环境

```bash
cd python
python3 -m venv venv
```

**为什么需要虚拟环境？**
- 隔离项目依赖
- 避免版本冲突
- 便于管理和部署

### 3.4 激活虚拟环境

**Linux/macOS**:
```bash
source venv/bin/activate
# 成功后，命令提示符会显示 (venv)
```

**Windows PowerShell**:
```powershell
venv\Scripts\Activate.ps1
```

**Windows CMD**:
```cmd
venv\Scripts\activate.bat
```

### 3.5 安装 Python 依赖

```bash
pip install -r requirements.txt
```

**依赖清单** (`requirements.txt`):
```text
# Phase 1: 基础框架
PyYAML==6.0.1              # 配置管理
questionary==2.0.1         # 交互菜单
rich==13.7.0               # 终端美化
click==8.1.7               # CLI 框架
python-dateutil==2.8.2     # 日期处理

# Phase 2: 爬虫核心
playwright==1.42.0         # 网页自动化
aiohttp==3.9.1             # 异步 HTTP
beautifulsoup4==4.12.3     # HTML 解析
tqdm==4.66.1               # 进度条
pytest==8.0.0              # 单元测试
jinja2==3.1.3              # HTML 模板

# Phase 4: 数据分析
Pillow>=10.0.0             # 图像处理（EXIF）
geopy>=2.3.0               # GPS 反查
jieba==0.42.1              # 中文分词
wordcloud==1.9.3           # 词云生成
matplotlib==3.8.2          # 可视化
seaborn==0.13.1            # 高级可视化
pandas==2.2.0              # 数据处理
numpy==1.26.3              # 数值计算
```

### 3.6 安装 Playwright 浏览器

```bash
# 只安装 Chromium（推荐，节省空间）
playwright install chromium

# 或安装所有浏览器（可选）
playwright install
```

**说明**:
- Chromium: ~150MB
- 所有浏览器: ~500MB

### 3.7 安装 Node.js 依赖（临时）

```bash
# 返回项目根目录
cd ..

# 安装 Node.js 依赖
npm install
```

**注意**: Phase 2 完成后，Node.js 依赖将不再需要。

---

## 4. 中文字体配置

### 4.1 为什么需要中文字体？

Phase 4 的数据分析功能（词云、图表）需要中文字体支持，否则中文字符会显示为方块（□）。

### 4.2 Linux (Ubuntu/Debian)

#### 方法 1: 安装文泉驿字体（推荐 ⭐）

```bash
# 安装文泉驿正黑和微米黑
sudo apt install fonts-wqy-zenhei fonts-wqy-microhei

# 验证安装
fc-list :lang=zh | grep -i wqy
```

#### 方法 2: 手动下载（无需 root）

```bash
# 创建用户字体目录
mkdir -p ~/.fonts

# 下载文泉驿正黑字体
cd ~/.fonts
wget https://github.com/anthonyfok/fonts-wqy-zenhei/raw/master/wqy-zenhei.ttc

# 更新字体缓存
fc-cache -fv

# 清理 matplotlib 缓存
rm -rf ~/.cache/matplotlib
```

### 4.3 macOS

macOS 系统自带中文字体，无需额外安装。

**常用字体路径**:
- PingFang: `/System/Library/Fonts/PingFang.ttc`
- Hiragino Sans: `/System/Library/Fonts/Hiragino Sans GB.ttc`

### 4.4 Windows

Windows 系统自带中文字体，无需额外安装。

**常用字体路径**:
- 微软雅黑: `C:\Windows\Fonts\msyh.ttc`
- 黑体: `C:\Windows\Fonts\simhei.ttf`
- 宋体: `C:\Windows\Fonts\simsun.ttc`

### 4.5 验证字体安装

```bash
# 运行字体测试
cd python
python -c "
from src.utils.font_config import FontConfig
result = FontConfig.test_chinese_display()
if result:
    print('✅ 中文字体配置成功')
else:
    print('❌ 中文字体配置失败')
"
```

### 4.6 手动配置字体（可选）

如果自动检测失败，可以手动指定字体路径：

编辑 `python/config.yaml`:
```yaml
analysis:
  visualization:
    font_path: "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"  # Linux
    # font_path: "/System/Library/Fonts/PingFang.ttc"  # macOS
    # font_path: "C:/Windows/Fonts/simhei.ttf"  # Windows
```

### 4.7 字体问题排查

如果遇到字体显示问题，请参考：
- `python/中文字体问题解决方案.md` - 完整的故障排查指南

---

## 5. 数据库配置

### 5.1 SQLite 数据库

系统使用 SQLite 作为数据库，无需额外配置。

**默认路径**: `python/data/forum_data.db`

### 5.2 首次运行自动导入

首次运行时，系统会自动：
1. 检测现有的归档数据
2. 导入到数据库（约 10-15 秒/350 篇）
3. 创建索引和视图

### 5.3 数据库结构

```
authors (作者表)
  ├─ id, name, url, added_date, last_update
  ├─ total_posts, forum_total_posts
  └─ tags (JSON)

posts (帖子表)
  ├─ id, author_id, url, title
  ├─ publish_date, publish_year, publish_month, publish_hour, publish_weekday
  ├─ content_length, word_count
  ├─ image_count, video_count
  └─ file_path, archived_date

media (媒体表)
  ├─ id, post_id, type (image/video)
  ├─ url, file_name, file_path
  ├─ width, height, duration
  ├─ exif_* (10 个 EXIF 字段)
  └─ download_date

deleted_posts (删除记录表)
  └─ 记录已删除的帖子
```

### 5.4 数据库维护

```bash
# 检查数据完整性
python -c "
from src.database import check_all
check_all()
"

# 查看统计信息
python -c "
from src.database import get_global_stats
stats = get_global_stats()
print(stats)
"
```

---

## 6. 验证安装

### 6.1 运行系统

```bash
cd python
python main.py
```

**预期输出**:
```
╔════════════════════════════════════════╗
║   论坛作者订阅归档系统 v1.4            ║
╠════════════════════════════════════════╣
║  当前关注: 0 位作者                    ║
║  最后更新: --                         ║
╠════════════════════════════════════════╣
║  [1] 关注新作者 (通过帖子链接)         ║
║  [2] 查看关注列表                      ║
║  [3] 立即更新所有作者                  ║
║  [4] 取消关注作者                      ║
║  [5] 查看统计                          ║
║  [6] 数据分析 ✨                       ║
║  [7] 系统设置                          ║
║  [0] 退出                              ║
╚════════════════════════════════════════╝
```

### 6.2 运行测试

#### Phase 1 测试
```bash
python test_phase1_config.py
```

#### Phase 3 测试（数据库）
```bash
python test_phase3_database.py
```

#### Phase 4 Week 2 测试（文本与时间分析）
```bash
python test_week2_features.py
```

#### Phase 4 Week 3 测试（可视化与报告）
```bash
python test_week3_features.py
```

### 6.3 生成演示报告

```bash
# 全局统计
python demo_analysis.py

# 作者统计（如果有数据）
python demo_analysis.py 作者名
```

---

## 7. 常见问题

### 7.1 Python 版本问题

**问题**: `SyntaxError` 或 `ModuleNotFoundError`

**解决**:
```bash
# 检查 Python 版本
python --version  # 必须是 3.10+

# 如果版本过低，使用 python3
python3 --version
python3 main.py
```

### 7.2 权限问题

**问题**: `Permission denied` 或无法安装依赖

**解决**:
```bash
# Linux/macOS
chmod +x main.py
sudo chown -R $USER:$USER venv

# 或使用用户安装
pip install --user -r requirements.txt
```

### 7.3 网络问题

**问题**: `pip install` 或 `playwright install` 超时

**解决**:
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或配置 pip
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 7.4 Playwright 问题

**问题**: `Browser not found` 或无法启动浏览器

**解决**:
```bash
# 重新安装浏览器
playwright install --force chromium

# 或安装依赖
sudo apt install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
                 libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
                 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
```

### 7.5 中文字体问题

**问题**: 图表中文显示为方块（□）

**解决**: 参考 [第 4 节 中文字体配置](#4-中文字体配置)

**快速修复**:
```bash
# 运行修复脚本
python fix_camera_ranking.py
```

### 7.6 虚拟环境问题

**问题**: 激活虚拟环境失败

**解决**:
```bash
# Windows PowerShell 执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或使用 CMD 而不是 PowerShell
venv\Scripts\activate.bat
```

### 7.7 数据库问题

**问题**: `database is locked` 或 `database disk image is malformed`

**解决**:
```bash
# 检查数据库完整性
sqlite3 python/data/forum_data.db "PRAGMA integrity_check;"

# 如果损坏，从备份恢复
cp python/data/forum_data.db.backup python/data/forum_data.db

# 或重新导入
rm python/data/forum_data.db
python main.py  # 会自动导入
```

---

## 8. 进阶配置

### 8.1 配置文件说明

主配置文件: `python/config.yaml`

```yaml
# 论坛配置
forum:
  base_url: "https://t66y.com"
  section_url: "thread0806.php?fid=7"
  timeout: 60000

# 存储配置
storage:
  archive_path: "../论坛存档"
  reports_path: "../分析报告"

# 数据库配置
database:
  path: "data/forum_data.db"
  backup_enabled: true
  backup_interval: 86400  # 24 小时

# 日志配置
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "../logs/app.log"
  max_size: 10485760  # 10MB
  backup_count: 5

# 分析配置
analysis:
  visualization:
    font_path: "auto"  # 自动检测，或指定字体路径
    dpi: 300
    output_dir: "data/analysis"
  reports:
    output_dir: "data/reports"
    embed_images: true  # base64 嵌入
```

### 8.2 定时任务配置

#### Linux (cron)

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天凌晨 2 点更新）
0 2 * * * cd /path/to/gemini-t66y/python && /path/to/venv/bin/python main.py --auto-update
```

#### Windows (任务计划程序)

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器（每天 2:00）
4. 操作: 启动程序
   - 程序: `C:\path\to\gemini-t66y\python\venv\Scripts\python.exe`
   - 参数: `main.py --auto-update`
   - 起始于: `C:\path\to\gemini-t66y\python`

### 8.3 环境变量

可选的环境变量：

```bash
# 配置文件路径
export T66Y_CONFIG=/path/to/config.yaml

# 数据库路径
export T66Y_DB=/path/to/forum_data.db

# 日志级别
export T66Y_LOG_LEVEL=DEBUG

# 字体路径
export T66Y_FONT_PATH=/path/to/font.ttf
```

### 8.4 性能优化

#### 数据库优化

```sql
-- 定期优化数据库
PRAGMA optimize;
VACUUM;
ANALYZE;
```

#### 清理缓存

```bash
# 清理 matplotlib 缓存
rm -rf ~/.cache/matplotlib

# 清理 Playwright 缓存
rm -rf ~/.cache/ms-playwright

# 清理 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## 9. 更新与维护

### 9.1 更新系统

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重新安装 Playwright（如有更新）
playwright install chromium
```

### 9.2 备份数据

```bash
# 备份数据库
cp python/data/forum_data.db python/data/forum_data.db.backup.$(date +%Y%m%d)

# 备份配置
cp python/config.yaml python/config.yaml.backup

# 备份归档内容
tar -czf 论坛存档.backup.$(date +%Y%m%d).tar.gz 论坛存档/
```

### 9.3 清理旧数据

```bash
# 清理 7 天前的日志
find logs/ -name "*.log" -mtime +7 -delete

# 清理临时文件
rm -rf python/data/analysis/*.png.tmp
rm -rf python/data/reports/*.html.tmp
```

---

## 10. 相关文档

- **[README.md](./README.md)** - 项目概述
- **[python/README.md](./python/README.md)** - Python 版本详细说明
- **[python/分析功能使用说明.md](./python/分析功能使用说明.md)** - 数据分析功能指南
- **[python/中文字体问题解决方案.md](./python/中文字体问题解决方案.md)** - 字体问题排查
- **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - 迁移指南
- **[GIT_GUIDE.md](./GIT_GUIDE.md)** - Git 使用指南

---

## 11. 获取帮助

### 11.1 查看帮助

```bash
# 命令行帮助
python main.py --help

# 系统内帮助
python main.py
# 选择 [7] 系统设置 → 查看帮助文档
```

### 11.2 测试与诊断

```bash
# 运行诊断脚本
python diagnose.py

# 查看系统信息
python -c "
import sys
import platform
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
"
```

### 11.3 问题反馈

遇到问题请提供以下信息：

1. 系统环境 (`python --version`, `pip list`)
2. 错误信息（完整的错误堆栈）
3. 操作步骤（如何复现问题）
4. 日志文件 (`logs/app.log`)

---

## 附录

### A. 完整安装脚本

创建 `install.sh`:

```bash
#!/bin/bash
# T66Y 论坛归档系统安装脚本

set -e

echo "=== T66Y 论坛归档系统 - 安装脚本 ==="
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

echo "✓ Python 版本: $(python3 --version)"

# 进入 Python 目录
cd python

# 创建虚拟环境
echo
echo "创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo
echo "安装 Python 依赖..."
pip install -r requirements.txt

# 安装 Playwright
echo
echo "安装 Playwright 浏览器..."
playwright install chromium

# 安装字体（Ubuntu/Debian）
if command -v apt &> /dev/null; then
    echo
    echo "检测到 apt 包管理器，尝试安装中文字体..."
    sudo apt install -y fonts-wqy-zenhei 2>/dev/null || echo "字体安装跳过（需要 root 权限）"
fi

# 完成
echo
echo "=== 安装完成！==="
echo
echo "启动系统："
echo "  cd python"
echo "  source venv/bin/activate"
echo "  python main.py"
echo
```

### B. 卸载脚本

创建 `uninstall.sh`:

```bash
#!/bin/bash
# 卸载脚本

echo "=== T66Y 论坛归档系统 - 卸载 ==="
echo

read -p "确定要卸载吗？[y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# 删除虚拟环境
rm -rf python/venv

# 删除缓存
rm -rf python/__pycache__
rm -rf python/src/__pycache__
rm -rf python/.pytest_cache

# 删除数据库（可选）
read -p "删除数据库？[y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f python/data/*.db
fi

echo
echo "卸载完成！"
```

---

**文档版本**: v1.4-phase4
**最后更新**: 2026-02-15
**维护者**: Claude Sonnet 4.5

如有问题，请参考 [常见问题](#7-常见问题) 或查看其他文档。
