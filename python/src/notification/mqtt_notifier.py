# python/src/notification/mqtt_notifier.py

import paho.mqtt.client as mqtt
import json
from typing import Dict
from datetime import datetime
import time
from .manager import NotifierBase


class MQTTNotifier(NotifierBase):
    """
    MQTT 通知器

    职责：
    - 连接 MQTT Broker
    - 发布结构化消息（JSON）
    - 自动重连和错误处理

    依赖：
    - paho-mqtt
    """

    def __init__(self, config: dict):
        """
        初始化 MQTT 通知器

        Args:
            config: 配置字典
                - notification.mqtt.enabled: 是否启用
                - notification.mqtt.broker: Broker 地址
                - notification.mqtt.port: Broker 端口
                - notification.mqtt.topic: 发布主题
                - notification.mqtt.qos: QoS 级别（0/1/2）
                - notification.mqtt.username: 用户名（可选）
                - notification.mqtt.password: 密码（可选）
                - notification.mqtt.client_id: 客户端 ID
                - notification.mqtt.publish_on: 发布事件配置
        """
        mqtt_config = config.get('notification', {}).get('mqtt', {})

        self.enabled = mqtt_config.get('enabled', False)
        if not self.enabled:
            return

        self.broker = mqtt_config.get('broker', 'localhost')
        self.port = mqtt_config.get('port', 1883)
        self.topic = mqtt_config.get('topic', 't66y/scheduler/events')
        self.qos = mqtt_config.get('qos', 1)
        self.publish_on = mqtt_config.get('publish_on', {})

        # 初始化客户端
        client_id = mqtt_config.get('client_id', 't66y-archiver')
        self.client = mqtt.Client(client_id=client_id)

        # 设置认证（如果配置）
        username = mqtt_config.get('username', '')
        password = mqtt_config.get('password', '')
        if username:
            self.client.username_pw_set(username, password)

        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # 连接 Broker
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()  # 后台线程
            print(f"🔌 MQTT 连接中: {self.broker}:{self.port}")
        except Exception as e:
            print(f"❌ MQTT 连接失败: {e}")
            self.enabled = False

    def should_send(self, level: str) -> bool:
        """
        判断是否应该发送（暂时总是返回 True）

        Args:
            level: 消息级别

        Returns:
            是否应该发送
        """
        return self.enabled

    def send(self, message: str, level: str = 'INFO', **kwargs):
        """
        发送纯文本消息（包装为 JSON）

        Args:
            message: 消息内容
            level: 消息级别
            **kwargs: 额外参数
        """
        if not self.enabled:
            return

        payload = {
            "source": "t66y-archiver",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": "message",
            "level": level,
            "data": {"message": message}
        }

        self._publish(payload)

    def send_task_completion(self, result: Dict):
        """
        发送任务完成消息

        Args:
            result: 任务结果字典
        """
        if not self.enabled:
            return

        # 检查是否应该发布此事件
        if not self.publish_on.get('task_complete', True):
            return

        message = {
            "source": "t66y-archiver",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": "task_completed",
            "level": "INFO",
            "data": {
                "task_id": result.get('task_id'),
                "task_name": result.get('task_name'),
                "author_name": result.get('author_name', 'Unknown'),
                "start_time": result.get('start_time'),
                "end_time": result.get('end_time'),
                "duration": result.get('duration'),
                "status": result.get('status', 'completed'),
                "new_posts": result.get('new_posts', 0),
                "skipped_posts": result.get('skipped_posts', 0),
                "failed_posts": result.get('failed_posts', 0),
                "total_archived": result.get('total_archived', 0),
                "total_forum": result.get('total_forum', 0),
                "completion_rate": result.get('completion_rate', 0)
            }
        }

        self._publish(message)

    def send_task_error(self, task_name: str, error: str):
        """
        发送任务失败消息

        Args:
            task_name: 任务名称
            error: 错误信息
        """
        if not self.enabled:
            return

        # 检查是否应该发布此事件
        if not self.publish_on.get('task_error', True):
            return

        message = {
            "source": "t66y-archiver",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": "task_failed",
            "level": "ERROR",
            "data": {
                "task_name": task_name,
                "error": error
            }
        }

        self._publish(message)

    def send_new_posts_found(self, author_name: str, count: int):
        """
        发送发现新帖消息

        Args:
            author_name: 作者名称
            count: 新帖数量
        """
        if not self.enabled:
            return

        # 检查是否应该发布此事件
        if not self.publish_on.get('new_posts_found', True):
            return

        message = {
            "source": "t66y-archiver",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": "new_posts_found",
            "level": "INFO",
            "data": {
                "author_name": author_name,
                "new_count": count
            }
        }

        self._publish(message)

    def test_connection(self) -> bool:
        """
        测试 MQTT 连接

        Returns:
            连接是否成功
        """
        if not self.enabled:
            return False

        test_message = {
            "source": "t66y-archiver",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": "connection_test",
            "level": "INFO",
            "data": {"message": "MQTT 连接测试"}
        }

        try:
            self._publish(test_message)
            return True
        except Exception:
            return False

    def _publish(self, message: dict, max_retries: int = 3):
        """
        发布消息到 MQTT（带重试）

        Args:
            message: 消息字典
            max_retries: 最大重试次数
        """
        if not self.enabled:
            return

        payload = json.dumps(message, ensure_ascii=False)

        for attempt in range(max_retries):
            try:
                result = self.client.publish(
                    self.topic,
                    payload,
                    qos=self.qos
                )

                # 等待发布完成
                result.wait_for_publish(timeout=5)

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    return  # 成功

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待 2 秒后重试
                else:
                    # 最后一次失败，记录日志
                    print(f"❌ MQTT 发送失败（{max_retries} 次）: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        """
        连接成功回调

        Args:
            client: MQTT 客户端
            userdata: 用户数据
            flags: 连接标志
            rc: 返回码
        """
        if rc == 0:
            print(f"✅ MQTT 连接成功: {self.broker}:{self.port}")
        else:
            print(f"❌ MQTT 连接失败，返回码: {rc}")
            self.enabled = False

    def _on_disconnect(self, client, userdata, rc):
        """
        断开连接回调

        Args:
            client: MQTT 客户端
            userdata: 用户数据
            rc: 返回码
        """
        if rc != 0:
            print(f"⚠️  MQTT 意外断开，尝试重连...")

    def close(self):
        """关闭连接"""
        if self.enabled:
            self.client.loop_stop()
            self.client.disconnect()
            print("🔌 MQTT 连接已关闭")
