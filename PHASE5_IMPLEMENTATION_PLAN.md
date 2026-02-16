# Phase 5 实施计划：调度器与 MQTT 通知

## 执行摘要

**目标**: 实现定时任务调度和 MQTT 消息发布功能

**工期**: 10 天（2026-02-15 至 2026-02-24）

**核心模块**:
- `TaskScheduler` - APScheduler 封装，Cron 表达式调度
- `IncrementalArchiver` - 增量归档（只下载新帖）
- `NotificationManager` - 通知管理器（多通道）
- `MQTTNotifier` - MQTT 消息发布
- `SchedulerMenu` - 任务管理菜单

**关键依赖**:
- `apscheduler==3.10.4` - 任务调度
- `paho-mqtt==1.6.1` - MQTT 客户端

**架构图**:
```
┌──────────────────┐         ┌──────────────────┐
│  SchedulerMenu   │────────>│  TaskScheduler   │
└──────────────────┘         └──────────────────┘
                                      │
                                      │ trigger
                                      v
                             ┌──────────────────┐
                             │Incremental       │
                             │Archiver          │
                             └──────────────────┘
                                      │
                                      │ notify
                                      v
                             ┌──────────────────┐
                             │Notification      │
                             │Manager           │
                             └──────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    v                 v                 v
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │Console       │  │File          │  │MQTT          │
            │Notifier      │  │Notifier      │  │Notifier      │
            └──────────────┘  └──────────────┘  └──────────────┘
                                                        │
                                                        v
                                                  MQTT Broker
                                                        │
                                                        v
                                                  Message Handler
                                                        │
                                                        v
                                                  Telegram Bot
```

---

## 1. 整体设计概览

### 1.1 核心需求回顾

**F-01: 作者选择**
- 从数据库读取作者列表（已归档作者）
- 用户勾选需要定时下载的作者
- 保存选择到配置文件

**F-02: 增量下载**
- 调用 PostChecker 检测新帖
- 只归档新帖 URL（避免重复下载）
- 使用 ForumArchiver.archive_author(target_urls=[...])

**F-03: 任务调度**
- Cron 表达式配置（例如 "0 2 * * *" 每天凌晨2点）
- APScheduler 后台运行
- 任务状态管理（启动/暂停/删除）

**F-04: MQTT 通知**
- 发布结构化 JSON 消息
- Topic: `t66y/scheduler/events`
- 事件类型: task_completed, task_error, new_posts_found

**F-05: 配置管理**
- 配置文件 `config.yaml` 扩展
- MQTT Broker 连接信息
- 调度任务持久化（scheduler_tasks.json）

---

### 1.2 技术栈

| 组件 | 库 | 版本 | 用途 |
|------|-----|------|------|
| 任务调度 | APScheduler | 3.10.4 | Cron 表达式调度 |
| MQTT 客户端 | paho-mqtt | 1.6.1 | 消息发布 |
| 数据库 | sqlite3 | 内置 | 查询作者列表 |
| 配置管理 | PyYAML | 6.0.1 | 读写配置 |
| 交互菜单 | questionary | 2.0.1 | 用户界面 |

---

### 1.3 文件清单

#### 新建文件

```
python/src/
├── scheduler/
│   ├── __init__.py           (10 行，导出类)
│   ├── task_scheduler.py     (300 行，APScheduler 封装)
│   └── incremental_archiver.py (150 行，增量归档逻辑)
├── notification/
│   ├── __init__.py           (10 行，导出类)
│   ├── manager.py            (200 行，通知管理器)
│   ├── console_notifier.py   (80 行，控制台输出)
│   ├── file_notifier.py      (80 行，日志文件记录)
│   └── mqtt_notifier.py      (250 行，MQTT 发布)
└── menu/
    └── scheduler_menu.py     (400 行，调度器菜单)

python/tools/
└── mqtt_to_telegram.py       (150 行，示例消息处理器)

python/data/
└── scheduler_tasks.json      (动态生成，任务配置)

python/
└── test_phase5_scheduler.py  (400 行，集成测试)
```

#### 修改文件

```
python/requirements.txt       (+2 行，新增依赖)
python/config.yaml            (+15 行，MQTT 配置)
python/src/menu/main_menu.py  (+5 行，调度器菜单入口)
```

---

## 2. 详细实施步骤

### Day 1: 环境准备和基础模块 (Task #19)

#### 子任务 1.1: 安装依赖（30 分钟）

**步骤**:
1. 编辑 `python/requirements.txt`
2. 添加新依赖:
   ```
   # ============ Phase 5: 调度器与通知 ============
   apscheduler==3.10.4        # 任务调度
   paho-mqtt==1.6.1           # MQTT 客户端
   ```
3. 安装: `pip install -r python/requirements.txt`

**验收**:
```bash
python -c "import apscheduler; print(apscheduler.__version__)"
python -c "import paho.mqtt.client as mqtt; print(mqtt.__version__)"
```

---

#### 子任务 1.2: 创建目录结构（10 分钟）

**步骤**:
```bash
mkdir -p python/src/scheduler
mkdir -p python/src/notification
mkdir -p python/tools
touch python/src/scheduler/__init__.py
touch python/src/notification/__init__.py
```

**验收**:
```bash
ls -d python/src/scheduler python/src/notification python/tools
```

---

#### 子任务 1.3: 实现 NotificationManager（1.5 小时）

**文件**: `python/src/notification/manager.py`

**代码结构**:
```python
# python/src/notification/manager.py

from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class NotifierBase(ABC):
    """通知器抽象基类"""

    @abstractmethod
    def should_send(self, level: str) -> bool:
        """判断是否应该发送此级别的消息"""
        pass

    @abstractmethod
    def send(self, message: str, level: str = 'INFO', **kwargs):
        """发送消息"""
        pass

    @abstractmethod
    def send_task_completion(self, result: Dict):
        """发送任务完成消息"""
        pass

    @abstractmethod
    def send_task_error(self, task_name: str, error: str):
        """发送任务失败消息"""
        pass

    @abstractmethod
    def send_new_posts_found(self, author_name: str, count: int):
        """发送发现新帖消息"""
        pass


class NotificationManager:
    """
    通知管理器

    职责：
    - 管理多个通知器（Console、File、MQTT）
    - 批量发送消息到所有通知器
    - 支持动态添加/移除通知器
    """

    def __init__(self):
        self.notifiers: List[NotifierBase] = []

    def add_notifier(self, notifier: NotifierBase):
        """添加通知器"""
        self.notifiers.append(notifier)

    def remove_notifier(self, notifier: NotifierBase):
        """移除通知器"""
        if notifier in self.notifiers:
            self.notifiers.remove(notifier)

    def send(self, message: str, level: str = 'INFO', **kwargs):
        """发送消息到所有通知器"""
        for notifier in self.notifiers:
            try:
                if notifier.should_send(level):
                    notifier.send(message, level, **kwargs)
            except Exception as e:
                print(f"⚠️  通知器发送失败: {e}")

    def send_task_completion(self, result: Dict):
        """发送任务完成消息"""
        for notifier in self.notifiers:
            try:
                notifier.send_task_completion(result)
            except Exception as e:
                print(f"⚠️  通知器发送失败: {e}")

    def send_task_error(self, task_name: str, error: str):
        """发送任务失败消息"""
        for notifier in self.notifiers:
            try:
                notifier.send_task_error(task_name, error)
            except Exception as e:
                print(f"⚠️  通知器发送失败: {e}")

    def send_new_posts_found(self, author_name: str, count: int):
        """发送发现新帖消息"""
        for notifier in self.notifiers:
            try:
                notifier.send_new_posts_found(author_name, count)
            except Exception as e:
                print(f"⚠️  通知器发送失败: {e}")
```

**验收**:
```python
from src.notification.manager import NotificationManager, NotifierBase

manager = NotificationManager()
assert len(manager.notifiers) == 0
```

---

#### 子任务 1.4: 实现 ConsoleNotifier（1 小时）

**文件**: `python/src/notification/console_notifier.py`

**代码结构**:
```python
# python/src/notification/console_notifier.py

from typing import Dict
from datetime import datetime
from .manager import NotifierBase


class ConsoleNotifier(NotifierBase):
    """
    控制台通知器

    职责：
    - 将消息打印到终端
    - 支持级别过滤（INFO/WARNING/ERROR）
    - 彩色输出（可选）
    """

    def __init__(self, config: dict):
        """
        初始化控制台通知器

        Args:
            config: 配置字典
                - min_level: 最低输出级别（DEBUG/INFO/WARNING/ERROR）
        """
        console_config = config.get('notification', {}).get('console', {})
        self.enabled = console_config.get('enabled', True)
        self.min_level = console_config.get('min_level', 'INFO')

        # 级别权重
        self.level_weights = {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 2,
            'ERROR': 3
        }

    def should_send(self, level: str) -> bool:
        """判断是否应该发送"""
        if not self.enabled:
            return False
        return self.level_weights.get(level, 1) >= self.level_weights.get(self.min_level, 1)

    def send(self, message: str, level: str = 'INFO', **kwargs):
        """发送消息"""
        if not self.should_send(level):
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        icon = self._get_icon(level)
        print(f"[{timestamp}] {icon} {message}")

    def send_task_completion(self, result: Dict):
        """发送任务完成消息"""
        if not self.enabled:
            return

        author = result.get('author_name', 'Unknown')
        new_posts = result.get('new_posts', 0)
        status = result.get('status', 'completed')

        if status == 'completed':
            print(f"✅ 任务完成: {author} - 新增 {new_posts} 篇帖子")
        else:
            print(f"⚠️  任务失败: {author}")

    def send_task_error(self, task_name: str, error: str):
        """发送任务失败消息"""
        if not self.enabled:
            return
        print(f"❌ 任务失败: {task_name} - {error}")

    def send_new_posts_found(self, author_name: str, count: int):
        """发送发现新帖消息"""
        if not self.enabled:
            return
        print(f"🔔 发现新帖: {author_name} - {count} 篇")

    def _get_icon(self, level: str) -> str:
        """获取级别图标"""
        icons = {
            'DEBUG': '🐛',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌'
        }
        return icons.get(level, 'ℹ️')
```

**验收**:
```python
from src.notification.console_notifier import ConsoleNotifier

config = {'notification': {'console': {'enabled': True, 'min_level': 'INFO'}}}
notifier = ConsoleNotifier(config)
notifier.send("测试消息", level='INFO')
# 应输出: [2026-02-15 ...] ℹ️ 测试消息
```

---

#### 子任务 1.5: 实现 FileNotifier（1 小时）

**文件**: `python/src/notification/file_notifier.py`

**代码结构**:
```python
# python/src/notification/file_notifier.py

from typing import Dict
from datetime import datetime
from pathlib import Path
from .manager import NotifierBase


class FileNotifier(NotifierBase):
    """
    文件通知器

    职责：
    - 将消息写入日志文件
    - 自动创建日志目录
    - 支持按日期分割日志
    """

    def __init__(self, config: dict):
        """
        初始化文件通知器

        Args:
            config: 配置字典
                - log_dir: 日志目录
                - log_file: 日志文件名
        """
        file_config = config.get('notification', {}).get('file', {})
        self.enabled = file_config.get('enabled', True)

        # 日志文件路径
        log_dir = Path(file_config.get('log_dir', 'logs'))
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = file_config.get('log_file', 'scheduler.log')
        self.log_path = log_dir / log_file

    def should_send(self, level: str) -> bool:
        """判断是否应该发送"""
        return self.enabled

    def send(self, message: str, level: str = 'INFO', **kwargs):
        """发送消息"""
        if not self.should_send(level):
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}\n"

        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_line)

    def send_task_completion(self, result: Dict):
        """发送任务完成消息"""
        if not self.enabled:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        author = result.get('author_name', 'Unknown')
        new_posts = result.get('new_posts', 0)
        status = result.get('status', 'completed')

        log_line = f"[{timestamp}] [TASK] {status.upper()} - {author} - 新增 {new_posts} 篇\n"

        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_line)

    def send_task_error(self, task_name: str, error: str):
        """发送任务失败消息"""
        if not self.enabled:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [ERROR] {task_name} - {error}\n"

        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_line)

    def send_new_posts_found(self, author_name: str, count: int):
        """发送发现新帖消息"""
        if not self.enabled:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [NEW] {author_name} - {count} 篇新帖\n"

        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_line)
```

**验收**:
```python
from src.notification.file_notifier import FileNotifier
from pathlib import Path

config = {'notification': {'file': {'enabled': True, 'log_dir': 'logs', 'log_file': 'test.log'}}}
notifier = FileNotifier(config)
notifier.send("测试消息", level='INFO')

# 检查日志文件
log_path = Path('logs/test.log')
assert log_path.exists()
content = log_path.read_text()
assert "测试消息" in content
```

---

#### 子任务 1.6: 导出类（10 分钟）

**文件**: `python/src/notification/__init__.py`

```python
# python/src/notification/__init__.py

from .manager import NotificationManager, NotifierBase
from .console_notifier import ConsoleNotifier
from .file_notifier import FileNotifier

__all__ = [
    'NotificationManager',
    'NotifierBase',
    'ConsoleNotifier',
    'FileNotifier',
]
```

---

#### 子任务 1.7: 单元测试（1 小时）

**文件**: `python/test_day1_notifications.py`

```python
#!/usr/bin/env python3
"""Day 1 单元测试：通知模块"""

from pathlib import Path
from src.notification import NotificationManager, ConsoleNotifier, FileNotifier


def test_notification_manager():
    """测试 1: NotificationManager 基础功能"""
    print("\n=== 测试 1: NotificationManager ===")

    manager = NotificationManager()
    assert len(manager.notifiers) == 0

    # 添加通知器
    console = ConsoleNotifier({'notification': {'console': {'enabled': True}}})
    manager.add_notifier(console)
    assert len(manager.notifiers) == 1

    # 移除通知器
    manager.remove_notifier(console)
    assert len(manager.notifiers) == 0

    print("✅ 通过")


def test_console_notifier():
    """测试 2: ConsoleNotifier"""
    print("\n=== 测试 2: ConsoleNotifier ===")

    config = {
        'notification': {
            'console': {
                'enabled': True,
                'min_level': 'INFO'
            }
        }
    }

    notifier = ConsoleNotifier(config)

    # 测试 should_send
    assert notifier.should_send('INFO') == True
    assert notifier.should_send('WARNING') == True
    assert notifier.should_send('DEBUG') == False

    # 测试发送消息
    notifier.send("测试消息", level='INFO')

    # 测试任务完成消息
    result = {
        'author_name': '测试作者',
        'new_posts': 5,
        'status': 'completed'
    }
    notifier.send_task_completion(result)

    print("✅ 通过")


def test_file_notifier():
    """测试 3: FileNotifier"""
    print("\n=== 测试 3: FileNotifier ===")

    # 使用临时日志文件
    config = {
        'notification': {
            'file': {
                'enabled': True,
                'log_dir': 'logs',
                'log_file': 'test_day1.log'
            }
        }
    }

    notifier = FileNotifier(config)

    # 发送消息
    notifier.send("测试日志", level='INFO')

    # 检查文件
    log_path = Path('logs/test_day1.log')
    assert log_path.exists(), "日志文件不存在"

    content = log_path.read_text(encoding='utf-8')
    assert "测试日志" in content, "日志内容不匹配"

    print(f"✅ 通过: {log_path}")


def test_manager_integration():
    """测试 4: NotificationManager 集成"""
    print("\n=== 测试 4: 集成测试 ===")

    config = {
        'notification': {
            'console': {'enabled': True, 'min_level': 'INFO'},
            'file': {'enabled': True, 'log_dir': 'logs', 'log_file': 'test_integration.log'}
        }
    }

    # 创建管理器
    manager = NotificationManager()
    manager.add_notifier(ConsoleNotifier(config))
    manager.add_notifier(FileNotifier(config))

    # 发送消息（应同时输出到控制台和文件）
    manager.send("集成测试消息", level='INFO')

    # 发送任务完成消息
    result = {
        'author_name': '测试作者',
        'new_posts': 10,
        'status': 'completed'
    }
    manager.send_task_completion(result)

    # 验证文件记录
    log_path = Path('logs/test_integration.log')
    content = log_path.read_text(encoding='utf-8')
    assert "集成测试消息" in content
    assert "测试作者" in content

    print("✅ 通过")


if __name__ == '__main__':
    test_notification_manager()
    test_console_notifier()
    test_file_notifier()
    test_manager_integration()
    print("\n✅ Day 1 所有测试完成！")
```

---

### Day 2: MQTT 通知器（Task #20）

#### 子任务 2.1: 实现 MQTTNotifier（2.5 小时）

**文件**: `python/src/notification/mqtt_notifier.py`

**参考设计文档**（/tmp/mqtt_notifier_impl.py 已提供完整代码）

**核心要点**:
- 使用 `paho.mqtt.client.Client`
- 后台线程 `client.loop_start()`
- 自动重连机制
- QoS = 1（至少一次送达）
- 结构化 JSON 消息

**验收**:
```bash
# 启动 Mosquitto（如已安装）
mosquitto -v

# 订阅消息
mosquitto_sub -t 't66y/#' -v

# 运行测试
python -c "
from src.notification.mqtt_notifier import MQTTNotifier

config = {
    'notification': {
        'mqtt': {
            'enabled': True,
            'broker': 'localhost',
            'port': 1883,
            'topic': 't66y/test',
            'qos': 1
        }
    }
}

notifier = MQTTNotifier(config)
notifier.send('测试消息', level='INFO')
notifier.close()
"
```

---

#### 子任务 2.2: 扩展配置文件（30 分钟）

**文件**: `python/config.yaml`

**新增配置**:
```yaml
notification:
  # 控制台通知
  console:
    enabled: true
    min_level: INFO  # DEBUG/INFO/WARNING/ERROR

  # 文件通知
  file:
    enabled: true
    log_dir: logs
    log_file: scheduler.log

  # MQTT 通知
  mqtt:
    enabled: false  # 默认禁用（需用户配置 Broker）
    broker: "localhost"
    port: 1883
    username: ""
    password: ""
    topic: "t66y/scheduler/events"
    qos: 1
    client_id: "t66y-archiver"
    publish_on:
      task_start: false
      task_complete: true
      task_error: true
      new_posts_found: true
```

---

#### 子任务 2.3: 测试 MQTT（1 小时）

**文件**: `python/test_day2_mqtt.py`

```python
#!/usr/bin/env python3
"""Day 2 单元测试：MQTT 通知器"""

from src.notification.mqtt_notifier import MQTTNotifier
import time


def test_mqtt_connection():
    """测试 1: MQTT 连接"""
    print("\n=== 测试 1: MQTT 连接 ===")
    print("请确保 Mosquitto 已启动: mosquitto -v")

    config = {
        'notification': {
            'mqtt': {
                'enabled': True,
                'broker': 'localhost',
                'port': 1883,
                'topic': 't66y/test',
                'qos': 1
            }
        }
    }

    notifier = MQTTNotifier(config)
    assert notifier.enabled, "MQTT 未启用"

    time.sleep(1)  # 等待连接

    # 测试连接
    result = notifier.test_connection()
    print(f"连接测试: {'✅ 成功' if result else '❌ 失败'}")

    notifier.close()
    print("✅ 通过")


def test_mqtt_messages():
    """测试 2: MQTT 消息发送"""
    print("\n=== 测试 2: MQTT 消息发送 ===")
    print("请在另一终端运行: mosquitto_sub -t 't66y/#' -v")

    config = {
        'notification': {
            'mqtt': {
                'enabled': True,
                'broker': 'localhost',
                'port': 1883,
                'topic': 't66y/test',
                'qos': 1
            }
        }
    }

    notifier = MQTTNotifier(config)
    time.sleep(1)

    # 发送普通消息
    notifier.send("测试消息", level='INFO')

    # 发送任务完成消息
    result = {
        'task_name': '测试任务',
        'author_name': '测试作者',
        'new_posts': 5,
        'status': 'completed',
        'start_time': '2026-02-15 10:00:00'
    }
    notifier.send_task_completion(result)

    # 发送新帖发现消息
    notifier.send_new_posts_found('测试作者', 3)

    time.sleep(1)
    notifier.close()
    print("✅ 通过")


if __name__ == '__main__':
    print("⚠️  注意：此测试需要 Mosquitto MQTT Broker")
    print("安装: sudo apt install mosquitto mosquitto-clients")
    print("启动: mosquitto -v")
    print()

    test_mqtt_connection()
    test_mqtt_messages()
    print("\n✅ Day 2 所有测试完成！")
```

---

### Day 3: 任务调度器基础（Task #21）

#### 子任务 3.1: 实现 TaskScheduler（3 小时）

**文件**: `python/src/scheduler/task_scheduler.py`

**核心功能**:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Callable, Optional, Dict, List
from datetime import datetime
import json
from pathlib import Path


class TaskScheduler:
    """
    任务调度器

    职责：
    - 管理 APScheduler 后台调度器
    - 添加/删除/暂停/恢复 Cron 任务
    - 持久化任务配置（scheduler_tasks.json）
    - 任务状态查询
    """

    def __init__(self, config: dict):
        self.config = config
        self.scheduler = BackgroundScheduler()

        # 任务配置文件
        data_dir = Path(config.get('data_dir', 'python/data'))
        self.tasks_file = data_dir / 'scheduler_tasks.json'

        # 任务回调函数注册表
        self.task_functions: Dict[str, Callable] = {}

    def register_task_function(self, name: str, func: Callable):
        """注册任务回调函数"""
        self.task_functions[name] = func

    def add_task(
        self,
        task_id: str,
        task_name: str,
        cron_expr: str,
        function_name: str,
        kwargs: Optional[Dict] = None
    ) -> bool:
        """
        添加任务

        Args:
            task_id: 任务唯一 ID
            task_name: 任务名称
            cron_expr: Cron 表达式（例如 "0 2 * * *"）
            function_name: 回调函数名（需提前注册）
            kwargs: 传递给回调函数的参数

        Returns:
            成功返回 True
        """
        if function_name not in self.task_functions:
            raise ValueError(f"未注册的任务函数: {function_name}")

        func = self.task_functions[function_name]

        # 添加到调度器
        self.scheduler.add_job(
            func,
            CronTrigger.from_crontab(cron_expr),
            id=task_id,
            name=task_name,
            kwargs=kwargs or {},
            replace_existing=True
        )

        # 持久化
        self._save_task_config(task_id, task_name, cron_expr, function_name, kwargs)

        return True

    def remove_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            self.scheduler.remove_job(task_id)
            self._remove_task_config(task_id)
            return True
        except:
            return False

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        try:
            self.scheduler.pause_job(task_id)
            return True
        except:
            return False

    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        try:
            self.scheduler.resume_job(task_id)
            return True
        except:
            return False

    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        tasks = []
        for job in self.scheduler.get_jobs():
            tasks.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None
            })
        return tasks

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()

    def _save_task_config(self, task_id, task_name, cron_expr, function_name, kwargs):
        """保存任务配置"""
        tasks = self._load_tasks_file()
        tasks[task_id] = {
            'name': task_name,
            'cron': cron_expr,
            'function': function_name,
            'kwargs': kwargs,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.tasks_file.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))

    def _remove_task_config(self, task_id):
        """删除任务配置"""
        tasks = self._load_tasks_file()
        if task_id in tasks:
            del tasks[task_id]
            self.tasks_file.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))

    def _load_tasks_file(self) -> Dict:
        """加载任务配置文件"""
        if self.tasks_file.exists():
            return json.loads(self.tasks_file.read_text())
        return {}
```

**验收**:
```python
from src.scheduler.task_scheduler import TaskScheduler

def test_func(**kwargs):
    print(f"任务执行: {kwargs}")

config = {'data_dir': 'python/data'}
scheduler = TaskScheduler(config)
scheduler.register_task_function('test_func', test_func)

# 添加任务（每分钟执行）
scheduler.add_task(
    task_id='test-1',
    task_name='测试任务',
    cron_expr='* * * * *',
    function_name='test_func',
    kwargs={'author': '测试'}
)

scheduler.start()
# 等待观察...
```

---

#### 子任务 3.2: 测试调度器（1 小时）

**文件**: `python/test_day3_scheduler.py`

```python
#!/usr/bin/env python3
"""Day 3 单元测试：任务调度器"""

from src.scheduler.task_scheduler import TaskScheduler
import time


execution_log = []


def test_task(**kwargs):
    """测试任务函数"""
    execution_log.append(kwargs)
    print(f"✅ 任务执行: {kwargs}")


def test_scheduler_basic():
    """测试 1: 调度器基础功能"""
    print("\n=== 测试 1: 调度器基础功能 ===")

    config = {'data_dir': 'python/data'}
    scheduler = TaskScheduler(config)

    # 注册函数
    scheduler.register_task_function('test_task', test_task)

    # 添加任务（每 5 秒执行）
    scheduler.add_task(
        task_id='test-task-1',
        task_name='测试任务 1',
        cron_expr='*/5 * * * * *',  # 每 5 秒
        function_name='test_task',
        kwargs={'author': '测试作者'}
    )

    # 启动
    scheduler.start()

    # 等待执行
    print("等待 10 秒，观察任务执行...")
    time.sleep(10)

    # 检查执行日志
    assert len(execution_log) >= 1, "任务未执行"
    print(f"执行次数: {len(execution_log)}")

    # 停止
    scheduler.stop()
    print("✅ 通过")


def test_scheduler_crud():
    """测试 2: 任务 CRUD"""
    print("\n=== 测试 2: 任务 CRUD ===")

    config = {'data_dir': 'python/data'}
    scheduler = TaskScheduler(config)
    scheduler.register_task_function('test_task', test_task)

    # 添加
    scheduler.add_task('task-1', '任务1', '0 0 * * *', 'test_task', {})

    # 查询
    tasks = scheduler.get_all_tasks()
    assert len(tasks) == 1
    assert tasks[0]['id'] == 'task-1'

    # 暂停
    scheduler.pause_task('task-1')

    # 恢复
    scheduler.resume_task('task-1')

    # 删除
    scheduler.remove_task('task-1')
    tasks = scheduler.get_all_tasks()
    assert len(tasks) == 0

    print("✅ 通过")


if __name__ == '__main__':
    test_scheduler_basic()
    test_scheduler_crud()
    print("\n✅ Day 3 所有测试完成！")
```

---

### Day 4: 增量归档器（Task #22）

#### 子任务 4.1: 实现 IncrementalArchiver（2.5 小时）

**文件**: `python/src/scheduler/incremental_archiver.py`

**核心逻辑**:
```python
from typing import List, Dict, Optional
from pathlib import Path
from ..scraper.post_checker import PostChecker
from ..scraper.archiver import ForumArchiver
from ..database.connection import get_default_connection
from ..database.models import Author
from datetime import datetime


class IncrementalArchiver:
    """
    增量归档器

    职责：
    - 检测作者的新帖
    - 只归档未归档的帖子
    - 返回归档结果统计
    """

    def __init__(self, config: dict):
        self.config = config
        self.db = get_default_connection()

    async def archive_author_incremental(
        self,
        author_name: str,
        max_pages: Optional[int] = None
    ) -> Dict:
        """
        增量归档单个作者

        Args:
            author_name: 作者名称
            max_pages: 最大扫描页数

        Returns:
            归档结果字典:
            {
                'author_name': str,
                'new_posts': int,
                'skipped_posts': int,
                'failed_posts': int,
                'start_time': str,
                'end_time': str,
                'duration': float,
                'status': 'completed' | 'failed'
            }
        """
        start_time = datetime.now()
        result = {
            'author_name': author_name,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'new_posts': 0,
            'skipped_posts': 0,
            'failed_posts': 0,
            'status': 'failed'
        }

        try:
            # 1. 获取作者信息
            author = Author.get_by_name(author_name, db=self.db)
            if not author:
                raise ValueError(f"作者不存在: {author_name}")

            author_url = author.url

            # 2. 检测新帖
            checker = PostChecker(self.config)
            check_result = await checker.check_new_posts(
                author_name=author_name,
                author_url=author_url,
                max_pages=max_pages
            )

            new_urls = check_result.get('new_urls', [])
            result['skipped_posts'] = check_result.get('existing_count', 0)

            if len(new_urls) == 0:
                result['status'] = 'completed'
                result['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                result['duration'] = (datetime.now() - start_time).total_seconds()
                return result

            # 3. 归档新帖
            archiver = ForumArchiver(self.config)
            archive_result = await archiver.archive_author(
                author_name=author_name,
                author_url=author_url,
                target_urls=new_urls  # ← 只归档新帖
            )

            result['new_posts'] = archive_result.get('success_count', 0)
            result['failed_posts'] = archive_result.get('failed_count', 0)
            result['status'] = 'completed'

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)

        finally:
            end_time = datetime.now()
            result['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
            result['duration'] = (end_time - start_time).total_seconds()

        return result

    async def archive_authors_batch(
        self,
        author_names: List[str],
        max_pages: Optional[int] = None
    ) -> List[Dict]:
        """
        批量增量归档

        Args:
            author_names: 作者列表
            max_pages: 最大扫描页数

        Returns:
            归档结果列表
        """
        results = []
        for author_name in author_names:
            result = await self.archive_author_incremental(
                author_name=author_name,
                max_pages=max_pages
            )
            results.append(result)

        return results
```

---

#### 子任务 4.2: 修改 ForumArchiver 支持 target_urls（1.5 小时）

**文件**: `python/src/scraper/archiver.py`

**修改位置**: `archive_author()` 方法

```python
async def archive_author(
    self,
    author_name: str,
    author_url: str,
    max_pages: Optional[int] = None,
    max_posts: Optional[int] = None,
    target_urls: Optional[List[str]] = None  # ← 新增参数
):
    """
    归档作者的所有帖子

    新增参数:
        target_urls: 目标帖子 URL 列表（增量模式）
                     如果提供，则只归档这些 URL，忽略 max_pages/max_posts
    """

    # ... 现有代码 ...

    # 1. 收集帖子 URL
    if target_urls is not None:
        # 增量模式：使用指定的 URL 列表
        post_urls = target_urls
        self.logger.info(f"增量模式：归档 {len(target_urls)} 篇指定帖子")
    else:
        # 全量模式：使用 extractor 收集
        post_urls = await self.extractor.collect_post_urls(
            author_url=author_url,
            max_pages=max_pages,
            max_posts=max_posts
        )
        self.logger.info(f"全量模式：收集到 {len(post_urls)} 篇帖子")

    # ... 其余代码保持不变 ...
```

---

#### 子任务 4.3: 测试增量归档（1 小时）

**文件**: `python/test_day4_incremental.py`

```python
#!/usr/bin/env python3
"""Day 4 单元测试：增量归档器"""

import asyncio
from src.scheduler.incremental_archiver import IncrementalArchiver
from src.config.config_manager import ConfigManager


async def test_incremental_archive():
    """测试增量归档"""
    print("\n=== 测试增量归档 ===")

    config_manager = ConfigManager()
    config = config_manager.config

    archiver = IncrementalArchiver(config)

    # 归档测试作者（假设已有部分帖子）
    result = await archiver.archive_author_incremental(
        author_name='同花顺心',
        max_pages=1  # 只扫描第 1 页
    )

    print(f"归档结果: {result}")
    assert result['status'] == 'completed'
    print(f"新增: {result['new_posts']} 篇")
    print(f"跳过: {result['skipped_posts']} 篇")
    print("✅ 通过")


if __name__ == '__main__':
    asyncio.run(test_incremental_archive())
```

---

### Day 5-6: 调度器菜单（Task #23）

#### 子任务 5.1: 实现 SchedulerMenu（4 小时）

**文件**: `python/src/menu/scheduler_menu.py`

**核心功能**:
- 查看任务列表
- 添加任务（选择作者 + Cron 表达式）
- 删除任务
- 启动/暂停任务
- 启动/停止调度器

**菜单结构**:
```
┌─────────────────────────────────┐
│   定时任务调度器                │
├─────────────────────────────────┤
│ 当前状态: ⏸  已停止             │
│ 活跃任务: 0 个                  │
└─────────────────────────────────┘

请选择操作:
  ▸ 查看任务列表
  ▸ 添加任务
  ▸ 删除任务
  ▸ 启动调度器
  ▸ 停止调度器
  ▸ 配置 MQTT
  ▸ 返回主菜单
```

**关键代码**:
```python
class SchedulerMenu:
    def __init__(self, config: dict):
        self.config = config
        self.scheduler = TaskScheduler(config)
        self.notification_manager = NotificationManager()

        # 初始化通知器
        self.notification_manager.add_notifier(ConsoleNotifier(config))
        self.notification_manager.add_notifier(FileNotifier(config))

        if config['notification']['mqtt']['enabled']:
            self.notification_manager.add_notifier(MQTTNotifier(config))

        # 注册任务函数
        self.scheduler.register_task_function(
            'incremental_archive',
            self._incremental_archive_task
        )

    def _incremental_archive_task(self, **kwargs):
        """增量归档任务（被调度器调用）"""
        author_name = kwargs['author_name']
        max_pages = kwargs.get('max_pages', 5)

        # 通知开始
        self.notification_manager.send(
            f"开始归档: {author_name}",
            level='INFO'
        )

        # 执行归档
        archiver = IncrementalArchiver(self.config)
        result = asyncio.run(archiver.archive_author_incremental(
            author_name=author_name,
            max_pages=max_pages
        ))

        # 通知结果
        if result['status'] == 'completed':
            self.notification_manager.send_task_completion(result)
            if result['new_posts'] > 0:
                self.notification_manager.send_new_posts_found(
                    author_name,
                    result['new_posts']
                )
        else:
            self.notification_manager.send_task_error(
                author_name,
                result.get('error', 'Unknown error')
            )

    def show_menu(self):
        """显示主菜单"""
        while True:
            # 显示状态
            status = "▶️  运行中" if self.scheduler.scheduler.running else "⏸  已停止"
            task_count = len(self.scheduler.get_all_tasks())

            print(f"\n{'='*50}")
            print(f"   定时任务调度器")
            print(f"{'='*50}")
            print(f"当前状态: {status}")
            print(f"活跃任务: {task_count} 个")
            print(f"{'='*50}\n")

            # 选择操作
            action = questionary.select(
                "请选择操作:",
                choices=[
                    '查看任务列表',
                    '添加任务',
                    '删除任务',
                    '启动调度器',
                    '停止调度器',
                    '配置 MQTT',
                    '返回主菜单'
                ]
            ).ask()

            if action == '查看任务列表':
                self._show_tasks()
            elif action == '添加任务':
                self._add_task()
            elif action == '删除任务':
                self._delete_task()
            elif action == '启动调度器':
                self._start_scheduler()
            elif action == '停止调度器':
                self._stop_scheduler()
            elif action == '配置 MQTT':
                self._configure_mqtt()
            elif action == '返回主菜单':
                break
```

---

#### 子任务 5.2: 集成到主菜单（30 分钟）

**文件**: `python/src/menu/main_menu.py`

**修改位置**: `show_menu()` 方法

```python
def show_menu(self):
    """显示主菜单"""
    while True:
        self._display_header()

        action = questionary.select(
            "请选择功能:",
            choices=[
                '作者管理',
                '数据统计',
                '📅 定时任务',  # ← 新增
                '配置管理',
                '退出程序'
            ]
        ).ask()

        # ... 现有代码 ...

        elif action == '📅 定时任务':
            from .scheduler_menu import SchedulerMenu
            scheduler_menu = SchedulerMenu(self.config)
            scheduler_menu.show_menu()

        # ... 其余代码 ...
```

---

### Day 7-8: 集成测试与文档（Task #24）

#### 子任务 7.1: 端到端测试（3 小时）

**文件**: `python/test_phase5_e2e.py`

```python
#!/usr/bin/env python3
"""Phase 5 端到端测试"""

import asyncio
from src.scheduler.task_scheduler import TaskScheduler
from src.scheduler.incremental_archiver import IncrementalArchiver
from src.notification import NotificationManager, ConsoleNotifier, FileNotifier, MQTTNotifier
from src.config.config_manager import ConfigManager


async def test_e2e_scheduled_archive():
    """端到端测试：定时归档"""
    print("\n=== 端到端测试：定时归档 ===")

    # 1. 加载配置
    config_manager = ConfigManager()
    config = config_manager.config

    # 2. 初始化通知管理器
    notification_manager = NotificationManager()
    notification_manager.add_notifier(ConsoleNotifier(config))
    notification_manager.add_notifier(FileNotifier(config))

    # 3. 初始化调度器
    scheduler = TaskScheduler(config)

    # 4. 定义任务函数
    async def archive_task(**kwargs):
        author_name = kwargs['author_name']
        notification_manager.send(f"开始归档: {author_name}", level='INFO')

        archiver = IncrementalArchiver(config)
        result = await archiver.archive_author_incremental(author_name, max_pages=1)

        if result['status'] == 'completed':
            notification_manager.send_task_completion(result)
        else:
            notification_manager.send_task_error(author_name, result.get('error', 'Unknown'))

    # 5. 注册并添加任务
    def sync_archive_task(**kwargs):
        asyncio.run(archive_task(**kwargs))

    scheduler.register_task_function('archive', sync_archive_task)

    scheduler.add_task(
        task_id='test-archive',
        task_name='测试定时归档',
        cron_expr='*/10 * * * * *',  # 每 10 秒
        function_name='archive',
        kwargs={'author_name': '同花顺心'}
    )

    # 6. 启动调度器
    scheduler.start()
    print("调度器已启动，等待 30 秒...")

    await asyncio.sleep(30)

    # 7. 停止调度器
    scheduler.stop()
    print("✅ 端到端测试完成")


if __name__ == '__main__':
    asyncio.run(test_e2e_scheduled_archive())
```

---

#### 子任务 7.2: 用户文档（2 小时）

**文件**: `PHASE5_USER_GUIDE.md`

**内容**:
- 功能介绍
- 快速开始
- Cron 表达式说明
- MQTT 配置指南
- 常见问题

---

### Day 9: MQTT 消息处理器（Task #25）

#### 子任务 9.1: 创建 mqtt_to_telegram.py（2 小时）

**文件**: `python/tools/mqtt_to_telegram.py`

**功能**: 订阅 MQTT 消息 → 格式化 → 发送到 Telegram Bot

（完整代码已在设计文档中提供）

---

#### 子任务 9.2: 文档和示例（1 小时）

**文件**: `MQTT_HANDLER_GUIDE.md`

**内容**:
- 消息处理器概念
- mqtt_to_telegram.py 使用说明
- Systemd 服务配置
- 其他通知渠道扩展（邮件、钉钉、企业微信）

---

### Day 10: 优化与验收（Task #26）

#### 子任务 10.1: 性能优化（2 小时）

- 调度器启动时间优化
- MQTT 连接超时处理
- 日志文件轮转

---

#### 子任务 10.2: 最终验收（2 小时）

**验收清单**:
- [ ] 所有单元测试通过
- [ ] 端到端测试通过
- [ ] MQTT 消息格式正确
- [ ] 任务持久化正常
- [ ] 增量归档准确（无重复下载）
- [ ] 配置文件向后兼容
- [ ] 文档完整

---

## 3. 任务依赖图

```
Day 1 (Task #19) - 基础通知模块
    │
    ├─> Day 2 (Task #20) - MQTT 通知器
    │
    └─> Day 3 (Task #21) - 任务调度器
            │
            ├─> Day 4 (Task #22) - 增量归档器
            │        │
            │        └─> Day 5-6 (Task #23) - 调度器菜单
            │                    │
            │                    └─> Day 7-8 (Task #24) - 集成测试
            │                            │
            │                            └─> Day 9 (Task #25) - 消息处理器
            │                                    │
            │                                    └─> Day 10 (Task #26) - 验收
            │
            └─> (并行) Day 9 消息处理器可与 Day 7-8 并行
```

**关键路径**: Day 1 → Day 3 → Day 4 → Day 5-6 → Day 7-8 → Day 10

**并行任务**: Day 2 (MQTT) 可与 Day 3 并行（建议顺序实施）

---

## 4. 风险与缓解

### 风险 1: MQTT Broker 未安装

**症状**: MQTTNotifier 连接失败

**缓解**:
```bash
# 安装 Mosquitto
sudo apt install mosquitto mosquitto-clients

# 验证
mosquitto -v
```

**降级方案**: 禁用 MQTT，仅使用 Console 和 File 通知器

---

### 风险 2: APScheduler 任务未触发

**症状**: Cron 任务不执行

**调试**:
```python
# 检查任务列表
scheduler.get_all_tasks()

# 检查调度器状态
scheduler.scheduler.running

# 查看日志
tail -f logs/scheduler.log
```

---

### 风险 3: 增量归档漏检新帖

**症状**: 有新帖但未归档

**原因**: PostChecker 误判为已存在

**缓解**: 检查 PostTracker 的 URL 规范化逻辑

---

### 风险 4: 异步函数调度问题

**症状**: `archive_author_incremental()` 无法被调度器调用

**原因**: APScheduler 不直接支持 async 函数

**解决**: 包装为同步函数
```python
def sync_wrapper(**kwargs):
    asyncio.run(async_function(**kwargs))

scheduler.register_task_function('task', sync_wrapper)
```

---

## 5. 配置文件变更

### python/config.yaml 新增配置

```yaml
# ==================== Phase 5: 调度器与通知 ====================
scheduler:
  enabled: false  # 是否启用调度器
  data_dir: "python/data"
  tasks_file: "scheduler_tasks.json"
  default_max_pages: 5  # 增量归档时的默认扫描页数

notification:
  console:
    enabled: true
    min_level: INFO

  file:
    enabled: true
    log_dir: logs
    log_file: scheduler.log

  mqtt:
    enabled: false
    broker: "localhost"
    port: 1883
    username: ""
    password: ""
    topic: "t66y/scheduler/events"
    qos: 1
    client_id: "t66y-archiver"
    publish_on:
      task_start: false
      task_complete: true
      task_error: true
      new_posts_found: true
```

---

## 6. 性能目标

| 操作 | 目标 | 备注 |
|------|------|------|
| 调度器启动 | < 1 秒 | 加载任务配置 |
| MQTT 连接 | < 2 秒 | 连接 Broker |
| 增量归档（无新帖）| < 5 秒 | 仅检测，不下载 |
| 增量归档（10 篇新帖）| < 60 秒 | 包含下载和 EXIF |
| 消息发送 | < 0.5 秒 | MQTT QoS 1 |
| 任务持久化 | < 0.1 秒 | JSON 文件写入 |

---

## 7. 验收标准

### 功能验收
- [ ] 可添加/删除/暂停/恢复任务
- [ ] Cron 表达式正确触发
- [ ] 增量归档无重复下载
- [ ] MQTT 消息格式正确
- [ ] 任务配置持久化
- [ ] 调度器重启后恢复任务

### 性能验收
- [ ] 增量归档（无新帖）< 5 秒
- [ ] MQTT 连接 < 2 秒
- [ ] 消息发送 < 0.5 秒

### 质量验收
- [ ] 所有单元测试通过
- [ ] 端到端测试通过
- [ ] 代码遵循 Phase 3/4 模式
- [ ] 错误处理完善
- [ ] 日志记录清晰
- [ ] 配置向后兼容

---

## 8. 后续优化方向（Phase 6）

**可能的功能扩展**:
1. **Web 界面**: Flask/FastAPI 实现 Web 管理界面
2. **任务链**: 支持任务依赖和顺序执行
3. **失败重试**: 自动重试失败的归档任务
4. **并发归档**: 同时归档多个作者
5. **统计报表**: 定时生成归档统计报告
6. **Webhook 通知**: 支持自定义 Webhook
7. **Docker 部署**: 容器化部署方案

---

## 9. 关键文件路径汇总

**新建文件**:
- `python/src/scheduler/task_scheduler.py` (300 行)
- `python/src/scheduler/incremental_archiver.py` (150 行)
- `python/src/notification/manager.py` (200 行)
- `python/src/notification/console_notifier.py` (80 行)
- `python/src/notification/file_notifier.py` (80 行)
- `python/src/notification/mqtt_notifier.py` (250 行)
- `python/src/menu/scheduler_menu.py` (400 行)
- `python/tools/mqtt_to_telegram.py` (150 行)
- `python/test_phase5_e2e.py` (400 行)
- `PHASE5_USER_GUIDE.md` (用户文档)
- `MQTT_HANDLER_GUIDE.md` (消息处理器指南)

**修改文件**:
- `python/requirements.txt` (+2 行)
- `python/config.yaml` (+25 行)
- `python/src/menu/main_menu.py` (+5 行)
- `python/src/scraper/archiver.py` (修改 `archive_author()` 方法)

---

## 10. 每日产出预期

| 日期 | 任务 | 产出 | 测试覆盖 |
|------|------|------|----------|
| Day 1 | Task #19 | manager.py, console_notifier.py, file_notifier.py | 4 tests |
| Day 2 | Task #20 | mqtt_notifier.py, config.yaml 扩展 | 2 tests |
| Day 3 | Task #21 | task_scheduler.py | 2 tests |
| Day 4 | Task #22 | incremental_archiver.py, archiver.py 修改 | 1 test |
| Day 5-6 | Task #23 | scheduler_menu.py, main_menu.py 集成 | 手动测试 |
| Day 7-8 | Task #24 | test_phase5_e2e.py, PHASE5_USER_GUIDE.md | E2E test |
| Day 9 | Task #25 | mqtt_to_telegram.py, MQTT_HANDLER_GUIDE.md | 手动测试 |
| Day 10 | Task #26 | 性能优化、最终验收 | 全面测试 |

---

## 11. 技术债务清单

**Phase 5 不解决的问题**（留待后续）:
1. 任务失败自动重试
2. 任务执行历史记录
3. Web 界面管理
4. 多用户权限管理
5. 归档速率限制
6. 并发归档多个作者
7. 任务优先级调度

**已知限制**:
1. 调度器单进程运行（无分布式）
2. MQTT 无 TLS 加密配置
3. 任务配置文件无版本控制
4. 增量归档串行执行（无并发）

---

## 12. 关键决策记录

### 决策 1: 使用 MQTT 而非 Telegram Bot

**背景**: 需要通知机制

**方案对比**:
- 方案 A: 直接集成 Telegram Bot
- 方案 B: MQTT + 独立消息处理器

**选择**: 方案 B (MQTT)

**理由**:
1. 解耦：归档系统不依赖 Telegram
2. 可扩展：轻松支持多个通知渠道
3. 多项目复用：一个 MQTT Broker 服务所有项目

---

### 决策 2: 使用 APScheduler 而非 Cron

**背景**: 需要任务调度

**方案对比**:
- 方案 A: 系统 Cron + Shell 脚本
- 方案 B: APScheduler 库

**选择**: 方案 B (APScheduler)

**理由**:
1. Python 原生：无需外部配置
2. 动态管理：运行时添加/删除任务
3. 跨平台：Windows/Linux/macOS 通用

---

### 决策 3: 增量归档使用 target_urls 参数

**背景**: 避免重复下载

**方案对比**:
- 方案 A: 在 extractor 内部过滤已存在的 URL
- 方案 B: 在调度器调用前检测新帖，传递 URL 列表

**选择**: 方案 B (target_urls)

**理由**:
1. 职责分离：PostChecker 负责检测，Archiver 负责下载
2. 灵活性：支持全量和增量两种模式
3. 性能：避免 extractor 重复查询数据库

---

## 13. 常见问题（FAQ）

**Q1: 如何修改 Cron 表达式？**

A: 编辑 `python/data/scheduler_tasks.json`，修改 `cron` 字段，重启调度器。

**Q2: MQTT 连接失败怎么办？**

A: 检查 Broker 是否启动：`sudo systemctl status mosquitto`

**Q3: 增量归档为什么还下载了已有帖子？**

A: 检查 PostChecker 的 URL 规范化逻辑，可能存在 URL 格式差异。

**Q4: 如何测试 MQTT 消息？**

A: 使用 `mosquitto_sub` 订阅：
```bash
mosquitto_sub -t 't66y/#' -v
```

**Q5: 调度器重启后任务消失？**

A: 检查 `python/data/scheduler_tasks.json` 是否存在，调度器启动时会自动加载。

---

## 14. 总结

**Phase 5 核心目标**:
- ✅ 自动化归档（定时任务）
- ✅ 增量下载（避免重复）
- ✅ 灵活通知（MQTT 解耦）
- ✅ 易于管理（交互式菜单）

**关键技术栈**:
- APScheduler - 任务调度
- paho-mqtt - 消息发布
- PostChecker - 新帖检测
- IncrementalArchiver - 增量归档

**工期**: 10 天（2026-02-15 至 2026-02-24）

**下一步**: 开始 Day 1 实施（安装依赖、创建目录、实现基础通知模块）
