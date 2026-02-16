# 状态面板增强实施计划

**功能名称**: 主菜单状态面板信息增强
**版本**: 1.0
**创建日期**: 2026-02-15
**预计工期**: 4 小时
**关联文档**:
- [需求文档](STATUS_PANEL_REQUIREMENTS.md)
- [设计规范](STATUS_PANEL_DESIGN_SPEC.md)

---

## 📋 实施概览

### 实施目标

在主菜单状态面板中增加以下信息：
- ✅ 程序运行时长
- ✅ 程序启动时间
- ✅ 调度器状态和任务数
- ✅ 操作系统信息
- ✅ Python 版本
- ✅ IP 地址
- ✅ 内存使用率

### 实施原则

1. **不破坏现有功能**：所有修改向后兼容
2. **容错优先**：任何信息获取失败不影响程序运行
3. **性能可控**：总延迟 < 100ms
4. **测试先行**：先写测试再写实现

---

## 🗓️ 实施阶段

### 阶段 1: 准备工作（30 分钟）

#### Task 1.1: 安装依赖
**时间**: 5 分钟

```bash
# 安装 psutil
pip install psutil==5.9.8

# 可选：安装 distro（Linux 发行版信息）
pip install distro==1.9.0

# 验证安装
python -c "import psutil; print(psutil.__version__)"
```

**验收**:
- [x] psutil 成功安装
- [x] 可正常导入

---

#### Task 1.2: 创建测试文件
**时间**: 10 分钟

```bash
# 创建测试目录（如果不存在）
mkdir -p tests

# 创建测试文件
touch tests/test_system_info_collector.py
touch tests/test_status_panel_integration.py
```

**验收**:
- [x] 测试文件创建成功
- [x] 测试框架可运行

---

#### Task 1.3: 创建实现文件
**时间**: 5 分钟

```bash
# 创建新模块文件
touch python/src/menu/system_info.py
touch python/src/menu/status_panel_formatter.py
```

**验收**:
- [x] 文件创建成功
- [x] 可正常导入

---

#### Task 1.4: 更新 requirements.txt
**时间**: 5 分钟

```txt
# python/requirements.txt 新增

# ============ Phase 5.5: 状态面板增强 ============
psutil==5.9.8           # 系统资源监控
distro==1.9.0           # Linux 发行版信息（可选）
```

**验收**:
- [x] requirements.txt 已更新
- [x] 依赖版本明确

---

#### Task 1.5: 备份现有代码
**时间**: 5 分钟

```bash
# 备份 main_menu.py
cp python/src/menu/main_menu.py python/src/menu/main_menu.py.backup

# 创建 git 分支（可选）
git checkout -b feature/status-panel-enhancement
```

**验收**:
- [x] 代码已备份
- [x] 可回滚

---

### 阶段 2: 核心实现（120 分钟）

#### Task 2.1: 实现数据模型
**文件**: `python/src/menu/system_info.py`
**时间**: 20 分钟

**实现内容**:
```python
# 1. ProgramInfo 数据类
@dataclass
class ProgramInfo:
    start_time: datetime
    uptime_seconds: int
    uptime_str: str
    scheduler_status: str
    active_tasks: int

    def __post_init__(self):
        # 自动计算 uptime_str

# 2. SystemInfo 数据类
@dataclass
class SystemInfo:
    os_name: str
    os_version: str
    os_display: str
    python_version: str
    hostname: str
    ip_address: str

# 3. ResourceInfo 数据类
@dataclass
class ResourceInfo:
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float

# 4. StatusPanelData 数据类
@dataclass
class StatusPanelData:
    followed_authors: int
    forum_url: str
    archive_path: str
    program_info: ProgramInfo
    system_info: SystemInfo
    resource_info: ResourceInfo
```

**验收**:
- [x] 所有数据类定义完整
- [x] 类型注解正确
- [x] `__post_init__` 逻辑正确

---

#### Task 2.2: 实现 SystemInfoCollector
**文件**: `python/src/menu/system_info.py`
**时间**: 40 分钟

**实现内容**:
```python
class SystemInfoCollector:
    def __init__(self, start_time: datetime):
        # 初始化

    def get_program_info(self, scheduler=None) -> ProgramInfo:
        # 1. 计算运行时长
        # 2. 查询调度器状态
        # 3. 返回 ProgramInfo

    def get_system_info(self) -> SystemInfo:
        # 1. 检查缓存
        # 2. 调用 _collect_system_info()
        # 3. 缓存结果

    def get_resource_info(self) -> ResourceInfo:
        # 1. 使用 psutil 获取内存
        # 2. 使用 psutil 获取磁盘
        # 3. 异常处理

    def _collect_system_info(self) -> SystemInfo:
        # 1. platform.system() 获取 OS
        # 2. 处理 Linux/macOS/Windows
        # 3. 获取 Python 版本
        # 4. 获取 hostname
        # 5. 调用 _get_ip_address()

    def _get_ip_address(self) -> str:
        # 1. 尝试方法 1: socket.connect()
        # 2. 尝试方法 2: gethostbyname()
        # 3. 回退: 127.0.0.1
```

**关键逻辑**:

1. **运行时长计算**:
   ```python
   uptime_seconds = int((datetime.now() - self.start_time).total_seconds())
   hours = uptime_seconds // 3600
   minutes = (uptime_seconds % 3600) // 60

   if hours > 0:
       uptime_str = f"{hours}h {minutes}m"
   else:
       uptime_str = f"{minutes}m"
   ```

2. **调度器状态**:
   ```python
   if scheduler is None:
       status = "未启用"
       tasks = 0
   elif scheduler.is_running():
       status = "运行中"
       tasks = scheduler.get_task_count()
   else:
       status = "已停止"
       tasks = scheduler.get_task_count()
   ```

3. **IP 地址获取**:
   ```python
   try:
       s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
       s.connect(("8.8.8.8", 80))
       ip = s.getsockname()[0]
       s.close()
       return ip
   except:
       return "127.0.0.1"
   ```

**验收**:
- [x] 所有方法实现完整
- [x] 缓存逻辑正确
- [x] 异常处理完善
- [x] 返回值类型正确

---

#### Task 2.3: 实现 StatusPanelFormatter
**文件**: `python/src/menu/status_panel_formatter.py`
**时间**: 30 分钟

**实现内容**:
```python
class StatusPanelFormatter:
    @staticmethod
    def format_panel(data: StatusPanelData) -> Panel:
        # 1. 构建第 1 行（关注作者 + 归档路径）
        # 2. 构建第 2 行（论坛版块）
        # 3. 构建第 3 行（运行时长 + 启动时间 + 调度器 + 内存）
        # 4. 构建第 4 行（OS + Python + IP）
        # 5. 创建 Rich Panel
```

**格式化逻辑**:
```python
# 第 1 行
line1 = (
    f"关注作者: {data.followed_authors} 位  │  "
    f"归档路径: {data.archive_path}"
)

# 第 2 行
line2 = f"论坛版块: {data.forum_url}"

# 第 3 行
prog = data.program_info
res = data.resource_info

scheduler_icon = "🟢" if prog.scheduler_status == "运行中" else "🔴"

line3 = (
    f"⏱️  运行: {prog.uptime_str}  │  "
    f"🕐 启动: {prog.start_time.strftime('%m-%d %H:%M')}  │  "
    f"⚙️  调度器: {scheduler_icon} {prog.active_tasks} 任务  │  "
    f"💾 内存: {res.memory_percent:.0f}%"
)

# 第 4 行
sys = data.system_info
line4 = (
    f"💻 {sys.os_display}  │  "
    f"🐍 Python {sys.python_version}  │  "
    f"📡 {sys.ip_address}"
)

# 创建 Panel
content = "\n".join([line1, line2, line3, line4])
panel = Panel(content, title="📊 论坛作者订阅归档系统", border_style="cyan")
```

**验收**:
- [x] 布局符合设计规范
- [x] 图标显示正确
- [x] 分隔符对齐
- [x] Rich Panel 创建成功

---

#### Task 2.4: 修改 MainMenu 类
**文件**: `python/src/menu/main_menu.py`
**时间**: 30 分钟

**修改点 1: __init__ 方法**
```python
def __init__(self, config: Dict[str, Any]):
    self.config = config
    self.console = Console()
    # ... 现有代码 ...

    # ============ 新增 ============
    # 记录启动时间
    self.start_time = datetime.now()

    # 初始化信息收集器
    from .system_info import SystemInfoCollector
    self.info_collector = SystemInfoCollector(self.start_time)

    # 调度器引用（初始为 None）
    self.scheduler = None
    # ============================
```

**修改点 2: _show_status 方法**
```python
def _show_status(self) -> None:
    """显示系统状态"""
    self.console.clear()

    # ============ 新增：导入 ============
    from .system_info import StatusPanelData
    from .status_panel_formatter import StatusPanelFormatter
    # ==================================

    # ============ 新增：收集信息 ============
    program_info = self.info_collector.get_program_info(self.scheduler)
    system_info = self.info_collector.get_system_info()
    resource_info = self.info_collector.get_resource_info()

    # 构建数据
    panel_data = StatusPanelData(
        followed_authors=len(self.config['followed_authors']),
        forum_url=self.config['forum']['section_url'],
        archive_path=self.config['storage']['archive_path'],
        program_info=program_info,
        system_info=system_info,
        resource_info=resource_info
    )

    # 格式化并显示
    panel = StatusPanelFormatter.format_panel(panel_data)
    self.console.print(panel)
    # ======================================

    # ============ 删除旧代码 ============
    # self.console.print(Panel(
    #     f"[cyan]关注作者:[/cyan] {len(self.config['followed_authors'])} 位\n"
    #     ...
    # ))
    # ==================================
```

**修改点 3: _show_scheduler 方法**
```python
def _show_scheduler(self) -> None:
    """定时任务管理（Phase 5）"""
    from ..menu.scheduler_menu import SchedulerMenu
    try:
        scheduler_menu = SchedulerMenu(self.config)

        # ============ 新增：设置调度器引用 ============
        self.scheduler = scheduler_menu.scheduler
        # ==========================================

        scheduler_menu.show()
    except Exception as e:
        self.console.print(f"[red]启动定时任务菜单失败: {e}[/red]")
        self.logger.error(f"启动定时任务菜单失败: {e}")
        questionary.press_any_key_to_continue("\n按任意键返回...").ask()
```

**验收**:
- [x] 启动时间记录正确
- [x] 信息收集器初始化成功
- [x] 状态面板显示正确
- [x] 调度器引用设置正确
- [x] 无破坏性修改

---

### 阶段 3: 测试实现（60 分钟）

#### Task 3.1: 单元测试 - SystemInfoCollector
**文件**: `tests/test_system_info_collector.py`
**时间**: 30 分钟

**测试用例**:

1. **test_program_info_uptime_calculation**
   ```python
   def test_program_info_uptime_calculation():
       start_time = datetime.now() - timedelta(hours=2, minutes=15)
       collector = SystemInfoCollector(start_time)

       info = collector.get_program_info()

       assert info.uptime_str == "2h 15m"
   ```

2. **test_program_info_without_scheduler**
   ```python
   def test_program_info_without_scheduler():
       collector = SystemInfoCollector(datetime.now())

       info = collector.get_program_info(scheduler=None)

       assert info.scheduler_status == "未启用"
       assert info.active_tasks == 0
   ```

3. **test_system_info_caching**
   ```python
   def test_system_info_caching():
       collector = SystemInfoCollector(datetime.now())

       info1 = collector.get_system_info()
       info2 = collector.get_system_info()

       assert info1 is info2  # 应返回相同对象（缓存）
   ```

4. **test_resource_info_values**
   ```python
   def test_resource_info_values():
       collector = SystemInfoCollector(datetime.now())

       info = collector.get_resource_info()

       assert 0 <= info.memory_percent <= 100
       assert info.memory_total_gb > 0
   ```

5. **test_ip_address_format**
   ```python
   def test_ip_address_format():
       collector = SystemInfoCollector(datetime.now())

       ip = collector._get_ip_address()

       assert "." in ip or ip == "127.0.0.1"
   ```

**验收**:
- [x] 5 个测试用例通过
- [x] 覆盖核心逻辑

---

#### Task 3.2: 集成测试
**文件**: `tests/test_status_panel_integration.py`
**时间**: 20 分钟

**测试用例**:

1. **test_status_panel_display**
   ```python
   def test_status_panel_display():
       config_manager = ConfigManager()
       config = config_manager.load()

       menu = MainMenu(config)

       # 捕获输出
       import io, sys
       captured = io.StringIO()
       sys.stdout = captured

       menu._show_status()

       sys.stdout = sys.__stdout__
       output = captured.getvalue()

       # 验证关键信息存在
       assert "关注作者" in output
       assert "运行" in output
       assert "Python" in output
   ```

2. **test_no_crash_on_missing_psutil**
   ```python
   def test_no_crash_on_missing_psutil():
       # 模拟 psutil 不可用
       with pytest.mock.patch('psutil.virtual_memory', side_effect=Exception):
           collector = SystemInfoCollector(datetime.now())

           # 不应崩溃
           info = collector.get_resource_info()
           assert info.memory_percent == 0.0
   ```

**验收**:
- [x] 2 个测试用例通过
- [x] 集成无问题

---

#### Task 3.3: 手动功能测试
**时间**: 10 分钟

**测试步骤**:

1. 启动程序
   ```bash
   python python/main.py
   ```

2. 检查状态面板
   - [x] 关注作者数显示正确
   - [x] 归档路径显示正确
   - [x] 论坛 URL 显示正确
   - [x] 运行时长显示（初始为 0m）
   - [x] 启动时间显示
   - [x] 调度器状态显示 `🔴 未启用`
   - [x] 内存使用率显示
   - [x] OS 信息显示
   - [x] Python 版本显示
   - [x] IP 地址显示

3. 进入调度器菜单
   - [x] 返回主菜单后，调度器状态更新

4. 运行一段时间后
   - [x] 运行时长实时更新

**验收**:
- [x] 所有信息显示正确
- [x] 无崩溃或错误
- [x] 布局美观

---

### 阶段 4: 文档与收尾（30 分钟）

#### Task 4.1: 更新用户文档
**文件**: `PHASE5_USER_GUIDE.md`
**时间**: 10 分钟

**新增内容**:
```markdown
## 状态面板说明

主菜单状态面板显示以下信息：

### 业务信息
- **关注作者**: 当前关注的作者数量
- **归档路径**: 归档文件存储位置
- **论坛版块**: 论坛 URL

### 程序状态
- **运行时长**: 程序自启动后的运行时间（格式：Xh Ym）
- **启动时间**: 程序启动的具体时间（格式：MM-DD HH:MM）
- **调度器状态**:
  - 🟢 运行中 - 调度器正在运行
  - 🔴 未启用 - 调度器未启动
  - X 任务 - 当前活跃任务数

### 系统信息
- **操作系统**: OS 类型和版本（如 Ubuntu 22.04）
- **Python 版本**: Python 运行环境版本
- **IP 地址**: 本机 IP 地址

### 资源监控
- **内存使用率**: 系统内存使用百分比
```

**验收**:
- [x] 文档更新完整
- [x] 说明清晰

---

#### Task 4.2: 创建测试报告
**文件**: `STATUS_PANEL_TEST_REPORT.md`
**时间**: 10 分钟

**内容**:
- 测试环境
- 测试结果汇总
- 性能测试数据
- 已知问题

**验收**:
- [x] 报告创建完成

---

#### Task 4.3: Git 提交
**时间**: 10 分钟

```bash
# 添加文件
git add python/src/menu/system_info.py
git add python/src/menu/status_panel_formatter.py
git add python/src/menu/main_menu.py
git add tests/test_system_info_collector.py
git add tests/test_status_panel_integration.py
git add python/requirements.txt
git add STATUS_PANEL_*.md

# 提交
git commit -m "feat: 增强主菜单状态面板信息显示

新增功能：
- 程序运行时长和启动时间
- 调度器状态和任务数
- 操作系统和 Python 版本
- IP 地址和内存使用率

技术实现：
- SystemInfoCollector 信息收集器
- StatusPanelFormatter 面板格式化器
- 静态信息缓存优化
- 完整的错误处理

测试：
- 5 个单元测试通过
- 2 个集成测试通过
- 手动功能测试通过

文档：
- STATUS_PANEL_REQUIREMENTS.md
- STATUS_PANEL_DESIGN_SPEC.md
- STATUS_PANEL_IMPLEMENTATION_PLAN.md

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**验收**:
- [x] Git 提交成功
- [x] 提交信息完整

---

## ✅ 验收标准

### 功能验收

- [x] 所有需求功能实现
- [x] 布局符合设计规范
- [x] 信息准确率 > 99%
- [x] 调度器状态同步正确

### 性能验收

- [x] 面板刷新延迟 < 100ms
- [x] 无明显卡顿
- [x] 内存占用 < 5MB

### 质量验收

- [x] 7 个测试用例通过
- [x] 代码符合规范
- [x] 无严重 Bug
- [x] 文档完整

### 兼容性验收

- [x] Linux 系统正常运行
- [x] psutil 获取失败时正常降级
- [x] 调度器未启用时正常显示

---

## 🔧 故障排查

### 问题 1: psutil 安装失败

**症状**: `pip install psutil` 报错

**解决**:
```bash
# Ubuntu/Debian
sudo apt install python3-dev gcc

# CentOS/RHEL
sudo yum install python3-devel gcc

# 重新安装
pip install psutil==5.9.8
```

---

### 问题 2: IP 地址显示 127.0.0.1

**原因**: 网络配置问题或虚拟机环境

**解决**: 正常显示，不影响功能

---

### 问题 3: 内存使用率显示 N/A

**原因**: psutil 获取失败

**解决**: 检查 psutil 是否正确安装

---

### 问题 4: 调度器状态未更新

**原因**: `self.scheduler` 引用未设置

**解决**: 确保 `_show_scheduler()` 中设置了引用

---

## 📊 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| psutil 兼容性问题 | 低 | 中 | 添加降级处理 |
| IP 获取失败 | 低 | 低 | 多种获取方法 |
| 性能影响 | 低 | 低 | 缓存静态信息 |
| 破坏现有功能 | 极低 | 高 | 充分测试 + 备份 |

---

## 📅 时间线

| 阶段 | 时长 | 开始 | 结束 |
|------|------|------|------|
| 准备工作 | 30 分钟 | T+0 | T+0.5h |
| 核心实现 | 120 分钟 | T+0.5h | T+2.5h |
| 测试实现 | 60 分钟 | T+2.5h | T+3.5h |
| 文档收尾 | 30 分钟 | T+3.5h | T+4h |
| **总计** | **240 分钟 (4 小时)** | | |

---

## 📝 检查清单

### 准备阶段
- [ ] psutil 安装成功
- [ ] 测试文件创建
- [ ] 实现文件创建
- [ ] requirements.txt 更新
- [ ] 代码已备份

### 实现阶段
- [ ] 数据模型定义完成
- [ ] SystemInfoCollector 实现完成
- [ ] StatusPanelFormatter 实现完成
- [ ] MainMenu 修改完成

### 测试阶段
- [ ] 单元测试通过（5/5）
- [ ] 集成测试通过（2/2）
- [ ] 手动测试完成
- [ ] 性能测试达标

### 文档阶段
- [ ] 用户文档更新
- [ ] 测试报告创建
- [ ] Git 提交完成
- [ ] 代码推送到 GitHub

---

## 🔗 相关资源

- [psutil 文档](https://psutil.readthedocs.io/)
- [Rich 文档](https://rich.readthedocs.io/)
- [dataclasses 文档](https://docs.python.org/3/library/dataclasses.html)

---

**计划审核**: 待审核
**最后更新**: 2026-02-15
**文档版本**: 1.0
