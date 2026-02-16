# Phase 5 任务追踪清单

**创建日期**: 2026-02-15
**预计完成**: 2026-02-24（10 天）
**当前进度**: 13/26 任务完成（50%）🎉

---

## 📊 总体进度

```
Week 1: 基础通知模块 ████████████████████  100% (10/10) ✅
Week 2: 调度与归档   ██████░░░░░░░░░░░░░░  30% (3/10)
Week 3: 测试与文档   ░░░░░░░░░░░░░░░░░░░░  0% (0/8)
```

**总计**: 13/26 任务完成（50%）🎉 **过半！**

**当前日期**: 2026-02-15
**状态**: 🚧 进行中 - Day 3 完成，准备 Day 4

---

## Week 1: 基础通知模块（Day 1-3）

### Day 1: 环境准备与通知管理器 ✅

**目标**: 完成依赖安装、目录创建和基础通知框架

- [✅] **Task #19.1** - 安装项目依赖（已完成）
  - 文件: `python/requirements.txt`
  - 内容: 添加 `apscheduler==3.10.4` 和 `paho-mqtt==1.6.1`
  - 验收: ✅ 依赖安装成功，可正常导入

- [✅] **Task #19.2** - 创建目录结构（已完成）
  - 目录: `python/src/scheduler/`, `python/src/notification/`, `python/tools/`
  - 验收: ✅ 目录创建成功，包含 `__init__.py`

- [✅] **Task #19.3** - 实现 NotificationManager（已完成）
  - 文件: `python/src/notification/manager.py`（179 行）
  - 内容: 抽象基类 `NotifierBase` + 管理器 `NotificationManager`
  - 验收: ✅ 可实例化，支持添加/移除/清空通知器

- [✅] **Task #19.4** - 实现 ConsoleNotifier（已完成）
  - 文件: `python/src/notification/console_notifier.py`（135 行）
  - 内容: 控制台输出通知器，支持级别过滤
  - 验收: ✅ 彩色图标输出，级别过滤正确

- [✅] **Task #19.5** - 实现 FileNotifier（已完成）
  - 文件: `python/src/notification/file_notifier.py`（143 行）
  - 内容: 日志文件通知器，自动创建目录
  - 验收: ✅ 日志写入成功，格式正确

- [✅] **Task #19.6** - 导出通知模块（已完成）
  - 文件: `python/src/notification/__init__.py`（10 行）
  - 内容: 导出所有通知器类
  - 验收: ✅ 可正常导入所有类

- [✅] **Task #19.7** - 单元测试（已完成）
  - 文件: `python/test_day1_notifications.py`（250 行）
  - 内容: 5 个测试用例
  - 验收: ✅ 5/5 测试通过

**Day 1 验收**: ✅ 通知框架完成，Console 和 File 通知器工作正常

**Git 提交**: `490b5ea` - feat(phase5): 实现 Day 1 基础通知模块

---

### Day 2: MQTT 通知器 ✅

**目标**: 实现 MQTT 消息发布功能

- [✅] **Task #20.1** - 实现 MQTTNotifier（已完成）
  - 文件: `python/src/notification/mqtt_notifier.py`（300 行）
  - 内容: MQTT 客户端封装，自动重连，QoS 1
  - 验收: ✅ 可连接 Broker，支持认证，带重试

- [✅] **Task #20.2** - 扩展配置文件（已完成）
  - 文件: `python/config.yaml`（+16 行）
  - 内容: 添加 `notification` 配置节
  - 验收: ✅ 配置正确，包含 console/file/mqtt

- [✅] **Task #20.3** - 单元测试（已完成）
  - 文件: `python/test_day2_mqtt.py`（300 行）
  - 内容: 5 个测试用例（包含容错处理）
  - 验收: ✅ 5/5 测试通过（Broker 不可用时正确跳过）

**Day 2 验收**: ✅ MQTT 通知器完成，支持结构化 JSON 消息发布

**Git 提交**: `3e2cee6` - feat(phase5): 实现 Day 2 MQTT 通知器

**注意**: MQTT 功能默认禁用，需用户自行配置 Broker

---

### Day 3: 任务调度器基础 ✅

**目标**: 实现 APScheduler 封装和任务管理

- [✅] **Task #21.1** - 实现 TaskScheduler（已完成）
  - 文件: `python/src/scheduler/task_scheduler.py`（370 行）
  - 内容: BackgroundScheduler 封装，Cron 支持，任务持久化
  - 验收: ✅ 支持 CRUD，持久化，错误处理

- [✅] **Task #21.2** - 导出调度模块（已完成）
  - 文件: `python/src/scheduler/__init__.py`（5 行）
  - 内容: 导出 TaskScheduler
  - 验收: ✅ 可正常导入

- [✅] **Task #21.3** - 单元测试（已完成）
  - 文件: `python/test_day3_scheduler.py`（280 行）
  - 内容: 8 个测试用例（包含实际执行测试）
  - 验收: ✅ 8/8 测试通过（包含 11 秒实际执行）

**Day 3 验收**: ✅ 调度器完成，支持 Cron 调度和任务持久化

**Git 提交**: `09a1e05` - feat(phase5): 实现 Day 3 任务调度器

**注意**: 修复了 next_run_time 在未启动时不可用的问题

---

## Week 2: 调度与归档（Day 4-7）

### Day 4: 增量归档器

**目标**: 实现增量归档逻辑（只下载新帖）

- [ ] **Task #22.1** - 实现 IncrementalArchiver（2.5 小时）
  - 文件: `python/src/scheduler/incremental_archiver.py`
  - 内容: 增量归档器，调用 PostChecker + ForumArchiver
  - 验收: 可检测新帖并归档

- [ ] **Task #22.2** - 修改 ForumArchiver 支持 target_urls（1.5 小时）
  - 文件: `python/src/scraper/archiver.py`
  - 修改: `archive_author()` 方法添加 `target_urls` 参数
  - 验收: 可传入 URL 列表，只归档指定帖子

- [ ] **Task #22.3** - 单元测试（1 小时）
  - 文件: `python/test_day4_incremental.py`
  - 内容: 测试增量归档流程
  - 验收: 增量归档成功，无重复下载

**Day 4 验收**: ✅ 增量归档器工作正常，无重复下载

---

### Day 5: 调度器菜单（Part 1）

**目标**: 实现调度器交互菜单

- [ ] **Task #23.1** - 创建 SchedulerMenu 框架（2 小时）
  - 文件: `python/src/menu/scheduler_menu.py`
  - 内容: SchedulerMenu 类，基础菜单结构
  - 验收: 菜单可显示，可返回主菜单

- [ ] **Task #23.2** - 实现查看任务列表（1 小时）
  - 功能: `_show_tasks()` 方法，表格显示任务
  - 验收: 可显示任务列表，包含 ID/名称/下次运行时间

- [ ] **Task #23.3** - 实现添加任务（2 小时）
  - 功能: `_add_task()` 方法，选择作者 + Cron 表达式
  - 验收: 可添加任务，自动保存配置

**Day 5 部分验收**: 菜单基础框架 + 任务列表 + 添加任务功能完成

---

### Day 6: 调度器菜单（Part 2）

**目标**: 完成调度器菜单所有功能

- [ ] **Task #23.4** - 实现删除任务（0.5 小时）
  - 功能: `_delete_task()` 方法
  - 验收: 可选择并删除任务

- [ ] **Task #23.5** - 实现启动/停止调度器（0.5 小时）
  - 功能: `_start_scheduler()` 和 `_stop_scheduler()` 方法
  - 验收: 调度器状态切换正常

- [ ] **Task #23.6** - 实现 MQTT 配置（1 小时）
  - 功能: `_configure_mqtt()` 方法，交互式配置 Broker
  - 验收: 可配置 MQTT 连接信息，保存到 config.yaml

- [ ] **Task #23.7** - 集成任务执行逻辑（1.5 小时）
  - 功能: `_incremental_archive_task()` 方法，连接通知管理器
  - 验收: 任务执行时发送通知

**Day 6 验收**: ✅ 调度器菜单功能完整

---

### Day 7: 主菜单集成

**目标**: 将调度器菜单集成到主菜单

- [ ] **Task #23.8** - 修改 main_menu.py（0.5 小时）
  - 文件: `python/src/menu/main_menu.py`
  - 修改: 添加"定时任务"菜单项，调用 SchedulerMenu
  - 验收: 可从主菜单进入调度器菜单

- [ ] **Task #23.9** - 手动测试完整流程（1 小时）
  - 测试: 添加任务 → 启动调度器 → 观察执行 → 查看通知
  - 验收: 完整流程无错误

**Day 7 验收**: ✅ 调度器菜单集成完成，用户可使用

**Week 2 总验收**: ✅ 定时归档功能完整可用

---

## Week 3: 测试与文档（Day 8-10）

### Day 8: 端到端测试

**目标**: 完整流程测试和集成验证

- [ ] **Task #24.1** - 创建 E2E 测试脚本（3 小时）
  - 文件: `python/test_phase5_e2e.py`
  - 内容: 端到端测试，完整流程验证
  - 验收: E2E 测试通过，所有功能正常

- [ ] **Task #24.2** - 性能测试（1 小时）
  - 测试: 调度器启动时间、MQTT 连接时间、增量归档速度
  - 验收: 满足性能目标（见性能目标表）

**Day 8 验收**: ✅ E2E 测试通过，性能达标

---

### Day 9: MQTT 消息处理器

**目标**: 创建消息处理器示例和文档

- [ ] **Task #25.1** - 创建 mqtt_to_telegram.py（2 小时）
  - 文件: `python/tools/mqtt_to_telegram.py`
  - 内容: MQTT 订阅 → Telegram Bot 发送
  - 验收: 可接收 MQTT 消息并转发到 Telegram

- [ ] **Task #25.2** - 编写消息处理器文档（1 小时）
  - 文件: `MQTT_HANDLER_GUIDE.md`
  - 内容: 部署指南、Systemd 服务配置、扩展指南
  - 验收: 文档完整，步骤清晰

**Day 9 验收**: ✅ 消息处理器示例完成，文档齐全

---

### Day 10: 优化与验收

**目标**: 性能优化和最终验收

- [ ] **Task #26.1** - 性能优化（2 小时）
  - 优化: 调度器启动、MQTT 重连、日志轮转
  - 验收: 启动时间 < 1 秒，MQTT 连接 < 2 秒

- [ ] **Task #26.2** - 用户文档（1.5 小时）
  - 文件: `PHASE5_USER_GUIDE.md`
  - 内容: 功能介绍、快速开始、Cron 表达式、常见问题
  - 验收: 文档完整，易于理解

- [ ] **Task #26.3** - 完成报告（1.5 小时）
  - 文件: `PHASE5_COMPLETION_REPORT.md`
  - 内容: 完成度、性能数据、代码统计、关键决策
  - 验收: 报告全面，数据准确

- [ ] **Task #26.4** - 更新项目文档（0.5 小时）
  - 文件: `README.md`, `MEMORY.md`, `FEATURES_DESIGN_OVERVIEW.md`
  - 内容: 添加 Phase 5 功能说明
  - 验收: 文档更新同步

**Day 10 验收**: ✅ 所有文档完成，Phase 5 正式交付

**Week 3 总验收**: ✅ 测试通过，文档齐全，性能达标

---

## 🎯 最终验收清单

### 功能验收

- [ ] **定时任务**: 可添加/删除/暂停/恢复任务
- [ ] **Cron 调度**: 任务按 Cron 表达式正确触发
- [ ] **增量归档**: 只下载新帖，无重复
- [ ] **MQTT 通知**: 消息格式正确，QoS 1 送达
- [ ] **任务持久化**: 重启后任务配置保留
- [ ] **多通知渠道**: Console、File、MQTT 同时工作
- [ ] **交互菜单**: 所有菜单操作流畅
- [ ] **配置管理**: MQTT 配置可修改并保存

### 性能验收

- [ ] **调度器启动**: < 1 秒
- [ ] **MQTT 连接**: < 2 秒
- [ ] **增量归档（无新帖）**: < 5 秒
- [ ] **增量归档（10 篇）**: < 60 秒
- [ ] **消息发送**: < 0.5 秒
- [ ] **任务持久化**: < 0.1 秒

### 质量验收

- [ ] **单元测试**: 所有测试通过
- [ ] **E2E 测试**: 完整流程无错误
- [ ] **错误处理**: 异常场景有友好提示
- [ ] **日志记录**: 关键操作有日志
- [ ] **配置兼容**: 向后兼容旧配置
- [ ] **代码风格**: 遵循 Phase 3/4 模式

### 文档验收

- [ ] **PHASE5_TASK_TRACKER.md**: 任务追踪完整
- [ ] **PHASE5_IMPLEMENTATION_PLAN.md**: 实施计划详细
- [ ] **PHASE5_USER_GUIDE.md**: 用户指南清晰
- [ ] **MQTT_HANDLER_GUIDE.md**: 消息处理器文档完整
- [ ] **PHASE5_COMPLETION_REPORT.md**: 完成报告全面
- [ ] **README.md**: 更新 Phase 5 功能说明
- [ ] **MEMORY.md**: 记录关键决策和陷阱

---

## 📝 使用说明

### 如何追踪进度

1. **开始任务**: 将 `[ ]` 改为 `[🔄]`
2. **完成任务**: 将 `[🔄]` 改为 `[✅]`
3. **阻塞任务**: 将 `[ ]` 改为 `[⛔]`，并注明原因
4. **跳过任务**: 将 `[ ]` 改为 `[⏭️]`，并注明原因

### 示例

```markdown
- [✅] Task #19.1 - 安装项目依赖（已完成）
- [🔄] Task #19.2 - 创建目录结构（进行中）
- [⛔] Task #19.3 - 实现 NotificationManager（阻塞：等待 Task #19.2）
- [ ] Task #19.4 - 实现 ConsoleNotifier（待开始）
- [⏭️] Task #20.2 - 扩展配置文件（跳过：配置已手动完成）
```

### 每日更新

每天结束时，更新：
1. **总体进度**: 更新进度条百分比
2. **完成任务**: 标记 ✅
3. **遇到问题**: 标记 ⛔ 并记录
4. **明天计划**: 预估明天完成的任务

---

## 🚀 快速开始

### 环境准备

```bash
# 1. 安装 Python 依赖
pip install -r python/requirements.txt

# 2. 安装 Mosquitto MQTT Broker（Ubuntu/Debian）
sudo apt update
sudo apt install mosquitto mosquitto-clients

# 3. 启动 Mosquitto
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# 4. 测试 MQTT（另开终端）
mosquitto_sub -t 't66y/#' -v
```

### 开始 Task #19.1

```bash
# 1. 编辑 requirements.txt
nano python/requirements.txt

# 2. 添加依赖
echo "" >> python/requirements.txt
echo "# ============ Phase 5: 调度器与通知 ============" >> python/requirements.txt
echo "apscheduler==3.10.4        # 任务调度" >> python/requirements.txt
echo "paho-mqtt==1.6.1           # MQTT 客户端" >> python/requirements.txt

# 3. 安装
pip install -r python/requirements.txt

# 4. 验证
python -c "import apscheduler; print(f'APScheduler: {apscheduler.__version__}')"
python -c "import paho.mqtt.client as mqtt; print(f'Paho MQTT: {mqtt.__version__}')"
```

---

## 📊 性能目标表

| 操作 | 目标 | 当前 | 状态 |
|------|------|------|------|
| 调度器启动 | < 1 秒 | - | ⏳ |
| MQTT 连接 | < 2 秒 | - | ⏳ |
| 增量归档（无新帖）| < 5 秒 | - | ⏳ |
| 增量归档（10 篇新帖）| < 60 秒 | - | ⏳ |
| 消息发送 | < 0.5 秒 | - | ⏳ |
| 任务持久化 | < 0.1 秒 | - | ⏳ |

---

## 🔧 故障排查

### MQTT 连接失败

**症状**: `MQTTNotifier` 报错 "连接失败"

**解决**:
```bash
# 1. 检查 Mosquitto 是否运行
sudo systemctl status mosquitto

# 2. 检查端口占用
sudo netstat -tulpn | grep 1883

# 3. 查看日志
sudo tail -f /var/log/mosquitto/mosquitto.log

# 4. 重启服务
sudo systemctl restart mosquitto
```

### APScheduler 任务不执行

**症状**: 任务添加成功但不触发

**解决**:
```python
# 1. 检查调度器状态
scheduler.scheduler.running  # 应为 True

# 2. 检查任务列表
scheduler.get_all_tasks()  # 应有任务

# 3. 查看下次运行时间
job.next_run_time  # 应不为 None

# 4. 检查 Cron 表达式
# 使用 https://crontab.guru/ 验证
```

### 增量归档重复下载

**症状**: 已归档的帖子再次下载

**解决**:
```bash
# 1. 检查 PostTracker
python -c "from src.scraper.post_tracker import PostTracker; pt = PostTracker(); print(pt.load_tracked_urls())"

# 2. 检查数据库
sqlite3 python/data/forum_data.db "SELECT COUNT(*) FROM posts;"

# 3. 验证 URL 格式
# 确保 URL 规范化一致
```

---

## 📅 里程碑

| 日期 | 里程碑 | 状态 |
|------|--------|------|
| 2026-02-15 | 项目启动 | ⏳ |
| 2026-02-17 | Week 1 完成（基础模块）| ⏳ |
| 2026-02-21 | Week 2 完成（调度归档）| ⏳ |
| 2026-02-24 | Week 3 完成（测试文档）| ⏳ |
| 2026-02-24 | Phase 5 正式交付 | ⏳ |

---

## 📚 相关文档

- **详细设计**: `PHASE5_DESIGN_SPEC.md`
- **需求文档**: `PHASE5_REQUIREMENTS.md`
- **实施计划**: `PHASE5_IMPLEMENTATION_PLAN.md`
- **用户指南**: `PHASE5_USER_GUIDE.md`（Day 10 创建）
- **消息处理器**: `MQTT_HANDLER_GUIDE.md`（Day 9 创建）
- **完成报告**: `PHASE5_COMPLETION_REPORT.md`（Day 10 创建）

---

## 💡 关键决策记录

### 决策 1: 使用 MQTT 而非 Telegram Bot

**理由**: 解耦、可扩展、多项目复用

**影响**: 需要额外部署 Mosquitto 和消息处理器

**权衡**: 初期复杂度增加，长期维护成本降低

---

### 决策 2: 使用 APScheduler 而非系统 Cron

**理由**: Python 原生、动态管理、跨平台

**影响**: 调度器需常驻运行

**权衡**: 牺牲部分系统集成（如 systemd），换取灵活性

---

### 决策 3: 增量归档使用 target_urls 参数

**理由**: 职责分离、灵活性、性能优化

**影响**: 需修改 `ForumArchiver.archive_author()` 方法

**权衡**: 代码改动小，收益大

---

**更新时间**: 2026-02-15
**下一步**: 开始 Task #19.1 - 安装项目依赖

---

**注**: 本文档将在开发过程中持续更新，每日结束时更新进度。
