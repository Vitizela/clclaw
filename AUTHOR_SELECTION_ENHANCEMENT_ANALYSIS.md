# 作者选择增强分析文档

**日期**: 2026-02-12
**需求来源**: 用户反馈
**优先级**: P1（用户体验改进）

---

## 📋 需求概述

### 需求 1: 选中作者的视觉标记
**用户需求**: 在"立即更新所有作者的列表"中，能够看到被选中的作者，请加上标记

**当前问题**:
- 作者表格显示在选择之前（line 152-154）
- checkbox 界面有选中指示，但不够直观
- 选择完成后没有可视化的确认反馈

### 需求 2: 按帖子数量下载
**用户需求**: 在"选择下载页数"菜单中，增加选择要下载的帖子数量，不只是页数

**用户痛点**:
- 有些作者只有 1 页，但已经有很多数据（例如 50+ 篇）
- 按页数选择不够精确
- 用户想控制"下载多少篇帖子"而不是"下载多少页"

---

## 🔍 当前实现分析

### 当前流程 (main_menu.py:142-316)

```
1. 显示作者表格（所有作者）
   ↓
2. 智能选择菜单
   - 使用上次选择
   - 重新选择
   - 更新所有
   ↓
3. [如果重新选择] checkbox 多选界面
   ↓
4. 选择下载页数
   - 1, 3, 5, 10 页
   - 全部页面
   - 自定义页数
   ↓
5. 执行更新
```

### 代码关键点

#### 1. 作者表格显示 (line 152-154)
```python
self.console.print("[cyan]当前关注的作者:[/cyan]\n")
show_author_table(self.config['followed_authors'])  # ← 显示所有作者，无标记
self.console.print()
```

#### 2. Checkbox 选择 (line 221-226)
```python
selected_authors = checkbox_with_keybindings(
    "请选择要更新的作者（Space 勾选，Enter 确认，ESC 返回）:",
    choices=author_choices,  # ← questionary.Choice 对象
    style=self.custom_style,  # ← 'selected' 样式为橙黄色
    validate=lambda x: x is None or len(x) > 0 or "至少选择一位作者"
)
```

**questionary 的默认视觉指示**:
- `[X]` = 已勾选
- `[ ]` = 未勾选
- 橙黄色高亮 = 已选中项（'selected' style）

#### 3. 页数选择 (line 234-267)
```python
page_options = select_with_keybindings(
    "选择下载页数:",
    choices=[
        questionary.Choice("📄 仅第 1 页（约 50 篇，推荐测试）", value=1),
        questionary.Choice("📄 前 3 页（约 150 篇）", value=3),
        # ... 其他选项
        questionary.Choice("⚙️  自定义页数", value='custom'),
    ],
    style=self.custom_style,
    default=1
)
```

**当前限制**:
- 只支持按页数 (max_pages)
- 估算的帖子数量（约 50 篇/页）不准确
- 无法精确控制帖子数量

---

## 💡 解决方案设计

### 方案 1: 选中作者标记 ✅ 推荐

#### 方案 1.1: 选择后显示确认表格 ⭐⭐⭐⭐⭐
**实现方式**: 在用户完成 checkbox 选择后，重新显示一个标记版的表格

**优点**:
- 清晰明确，用户可以看到选择结果
- 不干扰 questionary 的原生交互
- 易于实现，无需修改底层组件

**实现细节**:
```python
# Line 231 后添加

# 显示选中的作者（带标记）
self.console.print(f"\n[green]✓ 已选择 {len(selected_authors)} 位作者:[/green]\n")

# 创建对比表格：显示所有作者，标记选中的
from rich.table import Table
table = Table(show_header=True, header_style="bold cyan")
table.add_column("状态", justify="center", width=6)
table.add_column("作者名", style="cyan")
table.add_column("帖子数", justify="right")
table.add_column("最后更新", style="dim")

selected_names = {author['name'] for author in selected_authors}

for author in self.config['followed_authors']:
    status = "[green]✅[/green]" if author['name'] in selected_names else "[dim]⬜[/dim]"
    name = author['name']
    total_posts = author.get('total_posts', 0)
    last_update = author.get('last_update', '从未')

    table.add_row(
        status,
        name,
        str(total_posts) if total_posts > 0 else "-",
        last_update if last_update else "-"
    )

self.console.print(table)
self.console.print()
```

**视觉效果**:
```
✓ 已选择 2 位作者:

┏━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┓
┃ 状态 ┃ 作者名 ┃ 帖子数 ┃ 最后更新   ┃
┡━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━┩
│  ✅  │ 张三   │    150 │ 2026-02-11 │  ← 选中
│  ⬜  │ 李四   │     80 │ 2026-02-10 │
│  ✅  │ 王五   │    200 │ 2026-02-12 │  ← 选中
└──────┴────────┴────────┴────────────┘
```

#### 方案 1.2: 增强 checkbox 显示 ⭐⭐⭐
**实现方式**: 在 checkbox choice 的 title 中添加更明显的前缀

**实现细节**:
```python
# Line 199-219 修改
for author in self.config['followed_authors']:
    label = f"{author['name']}"
    total_posts = author.get('total_posts', 0)
    if total_posts > 0:
        label += f" ({total_posts} 篇)"

    # 检查是否在上次选择中
    if last_selected:
        checked = author['name'] in last_selected
        if checked:
            label = f"✅ {label}"  # ← 添加前缀标记
    else:
        checked = True
        label = f"✅ {label}"  # ← 默认全选，都添加标记

    author_choices.append(
        questionary.Choice(title=label, value=author, checked=checked)
    )
```

**视觉效果**:
```
请选择要更新的作者（Space 勾选，Enter 确认，ESC 返回）:
 ❯ [X] ✅ 张三 (150 篇)
   [ ] 李四 (80 篇)
   [X] ✅ 王五 (200 篇)
```

**缺点**:
- 前缀 ✅ 会一直显示，即使取消勾选后（questionary 不会动态更新 title）
- 可能造成混淆

#### 方案 1.3: 选择前显示预选状态 ⭐⭐
**实现方式**: 在 checkbox 之前，如果有 last_selected，先显示一个预览表格

**优点**:
- 用户可以看到"将要被选中"的作者

**缺点**:
- 增加了界面复杂度
- 如果用户修改选择，表格就不准确了

---

### 方案 2: 按帖子数量下载 ✅ 推荐

#### 方案 2.1: 混合选择模式（推荐） ⭐⭐⭐⭐⭐

**实现方式**: 增加一个顶层选择："按页数" 还是 "按帖子数"

**流程设计**:
```
选择下载方式:
  1. 📄 按页数限制（快速，推荐）
  2. 📊 按帖子数量限制（精确）
  3. ← 返回

[如果选择 1] → 现有的页数菜单
[如果选择 2] → 新的帖子数量菜单
```

**新的帖子数量菜单**:
```python
post_count_options = select_with_keybindings(
    "选择下载帖子数量:",
    choices=[
        questionary.Choice("📝 前 50 篇（推荐测试）", value=50),
        questionary.Choice("📝 前 100 篇", value=100),
        questionary.Choice("📝 前 200 篇", value=200),
        questionary.Choice("📝 前 500 篇", value=500),
        questionary.Choice("📚 全部帖子", value=None),
        questionary.Choice("⚙️  自定义数量", value='custom'),
        questionary.Choice("← 返回", value='cancel'),
    ],
    style=self.custom_style,
    default=50
)
```

**参数传递**:
```python
# 修改 _run_python_scraper 签名
async def _run_python_scraper(
    self,
    selected_authors: list = None,
    max_pages: int = None,
    max_posts: int = None,  # ← 新增参数
    mode: str = 'pages'      # ← 'pages' 或 'posts'
) -> None:
```

**scraper.archiver.py 修改**:
```python
# ForumArchiver.archive_author 需要支持 max_posts
async def archive_author(
    self,
    author_name: str,
    author_url: str,
    max_pages: int = None,
    max_posts: int = None  # ← 新增参数
) -> dict:
    """归档作者的所有帖子

    Args:
        max_pages: 最大页数限制（None = 无限制）
        max_posts: 最大帖子数限制（None = 无限制）

    逻辑: 如果同时提供，以先达到的限制为准
    """
    # 在 collect_post_urls 中添加计数逻辑
    post_urls = await self.extractor.collect_post_urls(
        author_url,
        max_pages=max_pages,
        max_posts=max_posts  # ← 传递参数
    )
```

**extractor.py 修改**:
```python
async def collect_post_urls(
    self,
    author_url: str,
    max_pages: Optional[int] = None,
    max_posts: Optional[int] = None  # ← 新增参数
) -> List[str]:
    """收集作者的所有帖子 URL"""
    post_urls = []
    page_num = 1

    while True:
        # 检查页数限制
        if max_pages and page_num > max_pages:
            break

        # 检查帖子数限制
        if max_posts and len(post_urls) >= max_posts:
            self.logger.info(f"已达到帖子数限制 ({max_posts} 篇)")
            break

        # ... 提取当前页的帖子 ...

        # 如果有帖子数限制，只添加需要的数量
        if max_posts:
            remaining = max_posts - len(post_urls)
            for link in links[:remaining]:  # ← 限制添加数量
                # ... 添加到 post_urls ...
        else:
            # 无限制，添加全部
            for link in links:
                # ... 添加到 post_urls ...

        page_num += 1
```

**优点**:
- ✅ 精确控制下载数量
- ✅ 适合"只有1页但很多帖子"的情况
- ✅ 保留原有的按页数选择（向后兼容）
- ✅ 逻辑清晰，用户可以选择适合自己的方式

**缺点**:
- 增加了菜单层级（但通过清晰的选项可以缓解）
- 需要修改 extractor 和 archiver 的逻辑

#### 方案 2.2: 仅增加帖子数选项 ⭐⭐⭐
**实现方式**: 在现有的页数菜单中直接添加帖子数选项

**修改后的菜单**:
```python
choices=[
    # 页数选项
    questionary.Choice("📄 按页数: 仅第 1 页", value=('pages', 1)),
    questionary.Choice("📄 按页数: 前 3 页", value=('pages', 3)),
    questionary.Choice("📄 按页数: 前 5 页", value=('pages', 5)),
    questionary.Choice("📄 按页数: 自定义", value=('pages', 'custom')),

    # 帖子数选项（新增）
    questionary.Choice("📝 按数量: 前 50 篇", value=('posts', 50)),
    questionary.Choice("📝 按数量: 前 100 篇", value=('posts', 100)),
    questionary.Choice("📝 按数量: 前 200 篇", value=('posts', 200)),
    questionary.Choice("📝 按数量: 自定义", value=('posts', 'custom')),

    # 全部
    questionary.Choice("📚 全部内容", value=('all', None)),
    questionary.Choice("← 返回", value=('cancel', None)),
]
```

**优点**:
- 单个菜单，选择更快
- 选项一目了然

**缺点**:
- 菜单选项过多（10+ 项），可能导致视觉疲劳
- 混合两种模式可能造成混淆

#### 方案 2.3: 智能建议 ⭐⭐⭐⭐
**实现方式**: 先快速查询第一页，根据实际情况提供建议

**流程**:
```
1. 快速获取第一页
   ↓
2. 分析帖子数量
   - 如果 ≤ 30 篇 → 建议"全部下载（只有X篇）"
   - 如果 > 30 篇 → 提供页数和帖子数选项
   ↓
3. 用户选择
```

**优点**:
- 智能化，根据实际情况调整
- 避免不必要的选择

**缺点**:
- 增加了初始延迟（需要预先查询）
- 实现复杂度较高
- 如果网络慢，体验不好

---

## 📊 方案对比

### 需求 1: 选中作者标记

| 方案 | 清晰度 | 实现难度 | 用户体验 | 推荐度 |
|------|--------|---------|---------|--------|
| **1.1 选择后确认表格** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ 强烈推荐 |
| 1.2 增强 checkbox 显示 | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | 可选 |
| 1.3 选择前预览 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 不推荐 |

**推荐组合**: **方案 1.1**（选择后显示带标记的确认表格）

### 需求 2: 按帖子数量下载

| 方案 | 灵活性 | 实现难度 | 用户体验 | 性能 | 推荐度 |
|------|--------|---------|---------|------|--------|
| **2.1 混合选择模式** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ 强烈推荐 |
| 2.2 单菜单混合 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 可选 |
| 2.3 智能建议 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 可选优化 |

**推荐组合**: **方案 2.1**（混合选择模式）+ **可选优化 2.3**（智能建议）

---

## 🎯 最终推荐方案

### 推荐实现: 方案 1.1 + 方案 2.1

#### 阶段 1: 选中作者标记（方案 1.1）
**修改文件**: `python/src/menu/main_menu.py`

**修改位置**: Line 231 后添加

**代码变更**:
```python
# Line 231 后添加
self.console.print(f"\n[green]✓ 已选择 {len(selected_authors)} 位作者:[/green]\n")

# 显示选中作者的对比表格
self._show_selection_summary(selected_authors)
self.console.print()
```

**新增方法**:
```python
def _show_selection_summary(self, selected_authors: list) -> None:
    """显示选中作者的汇总表格（带标记）

    Args:
        selected_authors: 用户选择的作者列表
    """
    from rich.table import Table

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("状态", justify="center", width=6)
    table.add_column("作者名", style="cyan")
    table.add_column("帖子数", justify="right")
    table.add_column("最后更新", style="dim")

    selected_names = {author['name'] for author in selected_authors}

    for author in self.config['followed_authors']:
        if author['name'] in selected_names:
            status = "[green]✅[/green]"
            name_style = "[bold cyan]"
        else:
            status = "[dim]⬜[/dim]"
            name_style = "[dim]"

        name = f"{name_style}{author['name']}[/]"
        total_posts = author.get('total_posts', 0)
        last_update = author.get('last_update', '从未')

        table.add_row(
            status,
            name,
            str(total_posts) if total_posts > 0 else "-",
            last_update if last_update else "-"
        )

    self.console.print(table)
```

**预期效果**: 用户选择完成后，看到带有 ✅ 标记的清晰表格

---

#### 阶段 2: 按帖子数量下载（方案 2.1）

**修改文件**:
1. `python/src/menu/main_menu.py` - 增加菜单选项和参数处理
2. `python/src/scraper/archiver.py` - 支持 max_posts 参数
3. `python/src/scraper/extractor.py` - 在 collect_post_urls 中添加帖子数限制

**Step 1: 菜单修改 (main_menu.py)**

**Line 233-267 替换为**:
```python
# 第一层：选择限制方式
download_mode = select_with_keybindings(
    "选择下载限制方式:",
    choices=[
        questionary.Choice("📄 按页数限制（快速，推荐测试）", value='pages'),
        questionary.Choice("📊 按帖子数量限制（精确控制）", value='posts'),
        questionary.Choice("📚 下载全部内容", value='all'),
        questionary.Choice("← 返回", value='cancel'),
    ],
    style=self.custom_style,
    default='pages'
)

if download_mode is None or download_mode == 'cancel':
    return

max_pages = None
max_posts = None

# 按页数限制
if download_mode == 'pages':
    page_options = select_with_keybindings(
        "选择下载页数:",
        choices=[
            questionary.Choice("📄 仅第 1 页（约 50 篇，推荐测试）", value=1),
            questionary.Choice("📄 前 3 页（约 150 篇）", value=3),
            questionary.Choice("📄 前 5 页（约 250 篇）", value=5),
            questionary.Choice("📄 前 10 页（约 500 篇）", value=10),
            questionary.Choice("⚙️  自定义页数", value='custom'),
            questionary.Choice("← 返回", value='cancel'),
        ],
        style=self.custom_style,
        default=1
    )

    if page_options is None or page_options == 'cancel':
        return

    if page_options == 'custom':
        custom_pages = text_with_keybindings(
            "请输入页数（正整数）:",
            validate=lambda x: x is None or (x.isdigit() and int(x) > 0) or "请输入正整数",
            style=self.custom_style
        )
        if custom_pages is None:
            return
        max_pages = int(custom_pages)
    else:
        max_pages = page_options

# 按帖子数量限制
elif download_mode == 'posts':
    post_options = select_with_keybindings(
        "选择下载帖子数量:",
        choices=[
            questionary.Choice("📝 前 50 篇（推荐测试）", value=50),
            questionary.Choice("📝 前 100 篇", value=100),
            questionary.Choice("📝 前 200 篇", value=200),
            questionary.Choice("📝 前 500 篇", value=500),
            questionary.Choice("⚙️  自定义数量", value='custom'),
            questionary.Choice("← 返回", value='cancel'),
        ],
        style=self.custom_style,
        default=50
    )

    if post_options is None or post_options == 'cancel':
        return

    if post_options == 'custom':
        custom_posts = text_with_keybindings(
            "请输入帖子数量（正整数）:",
            validate=lambda x: x is None or (x.isdigit() and int(x) > 0) or "请输入正整数",
            style=self.custom_style
        )
        if custom_posts is None:
            return
        max_posts = int(custom_posts)
    else:
        max_posts = post_options

# 全部内容
elif download_mode == 'all':
    max_pages = None
    max_posts = None

# 显示确认信息
if max_pages:
    limit_desc = f"前 {max_pages} 页"
elif max_posts:
    limit_desc = f"前 {max_posts} 篇帖子"
else:
    limit_desc = "全部内容"

self.console.print(
    f"\n[cyan]将为 {len(selected_authors)} 位作者下载 {limit_desc}[/cyan]\n"
)
```

**Step 2: 修改 _run_python_scraper 签名 (Line 318-321)**:
```python
async def _run_python_scraper(
    self,
    selected_authors: list = None,
    max_pages: int = None,
    max_posts: int = None  # ← 新增参数
) -> None:
```

**Step 3: 传递参数 (Line 364)**:
```python
result = await archiver.archive_author(
    author_name,
    author_url,
    max_pages=max_pages,
    max_posts=max_posts  # ← 传递参数
)
```

**Step 4: 修改 archiver.py**:
```python
async def archive_author(
    self,
    author_name: str,
    author_url: str,
    max_pages: Optional[int] = None,
    max_posts: Optional[int] = None  # ← 新增参数
) -> dict:
    """归档作者的所有帖子

    Args:
        max_pages: 最大页数限制（None = 无限制）
        max_posts: 最大帖子数限制（None = 无限制）
    """
    # ...

    # 阶段一：收集所有帖子 URL
    post_urls = await self.extractor.collect_post_urls(
        author_url,
        max_pages=max_pages,
        max_posts=max_posts  # ← 传递参数
    )
```

**Step 5: 修改 extractor.py**:
```python
async def collect_post_urls(
    self,
    author_url: str,
    max_pages: Optional[int] = None,
    max_posts: Optional[int] = None  # ← 新增参数
) -> List[str]:
    """收集作者的所有帖子 URL

    Args:
        max_pages: 最大页数限制
        max_posts: 最大帖子数限制（优先于 max_pages）
    """
    self.logger.info(f"开始收集帖子列表: {author_url}")

    # 显示限制信息
    if max_posts:
        self.logger.info(f"限制: 最多收集 {max_posts} 篇帖子")
    elif max_pages:
        self.logger.info(f"限制: 最多收集 {max_pages} 页")

    post_urls = []
    page_num = 1

    while True:
        # 检查帖子数限制（优先）
        if max_posts and len(post_urls) >= max_posts:
            self.logger.info(f"已达到帖子数限制: {len(post_urls)} 篇")
            break

        # 检查页数限制
        if max_pages and page_num > max_pages:
            self.logger.info(f"已达到页数限制: {page_num-1} 页")
            break

        # ... 获取当前页 ...

        # 提取链接
        links = await self.page.query_selector_all('#tbody tr .bl a')

        if not links:
            self.logger.info(f"第 {page_num} 页无更多帖子")
            break

        # 添加链接（考虑帖子数限制）
        for link in links:
            if max_posts and len(post_urls) >= max_posts:
                break  # ← 达到限制，停止添加

            href = await link.get_attribute('href')
            if href:
                full_url = self.base_url + href
                post_urls.append(full_url)

        self.logger.info(f"第 {page_num} 页: 收集 {len(links)} 篇帖子（累计 {len(post_urls)} 篇）")

        # 如果已达到帖子数限制，退出
        if max_posts and len(post_urls) >= max_posts:
            break

        # 检查下一页
        next_page = await self.page.query_selector('.pages .next')
        if not next_page:
            break

        page_num += 1
        await asyncio.sleep(0.5)

    self.logger.info(f"收集完成，共 {len(post_urls)} 篇帖子")
    return post_urls
```

---

## 🧪 测试计划

### 测试 1: 选中作者标记
```bash
cd python && python main.py
# 选择 [3] 立即更新
# 选择部分作者（不是全部）
# 确认后检查是否显示带 ✅ 标记的表格
```

**预期结果**:
- ✅ 表格显示所有作者
- ✅ 选中的作者有绿色 ✅ 标记
- ✅ 未选中的作者有灰色 ⬜ 标记

### 测试 2: 按页数下载
```bash
cd python && python main.py
# 选择 [3] 立即更新
# 选择"按页数限制"
# 选择"仅第 1 页"
# 确认下载
```

**预期结果**:
- ✅ 只下载第 1 页的帖子

### 测试 3: 按帖子数下载
```bash
cd python && python main.py
# 选择 [3] 立即更新
# 选择"按帖子数量限制"
# 选择"前 50 篇"
# 确认下载
```

**预期结果**:
- ✅ 只下载前 50 篇帖子（可能跨多页）
- ✅ 日志显示"已达到帖子数限制: 50 篇"

### 测试 4: 自定义数量
```bash
# 输入自定义数量: 75
```

**预期结果**:
- ✅ 下载前 75 篇帖子

### 测试 5: 全部内容
```bash
# 选择"下载全部内容"
```

**预期结果**:
- ✅ 下载所有帖子（无限制）

---

## 📝 实现清单

### 阶段 1: 选中作者标记（简单）
- [ ] 修改 `main_menu.py` Line 231 后添加调用
- [ ] 新增 `_show_selection_summary()` 方法
- [ ] 测试验证

**预计耗时**: 30 分钟

### 阶段 2: 按帖子数量下载（中等）
- [ ] 修改 `main_menu.py` 菜单流程（Line 233-267）
- [ ] 修改 `_run_python_scraper()` 签名和调用
- [ ] 修改 `archiver.py` 的 `archive_author()` 方法
- [ ] 修改 `extractor.py` 的 `collect_post_urls()` 方法
- [ ] 测试验证

**预计耗时**: 2-3 小时

### 总预计耗时: 3-4 小时

---

## 🔄 向后兼容性

### 保持兼容
- ✅ 不影响 Node.js 桥接模式（Node.js 仍使用旧逻辑）
- ✅ max_posts 为可选参数，默认 None（无限制）
- ✅ 现有代码不调用 max_posts 时，行为不变

### 配置迁移
- 无需修改 config.yaml
- 所有参数在运行时确定

---

## 🎨 用户体验改进

### 改进 1: 清晰的视觉反馈
**之前**: 选择作者后只显示 "已选择 2 位作者"
**之后**: 显示带标记的完整表格，一目了然

### 改进 2: 精确控制下载量
**之前**: 只能按页数，无法精确控制
**之后**: 可以选择"我只想下载 100 篇帖子"

### 改进 3: 灵活的选择模式
**之前**: 单一的页数限制
**之后**: 页数、帖子数、全部三种模式自由选择

---

## 📚 相关文档

- **KEYBOARD_SHORTCUTS_GUIDE.md** - 快捷键使用指南
- **PHASE2_DESIGN_SUPPLEMENT.md** - Phase 2 设计补充
- **main_menu.py** - 主菜单实现

---

**分析完成，等待用户确认后开始实施！**
