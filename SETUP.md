# 项目安装与环境配置 (SETUP.md)

## 1. 概述 (Overview)

本文档提供了搭建本项目自动化脚本运行环境所需的所有技术信息、依赖项和关键配置。遵循此文档可以快速、准确地复现项目的工作环境。

**项目状态**: 正在进行 Python 迁移（参见 ADR-002）

## 2. 核心依赖 (Core Dependencies)

### 2.1 Node.js 环境（当前使用，Phase 2 后逐步淘汰）

项目运行需要以下系统级软件：

-   **Node.js**: `v25.6.0` (通过 `node --version` 确认)
-   **npm**: `11.8.0` (通过 `npm --version` 确认)

### 2.2 Python 环境（新系统，推荐）

-   **Python**: `3.10+` (通过 `python --version` 确认)
-   **pip**: `最新版本` (通过 `pip --version` 确认)

## 3. 项目初始化与库安装 (Project Initialization & Libraries)

### 3.1 Node.js 版本（当前系统）

通过以下命令完成项目初始化和核心库的安装。

1.  **初始化 Node.js 项目**:
    ```bash
    npm init -y
    ```

2.  **安装 Playwright 自动化库**:
    ```bash
    npm install playwright
    ```

3.  **下载并安装 Playwright 所需的浏览器驱动**:
    ```bash
    npx playwright install
    ```

### 3.2 Python 版本（新系统，推荐）

1.  **进入 Python 目录**:
    ```bash
    cd python
    ```

2.  **创建虚拟环境**（推荐）:
    ```bash
    python3 -m venv venv
    ```

3.  **激活虚拟环境**:
    ```bash
    # Linux/macOS
    source venv/bin/activate

    # Windows
    venv\Scripts\activate
    ```

4.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **安装 Playwright 浏览器**（Phase 2 需要）:
    ```bash
    playwright install
    ```

6.  **运行系统**:
    ```bash
    # 菜单模式（推荐）
    python main.py

    # 命令行模式（Phase 5 完善）
    python main.py --help
    ```

## 4. 关键发现与配置 (Key Findings & Configuration)

以下是在开发和测试过程中总结出的关键技术参数，对于确保脚本稳定运行至关重要。

-   **CSS 选择器 (CSS Selector)**:
    -   **作者定位**: 经过对论坛页面 HTML 结构的分析，用于精确定位普通帖子作者的 CSS 选择器为 `#tbody .bl`。此选择器能有效排除页面顶部的版主和公告发布者，确保只抓取目标作者。

-   **脚本执行超时 (Timeout)**:
    -   目标网站的页面加载速度可能存在波动，有时会超过 Playwright 默认的 30 秒超时限制。为确保脚本的稳定性和鲁棒性，所有与页面导航和元素等待相关的操作（例如 `page.goto()`, `page.waitForNavigation()`, `page.waitForSelector()`）都应明确设置超时时间为 **60000** 毫秒。

## 5. 中文字体配置（Python 数据分析需要）

词云和图表生成需要中文字体支持：

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install fonts-wqy-microhei fonts-wqy-zenhei
```

### macOS
```bash
# 系统自带中文字体，无需额外安装
# 常用路径: /System/Library/Fonts/PingFang.ttc
```

### Windows
```
# 系统自带中文字体
# 常用路径: C:\Windows\Fonts\simhei.ttf
```

**配置文件**：在 `python/config.yaml` 中设置：
```yaml
analysis:
  visualization:
    wordcloud:
      font_path: "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"  # Linux
      # font_path: "/System/Library/Fonts/PingFang.ttc"  # macOS
      # font_path: "C:/Windows/Fonts/simhei.ttf"  # Windows
```

## 6. 迁移说明

本项目正在从 Node.js 迁移到 Python，详见：
- **ADR-002_Python_Migration_Plan.md** - 完整迁移方案
- **MIGRATION_GUIDE.md** - 详细实施指南

**当前阶段**: Phase 1 - 基础框架搭建

**推荐使用**: Python 版本（`cd python && python main.py`）
