# Phase 5 用户指南：定时任务与通知

本指南介绍如何使用 T66Y 归档系统的定时任务功能（Phase 5）。

---

## 📋 目录

1. [功能概述](#功能概述)
2. [快速开始](#快速开始)
3. [调度器菜单](#调度器菜单)
4. [Cron 表达式](#cron-表达式)
5. [通知配置](#通知配置)
6. [后台运行](#后台运行)
7. [常见问题](#常见问题)

---

## 功能概述

Phase 5 提供以下功能：

### ✅ 定时任务
- **自动归档**: 按 Cron 表达式定时归档作者新帖
- **增量归档**: 只下载新帖，不重复归档
- **任务管理**: 添加/删除/查看定时任务
- **任务持久化**: 重启后任务配置保留

### ✅ 多渠道通知
- **控制台通知**: 实时查看任务执行状态
- **文件日志**: 保存到 `logs/scheduler.log`
- **MQTT 通知**: 发送到 MQTT Broker，可转发到 Telegram/Email

### ✅ 灵活调度
- **Cron 表达式**: 支持标准 Cron 语法
- **手动执行**: 测试任务配置
- **调度器控制**: 启动/停止调度器

---

## 快速开始

### 步骤 1: 进入定时任务菜单

```bash
python python/main.py
```

选择：**⏰ 定时任务（Phase 5）**

### 步骤 2: 添加任务

1. 选择：**2. 添加新任务**
2. 从列表中选择作者
3. 输入 Cron 表达式（例如：`0 2 * * *` 表示每天凌晨 2 点）
4. 可选：设置最大扫描页数（留空表示全部）
5. 确认添加

### 步骤 3: 启动调度器

选择：**4. 启动调度器**

调度器状态会显示为 **🟢 运行中**

### 步骤 4: 验证任务

选择：**5. 执行任务（手动测试）**

手动运行任务，查看执行结果和通知。

---

## 调度器菜单

进入定时任务菜单后，您会看到：

```
============================================================
调度器管理
============================================================

调度器状态: 🟢 运行中
通知渠道: 控制台, 文件(scheduler.log)

当前任务列表 (共 2 个):
------------------------------------------------------------
ID                   任务名称              下次运行
------------------------------------------------------------
incremental_同花顺..  增量归档: 同花顺心     2026-02-16 02:00:00
incremental_cyrus..  增量归档: cyruscc      2026-02-16 10:00:00

操作选项:
  1. 查看任务详情
  2. 添加新任务
  3. 删除任务
  4. 停止调度器
  5. 执行任务（手动测试）
  6. 配置 MQTT 通知
  0. 返回主菜单

请选择操作 [0-6]:
```

### 菜单选项说明

| 选项 | 功能 | 说明 |
|------|------|------|
| **1** | 查看任务详情 | 显示任务 ID、Cron 表达式、参数 |
| **2** | 添加新任务 | 选择作者，设置 Cron 表达式 |
| **3** | 删除任务 | 从列表中选择要删除的任务 |
| **4** | 启动/停止调度器 | 切换调度器运行状态 |
| **5** | 执行任务（手动测试）| 立即执行任务，用于测试配置 |
| **6** | 配置 MQTT 通知 | 设置 MQTT Broker 连接信息 |
| **0** | 返回主菜单 | 返回主菜单（调度器继续运行）|

---

## Cron 表达式

Cron 表达式用于定义任务执行时间，格式为：

```
分 时 日 月 周
```

### 字段说明

| 字段 | 范围 | 特殊字符 |
|------|------|----------|
| **分** | 0-59 | `*` `,` `-` `/` |
| **时** | 0-23 | `*` `,` `-` `/` |
| **日** | 1-31 | `*` `,` `-` `/` |
| **月** | 1-12 | `*` `,` `-` `/` |
| **周** | 0-6 (0=周日) | `*` `,` `-` `/` |

### 常用示例

| Cron 表达式 | 说明 | 执行时间 |
|-------------|------|----------|
| `0 2 * * *` | 每天凌晨 2 点 | 02:00:00 |
| `0 */6 * * *` | 每 6 小时 | 00:00, 06:00, 12:00, 18:00 |
| `30 8 * * 1-5` | 工作日早上 8:30 | 周一到周五 08:30:00 |
| `0 0 * * 0` | 每周日午夜 | 周日 00:00:00 |
| `0 10 1 * *` | 每月 1 号上午 10 点 | 每月 1 日 10:00:00 |
| `*/15 * * * *` | 每 15 分钟 | :00, :15, :30, :45 |

### 特殊字符

- **`*`**: 匹配所有值
- **`,`**: 列表（例如：`1,3,5` 表示 1、3、5）
- **`-`**: 范围（例如：`1-5` 表示 1 到 5）
- **`/`**: 步长（例如：`*/5` 表示每 5 个单位）

### 在线工具

验证 Cron 表达式：https://crontab.guru/

---

## 通知配置

### 1. 控制台通知（默认启用）

实时显示任务执行状态：

```
[2026-02-16 02:00:15] ✅ 任务完成: 增量归档: 同花顺心
   新增归档: 3 篇
   跳过: 120 篇
   耗时: 45.2 秒
```

### 2. 文件日志（默认启用）

保存到 `logs/scheduler.log`：

```bash
# 查看最新日志
tail -f logs/scheduler.log

# 查看最近 50 行
tail -n 50 logs/scheduler.log
```

### 3. MQTT 通知（需配置）

#### 步骤 1: 安装 Mosquitto

```bash
# Ubuntu/Debian
sudo apt install mosquitto mosquitto-clients

# 启动服务
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

#### 步骤 2: 启用 MQTT 通知

1. 进入定时任务菜单
2. 选择：**6. 配置 MQTT 通知**
3. 选择：**1. 启用/禁用 MQTT**
4. 重启菜单以应用更改

#### 步骤 3: 验证

```bash
# 订阅 MQTT 主题
mosquitto_sub -h localhost -t "t66y/scheduler/events"
```

运行任务后，您应该能看到 JSON 格式的消息。

#### 步骤 4: 转发到 Telegram（可选）

参见 [MQTT_HANDLER_GUIDE.md](MQTT_HANDLER_GUIDE.md) 了解如何将通知转发到 Telegram Bot。

---

## 后台运行

调度器需要程序持续运行才能执行任务。以下是三种运行方式：

### 方式 1: screen（推荐）

```bash
# 创建后台会话
screen -S t66y-scheduler

# 运行程序
python python/main.py
# 进入定时任务菜单 → 添加任务 → 启动调度器

# 分离会话（按键）
Ctrl+A, 然后按 D

# 现在可以关闭终端了，调度器继续在后台运行 ✅

# 恢复会话
screen -r t66y-scheduler

# 停止
screen -X -S t66y-scheduler quit
```

### 方式 2: tmux

```bash
# 创建后台会话
tmux new -s t66y-scheduler

# 运行程序
python python/main.py
# 进入定时任务菜单 → 添加任务 → 启动调度器

# 分离会话（按键）
Ctrl+B, 然后按 D

# 恢复会话
tmux attach -t t66y-scheduler
```

### 方式 3: nohup

```bash
# 启动（需要修改为非交互模式）
nohup python python/main.py > /dev/null 2>&1 &

# 查看进程
ps aux | grep "python.*main.py"

# 停止
kill <PID>
```

⚠️ **注意**: nohup 方式需要程序支持非交互模式，目前 main.py 是交互式菜单，建议使用 screen 或 tmux。

---

## 常见问题

### Q1: 关闭程序后任务还会执行吗？

**A**: 不会。调度器运行在 Python 进程中，关闭程序后调度器停止。

**解决**: 使用 **screen** 或 **tmux** 让程序在后台持续运行。

---

### Q2: 如何查看任务执行历史？

**A**: 查看日志文件：

```bash
# 查看最近 100 行
tail -n 100 logs/scheduler.log

# 实时查看
tail -f logs/scheduler.log

# 搜索特定作者
grep "同花顺心" logs/scheduler.log
```

---

### Q3: 任务执行失败怎么办？

**A**:
1. 查看日志了解错误原因
2. 使用 **5. 执行任务（手动测试）** 调试
3. 检查网络连接和论坛可访问性
4. 确认数据库中作者信息正确

---

### Q4: 如何修改已有任务？

**A**: 目前不支持直接修改，需要：
1. 删除旧任务（选项 3）
2. 添加新任务（选项 2）

---

### Q5: Cron 表达式验证失败

**A**:
- 确保格式为 5 个字段：`分 时 日 月 周`
- 使用在线工具验证：https://crontab.guru/
- 常见错误：
  - ❌ `0 2 * *` (缺少周字段)
  - ❌ `2 0 * * *` (小时和分钟顺序错误)
  - ✅ `0 2 * * *` (正确)

---

### Q6: MQTT 连接失败

**A**:
1. 检查 Mosquitto 是否运行：`sudo systemctl status mosquitto`
2. 测试连接：`mosquitto_pub -h localhost -t "test" -m "hello"`
3. 查看端口：`sudo netstat -tlnp | grep 1883`

---

### Q7: 调度器占用资源过高

**A**:
- 调度器本身非常轻量（< 10MB 内存）
- 资源占用主要来自归档任务（Playwright）
- 建议：
  - 避免任务过于频繁（间隔至少 1 小时）
  - 限制扫描页数（`max_pages` 参数）
  - 错开任务执行时间

---

### Q8: 如何备份任务配置？

**A**: 任务配置保存在 `python/data/scheduler_tasks.json`：

```bash
# 备份
cp python/data/scheduler_tasks.json python/data/scheduler_tasks.json.backup

# 恢复
cp python/data/scheduler_tasks.json.backup python/data/scheduler_tasks.json
```

---

### Q9: 多个作者同时执行会冲突吗？

**A**: 不会冲突。调度器按任务顺序串行执行，确保数据一致性。

---

### Q10: 如何查看下次执行时间？

**A**:
1. 进入定时任务菜单
2. 任务列表会显示"下次运行"时间
3. 或选择 **1. 查看任务详情**

---

## 最佳实践

### 1. 任务时间安排

- **凌晨时段**: 适合大量归档（网络流量低）
- **工作时间**: 避免影响正常使用
- **错开时间**: 多个任务间隔至少 1 小时

**推荐配置**：
```
作者 A: 0 2 * * *   (凌晨 2 点)
作者 B: 0 3 * * *   (凌晨 3 点)
作者 C: 0 4 * * *   (凌晨 4 点)
```

### 2. 扫描页数

- **活跃作者**: max_pages=3（足够捕获新帖）
- **不活跃作者**: max_pages=1（减少资源占用）
- **首次归档**: 不限制页数（全量归档）

### 3. 监控与维护

- **每周检查日志**: `tail -n 500 logs/scheduler.log`
- **定期清理日志**: 保留最近 30 天
- **备份任务配置**: 每月备份 `scheduler_tasks.json`

### 4. 通知策略

- **控制台 + 文件**: 开发调试
- **文件**: 生产环境
- **MQTT → Telegram**: 移动通知

---

## 进阶用法

### 1. 自定义 Cron 任务

结合系统 cron 实现更灵活的调度：

```bash
# 编辑 crontab
crontab -e

# 添加：每天凌晨 2 点执行一键归档脚本
0 2 * * * cd /home/ben/gemini-work/gemini-t66y && python python/quick_archive.py
```

### 2. 任务执行脚本

创建 `python/quick_archive.py`：

```python
#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config.manager import ConfigManager
from scheduler.incremental_archiver import IncrementalArchiver

config = ConfigManager().load()
archiver = IncrementalArchiver(config)

async def main():
    result = await archiver.archive_author_incremental(
        author_name="同花顺心",
        max_pages=3
    )
    print(f"完成: {result['new_posts']} 篇新帖")

if __name__ == '__main__':
    asyncio.run(main())
```

### 3. 批量任务

创建多作者批量归档：

```python
authors = ["同花顺心", "cyruscc", "其他作者"]

for author in authors:
    result = await archiver.archive_author_incremental(
        author_name=author,
        max_pages=2
    )
    print(f"{author}: {result['new_posts']} 篇")
```

---

## 相关文档

- [MQTT_HANDLER_GUIDE.md](MQTT_HANDLER_GUIDE.md) - MQTT 消息处理器指南
- [PHASE5_IMPLEMENTATION_PLAN.md](PHASE5_IMPLEMENTATION_PLAN.md) - 技术实现细节
- [PHASE5_COMPLETION_REPORT.md](PHASE5_COMPLETION_REPORT.md) - 完成报告

---

**祝您使用愉快！** 🎉

如有问题，请提交 Issue：https://github.com/your-repo/issues
