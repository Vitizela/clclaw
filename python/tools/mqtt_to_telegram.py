#!/usr/bin/env python3
"""MQTT 到 Telegram 消息转发器

功能：
- 订阅 MQTT 主题接收调度器通知
- 解析消息并格式化
- 通过 Telegram Bot 发送通知

依赖：
  pip install python-telegram-bot==20.7
  pip install paho-mqtt==1.6.1

使用方法：
  1. 配置 Telegram Bot Token 和 Chat ID
  2. 运行: python tools/mqtt_to_telegram.py
  3. 可选：使用 systemd 设置为后台服务
"""

import sys
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict

# MQTT 客户端
import paho.mqtt.client as mqtt

# Telegram Bot (需要安装: pip install python-telegram-bot)
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️  警告: python-telegram-bot 未安装")
    print("   安装: pip install python-telegram-bot==20.7")


# 配置
CONFIG = {
    # MQTT 配置
    'mqtt': {
        'broker': 'localhost',
        'port': 1883,
        'topic': 't66y/scheduler/events',
        'client_id': 't66y-telegram-bridge',
        'username': None,  # 可选
        'password': None   # 可选
    },

    # Telegram 配置
    'telegram': {
        'bot_token': 'YOUR_BOT_TOKEN_HERE',  # 从 @BotFather 获取
        'chat_id': 'YOUR_CHAT_ID_HERE',      # 从 @userinfobot 获取
        'enabled': True
    },

    # 日志配置
    'log': {
        'level': 'INFO',
        'file': 'logs/mqtt_telegram_bridge.log'
    }
}


class MQTTToTelegramBridge:
    """MQTT 到 Telegram 桥接器"""

    def __init__(self, config: Dict):
        """
        初始化桥接器

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = self._setup_logger()
        self.mqtt_client = None
        self.telegram_bot = None

        if TELEGRAM_AVAILABLE and config['telegram']['enabled']:
            self.telegram_bot = Bot(token=config['telegram']['bot_token'])

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        logger = logging.getLogger('mqtt_telegram_bridge')
        logger.setLevel(self.config['log']['level'])

        # 文件处理器
        fh = logging.FileHandler(self.config['log']['file'], encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def format_message(self, payload: Dict) -> str:
        """
        格式化消息为 Telegram 格式

        Args:
            payload: MQTT 消息负载

        Returns:
            格式化后的文本
        """
        event_type = payload.get('event_type', 'unknown')

        if event_type == 'task_complete':
            # 任务完成通知
            author = payload.get('author_name', '未知作者')
            new_posts = payload.get('new_posts', 0)
            skipped = payload.get('skipped_posts', 0)
            duration = payload.get('duration', 0)

            message = f"🎉 任务完成\n\n"
            message += f"作者: {author}\n"
            message += f"新增归档: {new_posts} 篇\n"
            message += f"跳过: {skipped} 篇\n"
            message += f"耗时: {duration:.1f} 秒\n"
            message += f"时间: {payload.get('timestamp', '')}"

        elif event_type == 'task_error':
            # 任务失败通知
            task_name = payload.get('task_name', '未知任务')
            error = payload.get('error', '未知错误')

            message = f"❌ 任务失败\n\n"
            message += f"任务: {task_name}\n"
            message += f"错误: {error}\n"
            message += f"时间: {payload.get('timestamp', '')}"

        elif event_type == 'new_posts_found':
            # 发现新帖通知
            author = payload.get('author_name', '未知作者')
            count = payload.get('count', 0)

            message = f"🔔 发现新帖\n\n"
            message += f"作者: {author}\n"
            message += f"新帖数: {count} 篇\n"
            message += f"时间: {payload.get('timestamp', '')}"

        else:
            # 通用消息
            message = f"📨 {event_type}\n\n"
            message += f"内容: {payload.get('message', '')}\n"
            message += f"时间: {payload.get('timestamp', '')}"

        return message

    async def send_telegram_message(self, text: str):
        """
        发送 Telegram 消息

        Args:
            text: 消息文本
        """
        if not TELEGRAM_AVAILABLE:
            self.logger.warning("Telegram 库未安装，跳过发送")
            return

        if not self.config['telegram']['enabled']:
            self.logger.info("Telegram 通知已禁用，跳过发送")
            return

        try:
            chat_id = self.config['telegram']['chat_id']
            await self.telegram_bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='HTML'
            )
            self.logger.info(f"Telegram 消息已发送到 {chat_id}")

        except TelegramError as e:
            self.logger.error(f"Telegram 发送失败: {e}")
        except Exception as e:
            self.logger.error(f"发送消息时出错: {e}")

    def on_connect(self, client, userdata, flags, rc):
        """MQTT 连接回调"""
        if rc == 0:
            self.logger.info("✅ MQTT 连接成功")
            topic = self.config['mqtt']['topic']
            client.subscribe(topic)
            self.logger.info(f"📡 订阅主题: {topic}")
        else:
            self.logger.error(f"❌ MQTT 连接失败: {rc}")

    def on_message(self, client, userdata, msg):
        """MQTT 消息回调"""
        try:
            # 解析 JSON 消息
            payload = json.loads(msg.payload.decode('utf-8'))
            self.logger.info(f"收到消息: {payload.get('event_type', 'unknown')}")

            # 格式化消息
            text = self.format_message(payload)

            # 发送到 Telegram（异步）
            asyncio.run(self.send_telegram_message(text))

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析失败: {e}")
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")

    def on_disconnect(self, client, userdata, rc):
        """MQTT 断开连接回调"""
        if rc != 0:
            self.logger.warning(f"⚠️  MQTT 意外断开: {rc}")
        else:
            self.logger.info("MQTT 已断开")

    def run(self):
        """运行桥接器"""
        self.logger.info("=" * 60)
        self.logger.info("MQTT to Telegram Bridge 启动")
        self.logger.info("=" * 60)

        # 验证配置
        if not TELEGRAM_AVAILABLE:
            self.logger.error("❌ Telegram 库未安装，无法启动")
            sys.exit(1)

        if self.config['telegram']['bot_token'] == 'YOUR_BOT_TOKEN_HERE':
            self.logger.error("❌ 请配置 Telegram Bot Token")
            sys.exit(1)

        if self.config['telegram']['chat_id'] == 'YOUR_CHAT_ID_HERE':
            self.logger.error("❌ 请配置 Telegram Chat ID")
            sys.exit(1)

        # 创建 MQTT 客户端
        mqtt_config = self.config['mqtt']
        self.mqtt_client = mqtt.Client(client_id=mqtt_config['client_id'])

        # 设置回调
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect

        # 设置认证（如果需要）
        if mqtt_config.get('username'):
            self.mqtt_client.username_pw_set(
                mqtt_config['username'],
                mqtt_config.get('password')
            )

        # 连接到 MQTT Broker
        try:
            self.logger.info(f"连接到 MQTT Broker: {mqtt_config['broker']}:{mqtt_config['port']}")
            self.mqtt_client.connect(
                mqtt_config['broker'],
                mqtt_config['port'],
                keepalive=60
            )

            # 启动循环
            self.logger.info("桥接器正在运行...")
            self.mqtt_client.loop_forever()

        except KeyboardInterrupt:
            self.logger.info("\n收到中断信号，正在停止...")
            self.mqtt_client.disconnect()
            self.logger.info("桥接器已停止")

        except Exception as e:
            self.logger.error(f"运行时错误: {e}")
            sys.exit(1)


def main():
    """主函数"""
    print("=" * 60)
    print("MQTT to Telegram Bridge")
    print("=" * 60)
    print()

    # 检查配置
    if not TELEGRAM_AVAILABLE:
        print("❌ 缺少依赖: python-telegram-bot")
        print("   安装: pip install python-telegram-bot==20.7")
        sys.exit(1)

    # 显示配置说明
    print("配置说明:")
    print("  1. 获取 Bot Token: https://t.me/BotFather")
    print("  2. 获取 Chat ID: https://t.me/userinfobot")
    print("  3. 修改脚本中的 CONFIG 字典")
    print()

    if CONFIG['telegram']['bot_token'] == 'YOUR_BOT_TOKEN_HERE':
        print("⚠️  请先配置 Telegram Bot Token")
        sys.exit(1)

    # 创建并运行桥接器
    bridge = MQTTToTelegramBridge(CONFIG)
    bridge.run()


if __name__ == '__main__':
    main()
