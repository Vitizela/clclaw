# 状态面板增强设计规范

**功能名称**: 主菜单状态面板信息增强
**版本**: 1.0
**创建日期**: 2026-02-15
**关联需求**: [STATUS_PANEL_REQUIREMENTS.md](STATUS_PANEL_REQUIREMENTS.md)

---

## 📋 目录

1. [架构设计](#架构设计)
2. [数据模型](#数据模型)
3. [接口设计](#接口设计)
4. [布局设计](#布局设计)
5. [实现细节](#实现细节)
6. [错误处理](#错误处理)
7. [性能优化](#性能优化)
8. [测试策略](#测试策略)

---

## 🏗️ 架构设计

### 系统概览

```
┌─────────────────────────────────────────────────┐
│              MainMenu (主菜单)                   │
│  ┌───────────────────────────────────────────┐  │
│  │   _show_status() - 显示状态面板           │  │
│  └──────────────┬────────────────────────────┘  │
│                 │                                │
│                 ▼                                │
│  ┌───────────────────────────────────────────┐  │
│  │   SystemInfoCollector (信息收集器)        │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │ get_program_info()   - 程序信息     │  │  │
│  │  │ get_system_info()    - 系统信息     │  │  │
│  │  │ get_resource_info()  - 资源信息     │  │  │
│  │  │ get_scheduler_info() - 调度器信息   │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │   StatusPanelFormatter (格式化器)         │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │ format_panel()  - 格式化完整面板    │  │  │
│  │  │ format_row()    - 格式化单行        │  │  │
│  │  │ align_columns() - 对齐列            │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 设计原则

1. **单一职责**: 信息收集、格式化、显示分离
2. **低耦合**: 各模块独立，便于测试
3. **容错性**: 任何信息获取失败不影响整体
4. **性能优先**: 缓存静态信息，避免重复计算
5. **可扩展**: 便于未来添加新信息项

---

## 📊 数据模型

### SystemInfo 数据结构

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class ProgramInfo:
    """程序状态信息"""
    start_time: datetime      # 启动时间
    uptime_seconds: int       # 运行秒数
    uptime_str: str           # 运行时长（格式化）
    scheduler_status: str     # 调度器状态 ("运行中" | "已停止" | "未启用")
    active_tasks: int         # 活跃任务数

    def __post_init__(self):
        """自动计算运行时长字符串"""
        hours = self.uptime_seconds // 3600
        minutes = (self.uptime_seconds % 3600) // 60

        if hours > 0:
            self.uptime_str = f"{hours}h {minutes}m"
        else:
            self.uptime_str = f"{minutes}m"


@dataclass
class SystemInfo:
    """系统信息"""
    os_name: str              # OS 名称 (如 "Ubuntu")
    os_version: str           # OS 版本 (如 "22.04")
    os_display: str           # 显示字符串 (如 "Ubuntu 22.04")
    python_version: str       # Python 版本 (如 "3.10.12")
    hostname: str             # 主机名
    ip_address: str           # IP 地址

    @classmethod
    def from_platform(cls):
        """从系统平台信息构造"""
        # 实现见后文


@dataclass
class ResourceInfo:
    """资源使用信息"""
    memory_percent: float     # 内存使用率 (0-100)
    memory_used_gb: float     # 已用内存 (GB)
    memory_total_gb: float    # 总内存 (GB)
    disk_percent: float       # 磁盘使用率 (0-100)
    disk_used_gb: float       # 已用磁盘 (GB)
    disk_total_gb: float      # 总磁盘 (GB)


@dataclass
class StatusPanelData:
    """状态面板完整数据"""
    # 业务信息 (现有)
    followed_authors: int     # 关注作者数
    forum_url: str            # 论坛 URL
    archive_path: str         # 归档路径

    # 新增信息
    program_info: ProgramInfo
    system_info: SystemInfo
    resource_info: ResourceInfo
```

---

## 🔌 接口设计

### SystemInfoCollector 类

```python
class SystemInfoCollector:
    """系统信息收集器

    职责：
    - 收集程序、系统、资源信息
    - 缓存静态信息
    - 提供容错机制
    """

    def __init__(self, start_time: datetime):
        """
        初始化收集器

        Args:
            start_time: 程序启动时间
        """
        self.start_time = start_time

        # 缓存静态信息
        self._system_info: Optional[SystemInfo] = None
        self._system_info_cached = False

    def get_program_info(self, scheduler=None) -> ProgramInfo:
        """
        获取程序状态信息

        Args:
            scheduler: 调度器实例（可选）

        Returns:
            ProgramInfo 实例
        """
        uptime_seconds = int((datetime.now() - self.start_time).total_seconds())

        # 获取调度器状态
        if scheduler is None:
            scheduler_status = "未启用"
            active_tasks = 0
        elif scheduler.is_running():
            scheduler_status = "运行中"
            active_tasks = scheduler.get_task_count()
        else:
            scheduler_status = "已停止"
            active_tasks = scheduler.get_task_count()

        return ProgramInfo(
            start_time=self.start_time,
            uptime_seconds=uptime_seconds,
            uptime_str="",  # 由 __post_init__ 自动计算
            scheduler_status=scheduler_status,
            active_tasks=active_tasks
        )

    def get_system_info(self) -> SystemInfo:
        """
        获取系统信息（带缓存）

        Returns:
            SystemInfo 实例
        """
        if not self._system_info_cached:
            self._system_info = self._collect_system_info()
            self._system_info_cached = True

        return self._system_info

    def get_resource_info(self) -> ResourceInfo:
        """
        获取资源使用信息

        Returns:
            ResourceInfo 实例
        """
        try:
            import psutil

            # 内存信息
            mem = psutil.virtual_memory()
            memory_percent = mem.percent
            memory_used_gb = mem.used / (1024 ** 3)
            memory_total_gb = mem.total / (1024 ** 3)

            # 磁盘信息（可选）
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)

        except Exception as e:
            # 容错：返回默认值
            memory_percent = 0.0
            memory_used_gb = 0.0
            memory_total_gb = 0.0
            disk_percent = 0.0
            disk_used_gb = 0.0
            disk_total_gb = 0.0

        return ResourceInfo(
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb
        )

    def _collect_system_info(self) -> SystemInfo:
        """内部方法：收集系统信息"""
        import platform
        import socket

        try:
            # OS 信息
            os_system = platform.system()

            if os_system == "Linux":
                # 尝试读取发行版信息
                try:
                    import distro
                    os_name = distro.name()
                    os_version = distro.version()
                except ImportError:
                    # 回退方案
                    os_name = "Linux"
                    os_version = platform.release()
            elif os_system == "Darwin":
                os_name = "macOS"
                os_version = platform.mac_ver()[0]
            elif os_system == "Windows":
                os_name = "Windows"
                os_version = platform.release()
            else:
                os_name = os_system
                os_version = platform.release()

            # 格式化显示
            os_display = f"{os_name} {os_version}"

            # Python 版本
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

            # 主机名
            hostname = socket.gethostname()

            # IP 地址
            ip_address = self._get_ip_address()

        except Exception as e:
            # 容错：返回默认值
            os_name = "Unknown"
            os_version = ""
            os_display = "Unknown OS"
            python_version = "Unknown"
            hostname = "Unknown"
            ip_address = "Unknown"

        return SystemInfo(
            os_name=os_name,
            os_version=os_version,
            os_display=os_display,
            python_version=python_version,
            hostname=hostname,
            ip_address=ip_address
        )

    def _get_ip_address(self) -> str:
        """获取主 IP 地址（局域网地址优先）"""
        import socket

        try:
            # 方法 1: 连接外部地址获取本地 IP（不实际发送数据）
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            pass

        try:
            # 方法 2: 获取主机名对应的 IP
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip != "127.0.0.1":
                return ip
        except Exception:
            pass

        # 方法 3: 回退到 localhost
        return "127.0.0.1"
```

---

### StatusPanelFormatter 类

```python
class StatusPanelFormatter:
    """状态面板格式化器

    职责：
    - 格式化状态面板布局
    - 处理列对齐
    - 生成 Rich Panel
    """

    @staticmethod
    def format_panel(data: StatusPanelData) -> Panel:
        """
        格式化完整状态面板

        Args:
            data: StatusPanelData 实例

        Returns:
            Rich Panel 对象
        """
        from rich.panel import Panel
        from rich.text import Text

        # 构建面板内容
        lines = []

        # 第 1 行：关注作者 + 归档路径
        lines.append(
            f"关注作者: {data.followed_authors} 位  │  "
            f"归档路径: {data.archive_path}"
        )

        # 第 2 行：论坛版块
        lines.append(f"论坛版块: {data.forum_url}")

        # 第 3 行：程序状态
        prog = data.program_info
        res = data.resource_info

        if prog.scheduler_status == "运行中":
            scheduler_icon = "🟢"
        elif prog.scheduler_status == "已停止":
            scheduler_icon = "🟡"
        else:
            scheduler_icon = "🔴"

        lines.append(
            f"⏱️  运行: {prog.uptime_str}  │  "
            f"🕐 启动: {prog.start_time.strftime('%m-%d %H:%M')}  │  "
            f"⚙️  调度器: {scheduler_icon} {prog.active_tasks} 任务  │  "
            f"💾 内存: {res.memory_percent:.0f}%"
        )

        # 第 4 行：系统信息
        sys = data.system_info
        lines.append(
            f"💻 {sys.os_display}  │  "
            f"🐍 Python {sys.python_version}  │  "
            f"📡 {sys.ip_address}"
        )

        # 合并为文本
        content = "\n".join(lines)

        # 创建 Panel
        panel = Panel(
            content,
            title="📊 论坛作者订阅归档系统",
            border_style="cyan"
        )

        return panel
```

---

## 🎨 布局设计

### 详细布局规范

```
╭─────────────────────────────── 📊 论坛作者订阅归档系统 ───────────────────────────────╮
│ 关注作者: 14 位  │  归档路径: /home/ben/Download/t66y                                │  ← 第 1 行（业务信息 1）
│ 论坛版块: https://t66y.com/thread0806.php?fid=7                                     │  ← 第 2 行（业务信息 2）
│ ⏱️  运行: 2h 15m  │  🕐 启动: 02-15 22:30  │  ⚙️  调度器: 🟢 2 任务  │  💾 内存: 52%   │  ← 第 3 行（动态状态）
│ 💻 Ubuntu 22.04  │  🐍 Python 3.10.12  │  📡 192.168.1.100                          │  ← 第 4 行（静态信息）
╰──────────────────────────────────────────────────────────────────────────────────╯
```

### 行结构

| 行号 | 内容 | 信息类型 | 更新频率 |
|------|------|----------|----------|
| **1** | 关注作者 + 归档路径 | 业务信息 | 配置变更时 |
| **2** | 论坛版块 URL | 业务信息 | 配置变更时 |
| **3** | 运行时长 + 启动时间 + 调度器 + 内存 | 动态状态 | 每次显示 |
| **4** | OS + Python + IP | 静态信息 | 启动时一次 |

### 图标使用规范

| 图标 | 含义 | 使用场景 |
|------|------|----------|
| ⏱️ | 运行时长 | 程序运行时间 |
| 🕐 | 启动时间 | 程序启动时间点 |
| ⚙️ | 调度器 | 调度器状态 |
| 🟢 | 运行中 | 调度器运行中 |
| 🟡 | 已停止 | 调度器已停止 |
| 🔴 | 未启用 | 调度器未启用 |
| 💾 | 内存 | 内存使用率 |
| 💻 | 操作系统 | OS 信息 |
| 🐍 | Python | Python 版本 |
| 📡 | 网络 | IP 地址 |

### 分隔符规范

- **列分隔符**: `  │  ` (2 空格 + 竖线 + 2 空格)
- **边框**: Rich Panel 自动生成
- **对齐**: 左对齐

---

## 🔧 实现细节

### MainMenu 类修改

```python
class MainMenu:
    """主菜单系统"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.console = Console()
        # ... 现有代码 ...

        # 新增：记录启动时间
        self.start_time = datetime.now()

        # 新增：初始化信息收集器
        self.info_collector = SystemInfoCollector(self.start_time)

        # 新增：调度器引用（可选）
        self.scheduler = None  # 将在进入调度器菜单时设置

    def _show_status(self) -> None:
        """显示系统状态（修改版）"""
        self.console.clear()

        # 收集信息
        program_info = self.info_collector.get_program_info(self.scheduler)
        system_info = self.info_collector.get_system_info()
        resource_info = self.info_collector.get_resource_info()

        # 构建数据
        panel_data = StatusPanelData(
            followed_authors=len(self.config['followed_authors']),
            forum_url=self.config['forum']['section_url'],
            archive_path=self.config['storage']['archive_path'],
            program_info=program_info,
            system_info=system_info,
            resource_info=resource_info
        )

        # 格式化并显示
        panel = StatusPanelFormatter.format_panel(panel_data)
        self.console.print(panel)

    def _show_scheduler(self) -> None:
        """定时任务管理（修改版）"""
        from ..menu.scheduler_menu import SchedulerMenu
        try:
            scheduler_menu = SchedulerMenu(self.config)

            # 设置调度器引用（用于状态显示）
            self.scheduler = scheduler_menu.scheduler

            scheduler_menu.show()
        except Exception as e:
            # ... 错误处理 ...
```

---

## ⚠️ 错误处理

### 容错策略

| 错误场景 | 处理方式 | 降级值 |
|----------|----------|--------|
| **psutil 未安装** | 捕获 ImportError | 内存显示 `N/A` |
| **IP 获取失败** | 多种方法尝试 | 显示 `127.0.0.1` 或 `Unknown` |
| **OS 信息获取失败** | 捕获异常 | 显示 `Unknown OS` |
| **调度器未初始化** | 检查 None | 显示 `未启用` |
| **时间计算溢出** | 异常捕获 | 显示 `0m` |

### 错误日志

```python
import logging

logger = logging.getLogger('status_panel')

def get_system_info(self) -> SystemInfo:
    try:
        # ... 收集信息 ...
    except Exception as e:
        logger.warning(f"获取系统信息失败: {e}")
        return SystemInfo.default()  # 返回默认值
```

---

## ⚡ 性能优化

### 优化策略

1. **静态信息缓存**
   ```python
   # ✅ 好的做法
   if not self._system_info_cached:
       self._system_info = self._collect_system_info()
       self._system_info_cached = True
   return self._system_info

   # ❌ 坏的做法
   return self._collect_system_info()  # 每次都重新获取
   ```

2. **延迟导入**
   ```python
   # ✅ 好的做法
   def get_resource_info(self):
       import psutil  # 只在需要时导入
       # ...

   # ❌ 坏的做法
   import psutil  # 模块顶部导入（总是加载）
   ```

3. **快速失败**
   ```python
   # ✅ 好的做法
   try:
       ip = self._get_ip_address()
   except Exception:
       return "Unknown"  # 立即返回

   # ❌ 坏的做法
   # 多次重试，增加延迟
   ```

### 性能目标

| 操作 | 目标时间 |
|------|----------|
| `get_program_info()` | < 1ms |
| `get_system_info()` (首次) | < 50ms |
| `get_system_info()` (缓存) | < 0.1ms |
| `get_resource_info()` | < 10ms |
| `format_panel()` | < 5ms |
| **总延迟** | **< 100ms** |

---

## 🧪 测试策略

### 单元测试

```python
# tests/test_system_info_collector.py

import pytest
from datetime import datetime, timedelta
from menu.system_info import SystemInfoCollector

def test_program_info_uptime_calculation():
    """测试运行时长计算"""
    start_time = datetime.now() - timedelta(hours=2, minutes=15)
    collector = SystemInfoCollector(start_time)

    info = collector.get_program_info()

    assert info.uptime_str == "2h 15m"

def test_program_info_without_scheduler():
    """测试无调度器时的状态"""
    collector = SystemInfoCollector(datetime.now())

    info = collector.get_program_info(scheduler=None)

    assert info.scheduler_status == "未启用"
    assert info.active_tasks == 0

def test_system_info_caching():
    """测试系统信息缓存"""
    collector = SystemInfoCollector(datetime.now())

    info1 = collector.get_system_info()
    info2 = collector.get_system_info()

    # 应返回相同对象（缓存）
    assert info1 is info2

def test_resource_info_fallback():
    """测试资源信息获取失败时的降级"""
    # 模拟 psutil 不可用
    with pytest.mock.patch('psutil.virtual_memory', side_effect=Exception):
        collector = SystemInfoCollector(datetime.now())
        info = collector.get_resource_info()

        assert info.memory_percent == 0.0

def test_ip_address_fallback():
    """测试 IP 获取失败时的降级"""
    collector = SystemInfoCollector(datetime.now())

    ip = collector._get_ip_address()

    # 应返回有效 IP 或 127.0.0.1
    assert ip in ("127.0.0.1", "Unknown") or "." in ip
```

### 集成测试

```python
# tests/test_status_panel_integration.py

def test_status_panel_display():
    """测试状态面板完整显示"""
    config_manager = ConfigManager()
    config = config_manager.load()

    menu = MainMenu(config)

    # 捕获输出
    import io
    import sys
    captured_output = io.StringIO()
    sys.stdout = captured_output

    menu._show_status()

    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()

    # 验证关键信息存在
    assert "关注作者" in output
    assert "运行" in output
    assert "Python" in output

def test_status_panel_with_scheduler():
    """测试带调度器状态的面板"""
    config_manager = ConfigManager()
    config = config_manager.load()

    menu = MainMenu(config)

    # 模拟调度器
    from scheduler.task_scheduler import TaskScheduler
    scheduler = TaskScheduler(config)
    menu.scheduler = scheduler

    # ... 验证调度器状态显示 ...
```

---

## 📁 文件结构

```
python/src/menu/
├── main_menu.py                (修改：集成新功能)
├── system_info.py              (新增：信息收集器)
└── status_panel_formatter.py   (新增：面板格式化器)

tests/
├── test_system_info_collector.py    (新增：单元测试)
└── test_status_panel_integration.py (新增：集成测试)
```

---

## 🔄 版本兼容性

### Python 版本支持

| Python 版本 | 支持状态 | 备注 |
|-------------|----------|------|
| 3.8 | ✅ 支持 | psutil 5.9.8 兼容 |
| 3.9 | ✅ 支持 | |
| 3.10 | ✅ 支持 | 推荐版本 |
| 3.11 | ✅ 支持 | |
| 3.12 | ✅ 支持 | |
| 3.13 | ✅ 支持 | |

### 依赖版本

```txt
# requirements.txt 新增
psutil==5.9.8           # 系统资源监控
distro==1.9.0           # Linux 发行版信息（可选）
```

---

## 📊 关键指标

### 开发指标

- **新增代码**: ~400 行
- **修改代码**: ~50 行
- **测试代码**: ~300 行
- **开发工时**: 4 小时

### 运行时指标

- **内存占用**: < 5MB（psutil）
- **启动延迟**: < 100ms
- **刷新延迟**: < 100ms

---

## 📝 变更日志

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0 | 2026-02-15 | 初始设计规范 |

---

## 🔗 相关文档

- [功能需求文档](STATUS_PANEL_REQUIREMENTS.md)
- [实施计划](STATUS_PANEL_IMPLEMENTATION_PLAN.md) (待创建)
- [测试报告](STATUS_PANEL_TEST_REPORT.md) (待创建)

---

**设计审核**: 待审核
**最后更新**: 2026-02-15
**文档版本**: 1.0
