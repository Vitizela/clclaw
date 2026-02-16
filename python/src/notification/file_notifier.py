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
    - 支持按日期分割日志（可选）
    """

    def __init__(self, config: dict):
        """
        初始化文件通知器

        Args:
            config: 配置字典
                - notification.file.enabled: 是否启用
                - notification.file.log_dir: 日志目录
                - notification.file.log_file: 日志文件名
        """
        file_config = config.get('notification', {}).get('file', {})
        self.enabled = file_config.get('enabled', True)

        # 日志文件路径
        log_dir = Path(file_config.get('log_dir', 'logs'))
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = file_config.get('log_file', 'scheduler.log')
        self.log_path = log_dir / log_file

    def should_send(self, level: str) -> bool:
        """
        判断是否应该发送

        Args:
            level: 消息级别

        Returns:
            是否应该发送
        """
        return self.enabled

    def send(self, message: str, level: str = 'INFO', **kwargs):
        """
        发送消息

        Args:
            message: 消息内容
            level: 消息级别
            **kwargs: 额外参数
        """
        if not self.should_send(level):
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}\n"

        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"⚠️  写入日志文件失败: {e}")

    def send_task_completion(self, result: Dict):
        """
        发送任务完成消息

        Args:
            result: 任务结果字典
        """
        if not self.enabled:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        author = result.get('author_name', 'Unknown')
        new_posts = result.get('new_posts', 0)
        skipped = result.get('skipped_posts', 0)
        failed = result.get('failed_posts', 0)
        status = result.get('status', 'completed')
        duration = result.get('duration', 0)

        if status == 'completed':
            log_line = (
                f"[{timestamp}] [TASK] COMPLETED - {author} - "
                f"新增 {new_posts} 篇，跳过 {skipped} 篇，失败 {failed} 篇，"
                f"耗时 {duration:.1f}s\n"
            )
        else:
            error = result.get('error', 'Unknown error')
            log_line = f"[{timestamp}] [TASK] FAILED - {author} - {error}\n"

        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"⚠️  写入日志文件失败: {e}")

    def send_task_error(self, task_name: str, error: str):
        """
        发送任务失败消息

        Args:
            task_name: 任务名称
            error: 错误信息
        """
        if not self.enabled:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [ERROR] {task_name} - {error}\n"

        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"⚠️  写入日志文件失败: {e}")

    def send_new_posts_found(self, author_name: str, count: int):
        """
        发送发现新帖消息

        Args:
            author_name: 作者名称
            count: 新帖数量
        """
        if not self.enabled:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [NEW] {author_name} - {count} 篇新帖\n"

        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"⚠️  写入日志文件失败: {e}")

    def get_log_path(self) -> Path:
        """
        获取日志文件路径

        Returns:
            日志文件路径
        """
        return self.log_path
