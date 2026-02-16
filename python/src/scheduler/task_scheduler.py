# python/src/scheduler/task_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
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

    依赖：
    - APScheduler
    """

    def __init__(self, config: dict):
        """
        初始化任务调度器

        Args:
            config: 配置字典
                - data_dir: 数据目录（用于存储任务配置）
        """
        self.config = config
        self.scheduler = BackgroundScheduler()

        # 任务配置文件
        data_dir = Path(config.get('data_dir', 'python/data'))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = data_dir / 'scheduler_tasks.json'

        # 任务回调函数注册表
        self.task_functions: Dict[str, Callable] = {}

    def register_task_function(self, name: str, func: Callable):
        """
        注册任务回调函数

        Args:
            name: 函数名称（用于配置文件中引用）
            func: 可调用函数
        """
        self.task_functions[name] = func
        print(f"✅ 注册任务函数: {name}")

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
            task_name: 任务名称（显示用）
            cron_expr: Cron 表达式（例如 "0 2 * * *" 每天凌晨2点）
            function_name: 回调函数名（需提前注册）
            kwargs: 传递给回调函数的参数

        Returns:
            成功返回 True，失败返回 False
        """
        if function_name not in self.task_functions:
            print(f"❌ 未注册的任务函数: {function_name}")
            return False

        func = self.task_functions[function_name]

        try:
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

            print(f"✅ 添加任务: {task_name} ({cron_expr})")
            return True

        except Exception as e:
            print(f"❌ 添加任务失败: {e}")
            return False

    def remove_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID

        Returns:
            成功返回 True
        """
        try:
            self.scheduler.remove_job(task_id)
            self._remove_task_config(task_id)
            print(f"✅ 删除任务: {task_id}")
            return True
        except JobLookupError:
            print(f"⚠️  任务不存在: {task_id}")
            return False
        except Exception as e:
            print(f"❌ 删除任务失败: {e}")
            return False

    def pause_task(self, task_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务 ID

        Returns:
            成功返回 True
        """
        try:
            self.scheduler.pause_job(task_id)
            print(f"⏸️  暂停任务: {task_id}")
            return True
        except JobLookupError:
            print(f"⚠️  任务不存在: {task_id}")
            return False
        except Exception as e:
            print(f"❌ 暂停任务失败: {e}")
            return False

    def resume_task(self, task_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务 ID

        Returns:
            成功返回 True
        """
        try:
            self.scheduler.resume_job(task_id)
            print(f"▶️  恢复任务: {task_id}")
            return True
        except JobLookupError:
            print(f"⚠️  任务不存在: {task_id}")
            return False
        except Exception as e:
            print(f"❌ 恢复任务失败: {e}")
            return False

    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        获取单个任务信息

        Args:
            task_id: 任务 ID

        Returns:
            任务信息字典，不存在返回 None
        """
        try:
            job = self.scheduler.get_job(task_id)
            if job is None:
                return None

            # next_run_time 只在调度器运行时可用
            next_run = None
            if self.scheduler.running and hasattr(job, 'next_run_time') and job.next_run_time:
                next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')

            return {
                'id': job.id,
                'name': job.name,
                'next_run': next_run,
                'trigger': str(job.trigger)
            }
        except Exception as e:
            print(f"❌ 获取任务失败: {e}")
            return None

    def get_all_tasks(self) -> List[Dict]:
        """
        获取所有任务

        Returns:
            任务列表
        """
        tasks = []
        for job in self.scheduler.get_jobs():
            # next_run_time 只在调度器运行时可用
            next_run = None
            if self.scheduler.running and hasattr(job, 'next_run_time') and job.next_run_time:
                next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')

            tasks.append({
                'id': job.id,
                'name': job.name,
                'next_run': next_run,
                'trigger': str(job.trigger)
            })
        return tasks

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("▶️  调度器已启动")
        else:
            print("⚠️  调度器已在运行")

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            print("⏸️  调度器已停止")
        else:
            print("⚠️  调度器未运行")

    def is_running(self) -> bool:
        """
        检查调度器是否运行

        Returns:
            运行中返回 True
        """
        return self.scheduler.running

    def load_tasks_from_config(self):
        """
        从配置文件加载任务

        用于调度器重启后恢复任务
        """
        if not self.tasks_file.exists():
            print("ℹ️  无任务配置文件")
            return

        try:
            tasks = json.loads(self.tasks_file.read_text(encoding='utf-8'))

            for task_id, task_config in tasks.items():
                self.add_task(
                    task_id=task_id,
                    task_name=task_config['name'],
                    cron_expr=task_config['cron'],
                    function_name=task_config['function'],
                    kwargs=task_config.get('kwargs', {})
                )

            print(f"✅ 加载 {len(tasks)} 个任务")

        except Exception as e:
            print(f"❌ 加载任务配置失败: {e}")

    def _save_task_config(
        self,
        task_id: str,
        task_name: str,
        cron_expr: str,
        function_name: str,
        kwargs: Optional[Dict]
    ):
        """
        保存任务配置到文件

        Args:
            task_id: 任务 ID
            task_name: 任务名称
            cron_expr: Cron 表达式
            function_name: 函数名
            kwargs: 参数
        """
        tasks = self._load_tasks_file()
        tasks[task_id] = {
            'name': task_name,
            'cron': cron_expr,
            'function': function_name,
            'kwargs': kwargs or {},
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            self.tasks_file.write_text(
                json.dumps(tasks, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"⚠️  保存任务配置失败: {e}")

    def _remove_task_config(self, task_id: str):
        """
        删除任务配置

        Args:
            task_id: 任务 ID
        """
        tasks = self._load_tasks_file()
        if task_id in tasks:
            del tasks[task_id]
            try:
                self.tasks_file.write_text(
                    json.dumps(tasks, indent=2, ensure_ascii=False),
                    encoding='utf-8'
                )
            except Exception as e:
                print(f"⚠️  删除任务配置失败: {e}")

    def _load_tasks_file(self) -> Dict:
        """
        加载任务配置文件

        Returns:
            任务配置字典
        """
        if self.tasks_file.exists():
            try:
                return json.loads(self.tasks_file.read_text(encoding='utf-8'))
            except Exception as e:
                print(f"⚠️  读取任务配置失败: {e}")
                return {}
        return {}

    def get_task_count(self) -> int:
        """
        获取任务数量

        Returns:
            任务数量
        """
        return len(self.scheduler.get_jobs())

    def execute_task_now(self, task_id: str) -> Dict:
        """
        立即执行任务（手动测试用）

        Args:
            task_id: 任务 ID

        Returns:
            任务执行结果字典
        """
        # 读取任务配置
        task_config = self._load_tasks_file().get(task_id)
        if not task_config:
            return {
                'status': 'failed',
                'error': '任务配置不存在'
            }

        function_name = task_config.get('function')
        kwargs = task_config.get('kwargs', {})

        # 检查函数是否注册
        if function_name not in self.task_functions:
            return {
                'status': 'failed',
                'error': f'任务函数未注册: {function_name}'
            }

        # 执行任务函数
        try:
            func = self.task_functions[function_name]
            result = func(**kwargs)
            return result
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
