# 作者列表选中标记显示功能

**问题**: 用户希望在作者列表表格中直接显示哪些作者上次被选中
**日期**: 2026-02-12

---

## 🔍 问题表现

### 当前状态
作者列表表格**没有**显示上次选中的标记：

```
┏━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ 序号 ┃ 作者名       ┃ 上次更新         ┃ 关注日期   ┃ 帖子数 ┃ 标签               ┃
┡━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│    1 │ 独醉笑清风   │ 02-11 22:58      │ 2026-02-11 │     80 │ synced_from_nodejs │
│    2 │ 清风皓月     │ 02-11 23:19      │ 2026-02-11 │     77 │ synced_from_nodejs │
```

用户需要查看下方的提示才知道上次选择了哪些作者：
```
上次选择了 3 位作者: 纯情母老虎, 厦门一只狼, 我是抵触情绪
```

### 期望效果
在表格**第一列**添加"状态"列，一眼看出哪些作者上次被选中：

```
┏━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ 状态 ┃ 序号 ┃ 作者名       ┃ 上次更新         ┃ 关注日期   ┃ 帖子数 ┃ 标签               ┃
┡━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│  ✅  │    1 │ 独醉笑清风   │ 02-11 22:58      │ 2026-02-11 │     80 │ synced_from_nodejs │
│  ⬜  │    2 │ 清风皓月     │ 02-11 23:19      │ 2026-02-11 │     77 │ synced_from_nodejs │
│  ⬜  │    3 │ 无敌帅哥     │ 02-11 23:46      │ 2026-02-11 │      1 │ synced_from_nodejs │
│  ✅  │    4 │ 纯情母老虎   │ 02-12 16:41      │ 2026-02-12 │     18 │ from_nodejs        │
│  ⬜  │    5 │ 特兰克斯斯   │ 02-12 00:13      │ 2026-02-12 │      1 │ from_nodejs        │
│  ✅  │    6 │ 厦门一只狼   │ 02-12 16:41      │ 2026-02-12 │     70 │ from_nodejs        │
│  ✅  │    7 │ 我是抵触情绪 │ 02-12 16:43      │ 2026-02-12 │     10 │ from_nodejs        │
└──────┴──────┴──────────────┴──────────────────┴────────────┴────────┴────────────────────┘
```

---

## 🔎 代码分析

### 涉及的文件

1. **`python/src/utils/display.py`** (第 34 行)
   - `show_author_table()` 函数：显示作者列表表格
   - 当前不支持显示选中标记

2. **`python/src/menu/main_menu.py`** (第 153 行)
   - `_run_update()` 方法：调用 `show_author_table()`
   - 有 `last_selected` 数据但未传递

### 当前代码

**display.py (第 34-42 行)**:
```python
def show_author_table(authors: List[Dict[str, Any]], show_last_update: bool = True):
    """显示作者列表表格"""
    table = Table(title=f"当前关注 {len(authors)} 位作者")
    table.add_column("序号", style="cyan", justify="right", width=4)
    table.add_column("作者名", style="green")
    # ... 其他列
```

**main_menu.py (第 153 行)**:
```python
show_author_table(self.config['followed_authors'])
```

---

## 💡 解决方案

### 方案：修改 `show_author_table` 函数

#### Step 1: 修改函数签名，添加 `last_selected` 参数

```python
def show_author_table(
    authors: List[Dict[str, Any]],
    show_last_update: bool = True,
    last_selected: List[str] = None  # 新增参数
):
    """显示作者列表表格

    Args:
        authors: 作者列表
        show_last_update: 是否显示上次更新时间
        last_selected: 上次选择的作者名列表（用于显示 ✅/⬜ 标记）
    """
```

#### Step 2: 添加"状态"列（如果提供了 last_selected）

```python
table = Table(title=f"当前关注 {len(authors)} 位作者")

# 如果提供了上次选择的数据，显示状态列
if last_selected:
    table.add_column("状态", justify="center", width=4)

table.add_column("序号", style="cyan", justify="right", width=4)
table.add_column("作者名", style="green")
# ... 其他列
```

#### Step 3: 添加状态标记到行数据

```python
for i, author in enumerate(authors, 1):
    row_data = []

    # 如果提供了上次选择的数据，添加状态标记
    if last_selected:
        if author['name'] in last_selected:
            row_data.append("[green]✅[/green]")
        else:
            row_data.append("[dim]⬜[/dim]")

    row_data.extend([
        str(i),
        author['name'],
        # ... 其他数据
    ])

    table.add_row(*row_data)
```

#### Step 4: 修改调用方（main_menu.py）

```python
# 获取上次选择的作者名列表
last_selected = self.config.get('user_preferences', {}).get('last_selected_authors', [])

# 传递 last_selected 参数
show_author_table(
    self.config['followed_authors'],
    last_selected=last_selected if last_selected else None
)
```

---

## 📋 实施步骤

### Step 1: 修改 `display.py`

```python
def show_author_table(
    authors: List[Dict[str, Any]],
    show_last_update: bool = True,
    last_selected: List[str] = None
):
    """显示作者列表表格

    Args:
        authors: 作者列表
        show_last_update: 是否显示上次更新时间
        last_selected: 上次选择的作者名列表（用于显示标记）
    """
    table = Table(title=f"当前关注 {len(authors)} 位作者")

    # 如果提供了上次选择的数据，添加状态列
    if last_selected:
        table.add_column("状态", justify="center", width=4)

    table.add_column("序号", style="cyan", justify="right", width=4)
    table.add_column("作者名", style="green")

    if show_last_update:
        table.add_column("上次更新", style="yellow", width=16)

    table.add_column("关注日期", style="magenta", width=10)
    table.add_column("帖子数", justify="right", width=6)
    table.add_column("标签", style="dim")

    for i, author in enumerate(authors, 1):
        row_data = []

        # 添加状态标记（如果提供了 last_selected）
        if last_selected:
            if author['name'] in last_selected:
                row_data.append("[green]✅[/green]")
            else:
                row_data.append("[dim]⬜[/dim]")

        row_data.append(str(i))
        row_data.append(author['name'])

        if show_last_update:
            last_update = author.get('last_update', 'N/A')
            # 格式化时间：2026-02-11 22:28:01 -> 02-11 22:28
            if last_update and last_update != 'N/A':
                try:
                    last_update = last_update[5:16]
                except:
                    pass
            row_data.append(last_update)

        row_data.extend([
            author.get('added_date', 'N/A'),
            str(author.get('total_posts', 0)),
            ', '.join(author.get('tags', []))
        ])

        table.add_row(*row_data)

    console.print(table)
```

### Step 2: 修改 `main_menu.py` 的调用

找到第 153 行，修改为：

```python
# Phase 2-B 需求 1: 显示作者列表（带上次选择标记）
self.console.print("[cyan]当前关注的作者:[/cyan]\n")

# 获取上次选择的作者名列表
last_selected = self.config.get('user_preferences', {}).get('last_selected_authors', [])

# 传递 last_selected 参数，显示选中标记
show_author_table(
    self.config['followed_authors'],
    last_selected=last_selected if last_selected else None
)
```

---

## 🧪 测试用例

### Test 1: 首次运行（无上次选择）

**场景**: 第一次使用，`last_selected_authors` 为空

**预期**:
- 表格**不显示**"状态"列
- 显示原有的列：序号、作者名、上次更新等

### Test 2: 有上次选择

**场景**: `last_selected_authors = ['纯情母老虎', '厦门一只狼', '我是抵触情绪']`

**预期**:
- 表格**显示**"状态"列（第一列）
- 选中的作者显示 ✅（绿色）
- 未选中的作者显示 ⬜（灰色）
- 其他列正常显示

### Test 3: 部分作者被取消关注

**场景**: 上次选择了 3 个作者，但其中 1 个已被取消关注

**预期**:
- 只显示当前关注列表中的作者
- 已取消关注的作者不显示
- 状态标记正常工作

---

## 🎯 效果对比

### 修改前 ❌
```
用户看到表格
↓
看到下方文本提示："上次选择了 3 位作者: xxx, xxx, xxx"
↓
需要手动对比作者名
```

### 修改后 ✅
```
用户看到表格（第一列有 ✅/⬜ 标记）
↓
一眼看出哪些作者上次被选中
↓
无需额外对比
```

---

## 📝 注意事项

1. **向下兼容**: `last_selected` 参数是可选的，不传递时表现与原来一致
2. **性能影响**: 很小，只是简单的列表成员检查
3. **UI 一致性**: 状态标记与后续的汇总表格一致（都是 ✅/⬜）

---

## 🚀 后续优化（可选）

1. **高亮选中行**: 除了 ✅ 标记，还可以高亮整行
2. **显示选中数量**: 标题改为"当前关注 7 位作者（上次选择 3 位）"
3. **排序优化**: 将选中的作者排在前面

---

**预计工作量**: 10 分钟
**优先级**: P1（用户体验改进）
**风险**: 低
