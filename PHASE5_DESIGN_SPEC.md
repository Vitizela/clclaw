# Phase 5 技术设计规范

> **项目**: T66Y 论坛归档系统
> **阶段**: Phase 5 - 定时任务与 MQTT 通知系统
> **版本**: v2.0 (MQTT 方案)
> **创建日期**: 2026-02-15
> **更新日期**: 2026-02-15
> **状态**: 设计评审 ✅

---

## 📋 目录

1. [系统架构](#1-系统架构)
2. [模块设计](#2-模块设计)
3. [数据结构](#3-数据结构)
4. [接口规范](#4-接口规范)
5. [配置规范](#5-配置规范)
6. [数据库设计](#6-数据库设计)
7. [错误处理](#7-错误处理)
8. [测试方案](#8-测试方案)
9. [实施步骤](#9-实施步骤)
10. [代码规范](#10-代码规范)

---

## 1. 系统架构

### 1.1 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户界面层 (UI Layer)                    │
├─────────────────────────────────────────────────────────────┤
│  SchedulerMenu          │  NotificationMenu                 │
│  (定时任务菜单)          │  (MQTT 配置菜单)                  │
└─────────────┬───────────┴────────────┬──────────────────────┘
              │                        │
┌─────────────▼────────────────────────▼──────────────────────┐
│                   业务逻辑层 (Business Layer)                │
├─────────────────────────────────────────────────────────────┤
│  TaskScheduler          │  NotificationManager              │
│  (任务调度器)            │  (通知管理器)                     │
│                         │                                   │
│  IncrementalArchiver    │  - ConsoleNotifier                │
│  (增量归档器)            │  - FileNotifier                   │
│                         │  - MQTTNotifier ⭐                │
└─────────────┬───────────┴────────────┬──────────────────────┘
              │                        │
┌─────────────▼────────────────────────▼──────────────────────┐
│                  基础设施层 (Infrastructure Layer)           │
├─────────────────────────────────────────────────────────────┤
│  APScheduler            │  paho-mqtt                        │
│  (调度引擎)              │  (MQTT 客户端)                    │
│                         │      │                            │
│  PostChecker            │      ▼                            │
│  (新帖检测，已有)        │  MQTT Broker (Mosquitto)          │
│                         │  (用户自行部署)                    │
│  ForumArchiver          │                                   │
│  (归档器，已有)          │                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌────────────────────────────────────┐
        │  消息处理器 (用户侧，独立程序)       │
        │  - 订阅 MQTT 消息                  │
        │  - 发送 Telegram / 邮件 / Web等    │
        └────────────────────────────────────┘
```

### 1.2 模块依赖关系

```
SchedulerMenu
    └─> TaskScheduler
            ├─> IncrementalArchiver
            │       ├─> PostChecker (已有)
            │       └─> ForumArchiver (已有)
            └─> NotificationManager
                    ├─> ConsoleNotifier
                    ├─> FileNotifier
                    └─> MQTTNotifier
                            └─> paho-mqtt
                                    └─> MQTT Broker (Mosquitto)

NotificationMenu
    └─> NotificationManager
            └─> MQTTNotifier
```

### 1.3 数据流

```
用户添加任务
    │
    ▼
保存到 config.yaml
    │
    ▼
TaskScheduler.add_task()
    │
    ▼
APScheduler 持久化到 scheduler_jobs.db
    │
    ▼
定时触发
    │
    ▼
TaskScheduler.execute_task()
    │
    ▼
IncrementalArchiver.archive_author_incremental()
    ├─> PostChecker.check_new_posts() → 返回 new_urls
    └─> ForumArchiver.archive_author(target_urls=new_urls)
            │
            ▼
        归档完成，返回统计结果
            │
            ▼
保存到 scheduler_history 表
    │
    ▼
NotificationManager.send_task_completion()
    │
    ▼
MQTTNotifier.send_message()
    │
    ▼
用户收到 MQTT 消息发布
```

---

## 2. 模块设计

### 2.1 TaskScheduler（任务调度器）

#### 类定义

```python
# python/src/scheduler/task_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional, Dict, List
import asyncio
from pathlib import Path

class TaskScheduler:
    """
    任务调度器

    职责：
    - 管理定时任务的生命周期（添加、删除、启用、禁用）
    - 使用 APScheduler 执行定时触发
    - 协调增量归档和通知发送
    - 记录任务执行历史

    依赖：
    - APScheduler（调度引擎）
    - IncrementalArchiver（增量归档）
    - NotificationManager（通知发送）
    - DatabaseConnection（日志存储）
    """

    def __init__(self, config: dict, db_connection=None):
        """
        初始化调度器

        Args:
            config: 配置字典（从 config.yaml 加载）
            db_connection: 数据库连接（可选）
        """
        self.config = config
        self.db = db_connection

        # 配置 APScheduler
        jobstores = {
            'default': SQLAlchemyJobStore(
                url='sqlite:///python/data/scheduler_jobs.db'
            )
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone='Asia/Shanghai'  # 根据需要调整时区
        )

        # 初始化子模块
        self.incremental_archiver = IncrementalArchiver(config, db_connection)
        self.notification = NotificationManager(config)

        # 任务执行互斥锁（同时只允许 1 个归档任务）
        self._execution_lock = asyncio.Lock()

        # 调度器状态
        self._is_running = False

    def start(self) -> None:
        """
        启动调度器

        - 启动 APScheduler
        - 加载配置中的所有已启用任务
        - 设置状态为运行中
        """
        if self._is_running:
            return

        # 启动调度器
        self.scheduler.start()

        # 加载任务
        self._load_tasks_from_config()

        self._is_running = True

    def stop(self) -> None:
        """
        停止调度器

        - 等待正在执行的任务完成
        - 停止 APScheduler
        - 设置状态为已停止
        """
        if not self._is_running:
            return

        # 停止调度器（不强制中断正在执行的任务）
        self.scheduler.shutdown(wait=True)

        self._is_running = False

    def add_task(self, task_config: dict) -> bool:
        """
        添加定时任务

        Args:
            task_config: 任务配置字典
                {
                    'id': 'task_1',
                    'name': '每日更新-同花顺心',
                    'author_name': '同花顺心',
                    'author_url': 'https://t66y.com/@同花顺心',
                    'enabled': True,
                    'cron_expression': '0 3 * * *',
                    'max_pages': 3
                }

        Returns:
            bool: 添加成功返回 True，失败返回 False

        Raises:
            ValueError: task_id 已存在或 cron 表达式无效
        """
        task_id = task_config['id']

        # 验证 task_id 唯一性
        if self.scheduler.get_job(task_id):
            raise ValueError(f"任务 ID 已存在: {task_id}")

        # 解析 Cron 表达式
        try:
            trigger = CronTrigger.from_crontab(task_config['cron_expression'])
        except Exception as e:
            raise ValueError(f"Cron 表达式无效: {e}")

        # 添加到调度器
        self.scheduler.add_job(
            func=self._execute_task_wrapper,
            trigger=trigger,
            args=[task_config],
            id=task_id,
            name=task_config['name'],
            replace_existing=False
        )

        # 保存到配置文件
        self._save_task_to_config(task_config)

        return True

    def remove_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID

        Returns:
            bool: 删除成功返回 True，任务不存在返回 False
        """
        # 从调度器移除
        try:
            self.scheduler.remove_job(task_id)
        except:
            return False

        # 从配置文件移除
        self._remove_task_from_config(task_id)

        return True

    def update_task(self, task_config: dict) -> bool:
        """
        更新任务配置

        Args:
            task_config: 新的任务配置

        Returns:
            bool: 更新成功返回 True

        实现：
            删除旧任务 + 添加新任务
        """
        self.remove_task(task_config['id'])
        return self.add_task(task_config)

    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        获取任务详情

        Args:
            task_id: 任务 ID

        Returns:
            任务配置字典，不存在返回 None
        """
        job = self.scheduler.get_job(task_id)
        if not job:
            return None

        # 从配置文件读取完整配置
        return self._get_task_from_config(task_id)

    def get_all_tasks(self) -> List[Dict]:
        """
        获取所有任务列表

        Returns:
            任务配置列表，包含动态信息（下次执行时间）
            [
                {
                    'id': 'task_1',
                    'name': '每日更新-同花顺心',
                    'author_name': '同花顺心',
                    'enabled': True,
                    'cron_expression': '0 3 * * *',
                    'next_run_time': '2026-02-16 03:00:00',
                    'last_execution': {...}  # 最近一次执行结果
                },
                ...
            ]
        """
        tasks = []

        # 从配置文件读取
        config_tasks = self.config.get('scheduler_tasks', [])

        for task_config in config_tasks:
            task_id = task_config['id']

            # 获取 APScheduler 的动态信息
            job = self.scheduler.get_job(task_id)
            if job:
                task_config['next_run_time'] = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                task_config['next_run_time'] = None

            # 获取最近一次执行结果
            task_config['last_execution'] = self._get_last_execution(task_id)

            tasks.append(task_config)

        return tasks

    def execute_task_manually(self, task_id: str) -> Dict:
        """
        手动触发任务执行（不等定时）

        Args:
            task_id: 任务 ID

        Returns:
            执行结果字典
        """
        task_config = self.get_task(task_id)
        if not task_config:
            raise ValueError(f"任务不存在: {task_id}")

        # 直接调用执行方法
        return asyncio.run(self._execute_task(task_config))

    def _execute_task_wrapper(self, task_config: dict):
        """
        任务执行包装器（APScheduler 调用）

        Args:
            task_config: 任务配置

        说明：
            APScheduler 不支持 async 函数，需要包装
        """
        asyncio.run(self._execute_task(task_config))

    async def _execute_task(self, task_config: dict) -> Dict:
        """
        执行单个任务（核心逻辑）

        Args:
            task_config: 任务配置

        Returns:
            执行结果字典
            {
                'task_id': 'task_1',
                'task_name': '每日更新-同花顺心',
                'author_name': '同花顺心',
                'start_time': '2026-02-15 03:00:00',
                'end_time': '2026-02-15 03:02:35',
                'duration': '2分35秒',
                'status': 'success',  # success | failed | partial
                'new_posts': 5,
                'skipped_posts': 55,
                'failed_posts': 0,
                'total_archived': 60,
                'total_forum': 65,
                'completion_rate': 92.3,
                'error_message': None
            }
        """
        from datetime import datetime

        task_id = task_config['id']
        task_name = task_config['name']
        author_name = task_config['author_name']
        author_url = task_config['author_url']
        max_pages = task_config.get('max_pages', 3)

        start_time = datetime.now()
        result = {
            'task_id': task_id,
            'task_name': task_name,
            'author_name': author_name,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'failed',
            'error_message': None
        }

        try:
            # 互斥锁：同时只允许 1 个任务执行
            async with self._execution_lock:
                # 执行增量归档
                archive_result = await self.incremental_archiver.archive_author_incremental(
                    author_name=author_name,
                    author_url=author_url,
                    max_pages=max_pages
                )

                # 计算耗时
                end_time = datetime.now()
                duration = end_time - start_time
                duration_str = str(duration).split('.')[0]  # 去掉微秒

                # 更新结果
                result.update({
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': duration_str,
                    'status': archive_result.get('status', 'success'),
                    'new_posts': archive_result.get('new', 0),
                    'skipped_posts': archive_result.get('skipped', 0),
                    'failed_posts': archive_result.get('failed', 0),
                    'total_archived': archive_result.get('total_archived', 0),
                    'total_forum': archive_result.get('total_forum', 0),
                    'completion_rate': archive_result.get('completion_rate', 0)
                })

                # 保存执行历史
                self._save_execution_history(result)

                # 发送成功通知
                self.notification.send_task_completion(result)

        except Exception as e:
            # 错误处理
            end_time = datetime.now()
            duration = end_time - start_time

            result.update({
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': str(duration).split('.')[0],
                'status': 'failed',
                'error_message': str(e)
            })

            # 保存错误记录
            self._save_execution_history(result)

            # 发送错误通知
            self.notification.send_task_error(task_name, str(e))

        return result

    def _load_tasks_from_config(self):
        """从配置文件加载所有已启用的任务"""
        tasks = self.config.get('scheduler_tasks', [])
        for task in tasks:
            if task.get('enabled', True):
                try:
                    self.add_task(task)
                except:
                    pass  # 跳过无效任务

    def _save_task_to_config(self, task_config: dict):
        """保存任务到配置文件"""
        # 实现省略（调用 ConfigManager）
        pass

    def _remove_task_from_config(self, task_id: str):
        """从配置文件删除任务"""
        # 实现省略
        pass

    def _get_task_from_config(self, task_id: str) -> Optional[Dict]:
        """从配置文件读取任务"""
        # 实现省略
        pass

    def _save_execution_history(self, result: dict):
        """保存执行历史到数据库"""
        # 实现省略（写入 scheduler_history 表）
        pass

    def _get_last_execution(self, task_id: str) -> Optional[Dict]:
        """获取最近一次执行记录"""
        # 实现省略（查询 scheduler_history 表）
        pass
```

#### 关键方法说明

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `start()` | 无 | 无 | 启动调度器，加载任务 |
| `stop()` | 无 | 无 | 停止调度器，等待任务完成 |
| `add_task()` | task_config | bool | 添加任务到调度器和配置 |
| `remove_task()` | task_id | bool | 删除任务 |
| `update_task()` | task_config | bool | 更新任务（删除+添加）|
| `get_all_tasks()` | 无 | List[Dict] | 获取所有任务列表 |
| `execute_task_manually()` | task_id | Dict | 手动触发任务 |
| `_execute_task()` | task_config | Dict | 任务执行核心逻辑 |

---

### 2.2 IncrementalArchiver（增量归档器）

#### 类定义

```python
# python/src/scheduler/incremental_archiver.py

from typing import Dict, Optional
from pathlib import Path

class IncrementalArchiver:
    """
    增量归档器

    职责：
    - 检测新帖（调用 PostChecker）
    - 只归档新帖（调用 ForumArchiver）
    - 返回归档统计结果

    依赖：
    - PostChecker（新帖检测，Phase 2）
    - ForumArchiver（归档下载，Phase 2）
    - PostTracker（URL 追踪，Phase 2）
    """

    def __init__(self, config: dict, db_connection=None):
        """
        初始化增量归档器

        Args:
            config: 配置字典
            db_connection: 数据库连接（可选）
        """
        self.config = config
        self.db = db_connection

        # 初始化子模块
        from ..scraper.checker import PostChecker
        from ..scraper.archiver import ForumArchiver

        self.checker = PostChecker(config)
        self.archiver = ForumArchiver(config)

    async def archive_author_incremental(
        self,
        author_name: str,
        author_url: str,
        max_pages: int = 3
    ) -> Dict:
        """
        增量归档作者的新帖

        Args:
            author_name: 作者名
            author_url: 作者 URL
            max_pages: 扫描页数

        Returns:
            归档结果字典
            {
                'status': 'success',  # success | no_new_posts | failed
                'new': 5,              # 新增帖子数
                'skipped': 55,         # 跳过帖子数
                'failed': 0,           # 失败帖子数
                'total_archived': 60,  # 已归档总数
                'total_forum': 65,     # 论坛总数
                'completion_rate': 92.3  # 完成度百分比
            }
        """
        try:
            # 步骤 1：启动检测器
            await self.checker.start()

            # 步骤 2：检测新帖
            check_result = await self.checker.check_new_posts(
                author_name=author_name,
                author_url=author_url,
                max_pages=max_pages
            )

            # 步骤 3：关闭检测器
            await self.checker.close()

            # 步骤 4：判断是否有新帖
            if not check_result['has_new']:
                # 无新帖，直接返回
                return {
                    'status': 'no_new_posts',
                    'new': 0,
                    'skipped': check_result['total_archived'],
                    'failed': 0,
                    'total_archived': check_result['total_archived'],
                    'total_forum': check_result['total_forum'],
                    'completion_rate': 100.0 if check_result['total_forum'] > 0 else 0
                }

            # 步骤 5：归档新帖
            new_urls = check_result['new_urls']

            archive_result = await self.archiver.archive_author(
                author_name=author_name,
                author_url=author_url,
                max_pages=None,
                max_posts=None,
                target_urls=new_urls  # ← 关键：只归档这些 URL
            )

            # 步骤 6：计算完成度
            total_archived = check_result['total_archived'] + archive_result['new']
            total_forum = check_result['total_forum']
            completion_rate = (total_archived / total_forum * 100) if total_forum > 0 else 0

            # 步骤 7：返回结果
            return {
                'status': 'success',
                'new': archive_result['new'],
                'skipped': archive_result['skipped'],
                'failed': archive_result['failed'],
                'total_archived': total_archived,
                'total_forum': total_forum,
                'completion_rate': completion_rate
            }

        except Exception as e:
            # 错误处理
            return {
                'status': 'failed',
                'error': str(e),
                'new': 0,
                'skipped': 0,
                'failed': 0,
                'total_archived': 0,
                'total_forum': 0,
                'completion_rate': 0
            }
```

#### 关键修改：ForumArchiver.archive_author()

```python
# python/src/scraper/archiver.py

async def archive_author(
    self,
    author_name: str,
    author_url: str,
    max_pages: Optional[int] = None,
    max_posts: Optional[int] = None,
    target_urls: Optional[List[str]] = None  # ← 新增参数
) -> Dict:
    """
    归档作者的所有帖子

    Args:
        ...
        target_urls: 指定要归档的 URL 列表（可选）
            - None: 正常流程（收集 URL → 归档）
            - List: 增量模式（跳过收集，直接归档这些 URL）

    Returns:
        统计结果字典
    """
    # ... 现有代码 ...

    # 阶段一：收集帖子 URL
    if target_urls is not None:
        # ← 增量模式：直接使用提供的 URL 列表
        post_urls = target_urls
        total_posts = len(target_urls)
        forum_total = total_posts  # 或从其他地方获取
    else:
        # ← 正常模式：扫描论坛收集 URL
        post_urls = await self.extractor.collect_post_urls(
            author_url,
            max_pages,
            max_posts,
            author_name=author_name
        )
        total_posts = len(post_urls)
        forum_total = total_posts

    # 阶段二：逐个归档（不变）
    # ... 现有代码 ...
```

---

### 2.3 NotificationManager（通知管理器）

#### 类定义

```python
# python/src/notification/manager.py

from typing import List, Dict
from .console_notifier import ConsoleNotifier
from .file_notifier import FileNotifier
from .mqtt_notifier import MQTTNotifier

class NotificationManager:
    """
    通知管理器（统一接口）

    职责：
    - 管理多个通知渠道（Console, File, Telegram）
    - 根据配置启用/禁用渠道
    - 统一的消息发送接口
    - 消息优先级过滤

    依赖：
    - ConsoleNotifier
    - FileNotifier
    - MQTTNotifier
    """

    def __init__(self, config: dict):
        """
        初始化通知管理器

        Args:
            config: 配置字典（包含 notification 配置）
        """
        self.config = config
        self.notifiers = []

        # 根据配置启用通知器
        notification_config = config.get('notification', {})

        if notification_config.get('console', {}).get('enabled', True):
            self.notifiers.append(ConsoleNotifier(config))

        if notification_config.get('file', {}).get('enabled', True):
            self.notifiers.append(FileNotifier(config))

        if notification_config.get('telegram', {}).get('enabled', False):
            self.notifiers.append(MQTTNotifier(config))

    def send(self, message: str, level: str = 'INFO', **kwargs):
        """
        发送通用消息

        Args:
            message: 消息文本
            level: 消息级别（DEBUG, INFO, WARNING, ERROR）
            **kwargs: 额外参数
        """
        for notifier in self.notifiers:
            if notifier.should_send(level):
                notifier.send(message, level, **kwargs)

    def send_task_completion(self, result: Dict):
        """
        发送任务完成通知（格式化）

        Args:
            result: 任务执行结果字典
        """
        for notifier in self.notifiers:
            notifier.send_task_completion(result)

    def send_task_error(self, task_name: str, error: str):
        """
        发送任务失败通知

        Args:
            task_name: 任务名称
            error: 错误信息
        """
        for notifier in self.notifiers:
            notifier.send_task_error(task_name, error)

    def send_new_posts_found(self, author_name: str, count: int):
        """
        发送发现新帖通知

        Args:
            author_name: 作者名
            count: 新帖数量
        """
        for notifier in self.notifiers:
            notifier.send_new_posts_found(author_name, count)
```

---

### 2.4 MQTTNotifier（MQTT 通知器）

#### 类定义

```python
# python/src/notification/mqtt_notifier.py

import paho.mqtt.client as mqtt
import json
from typing import Dict
from datetime import datetime
import time

class MQTTNotifier:
    """
    MQTT 消息发布器

    职责：
    - 连接 MQTT Broker API
    - 发送格式化消息（Markdown）
    - 错误处理和重试

    依赖：
    - paho-mqtt
    """

    def __init__(self, config: dict):
        """
        初始化 MQTT 消息发布器

        Args:
            config: 配置字典
        """
        tg_config = config['notification']['telegram']

        self.bot_token = tg_config['bot_token']
        self.chat_id = tg_config['chat_id']
        self.min_level = tg_config.get('min_level', 'INFO')
        self.notify_on = tg_config.get('notify_on', {})
        self.format_config = tg_config.get('format', {})

        # 初始化 Bot
        try:
            self.bot = Bot(token=self.bot_token)
            self.enabled = True
        except TelegramError as e:
            print(f"MQTT Broker 初始化失败: {e}")
            self.enabled = False

    def should_send(self, level: str) -> bool:
        """
        判断是否应该发送（根据最低级别）

        Args:
            level: 消息级别

        Returns:
            bool: 应该发送返回 True
        """
        if not self.enabled:
            return False

        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        try:
            return levels.index(level) >= levels.index(self.min_level)
        except ValueError:
            return True

    def send(self, message: str, level: str = 'INFO', **kwargs):
        """
        发送纯文本消息

        Args:
            message: 消息文本
            level: 消息级别
            **kwargs: 额外参数
        """
        if not self.should_send(level):
            return

        self._send_with_retry(message)

    def send_task_completion(self, result: Dict):
        """
        发送任务完成通知（格式化）

        Args:
            result: 任务执行结果
        """
        if not self.notify_on.get('task_complete', True):
            return

        message = self._format_task_completion(result)
        self._send_with_retry(message)

    def send_task_error(self, task_name: str, error: str):
        """
        发送任务失败通知

        Args:
            task_name: 任务名称
            error: 错误信息
        """
        if not self.notify_on.get('task_error', True):
            return

        message = self._format_task_error(task_name, error)
        self._send_with_retry(message)

    def send_new_posts_found(self, author_name: str, count: int):
        """
        发送发现新帖通知

        Args:
            author_name: 作者名
            count: 新帖数量
        """
        if not self.notify_on.get('new_posts_found', True):
            return

        message = f"""
🆕 **发现新帖子**

👤 作者：{author_name}
📝 新帖数量：{count} 篇

💡 将在下次定时任务中自动下载
"""
        self._send_with_retry(message)

    def test_connection(self) -> bool:
        """
        测试 Telegram 连接

        Returns:
            bool: 连接成功返回 True
        """
        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text="🤖 T66Y 归档系统 - 连接测试成功！"
            )
            return True
        except TelegramError:
            return False

    def _send_with_retry(self, message: str, max_retries: int = 3):
        """
        发送消息（带重试）

        Args:
            message: 消息文本
            max_retries: 最大重试次数
        """
        for attempt in range(max_retries):
            try:
                self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                return  # 成功，退出
            except TelegramError as e:
                if attempt < max_retries - 1:
                    time.sleep(5)  # 等待 5 秒后重试
                else:
                    # 最后一次失败，记录日志
                    print(f"Telegram 发送失败（{max_retries} 次）: {e}")

    def _format_task_completion(self, result: Dict) -> str:
        """
        格式化任务完成消息

        Args:
            result: 任务执行结果

        Returns:
            格式化的 Markdown 消息
        """
        emoji = "✅" if result['status'] == 'success' else "⚠️"

        return f"""
{emoji} **定时任务完成**

📝 任务名称：{result['task_name']}
👤 作者：{result['author_name']}
⏰ 执行时间：{result['start_time']}
⏱️ 耗时：{result['duration']}

📊 **本次结果**：
  • 新增帖子：{result['new_posts']} 篇
  • 跳过帖子：{result['skipped_posts']} 篇
  • 失败：{result['failed_posts']} 篇

💾 **归档统计**：
  • 已归档总数：{result['total_archived']} 篇
  • 论坛总数：{result['total_forum']} 篇
  • 完成度：{result['completion_rate']:.1f}%
"""

    def _format_task_error(self, task_name: str, error: str) -> str:
        """
        格式化任务失败消息

        Args:
            task_name: 任务名称
            error: 错误信息

        Returns:
            格式化的 Markdown 消息
        """
        return f"""
❌ **定时任务失败**

📝 任务名称：{task_name}
⏰ 失败时间：{self._get_current_time()}

⚠️ **错误信息**：
{error}

💡 **建议**：
- 检查网络连接
- 稍后手动重试
- 查看详细日志
"""

    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
```

---

## 3. 数据结构

### 3.1 配置文件结构（config.yaml）

```yaml
# ============ 通知配置 ============
notification:
  enabled: true

  # 终端通知
  console:
    enabled: true
    min_level: INFO  # DEBUG | INFO | WARNING | ERROR

  # 文件日志通知
  file:
    enabled: true
    log_path: ./logs/notifications.log
    min_level: INFO

  # MQTT Broker 通知
  telegram:
    enabled: false  # 默认关闭，需要用户配置后启用
    bot_token: ""   # 用户填写
    chat_id: ""     # 用户填写
    min_level: INFO

    # 通知触发配置
    notify_on:
      task_start: false      # 任务开始时通知（默认关闭）
      task_complete: true    # 任务完成时通知
      task_error: true       # 任务失败时通知
      new_posts_found: true  # 发现新帖时通知

    # 消息格式配置
    format:
      use_markdown: true     # 使用 Markdown 格式
      include_stats: true    # 包含统计信息
      include_timestamp: true # 包含时间戳

# ============ 定时任务配置 ============
schedule:
  enabled: true                # 启用定时任务功能
  daemon_mode: false           # 守护进程模式（未实现）
  check_interval_seconds: 60   # 检查间隔（未使用）

scheduler_tasks:
  - id: "task_1"                           # 任务唯一 ID
    name: "每日更新-同花顺心"               # 任务名称
    author_name: "同花顺心"                 # 作者名
    author_url: "https://t66y.com/@同花顺心" # 作者 URL
    enabled: true                           # 是否启用
    schedule_type: "cron"                   # 调度类型（cron | interval）
    cron_expression: "0 3 * * *"            # Cron 表达式（每天凌晨3点）
    max_pages: 3                            # 扫描页数

    # 任务级别的通知配置（可选，覆盖全局）
    notification:
      telegram:
        enabled: true                       # 单独控制此任务的 MQTT 消息发布
```

### 3.2 数据库表结构

#### scheduler_history（任务执行历史表）

```sql
CREATE TABLE IF NOT EXISTS scheduler_history (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 任务标识
    task_id TEXT NOT NULL,                    -- 任务 ID（关联 config.yaml）
    task_name TEXT NOT NULL,                  -- 任务名称
    author_name TEXT NOT NULL,                -- 作者名

    -- 执行时间
    start_time TEXT NOT NULL,                 -- 开始时间（YYYY-MM-DD HH:MM:SS）
    end_time TEXT,                            -- 结束时间
    duration_seconds REAL,                    -- 耗时（秒）

    -- 执行结果
    status TEXT NOT NULL,                     -- 状态：success | failed | partial
    new_posts INTEGER DEFAULT 0,              -- 新增帖子数
    skipped_posts INTEGER DEFAULT 0,          -- 跳过帖子数
    failed_posts INTEGER DEFAULT 0,           -- 失败帖子数

    -- 统计信息
    total_archived INTEGER DEFAULT 0,         -- 已归档总数（任务完成后）
    total_forum INTEGER DEFAULT 0,            -- 论坛总数
    completion_rate REAL DEFAULT 0,           -- 完成度（百分比）

    -- 错误信息
    error_message TEXT,                       -- 错误信息（如果失败）

    -- 元数据
    created_at TEXT DEFAULT CURRENT_TIMESTAMP -- 记录创建时间
);

-- 索引：加速查询
CREATE INDEX IF NOT EXISTS idx_scheduler_history_task ON scheduler_history(task_id);
CREATE INDEX IF NOT EXISTS idx_scheduler_history_time ON scheduler_history(start_time);
CREATE INDEX IF NOT EXISTS idx_scheduler_history_status ON scheduler_history(status);
```

### 3.3 任务配置对象（TypedDict）

```python
from typing import TypedDict, Optional

class TaskConfig(TypedDict):
    """任务配置类型定义"""
    id: str                      # 任务 ID（唯一）
    name: str                    # 任务名称
    author_name: str             # 作者名
    author_url: str              # 作者 URL
    enabled: bool                # 是否启用
    schedule_type: str           # cron | interval
    cron_expression: str         # Cron 表达式
    max_pages: int               # 扫描页数
    notification: Optional[dict] # 通知配置（可选）

class TaskResult(TypedDict):
    """任务执行结果类型定义"""
    task_id: str
    task_name: str
    author_name: str
    start_time: str
    end_time: str
    duration: str
    status: str                  # success | failed | partial
    new_posts: int
    skipped_posts: int
    failed_posts: int
    total_archived: int
    total_forum: int
    completion_rate: float
    error_message: Optional[str]
```

---

## 4. 接口规范

### 4.1 TaskScheduler 接口

#### 4.1.1 start()

```python
def start() -> None:
    """
    启动调度器

    行为：
    - 启动 APScheduler
    - 从 config.yaml 加载所有已启用任务
    - 设置状态为运行中

    异常：
    - RuntimeError: 如果调度器已启动

    示例：
        scheduler = TaskScheduler(config)
        scheduler.start()
    ```

#### 4.1.2 add_task()

```python
def add_task(task_config: dict) -> bool:
    """
    添加定时任务

    参数：
        task_config: 任务配置字典（见 TaskConfig）

    返回：
        bool: 添加成功返回 True

    异常：
        ValueError: task_id 已存在或 cron 表达式无效

    副作用：
        - 任务添加到 APScheduler
        - 任务保存到 config.yaml

    示例：
        success = scheduler.add_task({
            'id': 'task_1',
            'name': '每日更新-同花顺心',
            'author_name': '同花顺心',
            'author_url': 'https://t66y.com/@同花顺心',
            'enabled': True,
            'cron_expression': '0 3 * * *',
            'max_pages': 3
        })
    ```

#### 4.1.3 execute_task_manually()

```python
def execute_task_manually(task_id: str) -> Dict:
    """
    手动触发任务执行

    参数：
        task_id: 任务 ID

    返回：
        TaskResult: 执行结果字典

    异常：
        ValueError: 任务不存在

    副作用：
        - 任务立即执行（不等定时）
        - 执行结果保存到 scheduler_history
        - 发送通知

    示例：
        result = scheduler.execute_task_manually('task_1')
        print(f"新增帖子：{result['new_posts']} 篇")
    ```

### 4.2 NotificationManager 接口

#### 4.2.1 send_task_completion()

```python
def send_task_completion(result: Dict) -> None:
    """
    发送任务完成通知

    参数：
        result: 任务执行结果（TaskResult）

    行为：
        - 遍历所有启用的通知器
        - 格式化消息（根据通知器类型）
        - 发送通知

    示例：
        notification.send_task_completion({
            'task_name': '每日更新-同花顺心',
            'author_name': '同花顺心',
            'new_posts': 5,
            'status': 'success',
            ...
        })
    ```

### 4.3 MQTTNotifier 接口

#### 4.3.1 test_connection()

```python
def test_connection() -> bool:
    """
    测试 Telegram 连接

    返回：
        bool: 连接成功返回 True，失败返回 False

    行为：
        - 发送测试消息到配置的 Chat ID
        - 捕获所有异常，不抛出

    示例：
        notifier = MQTTNotifier(config)
        if notifier.test_connection():
            print("✅ 连接成功")
        else:
            print("❌ 连接失败")
    ```

---

## 5. 配置规范

### 5.1 配置文件位置

- **主配置**：`python/config.yaml`
- **APScheduler 持久化**：`python/data/scheduler_jobs.db`（自动创建）
- **执行历史**：`python/data/forum_data.db` 中的 `scheduler_history` 表

### 5.2 配置加载优先级

1. 环境变量（如 `$TELEGRAM_BOT_TOKEN`）
2. `config.yaml` 文件
3. 默认值（代码中定义）

### 5.3 配置验证规则

| 字段 | 类型 | 验证规则 | 默认值 |
|------|------|----------|--------|
| `task_id` | str | 唯一，不能重复 | 无 |
| `task_name` | str | 长度 1-50，不能为空 | 无 |
| `author_name` | str | 必须在关注列表中 | 无 |
| `cron_expression` | str | 符合 Cron 语法 | 无 |
| `max_pages` | int | 范围 1-10 | 3 |
| `bot_token` | str | 格式 `^\d+:[A-Za-z0-9_-]+$` | 无 |
| `chat_id` | str | 格式 `^-?\d+$` | 无 |

---

## 6. 数据库设计

### 6.1 scheduler_history 表

见 [3.2 数据库表结构](#32-数据库表结构)

### 6.2 查询接口

```python
# python/src/database/query.py

def get_task_execution_history(
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    db=None
) -> List[dict]:
    """
    查询任务执行历史

    Args:
        task_id: 任务 ID（可选，筛选条件）
        status: 状态（可选，success | failed）
        start_date: 开始日期（可选，YYYY-MM-DD）
        end_date: 结束日期（可选，YYYY-MM-DD）
        limit: 返回数量限制
        db: 数据库连接

    Returns:
        执行历史记录列表
    """
    if db is None:
        db = _get_db()

    sql = "SELECT * FROM scheduler_history WHERE 1=1"
    params = []

    if task_id:
        sql += " AND task_id = ?"
        params.append(task_id)

    if status:
        sql += " AND status = ?"
        params.append(status)

    if start_date:
        sql += " AND start_time >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND start_time <= ?"
        params.append(end_date + ' 23:59:59')

    sql += f" ORDER BY start_time DESC LIMIT {limit}"

    conn = db.get_connection()
    cursor = conn.execute(sql, params)

    return [dict(row) for row in cursor.fetchall()]
```

---

## 7. 错误处理

### 7.1 错误分类

| 错误类型 | 处理策略 | 用户反馈 | 日志记录 |
|----------|----------|----------|----------|
| **配置错误** | 启动时检查，阻止启动 | 显示错误提示 | ERROR |
| **网络错误** | 重试 3 次，失败则跳过 | 通知用户 | WARNING |
| **Telegram 错误** | 降级到日志文件 | 不中断任务 | WARNING |
| **任务执行错误** | 记录日志，发送通知 | MQTT 消息发布 | ERROR |
| **数据库错误** | 记录日志，继续执行 | 不影响归档 | ERROR |

### 7.2 异常捕获模式

```python
async def _execute_task(self, task_config: dict) -> Dict:
    """任务执行（异常捕获示例）"""
    try:
        # 执行归档
        result = await self.incremental_archiver.archive_author_incremental(...)

        # 保存历史
        self._save_execution_history(result)

        # 发送通知
        self.notification.send_task_completion(result)

    except NetworkError as e:
        # 网络错误：记录日志，通知用户
        logger.error(f"网络错误: {e}")
        self.notification.send_task_error(task_name, f"网络错误: {e}")

    except Exception as e:
        # 未知错误：记录详细堆栈，通知用户
        logger.exception(f"任务执行失败: {e}")
        self.notification.send_task_error(task_name, f"未知错误: {e}")
```

### 7.3 错误恢复机制

| 场景 | 恢复策略 |
|------|----------|
| APScheduler 崩溃 | 系统重启后自动加载任务 |
| Telegram 不可用 | 降级到日志文件，不影响任务 |
| 单个任务失败 | 不影响其他任务，记录错误日志 |
| 数据库写入失败 | 记录到日志文件，下次启动时补录 |

---

## 8. 测试方案

### 8.1 单元测试

#### 测试文件：`python/tests/test_task_scheduler.py`

```python
import pytest
from src.scheduler.task_scheduler import TaskScheduler

def test_add_task():
    """测试添加任务"""
    scheduler = TaskScheduler(test_config)

    task_config = {
        'id': 'test_task_1',
        'name': '测试任务',
        'author_name': '测试作者',
        'author_url': 'https://example.com',
        'enabled': True,
        'cron_expression': '0 3 * * *',
        'max_pages': 3
    }

    assert scheduler.add_task(task_config) == True

    # 验证任务已添加
    task = scheduler.get_task('test_task_1')
    assert task is not None
    assert task['name'] == '测试任务'

def test_add_duplicate_task():
    """测试添加重复任务（应该失败）"""
    scheduler = TaskScheduler(test_config)

    task_config = {'id': 'test_task_1', ...}

    scheduler.add_task(task_config)

    with pytest.raises(ValueError):
        scheduler.add_task(task_config)  # 第二次添加应该抛出异常

def test_invalid_cron_expression():
    """测试无效的 Cron 表达式"""
    scheduler = TaskScheduler(test_config)

    task_config = {
        'id': 'test_task_2',
        'cron_expression': 'invalid_cron',  # 无效
        ...
    }

    with pytest.raises(ValueError):
        scheduler.add_task(task_config)
```

#### 测试文件：`python/tests/test_mqtt_notifier.py`

```python
import pytest
from src.notification.mqtt_notifier import MQTTNotifier

def test_telegram_connection():
    """测试 Telegram 连接"""
    notifier = MQTTNotifier(test_config)

    # 跳过测试（如果没有配置真实的 Bot Token）
    if not notifier.enabled:
        pytest.skip("Telegram 未配置")

    assert notifier.test_connection() == True

def test_send_task_completion():
    """测试发送任务完成通知"""
    notifier = MQTTNotifier(test_config)

    mock_result = {
        'task_name': '测试任务',
        'author_name': '测试作者',
        'new_posts': 5,
        'status': 'success',
        ...
    }

    # 应该不抛出异常
    notifier.send_task_completion(mock_result)

def test_message_formatting():
    """测试消息格式化"""
    notifier = MQTTNotifier(test_config)

    result = {
        'task_name': '测试任务',
        'author_name': '测试作者',
        'start_time': '2026-02-15 03:00:00',
        'duration': '2分35秒',
        'new_posts': 5,
        'skipped_posts': 10,
        'failed_posts': 0,
        'total_archived': 15,
        'total_forum': 20,
        'completion_rate': 75.0,
        'status': 'success'
    }

    message = notifier._format_task_completion(result)

    assert '测试任务' in message
    assert '5 篇' in message
    assert '75.0%' in message
```

### 8.2 集成测试

#### 测试文件：`python/tests/test_scheduler_integration.py`

```python
import pytest
import asyncio
from src.scheduler.task_scheduler import TaskScheduler

@pytest.mark.asyncio
async def test_end_to_end_execution():
    """端到端测试：添加任务 → 手动执行 → 验证结果"""
    scheduler = TaskScheduler(test_config)
    scheduler.start()

    # 1. 添加任务
    task_config = {
        'id': 'test_integration_1',
        'name': '集成测试任务',
        'author_name': '测试作者',  # 需要有真实数据
        'author_url': 'https://t66y.com/@测试作者',
        'enabled': True,
        'cron_expression': '0 3 * * *',
        'max_pages': 1
    }

    scheduler.add_task(task_config)

    # 2. 手动执行
    result = scheduler.execute_task_manually('test_integration_1')

    # 3. 验证结果
    assert result['status'] in ['success', 'no_new_posts']
    assert 'new_posts' in result
    assert 'total_archived' in result

    # 4. 验证历史记录
    history = get_task_execution_history(task_id='test_integration_1')
    assert len(history) == 1
    assert history[0]['task_id'] == 'test_integration_1'

    # 5. 清理
    scheduler.remove_task('test_integration_1')
    scheduler.stop()
```

### 8.3 测试覆盖率目标

| 模块 | 目标覆盖率 | 关键测试点 |
|------|-----------|------------|
| TaskScheduler | 80% | 添加/删除/执行任务 |
| IncrementalArchiver | 70% | 增量检测、归档流程 |
| NotificationManager | 60% | 消息分发、优先级 |
| MQTTNotifier | 70% | 连接测试、消息格式化 |

---

## 9. 实施步骤

### 9.1 Week 1: 定时任务核心（P0）

#### Day 1: 环境准备和基础模块

**上午**：
- [ ] 安装依赖：`pip install apscheduler==3.10.4 paho-mqtt==20.7`
- [ ] 创建目录结构：
  ```bash
  mkdir -p python/src/scheduler
  mkdir -p python/src/notification
  ```
- [ ] 创建 `__init__.py` 文件

**下午**：
- [ ] 实现 `NotificationManager` 基础类（100 行）
- [ ] 实现 `ConsoleNotifier`（80 行）
- [ ] 实现 `FileNotifier`（80 行）
- [ ] 单元测试：通知管理器

**验收标准**：
- 可以发送消息到终端和日志文件
- 消息优先级过滤正常

#### Day 2: IncrementalArchiver

**上午**：
- [ ] 创建 `incremental_archiver.py`
- [ ] 实现 `IncrementalArchiver` 类（150 行）
- [ ] 修改 `archiver.py`，添加 `target_urls` 参数（+10 行）

**下午**：
- [ ] 单元测试：增量检测
- [ ] 单元测试：增量归档
- [ ] 集成测试：检测 + 归档完整流程

**验收标准**：
- 可以检测新帖
- 可以只归档新帖
- 无新帖时跳过归档

#### Day 3: TaskScheduler（上）

**上午**：
- [ ] 创建 `task_scheduler.py`
- [ ] 实现 `TaskScheduler` 基础结构
- [ ] 实现 `start()` 和 `stop()` 方法
- [ ] 实现 `add_task()` 方法

**下午**：
- [ ] 实现 `remove_task()` 方法
- [ ] 实现 `update_task()` 方法
- [ ] 实现 `get_all_tasks()` 方法
- [ ] 单元测试：任务 CRUD

**验收标准**：
- 可以添加/删除/修改任务
- 任务列表显示正确

#### Day 4: TaskScheduler（下）

**上午**：
- [ ] 实现 `_execute_task()` 核心逻辑
- [ ] 实现 `execute_task_manually()` 方法
- [ ] 集成 `IncrementalArchiver`
- [ ] 集成 `NotificationManager`

**下午**：
- [ ] 实现配置文件读写（`_save_task_to_config` 等）
- [ ] 实现执行历史记录（`_save_execution_history`）
- [ ] 单元测试：任务执行
- [ ] 集成测试：端到端流程

**验收标准**：
- 可以手动执行任务
- 执行结果保存到数据库
- 发送通知到终端

#### Day 5: 数据库和 UI

**上午**：
- [ ] 创建 `scheduler_history` 表（SQL）
- [ ] 实现 `get_task_execution_history()` 查询函数
- [ ] 实现日志清理功能

**下午**：
- [ ] 创建 `scheduler_menu.py`（400 行）
- [ ] 实现"查看任务列表"功能
- [ ] 实现"添加任务"功能
- [ ] 实现"删除任务"功能
- [ ] 主菜单集成

**验收标准**：
- 可以通过 UI 添加/删除任务
- 任务列表显示完整信息
- 可以手动触发任务

### 9.2 Week 2: MQTT 消息发布（P1）

#### Day 6: MQTTNotifier

**上午**：
- [ ] 创建 `mqtt_notifier.py`
- [ ] 实现 `MQTTNotifier` 类（250 行）
- [ ] 实现消息格式化方法

**下午**：
- [ ] 实现 `test_connection()` 方法
- [ ] 实现重试机制
- [ ] 单元测试：MQTT 消息发布
- [ ] 集成到 `NotificationManager`

**验收标准**：
- 可以发布 MQTT 消息
- 消息格式正确
- 连接测试正常

#### Day 7: 通知配置 UI

**上午**：
- [ ] 创建 `notification_menu.py`（100 行）
- [ ] 实现配置输入界面（Bot Token, Chat ID）
- [ ] 实现配置验证

**下午**：
- [ ] 实现连接测试功能
- [ ] 实现配置保存
- [ ] 集成到主菜单

**验收标准**：
- 可以输入 Telegram 配置
- 配置验证正确
- 测试连接正常

#### Day 8-9: 测试和优化

**Day 8**：
- [ ] 端到端测试（完整流程）
- [ ] 性能测试（任务执行时间）
- [ ] 错误场景测试（网络断开、Telegram 不可用）
- [ ] Bug 修复

**Day 9**：
- [ ] 代码审查和重构
- [ ] 添加代码注释
- [ ] 编写用户文档（Telegram 配置指南）
- [ ] 更新 README.md

**验收标准**：
- 所有单元测试通过
- 集成测试通过
- 无严重 Bug

#### Day 10: 验收和发布

**上午**：
- [ ] 验收测试（按需求文档验收标准）
- [ ] 性能测试（确认达到指标）
- [ ] 用户验收测试（如有用户）

**下午**：
- [ ] 创建 Git Tag：`PHASE5_COMPLETED`
- [ ] 推送到 GitHub
- [ ] 编写完成报告（`PHASE5_COMPLETION_REPORT.md`）
- [ ] 更新项目文档

**验收标准**：
- 功能验收：所有 P0 功能完成
- 性能验收：达到性能目标
- 质量验收：测试覆盖率 > 70%

---

## 10. 代码规范

### 10.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `TaskScheduler` |
| 方法名 | snake_case | `execute_task()` |
| 私有方法 | 前缀 `_` | `_save_execution_history()` |
| 常量 | UPPER_CASE | `MAX_RETRIES` |
| 变量 | snake_case | `task_config` |

### 10.2 文档字符串

```python
def execute_task_manually(self, task_id: str) -> Dict:
    """
    手动触发任务执行

    Args:
        task_id: 任务 ID

    Returns:
        Dict: 执行结果字典，包含以下字段：
            - task_id: 任务 ID
            - status: 执行状态（success | failed）
            - new_posts: 新增帖子数
            - error_message: 错误信息（如果失败）

    Raises:
        ValueError: 任务不存在时抛出

    Example:
        >>> result = scheduler.execute_task_manually('task_1')
        >>> print(f"新增帖子：{result['new_posts']} 篇")
    """
    pass
```

### 10.3 类型注解

```python
from typing import Optional, Dict, List

def get_task(self, task_id: str) -> Optional[Dict]:
    """获取任务详情"""
    pass

async def _execute_task(self, task_config: Dict) -> Dict:
    """执行任务"""
    pass
```

### 10.4 错误处理

```python
# ✅ 好的做法
try:
    result = await self.incremental_archiver.archive_author_incremental(...)
except NetworkError as e:
    logger.error(f"网络错误: {e}")
    self.notification.send_task_error(task_name, f"网络错误: {e}")
except Exception as e:
    logger.exception(f"未知错误: {e}")
    raise

# ❌ 不好的做法
try:
    result = await self.incremental_archiver.archive_author_incremental(...)
except:
    pass  # 吞掉所有异常
```

### 10.5 日志规范

```python
import logging

logger = logging.getLogger(__name__)

# 使用不同级别
logger.debug("任务配置: %s", task_config)  # 调试信息
logger.info("任务开始执行: %s", task_name)  # 正常信息
logger.warning("Telegram 发送失败，降级到日志")  # 警告
logger.error("任务执行失败: %s", error)  # 错误
logger.exception("未知异常")  # 错误 + 堆栈
```

---

## 11. 附录

### 11.1 Cron 表达式快速参考

```
格式：分 时 日 月 周

字段：
  分钟：0-59
  小时：0-23
  日期：1-31
  月份：1-12
  星期：0-6（0=周日）

特殊字符：
  *    任意值
  ,    列表（1,3,5）
  -    范围（1-5）
  /    间隔（*/5 = 每5个单位）

示例：
  0 3 * * *       每天凌晨3点
  0 */6 * * *     每6小时
  0 2 * * 0       每周日凌晨2点
  30 14 * * 1-5   工作日下午2:30
  0 0 1 * *       每月1日凌晨
```

### 11.2 MQTT Broker API 参考

**创建 Bot**：
1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按提示设置名称
4. 获取 Bot Token

**获取 Chat ID**：
方法 1（推荐）：
1. 给 Bot 发送任意消息
2. 访问：`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. 查找 `"chat":{"id": 123456789}`

方法 2：
1. 搜索 `@userinfobot`
2. 发送 `/start`
3. 获取你的 Chat ID

**API 文档**：https://core.telegram.org/bots/api

### 11.3 APScheduler 参考

**官方文档**：https://apscheduler.readthedocs.io/

**常用触发器**：
- `CronTrigger`: 基于 Cron 表达式
- `IntervalTrigger`: 固定间隔（hours=6）
- `DateTrigger`: 一次性任务

**持久化**：
- `SQLAlchemyJobStore`: SQLite 持久化
- `MemoryJobStore`: 内存存储（不推荐）

---

**文档结束**

> **审批**：
> - 架构师：_______ 日期：_______
> - 技术负责人：_______ 日期：_______
> - 开发负责人：_______ 日期：_______

---

## 12. MQTT Broker 部署指南

### 12.1 Mosquitto 安装

**Ubuntu/Debian**：
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients

# 启动服务
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# 验证运行状态
sudo systemctl status mosquitto
```

**macOS**：
```bash
brew install mosquitto

# 启动服务
brew services start mosquitto

# 或手动启动
/usr/local/opt/mosquitto/sbin/mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf
```

**Windows**：
- 下载安装包：https://mosquitto.org/download/
- 运行安装程序
- 以服务方式启动

### 12.2 基础配置

创建配置文件 `/etc/mosquitto/mosquitto.conf`：

```conf
# 监听端口
listener 1883

# 允许匿名连接（测试环境）
allow_anonymous true

# 持久化配置
persistence true
persistence_location /var/lib/mosquitto/

# 日志配置
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
```

**重启服务**：
```bash
sudo systemctl restart mosquitto
```

### 12.3 测试连接

**终端 1：订阅消息**
```bash
mosquitto_sub -h localhost -t "t66y/scheduler/events" -v
```

**终端 2：发布测试消息**
```bash
mosquitto_pub -h localhost -t "t66y/scheduler/events" -m '{"test": "hello"}'
```

终端 1 应该收到消息。

### 12.4 生产环境配置（可选）

**启用认证**：
```bash
# 创建密码文件
sudo mosquitto_passwd -c /etc/mosquitto/passwd username

# 修改配置
echo "allow_anonymous false" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo "password_file /etc/mosquitto/passwd" | sudo tee -a /etc/mosquitto/mosquitto.conf

# 重启服务
sudo systemctl restart mosquitto
```

**启用 TLS（可选）**：
- 生成 SSL 证书
- 配置 `listener 8883` 和证书路径
- 客户端使用 TLS 连接

---

## 13. 消息处理器参考实现

### 13.1 MQTT → Telegram 转发器

创建文件 `python/tools/mqtt_to_telegram.py`：

```python
#!/usr/bin/env python3
"""
MQTT 消息处理器 - Telegram 转发

订阅 MQTT 消息并转发到 Telegram
"""

import paho.mqtt.client as mqtt
import json
import os
from telegram import Bot

# ============ 配置 ============
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 't66y/#')  # 订阅所有 t66y 消息

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ 请配置环境变量：TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")
    exit(1)

# 初始化 Telegram Bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ============ 消息格式化 ============

def format_task_completed(data):
    """格式化任务完成消息"""
    d = data['data']
    return f"""
✅ **任务完成**

📝 {d['task_name']}
👤 {d['author_name']}
⏱️ {d['duration']}

📊 **结果**：
  • 新增：{d['new_posts']} 篇
  • 跳过：{d['skipped_posts']} 篇
  • 失败：{d['failed_posts']} 篇

💾 **统计**：
  • 已归档：{d['total_archived']} 篇
  • 论坛总数：{d['total_forum']} 篇
  • 完成度：{d['completion_rate']:.1f}%
"""

def format_task_failed(data):
    """格式化任务失败消息"""
    d = data['data']
    return f"""
❌ **任务失败**

📝 {d['task_name']}
⚠️ 错误：{d['error']}

💡 建议：检查网络连接，稍后重试
"""

def format_new_posts_found(data):
    """格式化发现新帖消息"""
    d = data['data']
    return f"""
🆕 **发现新帖**

👤 {d['author_name']}
📝 数量：{d['new_count']} 篇

💡 将在下次定时任务中自动下载
"""

# ============ MQTT 回调 ============

def on_connect(client, userdata, flags, rc):
    """连接成功回调"""
    if rc == 0:
        print(f"✅ 已连接 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"📡 已订阅 Topic: {MQTT_TOPIC}")
    else:
        print(f"❌ 连接失败，返回码: {rc}")

def on_message(client, userdata, msg):
    """收到消息回调"""
    try:
        # 解析 JSON
        data = json.loads(msg.payload.decode())
        
        # 根据事件类型格式化消息
        event_type = data.get('event_type')
        
        if event_type == 'task_completed':
            text = format_task_completed(data)
        elif event_type == 'task_failed':
            text = format_task_failed(data)
        elif event_type == 'new_posts_found':
            text = format_new_posts_found(data)
        elif event_type == 'connection_test':
            text = "🤖 连接测试成功！"
        else:
            text = f"📨 未知消息类型：{event_type}\n\n```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```"
        
        # 发送到 Telegram
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode='Markdown'
        )
        
        print(f"✅ 已转发消息到 Telegram: {event_type}")
        
    except json.JSONDecodeError:
        print(f"⚠️  消息格式错误: {msg.payload}")
    except Exception as e:
        print(f"❌ 处理消息失败: {e}")

# ============ 主程序 ============

def main():
    """主程序"""
    print("=" * 60)
    print("  MQTT → Telegram 消息处理器")
    print("=" * 60)
    print(f"  MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  订阅 Topic: {MQTT_TOPIC}")
    print(f"  Telegram Chat ID: {TELEGRAM_CHAT_ID}")
    print("=" * 60)
    
    # 创建 MQTT 客户端
    client = mqtt.Client(client_id="mqtt-to-telegram")
    client.on_connect = on_connect
    client.on_message = on_message
    
    # 连接并循环
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        print("\n🤖 消息处理器已启动，等待消息...\n")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n\n👋 正在停止...")
        client.disconnect()
    except Exception as e:
        print(f"\n❌ 错误: {e}")

if __name__ == '__main__':
    main()
```

### 13.2 使用方式

**方式 1：直接运行**
```bash
# 设置环境变量
export MQTT_BROKER="localhost"
export MQTT_TOPIC="t66y/#"
export TELEGRAM_BOT_TOKEN="你的Bot Token"
export TELEGRAM_CHAT_ID="你的Chat ID"

# 运行
python python/tools/mqtt_to_telegram.py
```

**方式 2：后台运行**
```bash
nohup python python/tools/mqtt_to_telegram.py > /tmp/mqtt-telegram.log 2>&1 &
```

**方式 3：Systemd 服务（推荐）**

创建文件 `/etc/systemd/system/mqtt-to-telegram.service`：
```ini
[Unit]
Description=MQTT to Telegram Message Forwarder
After=network.target mosquitto.service

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/gemini-t66y
Environment="MQTT_BROKER=localhost"
Environment="MQTT_TOPIC=t66y/#"
Environment="TELEGRAM_BOT_TOKEN=你的Token"
Environment="TELEGRAM_CHAT_ID=你的ChatID"
ExecStart=/usr/bin/python3 /home/yourusername/gemini-t66y/python/tools/mqtt_to_telegram.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable mqtt-to-telegram.service
sudo systemctl start mqtt-to-telegram.service

# 查看状态
sudo systemctl status mqtt-to-telegram.service

# 查看日志
sudo journalctl -u mqtt-to-telegram.service -f
```

---

**文档结束**

> **审批**：
> - 架构师：_______ 日期：_______
> - 技术负责人：_______ 日期：_______
> - 开发负责人：_______ 日期：_______

