# Phase 1 测试与验收指南

> **完成日期**: 2026-02-11
> **状态**: ✅ 代码实施完成，待测试验收

---

## 📋 测试前准备

### 1. 确认环境

```bash
# 进入项目目录
cd /home/ben/gemini-work/gemini-t66y

# 检查 Node.js（确保现有系统可用）
node --version  # 应该显示 v25.6.0

# 检查 Python
python --version  # 应该 >= 3.10
```

### 2. 安装 Python 依赖

```bash
cd python

# 创建虚拟环境（推荐）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或者
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 验证安装
pip list | grep -E "(PyYAML|questionary|rich|click)"
```

预期输出：
```
click            8.1.7
PyYAML           6.0.1
questionary      2.0.1
rich             13.7.0
```

---

## 🧪 测试清单

### Test 1: 文件结构验证

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 检查目录结构
ls -la src/

# 检查所有 Python 文件
find . -name "*.py" | grep -v __pycache__
```

**验收标准**:
- ✅ 所有目录存在：config, menu, cli, bridge, utils, database, scraper, analysis
- ✅ 所有 __init__.py 文件存在
- ✅ 核心文件存在：main.py, config/manager.py, config/wizard.py 等

---

### Test 2: 配置管理器测试

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 测试导入
python3 -c "from src.config.manager import ConfigManager; print('✅ ConfigManager 导入成功')"
```

**预期输出**:
```
✅ ConfigManager 导入成功
```

**如果失败**:
- 检查是否在 python/ 目录下
- 检查虚拟环境是否激活
- 检查 PyYAML 是否安装

---

### Test 3: 配置迁移测试（如果有旧 config.json）

```bash
cd /home/ben/gemini-work/gemini-t66y

# 查看旧配置
cat config.json

# 测试迁移
cd python
python3 -c "
from src.config.manager import ConfigManager
cm = ConfigManager()
if cm.legacy_json_path.exists():
    config = cm.load()
    print('✅ 配置迁移成功')
    print(f'论坛 URL: {config[\"forum\"][\"section_url\"]}')
    print(f'关注作者: {len(config[\"followed_authors\"])} 位')
else:
    print('⚠️  旧配置文件不存在，跳过迁移测试')
"
```

**预期输出**（如果有 config.json）:
```
📦 检测到旧配置文件 config.json
🔄 正在从 config.json 迁移配置...
✓ 配置已成功迁移至: /home/ben/gemini-work/gemini-t66y/python/config.yaml
  - 论坛 URL: https://t66y.com/thread0806.php?fid=7
  - 关注作者: 1 位
✅ 配置迁移成功
论坛 URL: https://t66y.com/thread0806.php?fid=7
关注作者: 1 位
```

**验收标准**:
- ✅ 自动创建 config.yaml
- ✅ 论坛 URL 正确迁移
- ✅ 关注作者列表正确迁移

---

### Test 4: 桥接模块测试

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 测试桥接器初始化
python3 -c "
from src.bridge.nodejs_bridge import NodeJSBridge
try:
    bridge = NodeJSBridge('../')
    print('✅ 桥接器初始化成功')
    print(f'Node.js 目录: {bridge.nodejs_dir}')
except Exception as e:
    print(f'❌ 错误: {e}')
"
```

**预期输出**:
```
[桥接] Node.js 目录: /home/ben/gemini-work/gemini-t66y
✅ 桥接器初始化成功
Node.js 目录: /home/ben/gemini-work/gemini-t66y
```

**验收标准**:
- ✅ 能找到 Node.js 脚本目录
- ✅ 路径解析正确

---

### Test 5: 首次运行 - 配置向导

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 如果已有 config.yaml，先备份
if [ -f config.yaml ]; then
    mv config.yaml config.yaml.backup
    echo "已备份现有配置"
fi

# 运行配置向导
python main.py
```

**操作步骤**:
1. 系统提示"首次运行检测到，启动配置向导..."
2. **步骤 1/4**: 输入论坛 URL（默认即可）
3. **步骤 2/4**: 确认存储设置（默认即可）
4. **步骤 3/4**: 数据分析（选择 No）
5. **步骤 4/4**: 定时任务（选择 No）
6. 看到"✅ 配置完成！"
7. 按 Enter 进入主菜单

**验收标准**:
- ✅ 配置向导界面美观
- ✅ 所有问题都能正常回答
- ✅ 自动创建 config.yaml
- ✅ 进入主菜单

---

### Test 6: 主菜单测试

**在主菜单界面，测试以下功能**:

#### 6.1 查看关注列表

1. 选择 `[2] 📋 查看关注列表`
2. 应该看到一个表格，显示已关注的作者

**验收标准**:
- ✅ 表格显示正常
- ✅ 作者信息正确（名字、日期、帖子数）
- ✅ 可以按任意键返回

#### 6.2 系统设置

1. 选择 `[4] ⚙️  系统设置`
2. 选择 `[1] 修改论坛版块 URL`
3. 输入新 URL 或直接 Enter 保持原样
4. 看到 "✓ 已更新"
5. 返回主菜单

**验收标准**:
- ✅ 设置菜单显示正常
- ✅ 可以修改配置
- ✅ 修改后正确保存到 config.yaml

#### 6.3 查看完整配置

1. 进入系统设置
2. 选择 `[4] 查看完整配置`
3. 应该看到 YAML 格式的完整配置

**验收标准**:
- ✅ 配置显示完整
- ✅ YAML 格式正确
- ✅ 包含所有字段

---

### Test 7: 桥接功能测试（调用 Node.js）

⚠️ **重要**: 此测试会实际调用 Node.js 脚本，请确保有网络连接

#### 7.1 测试立即更新

1. 在主菜单选择 `[3] 🔄 立即更新所有作者`
2. 确认更新
3. 观察 Node.js 脚本的输出

**预期行为**:
- ✅ 显示 "[桥接] 执行: node ..." 信息
- ✅ 看到 Node.js 脚本的实时输出
- ✅ 完成后显示 "✓ 更新完成" 或 "✗ 更新失败"

**验收标准**:
- ✅ 能成功调用 Node.js 脚本
- ✅ 实时输出显示正常
- ✅ 返回主菜单

#### 7.2 测试关注新作者（可选）

⚠️ 需要一个有效的帖子 URL

1. 选择 `[1] 🔍 关注新作者（通过帖子链接）`
2. 输入一个帖子 URL
3. 观察处理过程

**验收标准**:
- ✅ 能成功调用 follow_author.js
- ✅ 作者添加到关注列表
- ✅ 配置文件更新

---

### Test 8: 取消关注测试

1. 在主菜单选择 `[4] ❌ 取消关注作者`
2. 选择一个作者
3. 确认取消关注
4. 回到主菜单
5. 再次查看关注列表，确认已移除

**验收标准**:
- ✅ 能选择作者
- ✅ 确认提示清晰
- ✅ 作者成功移除
- ✅ config.yaml 更新

---

### Test 9: 命令行模式测试

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 测试命令行模式
python main.py help
```

**预期输出**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  命令行模式将在 Phase 5 完善
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

当前请使用菜单模式：
  python main.py

可用的简单命令（Phase 1）：
  python main.py           # 菜单模式

计划的命令（Phase 5）：
  python main.py follow <URL>
  ...
```

**验收标准**:
- ✅ 显示提示信息
- ✅ 说明当前状态和未来计划

---

### Test 10: 错误处理测试

#### 10.1 测试无效输入

在配置向导中：
- 输入无效的超时时间（如 "abc"）
- 应该提示重新输入

#### 10.2 测试中断

```bash
# 运行主程序
python main.py

# 按 Ctrl+C 中断
```

**预期行为**:
- ✅ 显示 "用户中断，退出..."
- ✅ 优雅退出，不崩溃

---

## ✅ 完整验收清单

```
Phase 1 验收清单
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ 环境搭建
  □ Python 虚拟环境创建成功
  □ 所有依赖安装成功
  □ 目录结构正确

□ 配置管理
  □ ConfigManager 正常工作
  □ config.json → config.yaml 迁移成功
  □ 配置向导正常运行
  □ 配置读写正常

□ 菜单系统
  □ 主菜单显示正常
  □ 状态信息显示正确
  □ 所有菜单选项可导航
  □ 界面美观（Rich 样式）

□ 桥接功能
  □ 可以调用 follow_author.js
  □ 可以调用 archive_posts.js
  □ 可以调用 run_scheduled_update.js
  □ 实时输出正常显示

□ 功能验证
  □ 查看关注列表正常
  □ 添加/删除作者正常
  □ 系统设置修改正常
  □ 与 Node.js 版本功能一致

□ 错误处理
  □ 无效输入有提示
  □ Ctrl+C 优雅退出
  □ 异常有错误信息

□ 文档
  □ README 清晰
  □ 注释完整
```

---

## 🐛 常见问题

### 问题1：ModuleNotFoundError

```
ModuleNotFoundError: No module named 'yaml'
```

**解决**:
```bash
pip install -r requirements.txt
```

### 问题2：导入错误

```
ModuleNotFoundError: No module named 'src'
```

**解决**: 确保在 python/ 目录下运行
```bash
cd /home/ben/gemini-work/gemini-t66y/python
python main.py
```

### 问题3：Node.js 脚本找不到

```
FileNotFoundError: Node.js 目录不存在
```

**解决**: 检查配置
```bash
# 查看配置
cat config.yaml | grep nodejs_path

# 应该是
legacy:
  nodejs_path: "../"
```

### 问题4：中文显示问题

如果终端中文显示异常，确保终端支持 UTF-8：
```bash
export LANG=zh_CN.UTF-8
```

### 问题5：脚本路径错误（已修复）

```
FileNotFoundError: 脚本不存在: /home/ben/gemini-work/follow_author.js
```

**原因**: Phase 1 初始版本的路径计算 bug，路径少了一层目录
**状态**: ✅ 已在代码中修复
**解决**: 已更新 `nodejs_bridge.py`，无需手动操作

如果仍遇到此问题，请重新获取最新代码。

### 问题6：Node.js 依赖缺失（已修复）

```
Error: Cannot find module 'fs-extra'
```

**原因**: Node.js 项目缺少 `fs-extra` 依赖
**状态**: ✅ 已修复
**解决**:
```bash
cd /home/ben/gemini-work/gemini-t66y
npm install
```

### 问题7：配置文件不同步（已修复）

**现象**: 关注新作者成功，但查看列表显示为空

**原因**: Node.js 脚本修改 `config.json`，Python 读取 `config.yaml`，两者不同步
**状态**: ✅ 已在代码中修复
**解决**:

1. 代码已添加自动同步逻辑
2. 首次使用需要手动同步：
```bash
cd /home/ben/gemini-work/gemini-t66y/python
python sync_config.py
```

之后每次关注新作者或更新时会自动同步。

### 问题8：Python 版本要求

**问题**: 我的 Python 是 3.10，文档要求 3.11+

**解决**: Python 3.10 完全支持 Phase 1 所有功能，可以直接使用。文档已更新为 3.10+。

---

## 📊 性能基准

Phase 1 的性能指标：

| 操作 | 预期时间 |
|------|---------|
| 启动主菜单 | < 1秒 |
| 配置加载 | < 0.1秒 |
| 菜单导航 | 即时 |
| 调用 Node.js 脚本 | 取决于脚本本身 |

---

## 📝 测试报告模板

完成测试后，请填写以下报告：

```
Phase 1 测试报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试日期: 2026-02-__
测试人员: ____________
环境: Linux / macOS / Windows

测试结果:
□ 通过  □ 失败

功能测试:
- 配置向导: ✅ / ❌
- 主菜单: ✅ / ❌
- 桥接功能: ✅ / ❌
- 配置管理: ✅ / ❌

发现的问题:
1.
2.
3.

改进建议:
1.
2.

总体评价:
□ 可以进入 Phase 2
□ 需要修复后重新测试
```

---

## 🎯 Phase 1 完成标志

当以下条件全部满足时，Phase 1 验收通过：

1. ✅ 所有测试通过
2. ✅ 功能与 Node.js 版本一致
3. ✅ 无严重 bug
4. ✅ 文档完整
5. ✅ 代码注释清晰

**验收通过后**，可以进入 Phase 2 - Python 爬虫核心开发。

---

**测试文档结束**
