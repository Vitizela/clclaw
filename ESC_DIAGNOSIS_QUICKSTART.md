# ESC 键诊断 - 快速开始

> **目标**: 找出为什么 ESC 键不工作
> **耗时**: 5-10 分钟
> **操作**: 运行 3 个测试脚本

---

## 🎯 最关键的测试（必做）

### 测试 1: 原始 ESC 键测试 ⭐⭐⭐

**这是最重要的测试！**

```bash
python3 /tmp/test_raw_esc.py
```

**操作**:
1. 运行上面的命令
2. 按任意键开始
3. **按 ESC 键**
4. 观察输出

**预期输出示例**:
```
捕获到按键:
  字符: '\x1b'
  十六进制: 1b
  ASCII 码: 27
  ✅ 这是 ESC 键！
```

**判断**:
- ✅ **看到 "这是 ESC 键！"** → ESC 被终端发送了，问题在 questionary
- ❌ **没有任何输出** → ESC 被终端拦截了，问题在终端配置

**把结果告诉我！这会决定解决方案的方向。**

---

## 📋 其他测试（建议做）

### 测试 2: questionary 简单测试

```bash
python3 /tmp/test_questionary_esc_simple.py
```

**操作**:
- 测试 1: 在选择菜单中按 ESC
- 测试 2: 在输入框中按 ESC

**预期**:
- 如果返回 `None` → ✅ ESC 工作
- 如果没反应 → ❌ ESC 不工作

---

### 测试 3: 全面诊断

```bash
python3 /tmp/diagnose_esc_comprehensive.py
```

**操作**:
- 按照提示进行 6 个测试
- 每个测试都按 ESC
- 记录结果

---

## 🔍 环境检查（可选）

```bash
/tmp/check_terminal_env.sh
```

这会显示：
- 终端类型（TERM）
- 是否在 SSH/tmux/screen 中
- 终端配置（stty）

---

## 📊 快速诊断流程图

```
┌─────────────────────────────┐
│ 运行 test_raw_esc.py       │
│ 并按 ESC 键                 │
└──────────┬──────────────────┘
           │
           ▼
    看到 "这是 ESC 键！" 吗？
           │
     ┌─────┴─────┐
     │           │
    YES         NO
     │           │
     ▼           ▼
 问题在      问题在终端
 questionary     │
     │           ├─ 检查 tmux 配置
     │           ├─ 检查 SSH 设置
     │           └─ 修改终端配置
     │               │
     └───────┬───────┘
             │
             ▼
        使用替代方案
   （添加 q 和 Ctrl+B 键）
```

---

## 💡 立即可用的临时方案

在诊断期间，你可以这样返回：

### 方案 1: Ctrl+C
- 在菜单中按 **Ctrl+C**
- 会显示 "Cancelled by user" 并中断

### 方案 2: "← 返回" 选项
- 导航到 **"← 返回"** 选项
- 按 Enter 选择
- **最可靠的方式**

### 方案 3: 留空（输入框）
- 在输入框中不输入内容
- 直接按 Enter
- 触发留空返回逻辑

---

## 🚀 推荐的终极解决方案

**无论诊断结果如何，我强烈建议实施多键返回方案**：

### 方案：'q' + Ctrl+B + ESC 组合

**优势**:
- ✅ 不依赖单一按键
- ✅ 适配所有终端环境
- ✅ 用户总能找到可用的方式

**包含**:
- **ESC**: 标准返回键（如果能工作）
- **'q' 键**: vim 风格，单键快速（仅选择菜单）
- **Ctrl+B**: 组合键，不会被终端拦截（所有交互）

**实施时间**: 约 1 小时
**代码**: 已经写好在 `/home/ben/gemini-work/gemini-t66y/python/src/utils/keybindings.py`

---

## 📞 需要你做什么

### Step 1: 立即运行测试 1（最关键）

```bash
python3 /tmp/test_raw_esc.py
```

按 ESC，看结果，**告诉我结果**。

### Step 2: 告诉我你想要什么

**选项 A**: 继续诊断 ESC 问题
- 如果你一定要让 ESC 工作
- 可能需要修改终端配置

**选项 B**: 直接实施替代方案（推荐）
- 添加 'q' 和 Ctrl+B 键
- 不依赖 ESC
- 1 小时完成
- **更可靠，更用户友好**

---

## 📝 快速命令参考

```bash
# 最关键的测试
python3 /tmp/test_raw_esc.py

# 其他测试
python3 /tmp/test_questionary_esc_simple.py
python3 /tmp/diagnose_esc_comprehensive.py

# 环境检查
/tmp/check_terminal_env.sh

# 查看所有诊断脚本
ls -la /tmp/test_*.py /tmp/*esc*.sh
```

---

## ⚡ TL;DR（太长不看版）

1. **运行这个** → `python3 /tmp/test_raw_esc.py`
2. **按 ESC**
3. **告诉我结果**
4. 我会根据结果提供精确的解决方案

或者：

**直接告诉我"实施 q + Ctrl+B 方案"，我立即开始（推荐）**

---

**请立即运行测试 1，这是找到解决方案的关键！** 🔍
