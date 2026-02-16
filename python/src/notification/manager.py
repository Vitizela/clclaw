# python/src/notification/manager.py

from typing import List, Dict
from abc import ABC, abstractmethod


class NotifierBase(ABC):
    """
    通知器抽象基类

    所有通知器必须实现此接口
    """

    @abstractmethod
    def should_send(self, level: str) -> bool:
        """
        判断是否应该发送此级别的消息

        Args:
            level: 消息级别（DEBUG/INFO/WARNING/ERROR）

        Returns:
            是否应该发送
        """
        pass

    @abstractmethod
    def send(self, message: str, level: str = 'INFO', **kwargs):
        """
        发送消息

        Args:
            message: 消息内容
            level: 消息级别
            **kwargs: 额外参数
        """
        pass

    @abstractmethod
    def send_task_completion(self, result: Dict):
        """
        发送任务完成消息

        Args:
            result: 任务结果字典
        """
        pass

    @abstractmethod
    def send_task_error(self, task_name: str, error: str):
        """
        发送任务失败消息

        Args:
            task_name: 任务名称
            error: 错误信息
        """
        pass

    @abstractmethod
    def send_new_posts_found(self, author_name: str, count: int):
        """
        发送发现新帖消息

        Args:
            author_name: 作者名称
            count: 新帖数量
        """
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
        """初始化通知管理器"""
        self.notifiers: List[NotifierBase] = []

    def add_notifier(self, notifier: NotifierBase):
        """
        添加通知器

        Args:
            notifier: 通知器实例
        """
        if not isinstance(notifier, NotifierBase):
            raise TypeError(f"通知器必须继承 NotifierBase，收到: {type(notifier)}")
        self.notifiers.append(notifier)

    def remove_notifier(self, notifier: NotifierBase):
        """
        移除通知器

        Args:
            notifier: 通知器实例
        """
        if notifier in self.notifiers:
            self.notifiers.remove(notifier)

    def clear_notifiers(self):
        """清空所有通知器"""
        self.notifiers.clear()

    def send(self, message: str, level: str = 'INFO', **kwargs):
        """
        发送消息到所有通知器

        Args:
            message: 消息内容
            level: 消息级别
            **kwargs: 额外参数
        """
        for notifier in self.notifiers:
            try:
                if notifier.should_send(level):
                    notifier.send(message, level, **kwargs)
            except Exception as e:
                # 通知器发送失败不应影响主流程
                print(f"⚠️  通知器发送失败: {type(notifier).__name__} - {e}")

    def send_task_completion(self, result: Dict):
        """
        发送任务完成消息到所有通知器

        Args:
            result: 任务结果字典
                - task_name: 任务名称
                - author_name: 作者名称
                - new_posts: 新增帖子数
                - skipped_posts: 跳过帖子数
                - failed_posts: 失败帖子数
                - status: 任务状态
                - start_time: 开始时间
                - end_time: 结束时间
                - duration: 持续时间
        """
        for notifier in self.notifiers:
            try:
                notifier.send_task_completion(result)
            except Exception as e:
                print(f"⚠️  通知器发送失败: {type(notifier).__name__} - {e}")

    def send_task_error(self, task_name: str, error: str):
        """
        发送任务失败消息到所有通知器

        Args:
            task_name: 任务名称
            error: 错误信息
        """
        for notifier in self.notifiers:
            try:
                notifier.send_task_error(task_name, error)
            except Exception as e:
                print(f"⚠️  通知器发送失败: {type(notifier).__name__} - {e}")

    def send_new_posts_found(self, author_name: str, count: int):
        """
        发送发现新帖消息到所有通知器

        Args:
            author_name: 作者名称
            count: 新帖数量
        """
        for notifier in self.notifiers:
            try:
                notifier.send_new_posts_found(author_name, count)
            except Exception as e:
                print(f"⚠️  通知器发送失败: {type(notifier).__name__} - {e}")

    def get_notifier_count(self) -> int:
        """
        获取通知器数量

        Returns:
            通知器数量
        """
        return len(self.notifiers)
