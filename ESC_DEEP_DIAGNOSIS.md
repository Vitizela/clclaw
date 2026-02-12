# ESC 键深度诊断指南

> **状态**: 🔍 深度调查中
> **问题**: ESC 键在 questionary 中无法工作
> **上次修复**: validate 参数（但问题依然存在）

---

## 🎯 当前状况

### 已知信息
1. ✅ validate 参数已修复（添加了 `x is None` 检查）
2. ❌ ESC 键仍然无法工作
3. ❌ 测试脚本也无法工作
4. ✅ Ctrl+C 可以工作（显示 "Cancelled by user"）

### 可能的原因

#### 原因 1: 终端不发送 ESC 键码 ⭐⭐⭐
**最可能的原因**

某些终端配置或环境可能拦截了 ESC 键，导致应用程序根本收不到 ESC。

**表现**:
- 按 ESC 没有任何反应
- 应用程序完全收不到 ESC 键码

**诊断**:
```bash
/tmp/test_raw_esc.py
# 这个测试会直接读取键盘，检查 ESC 是否被发送
```

#### 原因 2: prompt_toolkit 配置问题 ⭐⭐
**中等可能性**

prompt_toolkit 或 questionary 的某些配置可能禁用了 ESC 的默认行为。

**表现**:
- ESC 键被发送了，但 questionary 不处理它
- 或者 ESC 触发了错误的行为

**诊断**:
```bash
/tmp/test_prompt_toolkit_esc.py
# 测试 prompt_toolkit 原生的 ESC 处理
```

#### 原因 3: questionary 版本问题 ⭐
**较低可能性**

虽然版本 2.0.1 应该支持 ESC，但可能有 bug。

**诊断**:
```bash
python3 -c "import questionary; print(questionary.__version__)"
```

#### 原因 4: 键盘映射冲突 ⭐⭐
**中等可能性**

tmux、screen、或其他工具可能拦截了 ESC。

**表现**:
- 在 tmux 外 ESC 工作，在 tmux 内不工作
- 或者 ESC 延迟（等待组合键）

**诊断**:
```bash
/tmp/check_terminal_env.sh
# 检查是否在 tmux/screen 中
```

---

## 📋 诊断步骤

### Step 1: 检查终端环境 (5 分钟)

```bash
chmod +x /tmp/check_terminal_env.sh
/tmp/check_terminal_env.sh
```

**请复制所有输出并发送给我。**

关键信息：
- TERM 变量
- 是否在 SSH 中
- 是否在 tmux/screen 中
- stty 设置

---

### Step 2: 原始 ESC 键测试 (2 分钟)

```bash
python3 /tmp/test_raw_esc.py
```

**操作**:
1. 运行脚本
2. 按 ESC 键
3. 观察输出

**预期**:
- 如果显示 "✅ 这是 ESC 键！" → ESC 被终端发送了
- 如果没有任何输出 → **ESC 被终端拦截了**（这是问题根源）

---

### Step 3: questionary 简单测试 (2 分钟)

```bash
python3 /tmp/test_questionary_esc_simple.py
```

**操作**:
1. 测试 1: 在 select 菜单中按 ESC
2. 测试 2: 在 text 输入中按 ESC

**预期**:
- 如果返回 None → ESC 工作
- 如果返回其他值或无反应 → ESC 不工作

---

### Step 4: 全面诊断 (5 分钟)

```bash
python3 /tmp/diagnose_esc_comprehensive.py
```

**操作**:
- 按照提示进行 6 个测试
- 每个测试都按 ESC 键
- 记录哪些测试通过（✅），哪些失败（❌）

**请复制完整输出并发送给我。**

---

## 🔧 可能的解决方案

### 方案 A: 如果终端不发送 ESC（Step 2 失败）

#### A1: 修改终端配置

**如果在 tmux 中**:
```bash
# 在 ~/.tmux.conf 中添加
set -s escape-time 0
```

**如果在 vim 中的终端**:
```vim
" 在 ~/.vimrc 中添加
set notimeout
set ttimeout
set ttimeoutlen=0
```

#### A2: 使用替代键（推荐）

**立即可用的解决方案 - 不依赖 ESC**:
- 使用 **Ctrl+C** 退出（已经可以工作）
- 选择 **"← 返回"** 选项
- 实施 **'q' 键** 和 **Ctrl+B** 方案

---

### 方案 B: 如果 questionary 不处理 ESC（Step 3 失败）

#### B1: 显式配置 questionary

在代码中添加 kbintr=False:
```python
result = questionary.select(
    "选择:",
    choices=choices,
    kbintr=False  # 禁用 Ctrl+C 捕获，可能让 ESC 工作
).ask()
```

#### B2: 使用自定义键绑定（已创建）

使用 `/home/ben/gemini-work/gemini-t66y/python/src/utils/keybindings.py` 中的自定义绑定：
```python
from utils.keybindings import MENU_KEYBINDINGS

result = questionary.select(
    "选择:",
    choices=choices,
    key_bindings=MENU_KEYBINDINGS  # 包含 q、Ctrl+B
).ask()
```

---

### 方案 C: 终极解决方案（推荐）⭐⭐⭐

**不依赖 ESC 键，提供多种返回方式**:

1. **保留 ESC**（如果能工作）
2. **添加 'q' 键**（vim 风格，单键快速）
3. **添加 Ctrl+B**（组合键，不会被终端拦截）

**优势**:
- 不依赖单一按键
- 适配各种终端环境
- 用户总能找到一种可用的方式

**实施时间**: 1 小时（已有完整方案和代码）

---

## 🧪 测试矩阵

| 测试 | 成功 | 失败 | 说明 |
|------|------|------|------|
| Step 1: 终端环境 | | | 识别环境配置 |
| Step 2: 原始 ESC | ✅ | ❌ | 判断 ESC 是否被发送 |
| Step 3: questionary 简单 | ✅ | ❌ | 判断 questionary 是否处理 ESC |
| Step 4: 全面诊断 | | | 6 个子测试 |
| → 4.1: select 默认 | ✅ | ❌ | |
| → 4.2: unsafe_ask | ✅ | ❌ | |
| → 4.3: prompt 原生 | ✅ | ❌ | |
| → 4.4: 自定义绑定 | ✅ | ❌ | |
| → 4.5: 配置检查 | | | |
| → 4.6: 环境变量 | | | |

---

## 📊 决策树

```
ESC 键不工作
    ↓
运行 Step 2（原始 ESC 测试）
    ↓
ESC 被捕获？
    ↓
  YES ───────────────────────→ 问题在 questionary/prompt_toolkit
    │                           ↓
    │                         运行 Step 3-4
    │                           ↓
    │                         检查 questionary 配置
    │                           ↓
    │                         方案 B: 修改 questionary 配置
    │                           ↓
    │                         方案 C: 添加替代键（推荐）
    │
  NO ────────────────────────→ 问题在终端
                                ↓
                              运行 Step 1
                                ↓
                              检查 tmux/ssh/screen
                                ↓
                              方案 A: 修改终端配置
                                ↓
                              方案 C: 添加替代键（推荐）
```

---

## 🚀 下一步行动

### 立即行动（你需要做）

1. **运行诊断脚本**（10 分钟）
   ```bash
   /tmp/check_terminal_env.sh > /tmp/env_check.log
   python3 /tmp/test_raw_esc.py > /tmp/raw_esc.log
   python3 /tmp/test_questionary_esc_simple.py > /tmp/simple_esc.log
   python3 /tmp/diagnose_esc_comprehensive.py > /tmp/full_diagnosis.log
   ```

2. **发送结果给我**
   - 复制所有输出
   - 或者发送日志文件内容
   - 特别注意 Step 2 的结果（最关键）

### 根据诊断结果

#### 如果 Step 2 显示 ESC 被捕获
→ 问题在 questionary 配置
→ 我会修改代码配置

#### 如果 Step 2 显示 ESC 未被捕获
→ 问题在终端环境
→ 需要修改终端配置或使用替代键

#### 无论哪种情况
→ **我强烈建议实施方案 C**（添加 q 和 Ctrl+B）
→ 这样就不依赖 ESC 键了

---

## 📝 已创建的诊断脚本

1. **/tmp/check_terminal_env.sh**
   - 检查终端环境配置
   - 检查 tmux/screen/ssh
   - 检查 stty 设置

2. **/tmp/test_raw_esc.py**
   - **最关键的测试**
   - 直接读取键盘，绕过 questionary
   - 判断 ESC 是否被终端发送

3. **/tmp/test_questionary_esc_simple.py**
   - 最简单的 questionary 测试
   - 无任何额外配置

4. **/tmp/test_prompt_toolkit_esc.py**
   - 测试 prompt_toolkit 原生行为
   - 测试自定义键绑定

5. **/tmp/diagnose_esc_comprehensive.py**
   - **最全面的诊断**
   - 6 个不同的测试
   - 自动检查环境变量

---

## 💡 临时解决方案（立即可用）

在等待诊断结果期间，你可以使用这些方式返回：

### 方式 1: Ctrl+C
```
在任何 questionary 菜单中按 Ctrl+C
→ 显示 "Cancelled by user"
→ 程序中断（比较粗暴）
```

### 方式 2: "← 返回" 选项
```
在有选项的菜单中，导航到 "← 返回"
→ 按 Enter 选择
→ 正常返回（最可靠）
```

### 方式 3: 留空返回（输入框）
```
在输入框中，不输入任何内容
→ 直接按 Enter
→ 触发留空返回逻辑
```

---

**请立即运行诊断脚本，特别是 Step 2（最关键）！** 🔍

把结果发给我，我会根据诊断结果提供精确的解决方案。
