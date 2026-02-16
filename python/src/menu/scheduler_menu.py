#!/usr/bin/env python3
"""调度器菜单模块

功能：
- 查看当前任务列表
- 添加新定时任务
- 删除任务
- 启动/停止调度器
- 配置 MQTT 通知
- 执行任务（手动测试）
"""

from typing import Optional, Dict, List
from pathlib import Path
import json
from datetime import datetime


class SchedulerMenu:
    """调度器菜单类"""

    def __init__(self, config: dict):
        """
        初始化调度器菜单

        Args:
            config: 全局配置字典
        """
        self.config = config

        # 延迟导入以避免循环依赖
        # 尝试相对导入（从 main.py 调用时）
        try:
            from ..scheduler.task_scheduler import TaskScheduler
            from ..scheduler.incremental_archiver import IncrementalArchiver
            from ..database.connection import get_default_connection
            from ..notification.manager import NotificationManager
            from ..notification.console_notifier import ConsoleNotifier
            from ..notification.file_notifier import FileNotifier
            from ..notification.mqtt_notifier import MQTTNotifier
        except ImportError:
            # 回退到绝对导入（从测试调用时）
            from scheduler.task_scheduler import TaskScheduler
            from scheduler.incremental_archiver import IncrementalArchiver
            from database.connection import get_default_connection
            from notification.manager import NotificationManager
            from notification.console_notifier import ConsoleNotifier
            from notification.file_notifier import FileNotifier
            from notification.mqtt_notifier import MQTTNotifier

        # 初始化组件
        self.db = get_default_connection()
        self.scheduler = TaskScheduler(config)
        self.archiver = IncrementalArchiver(config)

        # 初始化通知管理器
        self.notification_manager = NotificationManager()

        # 添加通知器
        console_config = config.get('notification', {}).get('console', {})
        if console_config.get('enabled', True):
            self.notification_manager.add_notifier(ConsoleNotifier(config))

        file_config = config.get('notification', {}).get('file', {})
        if file_config.get('enabled', True):
            self.notification_manager.add_notifier(FileNotifier(config))

        mqtt_config = config.get('notification', {}).get('mqtt', {})
        if mqtt_config.get('enabled', False):
            self.notification_manager.add_notifier(MQTTNotifier(config))

        # 注册任务函数
        self._register_task_functions()

    def _register_task_functions(self):
        """注册可用的任务函数"""
        import asyncio

        def incremental_archive_wrapper(**kwargs):
            """包装器：将 async 函数转为同步"""
            author_name = kwargs.get('author_name')
            max_pages = kwargs.get('max_pages', None)

            result = asyncio.run(
                self.archiver.archive_author_incremental(
                    author_name=author_name,
                    max_pages=max_pages
                )
            )

            # 发送通知
            if result['status'] == 'completed':
                self.notification_manager.send_task_completion(result)
                if result['new_posts'] > 0:
                    self.notification_manager.send_new_posts_found(
                        author_name=author_name,
                        count=result['new_posts']
                    )
            else:
                self.notification_manager.send_task_error(
                    task_name=f"增量归档: {author_name}",
                    error=result.get('error', '未知错误')
                )

            return result

        self.scheduler.register_task_function(
            'incremental_archive',
            incremental_archive_wrapper
        )

    def show(self):
        """显示调度器菜单（主入口）"""
        while True:
            print("\n" + "=" * 60)
            print("调度器管理")
            print("=" * 60)

            # 显示调度器状态
            self._display_scheduler_status()

            # 显示任务列表
            self._display_task_list()

            # 显示菜单选项
            print("\n操作选项:")
            print("  1. 查看任务详情")
            print("  2. 添加新任务")
            print("  3. 删除任务")
            if self.scheduler.is_running():
                print("  4. 停止调度器")
            else:
                print("  4. 启动调度器")
            print("  5. 执行任务（手动测试）")
            print("  6. 配置 MQTT 通知")
            print("  0. 返回主菜单")

            choice = input("\n请选择操作 [0-6]: ").strip()

            if choice == '0':
                break
            elif choice == '1':
                self._view_task_detail()
            elif choice == '2':
                self._add_task()
            elif choice == '3':
                self._delete_task()
            elif choice == '4':
                self._toggle_scheduler()
            elif choice == '5':
                self._execute_task_manually()
            elif choice == '6':
                self._configure_mqtt()
            else:
                print("❌ 无效选择，请重试")

    def _display_scheduler_status(self):
        """显示调度器状态"""
        status = "🟢 运行中" if self.scheduler.is_running() else "🔴 已停止"
        print(f"\n调度器状态: {status}")

        # 显示通知器状态
        notifiers = []
        if self.config.get('notification', {}).get('console', {}).get('enabled', True):
            notifiers.append("控制台")
        if self.config.get('notification', {}).get('file', {}).get('enabled', True):
            log_file = self.config.get('notification', {}).get('file', {}).get('log_file', 'scheduler.log')
            notifiers.append(f"文件({log_file})")
        if self.config.get('notification', {}).get('mqtt', {}).get('enabled', False):
            broker = self.config.get('notification', {}).get('mqtt', {}).get('broker', 'localhost')
            notifiers.append(f"MQTT({broker})")

        if notifiers:
            print(f"通知渠道: {', '.join(notifiers)}")
        else:
            print("通知渠道: 无")

    def _display_task_list(self):
        """显示任务列表"""
        tasks = self.scheduler.get_all_tasks()

        if not tasks:
            print("\n当前无定时任务")
            return

        print(f"\n当前任务列表 (共 {len(tasks)} 个):")
        print("-" * 60)
        print(f"{'ID':<20} {'任务名称':<20} {'下次运行':<20}")
        print("-" * 60)

        for task in tasks:
            task_id = task['id'][:18] + '..' if len(task['id']) > 20 else task['id']
            task_name = task['name'][:18] + '..' if len(task['name']) > 20 else task['name']
            next_run = task.get('next_run', '未知')
            if next_run and len(next_run) > 20:
                next_run = next_run[:17] + '...'

            print(f"{task_id:<20} {task_name:<20} {next_run or 'N/A':<20}")

    def _view_task_detail(self):
        """查看任务详情"""
        tasks = self.scheduler.get_all_tasks()
        if not tasks:
            print("\n❌ 当前无任务")
            return

        print("\n当前任务列表:")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. {task['name']} (ID: {task['id']})")

        choice = input("\n请选择任务序号 (0 取消): ").strip()
        if choice == '0':
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(tasks):
                task = tasks[index]
                self._show_task_detail(task['id'])
            else:
                print("❌ 无效序号")
        except ValueError:
            print("❌ 请输入数字")

    def _show_task_detail(self, task_id: str):
        """显示任务详细信息"""
        task = self.scheduler.get_task(task_id)
        if not task:
            print("❌ 任务不存在")
            return

        print("\n" + "=" * 60)
        print("任务详情")
        print("=" * 60)
        print(f"任务 ID: {task['id']}")
        print(f"任务名称: {task['name']}")
        print(f"触发器: {task['trigger']}")
        print(f"下次运行: {task.get('next_run', 'N/A')}")

        # 读取任务配置
        config = self._load_task_config(task_id)
        if config:
            print(f"\n任务类型: {config.get('function_name', '未知')}")
            print(f"Cron 表达式: {config.get('cron_expr', '未知')}")
            print(f"参数: {json.dumps(config.get('kwargs', {}), ensure_ascii=False, indent=2)}")

        input("\n按回车键继续...")

    def _add_task(self):
        """添加新任务"""
        print("\n" + "=" * 60)
        print("添加定时任务")
        print("=" * 60)

        # 获取作者列表
        try:
            from ..database.models import Author
        except ImportError:
            from database.models import Author
        authors = Author.get_all(db=self.db)

        if not authors:
            print("❌ 数据库中无作者，请先添加作者")
            return

        # 选择作者
        print("\n可用作者:")
        for i, author in enumerate(authors, 1):
            print(f"  {i}. {author.name}")

        author_choice = input("\n请选择作者序号 (0 取消): ").strip()
        if author_choice == '0':
            return

        try:
            author_index = int(author_choice) - 1
            if not (0 <= author_index < len(authors)):
                print("❌ 无效序号")
                return
            selected_author = authors[author_index]
        except ValueError:
            print("❌ 请输入数字")
            return

        # 输入 Cron 表达式
        print("\nCron 表达式格式: 分 时 日 月 周")
        print("示例:")
        print("  每天凌晨 2 点: 0 2 * * *")
        print("  每周一上午 10 点: 0 10 * * 1")
        print("  每小时: 0 * * * *")

        cron_expr = input("\n请输入 Cron 表达式: ").strip()
        if not cron_expr:
            print("❌ Cron 表达式不能为空")
            return

        # 验证 Cron 表达式
        if not self._validate_cron_expr(cron_expr):
            print("❌ 无效的 Cron 表达式")
            return

        # 输入扫描页数（可选）
        max_pages_input = input("\n最大扫描页数 (留空=全部): ").strip()
        max_pages = None
        if max_pages_input:
            try:
                max_pages = int(max_pages_input)
                if max_pages <= 0:
                    print("❌ 页数必须大于 0")
                    return
            except ValueError:
                print("❌ 请输入有效数字")
                return

        # 生成任务 ID 和名称
        task_id = f"incremental_{selected_author.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        task_name = f"增量归档: {selected_author.name}"

        # 任务参数
        kwargs = {
            'author_name': selected_author.name,
            'max_pages': max_pages
        }

        # 添加任务
        try:
            success = self.scheduler.add_task(
                task_id=task_id,
                task_name=task_name,
                cron_expr=cron_expr,
                function_name='incremental_archive',
                kwargs=kwargs
            )

            if success:
                print(f"\n✅ 任务添加成功！")
                print(f"   任务 ID: {task_id}")
                print(f"   作者: {selected_author.name}")
                print(f"   Cron: {cron_expr}")
                if max_pages:
                    print(f"   扫描页数: {max_pages}")
                else:
                    print(f"   扫描页数: 全部")

                # 发送通知
                self.notification_manager.send(
                    f"新增定时任务: {task_name}",
                    level='INFO'
                )
            else:
                print("❌ 任务添加失败")
        except Exception as e:
            print(f"❌ 添加任务时出错: {e}")

    def _delete_task(self):
        """删除任务"""
        tasks = self.scheduler.get_all_tasks()
        if not tasks:
            print("\n❌ 当前无任务")
            return

        print("\n当前任务列表:")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. {task['name']} (ID: {task['id']})")

        choice = input("\n请选择要删除的任务序号 (0 取消): ").strip()
        if choice == '0':
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(tasks):
                task = tasks[index]
                confirm = input(f"\n确认删除任务 '{task['name']}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    success = self.scheduler.remove_task(task['id'])
                    if success:
                        print(f"✅ 任务已删除: {task['name']}")
                        self.notification_manager.send(
                            f"删除定时任务: {task['name']}",
                            level='INFO'
                        )
                    else:
                        print("❌ 删除失败")
            else:
                print("❌ 无效序号")
        except ValueError:
            print("❌ 请输入数字")

    def _toggle_scheduler(self):
        """启动/停止调度器"""
        if self.scheduler.is_running():
            # 停止调度器
            confirm = input("\n确认停止调度器? (y/n): ").strip().lower()
            if confirm == 'y':
                self.scheduler.stop()
                print("✅ 调度器已停止")
                self.notification_manager.send(
                    "调度器已停止",
                    level='WARNING'
                )
        else:
            # 启动调度器
            tasks = self.scheduler.get_all_tasks()
            if not tasks:
                print("\n⚠️  当前无任务，启动调度器无意义")
                confirm = input("是否仍要启动? (y/n): ").strip().lower()
                if confirm != 'y':
                    return

            self.scheduler.start()
            print("✅ 调度器已启动")
            self.notification_manager.send(
                "调度器已启动",
                level='INFO'
            )

            if tasks:
                print(f"\n当前有 {len(tasks)} 个定时任务将按计划执行")

    def _execute_task_manually(self):
        """手动执行任务（用于测试）"""
        tasks = self.scheduler.get_all_tasks()
        if not tasks:
            print("\n❌ 当前无任务")
            return

        print("\n当前任务列表:")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. {task['name']} (ID: {task['id']})")

        choice = input("\n请选择要执行的任务序号 (0 取消): ").strip()
        if choice == '0':
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(tasks):
                task = tasks[index]
                print(f"\n⏳ 正在执行任务: {task['name']}...")

                # 读取任务配置
                config = self._load_task_config(task['id'])
                if not config:
                    print("❌ 无法读取任务配置")
                    return

                function_name = config.get('function_name')
                kwargs = config.get('kwargs', {})

                # 执行任务
                try:
                    result = self.scheduler.execute_task_now(task['id'])
                    print(f"\n✅ 任务执行完成")
                    print(f"   状态: {result.get('status', '未知')}")
                    print(f"   新增归档: {result.get('new_posts', 0)}")
                    print(f"   跳过: {result.get('skipped_posts', 0)}")
                    print(f"   失败: {result.get('failed_posts', 0)}")
                    print(f"   耗时: {result.get('duration', 0):.2f} 秒")

                    if result.get('error'):
                        print(f"   错误: {result['error']}")
                except Exception as e:
                    print(f"❌ 执行失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ 无效序号")
        except ValueError:
            print("❌ 请输入数字")

    def _configure_mqtt(self):
        """配置 MQTT 通知"""
        print("\n" + "=" * 60)
        print("MQTT 通知配置")
        print("=" * 60)

        mqtt_config = self.config.get('notification', {}).get('mqtt', {})

        # 显示当前配置
        print(f"\n当前配置:")
        print(f"  启用: {mqtt_config.get('enabled', False)}")
        print(f"  Broker: {mqtt_config.get('broker', 'localhost')}")
        print(f"  端口: {mqtt_config.get('port', 1883)}")
        print(f"  主题: {mqtt_config.get('topic', 't66y/scheduler/events')}")
        print(f"  QoS: {mqtt_config.get('qos', 1)}")

        print("\n操作选项:")
        print("  1. 启用/禁用 MQTT")
        print("  2. 修改 Broker 地址")
        print("  3. 修改端口")
        print("  4. 修改主题")
        print("  0. 返回")

        choice = input("\n请选择操作 [0-4]: ").strip()

        if choice == '1':
            current = mqtt_config.get('enabled', False)
            mqtt_config['enabled'] = not current
            self._save_notification_config()
            status = "启用" if mqtt_config['enabled'] else "禁用"
            print(f"✅ MQTT 已{status}")
            print("⚠️  需要重启菜单以应用更改")

        elif choice == '2':
            broker = input("请输入 Broker 地址: ").strip()
            if broker:
                mqtt_config['broker'] = broker
                self._save_notification_config()
                print(f"✅ Broker 已更新: {broker}")
                print("⚠️  需要重启菜单以应用更改")

        elif choice == '3':
            port_input = input("请输入端口号: ").strip()
            try:
                port = int(port_input)
                if 1 <= port <= 65535:
                    mqtt_config['port'] = port
                    self._save_notification_config()
                    print(f"✅ 端口已更新: {port}")
                    print("⚠️  需要重启菜单以应用更改")
                else:
                    print("❌ 端口号必须在 1-65535 之间")
            except ValueError:
                print("❌ 请输入有效数字")

        elif choice == '4':
            topic = input("请输入主题: ").strip()
            if topic:
                mqtt_config['topic'] = topic
                self._save_notification_config()
                print(f"✅ 主题已更新: {topic}")
                print("⚠️  需要重启菜单以应用更改")

    def _validate_cron_expr(self, cron_expr: str) -> bool:
        """验证 Cron 表达式"""
        try:
            from apscheduler.triggers.cron import CronTrigger
            CronTrigger.from_crontab(cron_expr)
            return True
        except Exception:
            return False

    def _load_task_config(self, task_id: str) -> Optional[Dict]:
        """加载任务配置"""
        tasks_file = Path(self.config.get('data_dir', 'python/data')) / 'scheduler_tasks.json'
        if not tasks_file.exists():
            return None

        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                all_tasks = json.load(f)
                return all_tasks.get(task_id)
        except Exception:
            return None

    def _save_notification_config(self):
        """保存通知配置到 config.yaml"""
        try:
            from ..config.manager import ConfigManager
        except ImportError:
            from config.manager import ConfigManager
        config_manager = ConfigManager()
        config_manager.save(self.config)
