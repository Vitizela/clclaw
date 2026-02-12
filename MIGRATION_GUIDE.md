# Python 迁移实施指南

> **面向**: 工程师、AI 编程助手
> **目标**: 逐步实施 Python 迁移，可审计、可追溯
> **参考**: ADR-002_Python_Migration_Plan.md

---

## 📋 目录

- [快速开始](#快速开始)
- [Phase 1: 基础框架](#phase-1-基础框架)
- [Phase 2: Python 爬虫](#phase-2-python-爬虫)
- [Phase 3: 数据库](#phase-3-数据库)
- [Phase 4: 数据分析](#phase-4-数据分析)
- [Phase 5: 完善优化](#phase-5-完善优化)
- [测试检查清单](#测试检查清单)
- [故障排除](#故障排除)

---

## 快速开始

### 前置条件

```bash
# 检查 Python 版本（需要 3.11+）
python3 --version

# 检查 Node.js 版本（确保现有系统可用）
node --version

# 检查 npm 版本
npm --version
```

### 当前系统验证

在开始迁移前，确保现有 Node.js 系统正常工作：

```bash
# 测试现有功能
cd /home/ben/gemini-work/gemini-t66y

# 查看配置
cat config.json

# 测试脚本（可选）
# node discover_authors_v2.js "https://t66y.com/thread0806.php?fid=7"
```

---

## Phase 1: 基础框架

**目标**: 建立 Python 项目，实现菜单系统，桥接 Node.js
**预计时间**: 2-3 天
**状态**: 🔴 未开始

### 第一步：创建项目结构

```bash
# 进入项目目录
cd /home/ben/gemini-work/gemini-t66y

# 创建 Python 目录结构
mkdir -p python/src/{config,menu,cli,bridge,utils,database,scraper,analysis}
mkdir -p python/data
mkdir -p logs
mkdir -p 分析报告

# 创建 __init__.py 文件
touch python/src/__init__.py
touch python/src/config/__init__.py
touch python/src/menu/__init__.py
touch python/src/cli/__init__.py
touch python/src/bridge/__init__.py
touch python/src/utils/__init__.py
touch python/src/database/__init__.py
touch python/src/scraper/__init__.py
touch python/src/analysis/__init__.py
```

**验证**:
```bash
tree python -I '__pycache__'
```

预期输出：
```
python
├── data
└── src
    ├── __init__.py
    ├── analysis
    │   └── __init__.py
    ├── bridge
    │   └── __init__.py
    ├── cli
    │   └── __init__.py
    ├── config
    │   └── __init__.py
    ├── database
    │   └── __init__.py
    ├── menu
    │   └── __init__.py
    ├── scraper
    │   └── __init__.py
    └── utils
        └── __init__.py
```

### 第二步：创建依赖文件

创建 `python/requirements.txt`:

```txt
# Phase 1: 基础框架
PyYAML==6.0.1
questionary==2.0.1
rich==13.7.0
click==8.1.7
python-dateutil==2.8.2
```

**安装依赖**:
```bash
cd python

# 创建虚拟环境（推荐）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

**验证**:
```bash
pip list | grep -E "(PyYAML|questionary|rich|click)"
```

### 第三步：实现配置管理器

创建 `python/src/config/manager.py`:

<details>
<summary>点击查看完整代码</summary>

```python
"""配置管理器"""
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class ConfigManager:
    """配置文件管理器

    职责:
    1. 加载和保存 YAML 配置
    2. 从旧 config.json 自动迁移
    3. 配置验证
    """

    DEFAULT_CONFIG = {
        'version': '2.0',
        'forum': {
            'section_url': '',
            'timeout': 60,
            'max_retries': 3
        },
        'followed_authors': [],
        'storage': {
            'archive_path': './论坛存档',
            'analysis_path': './分析报告',
            'database_path': './python/data/forum_data.db',
            'download': {
                'images': True,
                'videos': True,
                'max_file_size_mb': 100
            },
            'organization': {
                'structure': 'author/year/month/title',
                'filename_max_length': 100
            }
        },
        'analysis': {
            'enabled': False
        },
        'schedule': {
            'enabled': False,
            'frequency': 'daily',
            'time': '03:00'
        },
        'logging': {
            'level': 'INFO',
            'file': './logs/scraper.log',
            'max_size_mb': 50,
            'backup_count': 5
        },
        'advanced': {
            'parallel_downloads': 5,
            'browser_headless': True,
            'proxy': None
        },
        'experimental': {
            'use_python_scraper': False,
            'enable_database': False
        },
        'legacy': {
            'keep_nodejs_scripts': True,
            'nodejs_path': '../'
        }
    }

    def __init__(self, config_path: str = "config.yaml"):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径（相对于 python/ 目录）
        """
        # 配置文件路径（python/config.yaml）
        self.config_path = Path(__file__).parent.parent.parent / config_path

        # 旧配置文件路径（项目根目录/config.json）
        self.legacy_json_path = self.config_path.parent.parent / "config.json"

    def config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.config_path.exists()

    def load(self) -> Dict[str, Any]:
        """加载配置

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        if not self.config_exists():
            # 尝试从 JSON 迁移
            if self.legacy_json_path.exists():
                print("📦 检测到旧配置文件 config.json")
                return self._migrate_from_json()
            else:
                raise FileNotFoundError(
                    f"配置文件不存在: {self.config_path}\n"
                    "请运行配置向导或手动创建配置文件"
                )

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 合并默认配置（处理新增字段）
        config = self._merge_with_defaults(config)

        return config

    def save(self, config: Dict[str, Any]) -> None:
        """保存配置

        Args:
            config: 配置字典
        """
        # 更新时间戳
        config['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                indent=2
            )

    def add_author(self, author_name: str, tags: Optional[list] = None) -> None:
        """添加关注作者

        Args:
            author_name: 作者名
            tags: 可选标签
        """
        config = self.load()

        # 检查是否已存在
        for author in config['followed_authors']:
            if author['name'] == author_name:
                print(f"作者 {author_name} 已在关注列表中")
                return

        # 添加新作者
        config['followed_authors'].append({
            'name': author_name,
            'added_date': datetime.now().strftime('%Y-%m-%d'),
            'last_update': None,
            'total_posts': 0,
            'total_images': 0,
            'total_videos': 0,
            'tags': tags or [],
            'notes': ''
        })

        self.save(config)
        print(f"✓ 已添加作者: {author_name}")

    def remove_author(self, author_name: str) -> bool:
        """移除关注作者

        Args:
            author_name: 作者名

        Returns:
            是否成功移除
        """
        config = self.load()

        original_length = len(config['followed_authors'])
        config['followed_authors'] = [
            a for a in config['followed_authors']
            if a['name'] != author_name
        ]

        if len(config['followed_authors']) < original_length:
            self.save(config)
            print(f"✓ 已移除作者: {author_name}")
            return True
        else:
            print(f"作者 {author_name} 不在关注列表中")
            return False

    def _migrate_from_json(self) -> Dict[str, Any]:
        """从旧 config.json 迁移

        Returns:
            新配置字典
        """
        print("🔄 正在从 config.json 迁移配置...")

        with open(self.legacy_json_path, 'r', encoding='utf-8') as f:
            old_config = json.load(f)

        # 转换为新格式
        new_config = self.DEFAULT_CONFIG.copy()
        new_config.update({
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
                    'last_update': None,
                    'total_posts': 0,
                    'total_images': 0,
                    'total_videos': 0,
                    'tags': ['migrated'],
                    'notes': '从 config.json 迁移'
                }
                for author in old_config.get('followedAuthors', [])
            ]
        })

        # 保存新配置
        self.save(new_config)
        print(f"✓ 配置已成功迁移至: {self.config_path}")
        print(f"  - 论坛 URL: {new_config['forum']['section_url']}")
        print(f"  - 关注作者: {len(new_config['followed_authors'])} 位")

        return new_config

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置（处理新增字段）

        Args:
            config: 用户配置

        Returns:
            合并后的配置
        """
        def deep_merge(default: dict, custom: dict) -> dict:
            """递归合并字典"""
            result = default.copy()
            for key, value in custom.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(self.DEFAULT_CONFIG, config)
```

</details>

**验证**:
```bash
cd python
python3 -c "from src.config.manager import ConfigManager; cm = ConfigManager(); print('✓ ConfigManager 导入成功')"
```

### 第四步：实现配置向导

创建 `python/src/config/wizard.py`:

<details>
<summary>点击查看完整代码</summary>

```python
"""配置向导"""
import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from .manager import ConfigManager

class ConfigWizard:
    """配置向导

    引导用户完成首次配置
    """

    custom_style = Style([
        ('qmark', 'fg:#673ab7 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#f44336 bold'),
        ('pointer', 'fg:#673ab7 bold'),
        ('highlighted', 'fg:#673ab7 bold'),
        ('selected', 'fg:#cc5454'),
        ('separator', 'fg:#cc5454'),
        ('instruction', ''),
        ('text', ''),
    ])

    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager()

    def run(self) -> None:
        """运行配置向导"""
        self.console.print(Panel(
            "[bold cyan]欢迎使用论坛作者订阅归档系统[/bold cyan]\n\n"
            "首次运行检测到，启动配置向导...\n"
            "请按照提示完成配置。",
            title="🎉 欢迎",
            border_style="cyan"
        ))

        config = {}

        # 1. 基本设置
        self.console.print("\n[bold]📝 步骤 1/4: 基本设置[/bold]")
        config['forum'] = self._configure_forum()

        # 2. 存储设置
        self.console.print("\n[bold]📁 步骤 2/4: 存储设置[/bold]")
        config['storage'] = self._configure_storage()

        # 3. 分析设置
        self.console.print("\n[bold]📊 步骤 3/4: 数据分析设置[/bold]")
        config['analysis'] = self._configure_analysis()

        # 4. 定时任务
        self.console.print("\n[bold]⏰ 步骤 4/4: 定时任务[/bold]")
        config['schedule'] = self._configure_schedule()

        # 合并默认配置
        full_config = self.config_manager.DEFAULT_CONFIG.copy()
        full_config.update(config)

        # 保存配置
        self.config_manager.save(full_config)

        self.console.print(Panel(
            f"[green]✓ 配置完成！[/green]\n\n"
            f"配置文件已保存至: [cyan]{self.config_manager.config_path}[/cyan]\n\n"
            f"您现在可以开始使用系统了！",
            title="✅ 完成",
            border_style="green"
        ))

    def _configure_forum(self) -> dict:
        """配置论坛设置"""
        forum_url = questionary.text(
            "论坛版块 URL:",
            default="https://t66y.com/thread0806.php?fid=7",
            style=self.custom_style
        ).ask()

        timeout = questionary.text(
            "页面加载超时（秒）:",
            default="60",
            style=self.custom_style,
            validate=lambda x: x.isdigit() and int(x) > 0
        ).ask()

        return {
            'section_url': forum_url,
            'timeout': int(timeout),
            'max_retries': 3
        }

    def _configure_storage(self) -> dict:
        """配置存储设置"""
        archive_path = questionary.text(
            "归档存储路径:",
            default="./论坛存档",
            style=self.custom_style
        ).ask()

        download_images = questionary.confirm(
            "是否下载图片?",
            default=True,
            style=self.custom_style
        ).ask()

        download_videos = questionary.confirm(
            "是否下载视频?",
            default=True,
            style=self.custom_style
        ).ask()

        return {
            'archive_path': archive_path,
            'analysis_path': './分析报告',
            'database_path': './python/data/forum_data.db',
            'download': {
                'images': download_images,
                'videos': download_videos,
                'max_file_size_mb': 100
            },
            'organization': {
                'structure': 'author/year/month/title',
                'filename_max_length': 100
            }
        }

    def _configure_analysis(self) -> dict:
        """配置分析设置"""
        enable_analysis = questionary.confirm(
            "启用数据分析功能?（Phase 4 后可用）",
            default=False,
            style=self.custom_style
        ).ask()

        return {
            'enabled': enable_analysis
        }

    def _configure_schedule(self) -> dict:
        """配置定时任务"""
        enable_schedule = questionary.confirm(
            "是否配置定时更新?",
            default=False,
            style=self.custom_style
        ).ask()

        if not enable_schedule:
            return {
                'enabled': False,
                'frequency': 'daily',
                'time': '03:00'
            }

        frequency = questionary.select(
            "更新频率:",
            choices=[
                '每6小时',
                '每12小时',
                '每天凌晨3点（推荐）',
                '自定义'
            ],
            style=self.custom_style
        ).ask()

        freq_map = {
            '每6小时': ('6hours', None),
            '每12小时': ('12hours', None),
            '每天凌晨3点（推荐）': ('daily', '03:00'),
            '自定义': ('custom', None)
        }

        freq_value, time_value = freq_map[frequency]

        if freq_value == 'custom':
            time_value = questionary.text(
                "更新时间（24小时格式，如 14:30）:",
                default="03:00",
                style=self.custom_style
            ).ask()

        return {
            'enabled': True,
            'frequency': freq_value,
            'time': time_value or '03:00',
            'cron_expression': self._generate_cron(freq_value, time_value)
        }

    @staticmethod
    def _generate_cron(frequency: str, time: str) -> str:
        """生成 cron 表达式"""
        if frequency == 'daily':
            hour, minute = time.split(':')
            return f"{minute} {hour} * * *"
        elif frequency == '6hours':
            return "0 */6 * * *"
        elif frequency == '12hours':
            return "0 */12 * * *"
        else:
            hour, minute = time.split(':')
            return f"{minute} {hour} * * *"
```

</details>

### 第五步：实现桥接模块

创建 `python/src/bridge/nodejs_bridge.py`:

<details>
<summary>点击查看完整代码</summary>

```python
"""Node.js 脚本桥接器（Phase 2 前的临时方案）"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

class NodeJSBridge:
    """桥接器：调用现有 Node.js 脚本

    Phase 1 临时使用，Phase 2 完成后删除
    """

    def __init__(self, nodejs_dir: str = "../"):
        """初始化桥接器

        Args:
            nodejs_dir: Node.js 脚本目录（相对于 python/ 目录）
        """
        # 计算 Node.js 目录的绝对路径
        self.nodejs_dir = (Path(__file__).parent.parent.parent.parent / nodejs_dir).resolve()

        if not self.nodejs_dir.exists():
            raise FileNotFoundError(
                f"Node.js 目录不存在: {self.nodejs_dir}\n"
                f"请确保 Node.js 脚本在正确位置"
            )

        print(f"[桥接] Node.js 目录: {self.nodejs_dir}")

    def follow_author(self, post_url: str) -> Tuple[str, str, int]:
        """调用 follow_author.js

        Args:
            post_url: 帖子 URL

        Returns:
            (stdout, stderr, returncode)
        """
        return self._run_script("follow_author.js", [post_url])

    def archive_posts(self, authors: List[str]) -> Tuple[str, str, int]:
        """调用 archive_posts.js

        Args:
            authors: 作者名列表

        Returns:
            (stdout, stderr, returncode)
        """
        # 为每个作者名加引号（防止空格问题）
        quoted_authors = [f'"{author}"' for author in authors]
        return self._run_script("archive_posts.js", quoted_authors)

    def run_update(self) -> Tuple[str, str, int]:
        """调用 run_scheduled_update.js

        Returns:
            (stdout, stderr, returncode)
        """
        return self._run_script("run_scheduled_update.js", [])

    def discover_authors(self, forum_url: str) -> Tuple[str, str, int]:
        """调用 discover_authors_v2.js

        Args:
            forum_url: 论坛版块 URL

        Returns:
            (stdout, stderr, returncode)
        """
        return self._run_script("discover_authors_v2.js", [forum_url])

    def _run_script(self, script_name: str, args: List[str]) -> Tuple[str, str, int]:
        """执行 Node.js 脚本

        Args:
            script_name: 脚本文件名
            args: 命令行参数

        Returns:
            (stdout, stderr, returncode)
        """
        script_path = self.nodejs_dir / script_name

        if not script_path.exists():
            raise FileNotFoundError(f"脚本不存在: {script_path}")

        # 构建命令
        cmd = ["node", str(script_path)] + args

        print(f"[桥接] 执行: {' '.join(cmd)}")

        # 执行命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=str(self.nodejs_dir)  # 设置工作目录
        )

        # 实时显示输出
        stdout_lines = []
        stderr_lines = []

        # 读取 stdout
        if process.stdout:
            for line in process.stdout:
                print(line, end='')
                stdout_lines.append(line)

        # 读取 stderr
        if process.stderr:
            for line in process.stderr:
                print(line, end='', file=sys.stderr)
                stderr_lines.append(line)

        # 等待完成
        returncode = process.wait()

        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)

        if returncode != 0:
            print(f"[桥接] 脚本执行失败，返回码: {returncode}")
        else:
            print(f"[桥接] 脚本执行成功")

        return stdout, stderr, returncode
```

</details>

### 第六步：实现主菜单

创建 `python/src/menu/main_menu.py`:

<details>
<summary>点击查看完整代码（约300行）</summary>

```python
"""主菜单"""
import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Dict, Any

from ..config.manager import ConfigManager
from ..bridge.nodejs_bridge import NodeJSBridge

class MainMenu:
    """主菜单系统"""

    custom_style = Style([
        ('qmark', 'fg:#673ab7 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#f44336 bold'),
        ('pointer', 'fg:#673ab7 bold'),
        ('highlighted', 'fg:#673ab7 bold'),
        ('selected', 'fg:#cc5454'),
    ])

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.console = Console()
        self.config_manager = ConfigManager()
        self.bridge = NodeJSBridge(config['legacy']['nodejs_path'])

    def run(self) -> None:
        """运行主菜单"""
        while True:
            self._show_status()
            choice = self._show_main_menu()

            if choice is None:  # 用户取消
                break

            if "关注新作者" in choice:
                self._follow_author()
            elif "查看关注列表" in choice:
                self._view_followed_authors()
            elif "立即更新" in choice:
                self._run_update()
            elif "取消关注" in choice:
                self._unfollow_author()
            elif "系统设置" in choice:
                self._show_settings()
            elif "查看统计" in choice:
                self._show_statistics()
            elif "数据分析" in choice:
                self._show_analysis()
            elif "退出" in choice:
                self.console.print("[yellow]再见！[/yellow]")
                break

    def _show_status(self) -> None:
        """显示系统状态"""
        self.console.clear()
        self.console.print(Panel(
            f"[cyan]关注作者:[/cyan] {len(self.config['followed_authors'])} 位\n"
            f"[cyan]论坛版块:[/cyan] {self.config['forum']['section_url']}\n"
            f"[cyan]归档路径:[/cyan] {self.config['storage']['archive_path']}",
            title="📊 论坛作者订阅归档系统",
            border_style="cyan"
        ))

    def _show_main_menu(self) -> str:
        """显示主菜单"""
        choices = [
            "🔍 关注新作者（通过帖子链接）",
            "📋 查看关注列表",
            "🔄 立即更新所有作者",
            "❌ 取消关注作者",
            "⚙️  系统设置",
            "📊 查看统计（Phase 3 后可用）",
            "📈 数据分析（Phase 4 后可用）",
            "🚪 退出"
        ]

        return questionary.select(
            "\n请选择操作：",
            choices=choices,
            style=self.custom_style
        ).ask()

    def _follow_author(self) -> None:
        """关注新作者"""
        self.console.print("\n[bold]🔍 关注新作者[/bold]\n")

        post_url = questionary.text(
            "请输入帖子 URL:",
            style=self.custom_style,
            validate=lambda x: len(x) > 0
        ).ask()

        if not post_url:
            return

        self.console.print(f"\n[cyan]正在调用 Node.js 脚本处理...[/cyan]\n")

        # 调用 Node.js 脚本
        stdout, stderr, returncode = self.bridge.follow_author(post_url)

        if returncode == 0:
            self.console.print(f"\n[green]✓ 操作完成[/green]")
            # 重新加载配置
            self.config = self.config_manager.load()
        else:
            self.console.print(f"\n[red]✗ 操作失败[/red]")

        questionary.press_any_key_to_continue("按任意键继续...").ask()

    def _view_followed_authors(self) -> None:
        """查看关注列表"""
        self.console.print("\n[bold]📋 关注列表[/bold]\n")

        if not self.config['followed_authors']:
            self.console.print("[yellow]暂无关注的作者[/yellow]")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        # 创建表格
        table = Table(title=f"当前关注 {len(self.config['followed_authors'])} 位作者")
        table.add_column("序号", style="cyan", justify="right")
        table.add_column("作者名", style="green")
        table.add_column("关注日期", style="yellow")
        table.add_column("帖子数", justify="right")
        table.add_column("标签", style="magenta")

        for i, author in enumerate(self.config['followed_authors'], 1):
            table.add_row(
                str(i),
                author['name'],
                author.get('added_date', 'N/A'),
                str(author.get('total_posts', 0)),
                ', '.join(author.get('tags', []))
            )

        self.console.print(table)

        questionary.press_any_key_to_continue("\n按任意键返回...").ask()

    def _run_update(self) -> None:
        """立即更新所有作者"""
        self.console.print("\n[bold]🔄 立即更新[/bold]\n")

        if not self.config['followed_authors']:
            self.console.print("[yellow]暂无关注的作者，无需更新[/yellow]")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        confirm = questionary.confirm(
            f"确认为 {len(self.config['followed_authors'])} 位作者执行更新？",
            default=True,
            style=self.custom_style
        ).ask()

        if not confirm:
            return

        self.console.print(f"\n[cyan]正在调用 Node.js 脚本更新...[/cyan]\n")

        # 调用 Node.js 脚本
        stdout, stderr, returncode = self.bridge.run_update()

        if returncode == 0:
            self.console.print(f"\n[green]✓ 更新完成[/green]")
        else:
            self.console.print(f"\n[red]✗ 更新失败[/red]")

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _unfollow_author(self) -> None:
        """取消关注作者"""
        self.console.print("\n[bold]❌ 取消关注[/bold]\n")

        if not self.config['followed_authors']:
            self.console.print("[yellow]暂无关注的作者[/yellow]")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        # 选择作者
        author_choices = [a['name'] for a in self.config['followed_authors']]
        author_choices.append("← 返回")

        author_name = questionary.select(
            "选择要取消关注的作者：",
            choices=author_choices,
            style=self.custom_style
        ).ask()

        if author_name == "← 返回" or not author_name:
            return

        # 确认
        confirm = questionary.confirm(
            f"确认取消关注 {author_name}？（不会删除已归档的内容）",
            default=False,
            style=self.custom_style
        ).ask()

        if confirm:
            self.config_manager.remove_author(author_name)
            self.config = self.config_manager.load()

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _show_settings(self) -> None:
        """显示设置菜单"""
        self.console.print("\n[bold]⚙️  系统设置[/bold]\n")

        setting_choices = [
            "修改论坛版块 URL",
            "修改归档路径",
            "下载选项设置",
            "查看完整配置",
            "← 返回"
        ]

        choice = questionary.select(
            "选择设置项：",
            choices=setting_choices,
            style=self.custom_style
        ).ask()

        if not choice or choice == "← 返回":
            return

        if "论坛版块" in choice:
            self._edit_forum_url()
        elif "归档路径" in choice:
            self._edit_archive_path()
        elif "下载选项" in choice:
            self._edit_download_options()
        elif "完整配置" in choice:
            self._view_full_config()

    def _edit_forum_url(self) -> None:
        """修改论坛 URL"""
        current = self.config['forum']['section_url']
        self.console.print(f"当前 URL: [cyan]{current}[/cyan]")

        new_url = questionary.text(
            "新 URL:",
            default=current,
            style=self.custom_style
        ).ask()

        if new_url and new_url != current:
            self.config['forum']['section_url'] = new_url
            self.config_manager.save(self.config)
            self.console.print("[green]✓ 已更新[/green]")

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _edit_archive_path(self) -> None:
        """修改归档路径"""
        current = self.config['storage']['archive_path']
        self.console.print(f"当前路径: [cyan]{current}[/cyan]")

        new_path = questionary.text(
            "新路径:",
            default=current,
            style=self.custom_style
        ).ask()

        if new_path and new_path != current:
            self.config['storage']['archive_path'] = new_path
            self.config_manager.save(self.config)
            self.console.print("[green]✓ 已更新[/green]")

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _edit_download_options(self) -> None:
        """修改下载选项"""
        download_images = questionary.confirm(
            "下载图片?",
            default=self.config['storage']['download']['images'],
            style=self.custom_style
        ).ask()

        download_videos = questionary.confirm(
            "下载视频?",
            default=self.config['storage']['download']['videos'],
            style=self.custom_style
        ).ask()

        self.config['storage']['download']['images'] = download_images
        self.config['storage']['download']['videos'] = download_videos
        self.config_manager.save(self.config)

        self.console.print("[green]✓ 已更新[/green]")
        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _view_full_config(self) -> None:
        """查看完整配置"""
        import yaml
        self.console.print("\n[bold]完整配置:[/bold]\n")
        self.console.print(yaml.dump(self.config, allow_unicode=True, sort_keys=False))
        questionary.press_any_key_to_continue("\n按任意键返回...").ask()

    def _show_statistics(self) -> None:
        """查看统计（Phase 3 后实现）"""
        self.console.print("\n[yellow]此功能将在 Phase 3 实现[/yellow]")
        questionary.press_any_key_to_continue("\n按任意键返回...").ask()

    def _show_analysis(self) -> None:
        """数据分析（Phase 4 后实现）"""
        self.console.print("\n[yellow]此功能将在 Phase 4 实现[/yellow]")
        questionary.press_any_key_to_continue("\n按任意键返回...").ask()
```

</details>

### 第七步：实现 CLI 框架

创建 `python/src/cli/commands.py`:

```python
"""命令行接口（简化版）"""
import click
from ..config.manager import ConfigManager

class CLI:
    """命令行接口"""

    def __init__(self, config):
        self.config = config

    def run(self):
        """运行 CLI"""
        # Phase 1: 简单提示
        print("命令行模式将在后续 Phase 完善")
        print("当前请使用菜单模式：python main.py")
```

### 第八步：实现主入口

创建 `python/main.py`:

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

from src.config.manager import ConfigManager
from src.config.wizard import ConfigWizard
from src.menu.main_menu import MainMenu
from src.cli.commands import CLI

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

### 第九步：测试验证

```bash
cd python

# 测试 1: 首次运行（配置向导）
python main.py

# 预期：显示配置向导，完成配置后生成 config.yaml

# 测试 2: 再次运行（主菜单）
python main.py

# 预期：显示主菜单

# 测试 3: 查看关注列表
# 在菜单中选择 "查看关注列表"

# 测试 4: 测试桥接（可选）
# 在菜单中选择 "立即更新所有作者"
# 应该能看到 Node.js 脚本的输出
```

### Phase 1 验收清单

```
✅ Phase 1 验收清单
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ 环境搭建
  □ Python 虚拟环境创建成功
  □ 所有依赖安装成功
  □ 目录结构正确

□ 配置管理
  □ ConfigManager 正常工作
  □ config.json → config.yaml 迁移成功
  □ 配置向导正常运行
  □ 配置读写正常

□ 菜单系统
  □ 主菜单显示正常
  □ 状态信息显示正确
  □ 所有菜单选项可导航

□ 桥接功能
  □ 可以调用 follow_author.js
  □ 可以调用 archive_posts.js
  □ 可以调用 run_scheduled_update.js
  □ 实时输出正常显示

□ 功能验证
  □ 查看关注列表正常
  □ 添加/删除作者正常
  □ 系统设置修改正常
  □ 与 Node.js 版本功能一致

□ 文档
  □ README 更新（如需）
  □ 注释完整

✅ Phase 1 完成标志
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
运行 python main.py 可以正常使用所有功能，
且与 Node.js 版本功能完全一致。
```

---

## Phase 2: Python 爬虫

**目标**: 用 Python 实现爬虫，替换 Node.js
**预计时间**: 5-7 天
**状态**: 🔴 未开始

---

### ⚠️ 关键注意事项（必读！）

在开始 Phase 2 实施前，请务必阅读以下注意事项：

#### 1. **文件名安全化必须与 Node.js 完全一致** 🔴 P0

**为什么重要**: 如果生成的文件名不一致，会导致重复归档或找不到已有内容。

**Node.js 原始逻辑**:
```javascript
function sanitizeFilename(name) {
    return name.replace(/[<>:"/\\|?*]/g, '_').substring(0, 100);
}
```

**Python 实现（必须完全一致）**:
```python
def sanitize_filename(name: str, max_length: int = 100) -> str:
    # 与 Node.js 正则 /[<>:"/\\|?*]/g 完全一致
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)

    # 截断到指定长度
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]

    # 去除首尾空格和点
    safe_name = safe_name.strip(' .')

    return safe_name if safe_name else 'untitled'
```

**测试验证**: 见 [PHASE2_TESTING.md](./PHASE2_TESTING.md) Test 1

---

#### 2. **Playwright API 差异** 🔴 P0

Python 和 Node.js 的 Playwright API 有重要差异，详见：[PHASE2_API_MAPPING.md](./PHASE2_API_MAPPING.md)

**最关键的差异**:
- `page.$$(selector)` → `page.query_selector_all(selector)`
- `page.$$eval()` → `page.eval_on_selector_all()`
- `page.waitForNavigation()` → `page.wait_for_load_state()`
- 驼峰命名 → 下划线命名
- 对象参数 → 关键字参数

**示例对比**: 见 API 映射文档

---

#### 3. **增量检查逻辑改进** 🟡 P1

Node.js 版本只检查目录存在性，有以下问题：
- 下载失败的帖子会被永久跳过
- 标题冲突可能导致内容覆盖

**改进方案**: 使用完整性标记 + URL hash 验证

详细设计见 `ADR-002_Python_Migration_Plan.md` 第 5.2.3 节

---

#### 4. **路径计算陷阱** 🟡 P1

Phase 1 的 Bug #1 就是路径计算错误，Phase 2 需特别注意：

```python
# 在 Archiver 中
class Archiver:
    def __init__(self, config):
        # __file__ 是 .../python/src/scraper/archiver.py
        # parent.parent.parent 到达 python/ 目录
        self.base_dir = Path(__file__).parent.parent.parent

        # 归档路径相对于项目根目录
        self.archive_path = (self.base_dir.parent / config['storage']['archive_path']).resolve()

        # 添加断言验证
        assert self.archive_path.parent.exists(), \
            f"归档路径父目录不存在: {self.archive_path.parent}"
```

---

#### 5. **日志和错误处理统一** 🟡 P1

所有 Scraper 组件必须使用统一的日志系统：

```python
from src.utils.logger import get_logger

class Archiver:
    def __init__(self, config):
        self.logger = get_logger()

    async def _archive_post(self, page, post_info):
        try:
            # ... 归档逻辑
            self.logger.info(f"成功归档: {post_info['title']}")
        except Exception as e:
            self.logger.error(f"归档失败: {post_info['url']}", exc_info=True)
            raise
```

详细设计见 `ADR-002_Python_Migration_Plan.md` 第 5.2.3 节

---

#### 6. **性能要求** 🟢 P2

Python 版本不应慢于 Node.js 20% 以上。

**优化要点**:
- 使用异步并发下载（`asyncio.gather`）
- 浏览器 headless 模式
- 合理的延迟设置（`rate_limit_delay`）

详细测试见 [PHASE2_TESTING.md](./PHASE2_TESTING.md) Test 7

---

### 前置准备

#### 1. 更新依赖

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 安装 Phase 2 依赖
pip install playwright aiohttp beautifulsoup4 tqdm requests

# 安装 Playwright 浏览器
playwright install chromium

# 验证安装
python check_dependencies.py
```

#### 2. 创建必要的工具模块

```bash
# 创建文件
touch src/scraper/__init__.py
touch src/scraper/archiver.py
touch src/scraper/extractor.py
touch src/scraper/downloader.py
touch src/scraper/follower.py
touch src/scraper/utils.py
```

---

### 实施步骤

#### 第一步: 实现工具函数（src/scraper/utils.py）

**代码**: 见 `ADR-002_Python_Migration_Plan.md` 第 5.2.3 节

**必须实现**:
- `sanitize_filename()` - 文件名安全化
- `check_post_exists()` - 增量检查
- `mark_post_complete()` - 完整性标记
- `build_post_path()` - 路径构建

**测试**: 运行 `PHASE2_TESTING.md` Test 1, 3

---

#### 第二步: 实现 Extractor 类（src/scraper/extractor.py）

```python
"""内容提取器"""
from playwright.async_api import Page
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List
import re

class Extractor:
    """帖子内容提取器"""

    def __init__(self, config: dict):
        self.config = config

    async def extract_metadata(self, page: Page) -> Dict:
        """提取帖子元数据

        Returns:
            {
                'title': str,
                'author': str,
                'date': datetime,
                'url': str
            }
        """
        # 提取标题
        title_el = await page.wait_for_selector('h4.f16', timeout=10000)
        title = (await title_el.text_content()).strip()

        # 提取作者
        author_el = await page.wait_for_selector('.tr1.do_not_catch b', timeout=10000)
        author = (await author_el.text_content()).strip()

        # 提取时间戳
        timestamp_el = await page.wait_for_selector('span[data-timestamp]', timeout=10000)
        timestamp = await timestamp_el.get_attribute('data-timestamp')
        date = datetime.fromtimestamp(int(timestamp))

        return {
            'title': title,
            'author': author,
            'date': date,
            'url': page.url
        }

    async def extract_content(self, page: Page) -> str:
        """提取帖子正文内容

        Returns:
            清理后的文本内容
        """
        content_el = await page.wait_for_selector('.tpc_content', timeout=10000)
        raw_html = await content_el.inner_html()

        # 使用 BeautifulSoup 清理 HTML
        soup = BeautifulSoup(raw_html, 'html.parser')

        # 移除脚本和样式
        for script in soup(['script', 'style']):
            script.decompose()

        # 获取文本
        text = soup.get_text()

        # 清理多余空白
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)

        return text

    async def extract_media(self, page: Page) -> List[Dict]:
        """提取图片和视频链接

        Returns:
            [{'type': 'image'|'video', 'url': str, 'filename': str}, ...]
        """
        media_list = []

        # 提取图片
        img_els = await page.query_selector_all('.tpc_content img[src]')
        for img_el in img_els:
            src = await img_el.get_attribute('src')
            if src and not src.startswith('data:'):
                filename = src.split('/')[-1].split('?')[0]
                media_list.append({
                    'type': 'image',
                    'url': src,
                    'filename': filename
                })

        # 提取视频（如果有）
        video_els = await page.query_selector_all('.tpc_content video source[src], .tpc_content a[href*=".mp4"]')
        for video_el in video_els:
            src = await video_el.get_attribute('src') or await video_el.get_attribute('href')
            if src:
                filename = src.split('/')[-1].split('?')[0]
                media_list.append({
                    'type': 'video',
                    'url': src,
                    'filename': filename
                })

        return media_list
```

**测试**: 运行 `PHASE2_TESTING.md` Test 5

---

#### 第三步: 实现 Downloader 类（src/scraper/downloader.py）

```python
"""媒体下载器"""
import aiohttp
import asyncio
from pathlib import Path
from typing import List, Dict
from asyncio import Semaphore
from tqdm.asyncio import tqdm_asyncio

from ..utils.logger import get_logger

class Downloader:
    """媒体文件下载器"""

    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger()

        # 并发控制
        self.max_concurrent = config['advanced']['parallel_downloads']
        self.semaphore = Semaphore(self.max_concurrent)

        # 下载设置
        self.timeout = aiohttp.ClientTimeout(
            total=config['advanced']['download_timeout']
        )
        self.retry = config['advanced']['download_retry']

    async def download_batch(self, media_list: List[Dict], post_dir: Path) -> Dict:
        """批量下载媒体文件

        Args:
            media_list: 媒体列表
            post_dir: 帖子目录

        Returns:
            {'success': int, 'failed': int, 'skipped': int, 'errors': List[str]}
        """
        stats = {'success': 0, 'failed': 0, 'skipped': 0, 'errors': []}

        # 过滤需要下载的类型
        download_images = self.config['storage']['download']['images']
        download_videos = self.config['storage']['download']['videos']

        filtered = []
        for media in media_list:
            if media['type'] == 'image' and download_images:
                filtered.append(media)
            elif media['type'] == 'video' and download_videos:
                filtered.append(media)
            else:
                stats['skipped'] += 1

        if not filtered:
            return stats

        # 并发下载
        async def download_with_semaphore(media_info):
            async with self.semaphore:
                try:
                    await self._download_single(media_info, post_dir)
                    stats['success'] += 1
                except Exception as e:
                    stats['failed'] += 1
                    error_msg = f"{media_info['url']}: {str(e)}"
                    stats['errors'].append(error_msg)
                    self.logger.error(f"下载失败: {error_msg}")

        tasks = [download_with_semaphore(m) for m in filtered]

        # 使用 tqdm 显示进度
        await tqdm_asyncio.gather(*tasks, desc="下载媒体")

        return stats

    async def _download_single(self, media_info: Dict, post_dir: Path) -> None:
        """下载单个媒体文件

        Args:
            media_info: {'type': ..., 'url': ..., 'filename': ...}
            post_dir: 帖子目录

        Raises:
            Exception: 下载失败
        """
        url = media_info['url']
        filename = media_info['filename']
        media_type = media_info['type']

        # 确定保存路径
        if media_type == 'image':
            save_dir = post_dir / 'photo'
        elif media_type == 'video':
            save_dir = post_dir / 'video'
        else:
            raise ValueError(f"未知媒体类型: {media_type}")

        save_dir.mkdir(exist_ok=True)
        save_path = save_dir / filename

        # 如果文件已存在，跳过
        if save_path.exists():
            self.logger.debug(f"文件已存在，跳过: {filename}")
            return

        # 下载文件（带重试）
        for attempt in range(self.retry):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url) as response:
                        response.raise_for_status()

                        # 检查文件大小
                        content_length = response.headers.get('Content-Length')
                        if content_length:
                            size_mb = int(content_length) / (1024 * 1024)
                            max_size = self.config['storage']['download']['max_file_size_mb']
                            if size_mb > max_size:
                                raise ValueError(f"文件过大: {size_mb:.1f}MB > {max_size}MB")

                        # 写入文件
                        with open(save_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)

                self.logger.debug(f"下载成功: {filename}")
                return

            except Exception as e:
                if attempt == self.retry - 1:
                    # 最后一次尝试仍失败
                    raise
                else:
                    self.logger.warning(f"下载失败，重试 {attempt+1}/{self.retry}: {url}")
                    await asyncio.sleep(1)
```

---

#### 第四步: 实现 Archiver 类（src/scraper/archiver.py）

**代码**: 见 `ADR-002_Python_Migration_Plan.md` 第 5.2.3 节（完整的 Archiver 类示例）

**关键方法**:
- `archive_authors()` - 主入口
- `_collect_posts()` - 收集帖子链接
- `_archive_post()` - 归档单个帖子
- `_generate_markdown()` - 生成 Markdown 文件

**测试**: 运行 `PHASE2_TESTING.md` Test 4, 6

---

#### 第五步: 菜单集成

修改 `src/menu/main_menu.py`，添加 Python 爬虫调用：

```python
def _run_update(self) -> None:
    """立即更新所有作者"""
    # 检查是否使用 Python 爬虫
    use_python = self.config.get('experimental', {}).get('use_python_scraper', False)

    if use_python:
        # Python 版本
        self._run_update_python()
    else:
        # Node.js 版本（原有逻辑）
        self._run_update_nodejs()

def _run_update_python(self) -> None:
    """Python 版本更新"""
    import asyncio
    from src.scraper.archiver import Archiver

    self.console.print(f"\n[cyan]正在使用 Python 爬虫更新...[/cyan]\n")

    authors = [a['name'] for a in self.config['followed_authors']]

    try:
        archiver = Archiver(self.config)
        stats = asyncio.run(archiver.archive_authors(authors))

        self.console.print(f"\n[green]✓ 更新完成[/green]")
        self.console.print(f"  总计: {stats['total']}")
        self.console.print(f"  新增: {stats['new']}")
        self.console.print(f"  跳过: {stats['skipped']}")
        self.console.print(f"  失败: {stats['failed']}")
    except Exception as e:
        self.console.print(f"\n[red]✗ 更新失败: {str(e)}[/red]")

        # 如果配置了回退
        if self.config.get('experimental', {}).get('fallback_to_nodejs', False):
            self.console.print("[yellow]⚠️  切换到 Node.js 版本重试...[/yellow]")
            self._run_update_nodejs()
    finally:
        questionary.press_any_key_to_continue("按任意键继续...").ask()
```

**测试**: 运行 `PHASE2_TESTING.md` Test 8

---

### 验收标准

完成 Phase 2 后，运行以下验收测试：

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 运行完整测试套件
pytest tests/phase2/ -v

# 运行一致性对比测试
python validate_phase2.py

# 运行性能基准测试
python benchmark_phase2.py
```

**必须通过**:
- ✅ 所有 P0 测试（文件名、收集、提取）
- ✅ 性能测试（不慢于 Node.js 120%）
- ✅ 完整归档流程测试

**文档**: 详见 [PHASE2_TESTING.md](./PHASE2_TESTING.md)

---

## Phase 3: 数据库

**状态**: 🔴 未开始

---

## Phase 4: 数据分析

**状态**: 🔴 未开始

---

## Phase 5: 完善优化

**状态**: 🔴 未开始

---

## 测试检查清单

### 功能测试

```bash
# 1. 配置测试
python3 -c "from src.config.manager import ConfigManager; cm = ConfigManager(); print(cm.load())"

# 2. 桥接测试
python3 -c "from src.bridge.nodejs_bridge import NodeJSBridge; bridge = NodeJSBridge(); print('✓ 桥接器正常')"

# 3. 菜单测试
python main.py
```

### 对比测试

```bash
# 测试 Node.js 版本
cd ..
node run_scheduled_update.js

# 测试 Python 版本（Phase 1 通过桥接）
cd python
python main.py
# 选择 "立即更新所有作者"

# 对比输出是否一致
```

---

## 故障排除

### 问题1：导入错误

```
ModuleNotFoundError: No module named 'src'
```

**解决**:
```bash
# 确保在 python/ 目录下运行
cd python
python main.py
```

### 问题2：Node.js 脚本找不到

```
FileNotFoundError: Node.js 目录不存在
```

**解决**:
```bash
# 检查目录结构
ls -la ../
# 应该能看到 Node.js 脚本文件

# 或修改 config.yaml 中的 legacy.nodejs_path
```

### 问题3：配置迁移失败

```bash
# 手动检查
cat ../config.json
cat config.yaml

# 手动迁移
python3 -c "from src.config.manager import ConfigManager; cm = ConfigManager(); cm._migrate_from_json()"
```

---

**Phase 1 完成后，继续 Phase 2...**
