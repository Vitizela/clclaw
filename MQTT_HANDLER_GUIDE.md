# MQTT 消息处理器指南

本文档介绍如何使用 MQTT 接收调度器通知，并提供 Telegram Bot 转发示例。

---

## 📋 目录

1. [概述](#概述)
2. [消息格式](#消息格式)
3. [Telegram Bot 设置](#telegram-bot-设置)
4. [运行消息处理器](#运行消息处理器)
5. [Systemd 服务配置](#systemd-服务配置)
6. [扩展指南](#扩展指南)
7. [故障排查](#故障排查)

---

## 概述

T66Y 归档系统通过 MQTT 发布调度器事件通知，您可以订阅这些消息并转发到各种平台：

```
调度器 → MQTT Broker → 消息处理器 → Telegram/Email/Slack/...
```

**提供的示例**：
- `python/tools/mqtt_to_telegram.py` - MQTT 到 Telegram Bot

**支持的事件类型**：
- `task_complete` - 任务完成
- `task_error` - 任务失败
- `new_posts_found` - 发现新帖

---

## 消息格式

### 1. 任务完成 (task_complete)

```json
{
  "event_type": "task_complete",
  "author_name": "同花顺心",
  "new_posts": 5,
  "skipped_posts": 120,
  "failed_posts": 0,
  "total_archived": 125,
  "total_forum": 130,
  "start_time": "2026-02-15 02:00:00",
  "end_time": "2026-02-15 02:03:45",
  "duration": 225.3,
  "status": "completed",
  "timestamp": "2026-02-15T02:03:45"
}
```

### 2. 任务失败 (task_error)

```json
{
  "event_type": "task_error",
  "task_name": "增量归档: 同花顺心",
  "error": "连接超时",
  "timestamp": "2026-02-15T02:00:15"
}
```

### 3. 发现新帖 (new_posts_found)

```json
{
  "event_type": "new_posts_found",
  "author_name": "同花顺心",
  "count": 5,
  "timestamp": "2026-02-15T02:01:30"
}
```

---

## Telegram Bot 设置

### 步骤 1: 创建 Telegram Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按提示设置机器人名称
4. 获取 **Bot Token**（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 步骤 2: 获取 Chat ID

1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息
3. 机器人会回复您的 **Chat ID**（数字格式）

### 步骤 3: 配置消息处理器

编辑 `python/tools/mqtt_to_telegram.py` 的 `CONFIG` 字典：

```python
CONFIG = {
    'mqtt': {
        'broker': 'localhost',  # MQTT Broker 地址
        'port': 1883,
        'topic': 't66y/scheduler/events',
        'client_id': 't66y-telegram-bridge'
    },
    'telegram': {
        'bot_token': '123456789:ABCdefGHIjklMNOpqrsTUVwxyz',  # ← 填入您的 Bot Token
        'chat_id': '123456789',  # ← 填入您的 Chat ID
        'enabled': True
    }
}
```

---

## 运行消息处理器

### 方式 1: 直接运行（前台）

```bash
# 1. 安装依赖
pip install python-telegram-bot==20.7 paho-mqtt==1.6.1

# 2. 运行
python python/tools/mqtt_to_telegram.py
```

**输出示例**：
```
============================================================
MQTT to Telegram Bridge
============================================================

2026-02-15 22:00:00 - INFO - ✅ MQTT 连接成功
2026-02-15 22:00:00 - INFO - 📡 订阅主题: t66y/scheduler/events
2026-02-15 22:00:00 - INFO - 桥接器正在运行...
```

按 `Ctrl+C` 停止。

---

### 方式 2: 后台运行（nohup）

```bash
# 启动
nohup python python/tools/mqtt_to_telegram.py > /dev/null 2>&1 &

# 查看进程
ps aux | grep mqtt_to_telegram

# 停止
kill <PID>
```

---

### 方式 3: 使用 screen/tmux

```bash
# screen 方式
screen -S mqtt-bridge
python python/tools/mqtt_to_telegram.py
# 按 Ctrl+A, D 分离会话

# 恢复会话
screen -r mqtt-bridge

# tmux 方式
tmux new -s mqtt-bridge
python python/tools/mqtt_to_telegram.py
# 按 Ctrl+B, D 分离会话

# 恢复会话
tmux attach -t mqtt-bridge
```

---

## Systemd 服务配置

创建系统服务，实现开机自启和自动重启。

### 步骤 1: 创建服务文件

创建 `/etc/systemd/system/t66y-mqtt-bridge.service`：

```ini
[Unit]
Description=T66Y MQTT to Telegram Bridge
After=network.target mosquitto.service

[Service]
Type=simple
User=ben
WorkingDirectory=/home/ben/gemini-work/gemini-t66y
ExecStart=/usr/bin/python3 /home/ben/gemini-work/gemini-t66y/python/tools/mqtt_to_telegram.py
Restart=always
RestartSec=10

# 日志
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 步骤 2: 启用服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable t66y-mqtt-bridge

# 启动服务
sudo systemctl start t66y-mqtt-bridge

# 查看状态
sudo systemctl status t66y-mqtt-bridge

# 查看日志
sudo journalctl -u t66y-mqtt-bridge -f
```

### 步骤 3: 管理服务

```bash
# 停止服务
sudo systemctl stop t66y-mqtt-bridge

# 重启服务
sudo systemctl restart t66y-mqtt-bridge

# 禁用开机自启
sudo systemctl disable t66y-mqtt-bridge

# 查看最近 100 行日志
sudo journalctl -u t66y-mqtt-bridge -n 100
```

---

## 扩展指南

### 1. 添加新的通知渠道

您可以基于 `mqtt_to_telegram.py` 创建其他通知渠道：

**Email 通知**：
```python
# mqtt_to_email.py
import smtplib
from email.mime.text import MIMEText

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'your@email.com'
    msg['To'] = 'recipient@email.com'

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('your@email.com', 'password')
        smtp.send_message(msg)
```

**Slack 通知**：
```python
# mqtt_to_slack.py
import requests

def send_slack(text):
    webhook_url = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    payload = {'text': text}
    requests.post(webhook_url, json=payload)
```

**企业微信通知**：
```python
# mqtt_to_wechat.py
import requests

def send_wechat(text):
    webhook_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY'
    payload = {
        'msgtype': 'text',
        'text': {'content': text}
    }
    requests.post(webhook_url, json=payload)
```

### 2. 消息过滤

只接收特定类型的消息：

```python
def on_message(self, client, userdata, msg):
    payload = json.loads(msg.payload.decode('utf-8'))

    # 只处理任务完成和失败消息
    if payload['event_type'] in ['task_complete', 'task_error']:
        text = self.format_message(payload)
        asyncio.run(self.send_telegram_message(text))
```

### 3. 消息聚合

每 5 分钟汇总一次消息：

```python
from collections import defaultdict
import time

class AggregatedBridge:
    def __init__(self):
        self.message_buffer = defaultdict(list)
        self.last_send_time = time.time()

    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode('utf-8'))
        self.message_buffer[payload['event_type']].append(payload)

        # 每 5 分钟发送一次
        if time.time() - self.last_send_time > 300:
            self.send_aggregated()
            self.message_buffer.clear()
            self.last_send_time = time.time()
```

---

## 故障排查

### 问题 1: MQTT 连接失败

**错误**: `❌ MQTT 连接失败: 5`

**原因**: Mosquitto 未运行

**解决**:
```bash
# 启动 Mosquitto
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# 验证
sudo systemctl status mosquitto
```

---

### 问题 2: Telegram 发送失败

**错误**: `TelegramError: Unauthorized`

**原因**: Bot Token 错误

**解决**:
1. 检查 Bot Token 是否正确
2. 确保 Token 没有多余空格
3. 重新从 @BotFather 获取 Token

---

### 问题 3: 收不到消息

**原因**: Chat ID 错误或未启动对话

**解决**:
1. 确认 Chat ID 正确
2. 在 Telegram 中给 Bot 发送 `/start`
3. 检查 Bot 是否被阻止

---

### 问题 4: 消息格式错乱

**原因**: JSON 解析失败

**解决**:
```python
# 添加调试日志
def on_message(self, client, userdata, msg):
    try:
        payload_str = msg.payload.decode('utf-8')
        print(f"收到原始消息: {payload_str}")  # 调试
        payload = json.loads(payload_str)
        # ...
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        print(f"原始数据: {msg.payload}")
```

---

### 问题 5: 服务崩溃

**查看崩溃日志**:
```bash
# 查看最近的错误
sudo journalctl -u t66y-mqtt-bridge --since "10 minutes ago" -p err

# 查看完整日志
sudo journalctl -u t66y-mqtt-bridge -n 200
```

**常见崩溃原因**:
1. Python 环境错误 → 检查服务文件中的 `ExecStart` 路径
2. 权限问题 → 确保 `User` 有权限访问项目目录
3. 依赖缺失 → 在服务文件中添加 `Environment="PATH=/path/to/venv/bin:$PATH"`

---

## 测试消息发送

创建测试脚本验证配置：

```python
# test_mqtt_publish.py
import paho.mqtt.client as mqtt
import json
from datetime import datetime

def test_publish():
    client = mqtt.Client()
    client.connect('localhost', 1883, 60)

    # 测试消息
    payload = {
        'event_type': 'task_complete',
        'author_name': '测试作者',
        'new_posts': 3,
        'skipped_posts': 10,
        'duration': 45.2,
        'timestamp': datetime.now().isoformat()
    }

    client.publish('t66y/scheduler/events', json.dumps(payload, ensure_ascii=False))
    print("✅ 测试消息已发送")
    client.disconnect()

if __name__ == '__main__':
    test_publish()
```

运行测试：
```bash
python test_mqtt_publish.py
```

如果 Telegram Bot 收到消息，说明配置成功！ 🎉

---

## 高级配置

### 1. MQTT 认证

如果您的 Mosquitto 启用了认证：

```python
CONFIG = {
    'mqtt': {
        'broker': 'localhost',
        'port': 1883,
        'username': 'mqtt_user',  # ← 添加用户名
        'password': 'mqtt_pass'   # ← 添加密码
    }
}
```

### 2. TLS/SSL 加密

使用加密连接：

```python
mqtt_config = self.config['mqtt']
self.mqtt_client.tls_set(
    ca_certs='/path/to/ca.crt',
    certfile='/path/to/client.crt',
    keyfile='/path/to/client.key'
)
self.mqtt_client.connect(mqtt_config['broker'], 8883)  # 使用 8883 端口
```

### 3. 消息持久化

保存消息到数据库：

```python
import sqlite3

def save_message(payload):
    conn = sqlite3.connect('mqtt_messages.db')
    conn.execute("""
        INSERT INTO messages (event_type, payload, timestamp)
        VALUES (?, ?, ?)
    """, (payload['event_type'], json.dumps(payload), payload['timestamp']))
    conn.commit()
    conn.close()
```

---

## 相关资源

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **MQTT 协议**: https://mqtt.org/
- **Mosquitto 文档**: https://mosquitto.org/documentation/
- **python-telegram-bot**: https://python-telegram-bot.readthedocs.io/

---

**祝您使用愉快！** 🚀
