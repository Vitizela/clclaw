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
                - notification.console.enabled: 是否启用
                - notification.console.min_level: 最低输出级别
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
        """
        判断是否应该发送

        Args:
            level: 消息级别

        Returns:
            是否应该发送
        """
        if not self.enabled:
            return False

        level_weight = self.level_weights.get(level, 1)
        min_weight = self.level_weights.get(self.min_level, 1)

        return level_weight >= min_weight

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
        icon = self._get_icon(level)
        print(f"[{timestamp}] {icon} {message}")

    def send_task_completion(self, result: Dict):
        """
        发送任务完成消息

        Args:
            result: 任务结果字典
        """
        if not self.enabled:
            return

        author = result.get('author_name', 'Unknown')
        new_posts = result.get('new_posts', 0)
        skipped = result.get('skipped_posts', 0)
        failed = result.get('failed_posts', 0)
        status = result.get('status', 'completed')
        duration = result.get('duration', 0)

        if status == 'completed':
            if new_posts > 0:
                print(f"✅ 任务完成: {author} - 新增 {new_posts} 篇，跳过 {skipped} 篇，耗时 {duration:.1f}s")
            else:
                print(f"✅ 任务完成: {author} - 无新帖，跳过 {skipped} 篇，耗时 {duration:.1f}s")
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ 任务失败: {author} - {error}")

    def send_task_error(self, task_name: str, error: str):
        """
        发送任务失败消息

        Args:
            task_name: 任务名称
            error: 错误信息
        """
        if not self.enabled:
            return

        print(f"❌ 任务失败: {task_name} - {error}")

    def send_new_posts_found(self, author_name: str, count: int):
        """
        发送发现新帖消息

        Args:
            author_name: 作者名称
            count: 新帖数量
        """
        if not self.enabled:
            return

        if count > 0:
            print(f"🔔 发现新帖: {author_name} - {count} 篇")
        else:
            print(f"ℹ️  无新帖: {author_name}")

    def _get_icon(self, level: str) -> str:
        """
        获取级别图标

        Args:
            level: 消息级别

        Returns:
            图标字符
        """
        icons = {
            'DEBUG': '🐛',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌'
        }
        return icons.get(level, 'ℹ️')
