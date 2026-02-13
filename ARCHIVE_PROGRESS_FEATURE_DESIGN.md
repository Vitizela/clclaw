# 归档进度显示功能 - 详细设计文档

**功能代号**: FEAT-ARCHIVE-PROGRESS
**版本**: v1.0
**创建日期**: 2026-02-12
**设计者**: Claude AI
**审批状态**: 待审批

---

## 📋 文档目的

本文档提供归档进度显示功能的完整技术设计，面向AI自动化编程实现。
每个步骤都提供清晰的：
- 输入条件
- 输出结果
- 验收标准
- 回滚方案

---

## 🎯 需求概述

### 用户需求

**当前问题**:
- 作者列表显示"帖子数"，含义不清（是论坛总数？还是已归档数？）
- 用户无法知道归档完成度
- 无法评估是否需要继续更新

**期望效果**:
```
┏━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ 状态 ┃ 序号 ┃ 作者名       ┃ 上次更新         ┃ 关注日期   ┃ 归档进度         ┃ 标签               ┃
┡━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│  ⬜  │    1 │ 独醉笑清风   │ 02-11 22:58      │ 2026-02-11 │ 80/120 (67%)     │ synced_from_nodejs │
│  ⬜  │    2 │ 清风皓月     │ 02-11 23:19      │ 2026-02-11 │ 77/150 (51%)     │ synced_from_nodejs │
│  ✅  │    3 │ 无敌帅哥     │ 02-12 16:56      │ 2026-02-11 │ 2/2 (100%) ✓     │ synced_from_nodejs │
└──────┴──────┴──────────────┴──────────────────┴────────────┴──────────────────┴────────────────────┘
```

**信息展示**:
- `80/120` - 已归档/论坛总数
- `(67%)` - 百分比
- `✓` - 100%完成标记

---

## 🏗️ 技术架构

### 系统层次

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层 (UI)                       │
│                  display.py: show_author_table()        │
└─────────────────────────────────────────────────────────┘
                            ↑
                            │ 格式化显示
                            │
┌─────────────────────────────────────────────────────────┐
│                    业务逻辑层 (BL)                       │
│              main_menu.py: 菜单交互和流程控制             │
└─────────────────────────────────────────────────────────┘
                            ↑
                            │ 数据获取和更新
                            │
┌─────────────────────────────────────────────────────────┐
│                    数据访问层 (DAL)                      │
│  extractor.py: 爬取论坛数据                              │
│  manager.py: 配置文件读写                                │
└─────────────────────────────────────────────────────────┘
                            ↑
                            │ 持久化
                            │
┌─────────────────────────────────────────────────────────┐
│                    数据存储层 (Data)                     │
│                   config.yaml: 配置存储                  │
└─────────────────────────────────────────────────────────┘
```

### 数据流向

```
[论坛网站]
    ↓ HTTP请求
[Playwright浏览器]
    ↓ HTML解析
[PostExtractor.get_author_total_posts()]
    ↓ 返回总帖子数
[ConfigManager.save()]
    ↓ 写入
[config.yaml]
    ↓ 读取
[MainMenu._run_update()]
    ↓ 传递数据
[display.show_author_table()]
    ↓ 渲染
[用户终端显示]
```

---

## 📊 数据结构设计

### 配置文件结构 (config.yaml)

#### 当前结构（v2.6）
```yaml
followed_authors:
  - name: "独醉笑清风"
    url: "https://t66y.com/htm_data/7/2402/..."
    added_date: "2026-02-11"
    last_update: "2026-02-11 22:58:01"
    total_posts: 80                    # 已归档数
    tags: ["synced_from_nodejs"]
```

#### 新增字段（v2.7）
```yaml
followed_authors:
  - name: "独醉笑清风"
    url: "https://t66y.com/htm_data/7/2402/..."
    added_date: "2026-02-11"
    last_update: "2026-02-11 22:58:01"
    total_posts: 80                        # 已归档数（保持不变）
    forum_total_posts: 120                 # 新增：论坛总帖子数
    forum_stats_updated: "2026-02-12"      # 新增：论坛数据获取时间
    tags: ["synced_from_nodejs"]
```

#### 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `name` | string | ✅ | - | 作者名 |
| `url` | string | ✅ | - | 作者主页URL |
| `added_date` | string | ✅ | - | 关注日期（YYYY-MM-DD） |
| `last_update` | string | ❌ | null | 上次归档时间（YYYY-MM-DD HH:MM:SS） |
| `total_posts` | integer | ✅ | 0 | 已归档的帖子数（累计） |
| `forum_total_posts` | integer | ❌ | null | **新增**：论坛总帖子数 |
| `forum_stats_updated` | string | ❌ | null | **新增**：论坛数据获取时间（YYYY-MM-DD） |
| `tags` | array | ✅ | [] | 标签列表 |

#### 向下兼容性

**兼容策略**:
- 旧数据：`forum_total_posts` 为 `null` 或不存在
- 显示逻辑：检查 `forum_total_posts`，如果为 `null` 则只显示已归档数
- 自动升级：下次更新时自动获取论坛总数

**示例**:
```yaml
# 旧数据（v2.6）
- name: "独醉笑清风"
  total_posts: 80
  # forum_total_posts 不存在

# 显示结果
┃ 归档进度 ┃
│   80     │  ← 只显示已归档数，无法计算百分比

# 首次更新后自动升级为新格式（v2.7）
- name: "独醉笑清风"
  total_posts: 82
  forum_total_posts: 120
  forum_stats_updated: "2026-02-12"

# 显示结果
┃ 归档进度         ┃
│ 82/120 (68%)     │  ← 显示完整进度
```

---

## 🔧 技术实现方案

### 方案选择

#### 方案A: 实时爬取（不推荐）❌
- 每次显示表格时爬取论坛总数
- **缺点**: 慢、频繁请求、可能被封IP

#### 方案B: 缓存 + 定期刷新（推荐）✅
- 关注作者时获取并缓存
- 定期刷新（默认7天）
- 手动刷新选项

**选择**: 方案B

---

### 核心功能模块

#### 模块1: 论坛数据爬取

**文件**: `python/src/scraper/extractor.py`

**新增方法**:
```python
async def get_author_total_posts(self, author_url: str) -> Optional[int]:
    """获取作者在论坛的总帖子数

    Args:
        author_url: 作者主页URL

    Returns:
        int: 论坛总帖子数，失败返回 None

    Example:
        >>> extractor = PostExtractor(...)
        >>> total = await extractor.get_author_total_posts("https://...")
        >>> print(total)  # 120
    """
```

**实现逻辑**:
```
1. 访问作者主页（author_url）
2. 等待页面加载（domcontentloaded）
3. 查找包含帖子统计的元素
4. 提取总帖子数
5. 返回整数值
```

**HTML结构分析**（需要确认）:
```html
<!-- 假设的HTML结构，实际需要检查论坛页面 -->
<div class="author-stats">
    <span>主题数: <strong>120</strong></span>
    <span>回复数: <strong>3456</strong></span>
</div>
```

**选择器策略**:
```python
# 策略1: 直接选择器
selector = '.author-stats strong'

# 策略2: 文本匹配
text_content = page.text_content()
match = re.search(r'主题数[:\s]+(\d+)', text_content)

# 策略3: 多个候选选择器（fallback）
selectors = [
    '.author-stats strong',
    '.post-count',
    '[data-posts]'
]
```

**错误处理**:
- 页面加载超时 → 返回 `None`
- 选择器未找到 → 返回 `None`
- 解析失败 → 返回 `None`
- 记录错误日志

---

#### 模块2: 数据存储和管理

**文件**: `python/src/config/manager.py`

**修改方法**: `follow_author()`

**新增逻辑**:
```python
# 关注作者时获取论坛总数
async def follow_author(self, name: str, url: str) -> Dict[str, Any]:
    """关注新作者

    新增功能:
    - 获取论坛总帖子数
    - 记录获取时间
    """
    # 原有逻辑 ...

    # 新增：获取论坛总数
    forum_total = await self._get_forum_total_posts(url)

    author_data = {
        'name': name,
        'url': url,
        'added_date': datetime.now().strftime('%Y-%m-%d'),
        'total_posts': 0,
        'forum_total_posts': forum_total,  # 新增
        'forum_stats_updated': datetime.now().strftime('%Y-%m-%d') if forum_total else None,  # 新增
        'tags': []
    }

    return author_data
```

**新增配置项** (config.yaml):
```yaml
advanced:
  refresh_forum_stats: true       # 是否自动刷新论坛统计
  forum_stats_refresh_days: 7     # 刷新间隔（天）
  forum_stats_timeout: 30         # 获取超时（秒）
```

---

#### 模块3: 显示逻辑

**文件**: `python/src/utils/display.py`

**修改方法**: `show_author_table()`

**当前签名**:
```python
def show_author_table(
    authors: List[Dict[str, Any]],
    show_last_update: bool = True,
    last_selected: List[str] = None
):
```

**保持不变**（无需修改签名）

**修改内容**:

```python
# 第59行：修改列名
table.add_column("归档进度", justify="right", width=18)  # 原来是"帖子数", width=6

# 第85-89行：修改显示逻辑
row_data.extend([
    author.get('added_date', 'N/A'),
    format_archive_progress(author),  # 新增函数
    ', '.join(author.get('tags', []))
])
```

**新增辅助函数**:
```python
def format_archive_progress(author: Dict[str, Any]) -> str:
    """格式化归档进度显示

    Args:
        author: 作者数据字典

    Returns:
        格式化的进度字符串

    Examples:
        >>> author = {'total_posts': 80, 'forum_total_posts': 120}
        >>> format_archive_progress(author)
        '80/120 (67%)'

        >>> author = {'total_posts': 80, 'forum_total_posts': None}
        >>> format_archive_progress(author)
        '80'

        >>> author = {'total_posts': 50, 'forum_total_posts': 50}
        >>> format_archive_progress(author)
        '50/50 (100%) ✓'
    """
    archived = author.get('total_posts', 0)
    forum_total = author.get('forum_total_posts')

    # 情况1: 没有论坛总数数据（旧数据或获取失败）
    if forum_total is None or forum_total == 0:
        return str(archived)

    # 情况2: 有论坛总数数据
    percentage = int((archived / forum_total) * 100) if forum_total > 0 else 0

    # 情况3: 已完整归档（100%）
    if percentage >= 100:
        return f"{archived}/{forum_total} (100%) ✓"

    # 情况4: 部分归档
    return f"{archived}/{forum_total} ({percentage}%)"
```

**边界情况处理**:

| 场景 | archived | forum_total | 显示结果 | 说明 |
|------|----------|-------------|----------|------|
| 旧数据 | 80 | None | `80` | 向下兼容 |
| 获取失败 | 80 | None | `80` | 优雅降级 |
| 正常 | 80 | 120 | `80/120 (67%)` | 标准显示 |
| 完成 | 50 | 50 | `50/50 (100%) ✓` | 完成标记 |
| 新帖子 | 50 | 60 | `50/60 (83%)` | 正常 |
| 超过 | 120 | 100 | `120/100 (100%) ✓` | 视为完成 |
| 初始 | 0 | 120 | `0/120 (0%)` | 未归档 |

---

#### 模块4: 菜单集成

**文件**: `python/src/menu/main_menu.py`

**修改位置1**: `_follow_author()` 方法

```python
async def _follow_author(self) -> None:
    """关注新作者"""
    # ... 原有代码 ...

    # 获取作者URL
    author_url = text_with_keybindings("请输入作者主页URL:").strip()

    # 新增：提示用户正在获取论坛数据
    self.console.print("[dim]正在获取作者信息...[/dim]")

    # 新增：调用异步方法获取论坛总数
    try:
        from ..scraper.extractor import PostExtractor
        extractor = PostExtractor(self.config['forum']['url'], Path('logs'))
        await extractor.start()

        forum_total = await extractor.get_author_total_posts(author_url)

        await extractor.close()

        if forum_total:
            self.console.print(f"[green]✓ 检测到作者共有 {forum_total} 篇帖子[/green]")
        else:
            self.console.print("[yellow]⚠️  无法获取论坛统计信息，将在下次更新时重试[/yellow]")
    except Exception as e:
        self.console.print(f"[yellow]⚠️  获取论坛信息失败: {str(e)}[/yellow]")
        forum_total = None

    # 保存作者信息（包含 forum_total_posts）
    # ... 原有代码 ...
```

**修改位置2**: `_run_update()` 方法

```python
async def _run_update(self) -> None:
    """更新作者内容"""
    # ... 原有代码 ...

    # 新增：检查是否需要刷新论坛统计
    await self._refresh_forum_stats_if_needed(selected_authors)

    # 显示作者列表（已包含进度信息）
    show_author_table(self.config['followed_authors'], last_selected=last_selected)

    # ... 原有代码 ...
```

**新增方法**: `_refresh_forum_stats_if_needed()`

```python
async def _refresh_forum_stats_if_needed(self, authors: List[Dict[str, Any]]) -> None:
    """刷新论坛统计信息（如果需要）

    检查逻辑:
    1. 检查配置是否启用自动刷新
    2. 检查距离上次刷新是否超过间隔天数
    3. 如果需要，重新获取论坛总数
    """
    if not self.config.get('advanced', {}).get('refresh_forum_stats', True):
        return

    refresh_days = self.config.get('advanced', {}).get('forum_stats_refresh_days', 7)
    today = datetime.now().date()

    authors_to_refresh = []
    for author in authors:
        last_refresh = author.get('forum_stats_updated')

        # 需要刷新的情况：
        # 1. 从未获取过（None）
        # 2. 超过刷新间隔
        if last_refresh is None:
            authors_to_refresh.append(author)
        else:
            last_refresh_date = datetime.strptime(last_refresh, '%Y-%m-%d').date()
            days_since = (today - last_refresh_date).days
            if days_since >= refresh_days:
                authors_to_refresh.append(author)

    if not authors_to_refresh:
        return

    self.console.print(f"[dim]正在刷新 {len(authors_to_refresh)} 位作者的论坛统计信息...[/dim]")

    # 批量刷新
    from ..scraper.extractor import PostExtractor
    extractor = PostExtractor(self.config['forum']['url'], Path('logs'))
    await extractor.start()

    for author in authors_to_refresh:
        try:
            forum_total = await extractor.get_author_total_posts(author['url'])
            if forum_total:
                author['forum_total_posts'] = forum_total
                author['forum_stats_updated'] = today.strftime('%Y-%m-%d')
        except Exception as e:
            self.logger.warning(f"刷新 {author['name']} 的统计失败: {str(e)}")

    await extractor.close()

    # 保存配置
    self.config_manager.save(self.config)
```

---

## 🔍 HTML选择器定位

### 需要确定的信息

在实施前，需要访问实际的论坛页面，确定以下信息：

**作者主页URL格式**:
```
示例: https://t66y.com/htm_data/7/2402/xxxxx.html
```

**HTML结构** (需要实际查看):
```html
<!-- 需要找到显示帖子数的元素 -->
<div class="???">
    <span>主题: <strong>120</strong></span>
</div>
```

**可能的选择器**:
1. CSS选择器：`.author-info .post-count`
2. XPath：`//div[@class='author-info']//strong`
3. 文本匹配：正则表达式匹配"主题数: 120"

### 探测脚本

在实施Step 2之前，需要先运行探测脚本：

```python
# tools/explore_forum_html.py
"""探测论坛HTML结构，找到帖子数位置"""
import asyncio
from playwright.async_api import async_playwright

async def explore_author_page(url: str):
    """探测作者主页HTML结构"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 可视化模式
        page = await browser.new_page()

        await page.goto(url, wait_until='domcontentloaded')

        # 获取完整HTML
        html = await page.content()

        # 保存到文件
        with open('author_page.html', 'w', encoding='utf-8') as f:
            f.write(html)

        print("HTML已保存到 author_page.html")
        print("\n请查找包含帖子数的元素，确定选择器")

        # 交互式调试
        await page.pause()  # 暂停，可以在浏览器中手动选择元素

        await browser.close()

# 使用方法
# asyncio.run(explore_author_page("https://t66y.com/htm_data/7/2402/xxxxx.html"))
```

**输出**:
- `author_page.html` - 完整的页面HTML
- 手动查找帖子数位置
- 确定选择器

---

## 📝 实施步骤

### Step 0: 准备阶段（探测HTML结构）⚠️

**目标**: 确定论坛HTML结构和选择器

**输入**:
- 一个有效的作者主页URL

**操作**:
1. 创建探测脚本 `tools/explore_forum_html.py`
2. 运行脚本访问作者主页
3. 保存HTML并手动分析
4. 确定帖子数的CSS选择器或XPath
5. 记录到设计文档中

**输出**:
- `author_page.html` - 页面HTML快照
- 选择器字符串（如：`.author-stats strong`）
- 测试用例（至少2个不同作者的URL）

**验收标准**:
- [ ] 能够在保存的HTML中找到帖子数
- [ ] 选择器在至少2个不同作者页面上有效
- [ ] 记录了fallback策略（如果主选择器失败）

**预计耗时**: 10-15分钟

**如果失败**:
- 尝试不同的作者URL
- 检查是否需要登录
- 考虑使用正则表达式匹配文本

---

### Step 1: 修改数据结构（config/manager.py）

**目标**: 添加 `forum_total_posts` 和 `forum_stats_updated` 字段支持

**前置条件**:
- ✅ Step 0 完成（确定了选择器）

**文件**: `python/src/config/manager.py`

**修改位置1**: `follow_author()` 方法（约第150行）

**当前代码**:
```python
def follow_author(self, name: str, url: str) -> bool:
    """关注新作者"""
    # ...
    new_author = {
        'name': name,
        'url': url,
        'added_date': datetime.now().strftime('%Y-%m-%d'),
        'total_posts': 0,
        'tags': []
    }
    # ...
```

**修改为**:
```python
def follow_author(self, name: str, url: str, forum_total_posts: Optional[int] = None) -> bool:
    """关注新作者

    Args:
        name: 作者名
        url: 作者主页URL
        forum_total_posts: 论坛总帖子数（可选）
    """
    # ...
    new_author = {
        'name': name,
        'url': url,
        'added_date': datetime.now().strftime('%Y-%m-%d'),
        'total_posts': 0,
        'forum_total_posts': forum_total_posts,  # 新增
        'forum_stats_updated': datetime.now().strftime('%Y-%m-%d') if forum_total_posts else None,  # 新增
        'tags': []
    }
    # ...
```

**验收标准**:
- [ ] `follow_author()` 方法接受 `forum_total_posts` 参数
- [ ] 新关注的作者数据包含 `forum_total_posts` 字段
- [ ] 新关注的作者数据包含 `forum_stats_updated` 字段
- [ ] 参数为 `None` 时，字段值为 `None`
- [ ] 参数为整数时，字段值为该整数，且 `forum_stats_updated` 为当前日期

**测试用例**:
```python
# 测试1: 带论坛总数
manager.follow_author("测试作者1", "http://test.com/1", forum_total_posts=100)
# 期望: forum_total_posts=100, forum_stats_updated="2026-02-12"

# 测试2: 不带论坛总数
manager.follow_author("测试作者2", "http://test.com/2")
# 期望: forum_total_posts=None, forum_stats_updated=None
```

**回滚方案**:
```bash
git checkout python/src/config/manager.py
```

**预计耗时**: 10分钟

---

### Step 2: 实现论坛数据爬取（scraper/extractor.py）

**目标**: 实现 `get_author_total_posts()` 方法

**前置条件**:
- ✅ Step 0 完成（有选择器）
- ✅ Step 1 完成（数据结构已修改）

**文件**: `python/src/scraper/extractor.py`

**添加方法**（约第150行，在类的末尾）:

```python
async def get_author_total_posts(self, author_url: str) -> Optional[int]:
    """获取作者在论坛的总帖子数

    Args:
        author_url: 作者主页URL

    Returns:
        int: 论坛总帖子数，失败返回 None

    Implementation:
        1. 访问作者主页
        2. 等待页面加载
        3. 使用选择器查找帖子数
        4. 解析并返回整数

    Error Handling:
        - 网络错误: 返回 None
        - 选择器未找到: 返回 None
        - 解析失败: 返回 None
    """
    if not self.page:
        self.logger.error("浏览器未启动，请先调用 start()")
        return None

    try:
        self.logger.info(f"获取论坛总数: {author_url}")

        # 访问作者主页
        await self.page.goto(
            author_url,
            wait_until=self.wait_until,
            timeout=self.page_timeout
        )

        # TODO: 根据Step 0的结果填写实际的选择器
        # 策略1: CSS选择器（根据实际HTML结构调整）
        selector = '.author-stats .post-count'  # 示例，需要替换

        # 查找元素
        element = await self.page.query_selector(selector)

        if not element:
            self.logger.warning(f"未找到帖子数元素（选择器: {selector}）")

            # Fallback策略: 尝试正则表达式匹配
            content = await self.page.content()
            import re
            match = re.search(r'主题[:\s]+(\d+)', content)  # 示例，需要调整
            if match:
                total = int(match.group(1))
                self.logger.info(f"通过正则匹配找到总数: {total}")
                return total

            return None

        # 提取文本并转换为整数
        text = await element.inner_text()
        text = text.strip()

        # 移除可能的逗号分隔符（如 "1,234" -> "1234"）
        text = text.replace(',', '')

        total = int(text)

        self.logger.info(f"成功获取论坛总数: {total}")
        return total

    except Exception as e:
        self.logger.error(f"获取论坛总数失败: {str(e)}")
        return None
```

**验收标准**:
- [ ] 方法能够成功访问作者主页
- [ ] 能够找到并提取帖子数
- [ ] 返回正确的整数值
- [ ] 错误时返回 `None` 且不抛出异常
- [ ] 记录了适当的日志

**测试用例**:
```python
# 测试1: 正常获取
extractor = PostExtractor(...)
await extractor.start()
total = await extractor.get_author_total_posts("http://实际URL")
assert total > 0  # 期望返回正整数

# 测试2: 无效URL
total = await extractor.get_author_total_posts("http://invalid")
assert total is None  # 期望返回None

# 测试3: 选择器未找到
# 使用一个不存在帖子数的页面
total = await extractor.get_author_total_posts("http://其他页面")
assert total is None  # 期望返回None
```

**回滚方案**:
```bash
git checkout python/src/scraper/extractor.py
```

**预计耗时**: 30分钟

**特别注意**:
- ⚠️ Step 0的选择器必须先确定
- ⚠️ 需要实际测试至少3个不同作者的页面
- ⚠️ 确保错误不会影响其他功能

---

### Step 3: 修改显示逻辑（utils/display.py）

**目标**: 修改列名和显示格式，支持进度显示

**前置条件**:
- ✅ Step 1 完成（数据结构支持）
- ✅ Step 2 完成（能获取论坛总数）

**文件**: `python/src/utils/display.py`

**修改位置1**: 添加辅助函数（文件开头，第10行附近）

```python
def format_archive_progress(author: Dict[str, Any]) -> str:
    """格式化归档进度显示

    Args:
        author: 作者数据字典，包含 total_posts 和 forum_total_posts

    Returns:
        格式化的进度字符串

    Examples:
        >>> format_archive_progress({'total_posts': 80, 'forum_total_posts': 120})
        '80/120 (67%)'

        >>> format_archive_progress({'total_posts': 80, 'forum_total_posts': None})
        '80'

        >>> format_archive_progress({'total_posts': 50, 'forum_total_posts': 50})
        '50/50 (100%) ✓'

        >>> format_archive_progress({'total_posts': 0, 'forum_total_posts': 120})
        '0/120 (0%)'
    """
    archived = author.get('total_posts', 0)
    forum_total = author.get('forum_total_posts')

    # 情况1: 没有论坛总数（旧数据或获取失败）
    if forum_total is None or forum_total == 0:
        return str(archived)

    # 情况2: 有论坛总数
    # 计算百分比（避免除以0）
    if forum_total > 0:
        percentage = int((archived / forum_total) * 100)
    else:
        percentage = 0

    # 情况3: 已完整归档（>=100%）
    if percentage >= 100:
        return f"{archived}/{forum_total} (100%) ✓"

    # 情况4: 部分归档
    return f"{archived}/{forum_total} ({percentage}%)"
```

**修改位置2**: 修改列定义（第59行）

**当前代码**:
```python
table.add_column("帖子数", justify="right", width=6)
```

**修改为**:
```python
table.add_column("归档进度", justify="right", width=18)
```

**修改位置3**: 修改数据填充（第85-89行）

**当前代码**:
```python
row_data.extend([
    author.get('added_date', 'N/A'),
    str(author.get('total_posts', 0)),
    ', '.join(author.get('tags', []))
])
```

**修改为**:
```python
row_data.extend([
    author.get('added_date', 'N/A'),
    format_archive_progress(author),
    ', '.join(author.get('tags', []))
])
```

**验收标准**:
- [ ] `format_archive_progress()` 函数正确处理所有情况
- [ ] 列名显示为"归档进度"
- [ ] 列宽度足够显示最长的进度字符串（`XXX/XXX (100%) ✓`）
- [ ] 旧数据（无 `forum_total_posts`）显示为纯数字
- [ ] 新数据显示为"已归档/总数 (百分比)"
- [ ] 100%完成时显示 ✓ 标记

**测试用例**:
```python
# 测试1: 旧数据
author1 = {'total_posts': 80}
assert format_archive_progress(author1) == '80'

# 测试2: 新数据，部分完成
author2 = {'total_posts': 80, 'forum_total_posts': 120}
assert format_archive_progress(author2) == '80/120 (67%)'

# 测试3: 完成
author3 = {'total_posts': 50, 'forum_total_posts': 50}
assert format_archive_progress(author3) == '50/50 (100%) ✓'

# 测试4: 超过100%（作者发了新帖）
author4 = {'total_posts': 120, 'forum_total_posts': 100}
assert format_archive_progress(author4) == '120/100 (100%) ✓'

# 测试5: 未开始
author5 = {'total_posts': 0, 'forum_total_posts': 120}
assert format_archive_progress(author5) == '0/120 (0%)'

# 测试6: forum_total_posts 为 0
author6 = {'total_posts': 10, 'forum_total_posts': 0}
assert format_archive_progress(author6) == '10'
```

**回滚方案**:
```bash
git checkout python/src/utils/display.py
```

**预计耗时**: 20分钟

---

### Step 4: 菜单集成（menu/main_menu.py）

**目标**: 在关注和更新作者时集成论坛数据获取

**前置条件**:
- ✅ Step 1-3 全部完成

**文件**: `python/src/menu/main_menu.py`

#### 修改位置1: `_follow_author()` 方法

**查找位置**: 搜索 `def _follow_author(`

**在调用 `config_manager.follow_author()` 之前添加**:

```python
# 获取论坛统计信息
forum_total = None
try:
    self.console.print("[dim]正在获取作者论坛信息...[/dim]")

    # 导入并初始化extractor
    from ..scraper.extractor import PostExtractor
    from pathlib import Path

    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    extractor = PostExtractor(
        self.config['forum']['url'],
        log_dir
    )

    # 启动浏览器
    await extractor.start()

    # 获取论坛总数
    forum_total = await extractor.get_author_total_posts(author_url)

    # 关闭浏览器
    await extractor.close()

    if forum_total:
        self.console.print(f"[green]✓ 检测到该作者共有 {forum_total} 篇帖子[/green]")
    else:
        self.console.print("[yellow]⚠️  暂时无法获取论坛统计，将在下次更新时重试[/yellow]")

except Exception as e:
    self.console.print(f"[yellow]⚠️  获取论坛信息时出错: {str(e)}[/yellow]")
    forum_total = None

# 调用 follow_author（传递 forum_total）
success = self.config_manager.follow_author(author_name, author_url, forum_total_posts=forum_total)
```

#### 修改位置2: `_run_update()` 方法开头

**查找位置**: 搜索 `def _run_update(`

**在显示作者列表之前添加**:

```python
# 刷新论坛统计信息（如果需要）
await self._refresh_forum_stats_if_needed()
```

#### 修改位置3: 添加新方法 `_refresh_forum_stats_if_needed()`

**在类的末尾添加**:

```python
async def _refresh_forum_stats_if_needed(self) -> None:
    """检查并刷新论坛统计信息

    刷新条件:
    1. 配置启用了自动刷新
    2. 距离上次刷新超过了配置的天数
    3. 或者从未获取过
    """
    # 检查是否启用自动刷新
    if not self.config.get('advanced', {}).get('refresh_forum_stats', True):
        return

    refresh_days = self.config.get('advanced', {}).get('forum_stats_refresh_days', 7)
    today = datetime.now().date()

    # 找出需要刷新的作者
    authors_to_refresh = []
    for author in self.config['followed_authors']:
        last_refresh = author.get('forum_stats_updated')

        if last_refresh is None:
            # 从未获取过
            authors_to_refresh.append(author)
        else:
            # 检查是否超过刷新间隔
            try:
                last_refresh_date = datetime.strptime(last_refresh, '%Y-%m-%d').date()
                days_since = (today - last_refresh_date).days
                if days_since >= refresh_days:
                    authors_to_refresh.append(author)
            except:
                # 日期解析失败，标记为需要刷新
                authors_to_refresh.append(author)

    if not authors_to_refresh:
        return

    # 提示用户
    self.console.print(f"\n[dim]正在更新 {len(authors_to_refresh)} 位作者的论坛统计信息...[/dim]")

    # 初始化extractor
    from ..scraper.extractor import PostExtractor
    from pathlib import Path

    log_dir = Path('logs')
    extractor = PostExtractor(self.config['forum']['url'], log_dir)

    try:
        await extractor.start()

        # 批量刷新
        for author in authors_to_refresh:
            try:
                forum_total = await extractor.get_author_total_posts(author['url'])
                if forum_total:
                    author['forum_total_posts'] = forum_total
                    author['forum_stats_updated'] = today.strftime('%Y-%m-%d')
                    self.console.print(f"  [dim]✓ {author['name']}: {forum_total} 篇[/dim]")
            except Exception as e:
                self.console.print(f"  [dim]✗ {author['name']}: 失败[/dim]")

        await extractor.close()

        # 保存配置
        self.config_manager.save(self.config)

        self.console.print("[green]✓ 论坛统计信息已更新[/green]\n")

    except Exception as e:
        self.console.print(f"[yellow]⚠️  刷新论坛统计时出错: {str(e)}[/yellow]\n")
        if extractor.browser:
            await extractor.close()
```

**验收标准**:
- [ ] 关注新作者时自动获取论坛总数
- [ ] 获取成功时显示提示信息
- [ ] 获取失败时优雅降级（不影响关注功能）
- [ ] 更新作者时自动检查是否需要刷新统计
- [ ] 超过刷新间隔时自动刷新
- [ ] 刷新过程显示进度提示
- [ ] 刷新完成后保存配置

**测试用例**:
```python
# 测试1: 关注新作者（获取成功）
# 操作: 关注一个有效的作者
# 期望:
#   - 显示"正在获取作者论坛信息..."
#   - 显示"✓ 检测到该作者共有 XXX 篇帖子"
#   - config.yaml 中包含 forum_total_posts 和 forum_stats_updated

# 测试2: 关注新作者（获取失败）
# 操作: 关注一个无效的URL或网络断开
# 期望:
#   - 显示"⚠️  暂时无法获取论坛统计"
#   - 仍然成功关注作者
#   - forum_total_posts 为 None

# 测试3: 更新作者（需要刷新）
# 准备: 将某个作者的 forum_stats_updated 改为7天前
# 操作: 运行更新
# 期望:
#   - 显示"正在更新 X 位作者的论坛统计信息..."
#   - 刷新完成后显示"✓ 论坛统计信息已更新"
#   - forum_stats_updated 更新为今天

# 测试4: 更新作者（不需要刷新）
# 准备: 所有作者的 forum_stats_updated 都是今天
# 操作: 运行更新
# 期望:
#   - 不显示刷新提示
#   - 直接显示作者列表
```

**回滚方案**:
```bash
git checkout python/src/menu/main_menu.py
```

**预计耗时**: 30分钟

---

### Step 5: 配置文件更新（config.yaml）

**目标**: 添加新的配置项

**前置条件**:
- ✅ Step 4 完成（代码已引用这些配置）

**文件**: `python/config.yaml`

**添加位置**: `advanced` 部分

```yaml
advanced:
  # 现有配置 ...
  max_concurrent: 5
  download_retry: 3
  download_timeout: 30
  rate_limit_delay: 0.5
  page_load_timeout: 60
  wait_until: domcontentloaded

  # 新增：论坛统计刷新配置
  refresh_forum_stats: true       # 是否自动刷新论坛统计信息
  forum_stats_refresh_days: 7     # 刷新间隔（天）
  forum_stats_timeout: 30         # 获取论坛统计的超时时间（秒）
```

**配置说明**:

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `refresh_forum_stats` | boolean | true | 是否在更新时自动刷新论坛统计 |
| `forum_stats_refresh_days` | integer | 7 | 多少天刷新一次（避免频繁请求） |
| `forum_stats_timeout` | integer | 30 | 获取论坛统计的超时时间（秒） |

**验收标准**:
- [ ] 配置项正确添加到 `config.yaml`
- [ ] 格式符合YAML语法
- [ ] 注释清晰说明用途

**回滚方案**:
```bash
git checkout python/config.yaml
```

**预计耗时**: 5分钟

---

### Step 6: 测试和验证

**目标**: 全面测试功能，确保向下兼容和边界情况

**前置条件**:
- ✅ Step 1-5 全部完成

#### 测试场景1: 新关注作者

**操作步骤**:
1. 运行 `python main.py`
2. 选择 `[1] 关注新作者`
3. 输入作者名和URL
4. 观察输出和配置文件

**期望结果**:
- ✅ 显示"正在获取作者论坛信息..."
- ✅ 显示"✓ 检测到该作者共有 XXX 篇帖子"
- ✅ config.yaml 中该作者包含 `forum_total_posts` 和 `forum_stats_updated`

#### 测试场景2: 显示作者列表（混合数据）

**准备**:
- 旧作者（无 `forum_total_posts`）
- 新作者（有 `forum_total_posts`）

**操作步骤**:
1. 运行 `python main.py`
2. 选择 `[2] 查看关注列表`

**期望结果**:
```
┏━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ 状态 ┃ 序号 ┃ 作者名       ┃ 上次更新         ┃ 关注日期   ┃ 归档进度         ┃ 标签               ┃
┡━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│  ⬜  │    1 │ 旧作者       │ 02-11 22:58      │ 2026-02-11 │ 80               │ synced_from_nodejs │  ← 无进度
│  ✅  │    2 │ 新作者       │ 02-12 16:56      │ 2026-02-12 │ 50/100 (50%)     │ from_nodejs        │  ← 有进度
```

#### 测试场景3: 自动刷新统计

**准备**:
1. 修改某个作者的 `forum_stats_updated` 为 10天前
2. 确保 `refresh_forum_stats: true` 且 `forum_stats_refresh_days: 7`

**操作步骤**:
1. 运行 `python main.py`
2. 选择 `[3] 立即更新所有作者` 或选择要更新的作者

**期望结果**:
- ✅ 显示"正在更新 1 位作者的论坛统计信息..."
- ✅ 显示该作者的刷新进度
- ✅ 显示"✓ 论坛统计信息已更新"
- ✅ config.yaml 中 `forum_stats_updated` 更新为今天

#### 测试场景4: 获取失败的处理

**操作步骤**:
1. 关闭网络连接或使用无效URL
2. 尝试关注作者

**期望结果**:
- ✅ 显示"⚠️  暂时无法获取论坛统计"
- ✅ 仍然成功关注作者
- ✅ `forum_total_posts` 为 `None`
- ✅ 后续更新时会尝试重新获取

#### 测试场景5: 完成度100%的显示

**准备**:
- 修改某个作者：`total_posts: 50`, `forum_total_posts: 50`

**操作步骤**:
1. 查看关注列表

**期望结果**:
```
┃ 归档进度         ┃
│ 50/50 (100%) ✓   │  ← 显示 ✓ 标记
```

#### 测试场景6: 边界情况

**测试用例**:
```python
# 用例1: total_posts 为 0
author = {'total_posts': 0, 'forum_total_posts': 100}
# 期望: "0/100 (0%)"

# 用例2: forum_total_posts 为 0
author = {'total_posts': 10, 'forum_total_posts': 0}
# 期望: "10"

# 用例3: 超过 100%
author = {'total_posts': 120, 'forum_total_posts': 100}
# 期望: "120/100 (100%) ✓"

# 用例4: 负数（不应该发生，但要处理）
author = {'total_posts': -5, 'forum_total_posts': 100}
# 期望: 不崩溃，显示合理结果
```

**验收标准**:
- [ ] 所有6个测试场景通过
- [ ] 没有Python异常或崩溃
- [ ] 显示格式美观且一致
- [ ] 向下兼容旧数据
- [ ] 错误处理优雅

**预计耗时**: 30分钟

---

## 🔙 回滚方案

### 完全回滚

如果发现严重问题，需要完全回滚：

```bash
# 1. 回滚所有代码文件
git checkout python/src/config/manager.py
git checkout python/src/scraper/extractor.py
git checkout python/src/utils/display.py
git checkout python/src/menu/main_menu.py
git checkout python/config.yaml

# 2. 验证回滚成功
python main.py

# 3. 如果配置文件已经有了新字段，需要手动删除或备份恢复
cp config.yaml.backup config.yaml  # 如果有备份
```

### 部分回滚

如果只是某个步骤有问题：

```bash
# 例如：Step 3 显示有问题，回滚显示逻辑
git checkout python/src/utils/display.py

# 其他步骤保持不变
```

### 数据回滚

如果配置文件被破坏：

```bash
# 方案1: 从备份恢复
cp ~/.claude/projects/xxx/config.yaml.backup python/config.yaml

# 方案2: 手动删除新字段
# 编辑 config.yaml，删除 forum_total_posts 和 forum_stats_updated 字段
```

---

## 🚨 风险评估

### 高风险项

1. **HTML选择器失效**
   - **概率**: 中等
   - **影响**: 无法获取论坛总数
   - **缓解**:
     - 实施Step 0充分测试
     - 提供fallback策略（正则匹配）
     - 优雅降级（获取失败不影响其他功能）

2. **数据迁移问题**
   - **概率**: 低
   - **影响**: 旧数据无法正常显示
   - **缓解**:
     - 向下兼容设计
     - 充分测试混合数据场景
     - 提供数据修复脚本

3. **性能问题**
   - **概率**: 低
   - **影响**: 刷新统计时速度慢
   - **缓解**:
     - 缓存机制（7天刷新一次）
     - 异步处理
     - 可配置关闭自动刷新

### 中风险项

1. **网络请求失败**
   - **概率**: 中等
   - **影响**: 无法获取论坛总数
   - **缓解**:
     - 超时设置
     - 错误捕获
     - 用户提示

2. **论坛HTML结构变化**
   - **概率**: 低（长期风险）
   - **影响**: 选择器失效
   - **缓解**:
     - 文档记录选择器来源
     - 提供更新指南
     - 支持手动输入

---

## 📈 性能考虑

### 时间消耗预估

| 操作 | 时间 | 频率 |
|------|------|------|
| 关注新作者（含获取统计） | +5秒 | 偶尔 |
| 更新作者（无需刷新） | +0秒 | 常见 |
| 更新作者（刷新1个） | +5秒 | 每7天 |
| 更新作者（刷新10个） | +30秒 | 每7天 |
| 显示作者列表 | +0秒 | 常见 |

### 优化策略

1. **批量刷新**: 同时刷新多个作者时复用浏览器实例
2. **缓存**: 7天内不重复请求
3. **可配置**: 用户可关闭自动刷新
4. **异步**: 不阻塞主流程

---

## 📚 文档更新

### 需要更新的文档

实施完成后需要更新以下文档：

1. **CHANGELOG.md**
   ```markdown
   ## [2.7.0] - 2026-02-12

   ### ✨ 新增功能

   #### 归档进度显示
   - **进度可视化**: 显示"已归档/论坛总数 (百分比)"
   - **完成标记**: 100%完成时显示 ✓ 标记
   - **自动刷新**: 每7天自动更新论坛统计信息
   - **向下兼容**: 兼容旧数据，优雅降级

   ### 🔧 改进

   - 列名更改："帖子数" → "归档进度"
   - 新增配置项：`refresh_forum_stats`, `forum_stats_refresh_days`
   ```

2. **README.md**
   - 更新功能列表
   - 添加归档进度说明
   - 更新配置示例

3. **SESSION_2026-02-12_PART2.md**
   - 标记功能3为"已完成"
   - 添加实施记录

---

## ✅ 验收清单

### 功能验收

- [ ] 新关注作者时自动获取论坛总数
- [ ] 作者列表显示"归档进度"列
- [ ] 旧数据（无论坛总数）正常显示
- [ ] 新数据显示"XX/XX (XX%)"格式
- [ ] 100%完成显示 ✓ 标记
- [ ] 自动刷新统计功能正常
- [ ] 获取失败时优雅降级
- [ ] 配置项生效

### 代码质量验收

- [ ] 所有新增代码有类型注解
- [ ] 所有新增函数有docstring
- [ ] 错误处理完整
- [ ] 日志记录适当
- [ ] 没有硬编码选择器（可配置）

### 测试验收

- [ ] 所有测试场景通过
- [ ] 边界情况处理正确
- [ ] 没有Python异常
- [ ] 向下兼容验证通过

### 文档验收

- [ ] CHANGELOG.md 已更新
- [ ] README.md 已更新
- [ ] 会话记录已更新
- [ ] 设计文档完整

---

## 📞 实施协调

### 实施前检查

- [ ] Step 0 完成（选择器已确定）
- [ ] 有至少2个测试用的作者URL
- [ ] 代码已备份（git commit）
- [ ] config.yaml 已备份

### 实施顺序

**必须按顺序执行**:
1. Step 0（探测HTML）→ Step 1（数据结构）→ Step 2（爬取）→ Step 3（显示）→ Step 4（集成）→ Step 5（配置）→ Step 6（测试）

**不可跳过**:
- Step 0: 必须先确定选择器
- Step 1: 数据结构是基础
- Step 6: 测试是质量保证

### 实施后检查

- [ ] 运行 `python main.py` 无错误
- [ ] 查看关注列表显示正常
- [ ] 关注新作者功能正常
- [ ] 更新作者功能正常
- [ ] config.yaml 格式正确

---

## 🎯 成功标准

### 用户体验目标

用户应该能够：
1. ✅ 一眼看出每个作者的归档完成度
2. ✅ 知道作者在论坛有多少帖子
3. ✅ 评估是否需要继续归档
4. ✅ 无需担心旧数据兼容性

### 技术目标

系统应该：
1. ✅ 稳定运行，无崩溃
2. ✅ 向下兼容旧数据
3. ✅ 优雅处理错误
4. ✅ 性能影响小于5秒/作者

### 可维护性目标

代码应该：
1. ✅ 结构清晰，易于理解
2. ✅ 文档完整，易于修改
3. ✅ 错误信息明确，易于调试
4. ✅ 选择器可配置，易于适配

---

## 📝 附录

### A. HTML选择器参考

**待填写**（Step 0完成后）

```python
# 选择器定义
SELECTORS = {
    'post_count': '.author-stats .count',  # 示例
    'fallback': [
        '.post-num',
        '[data-posts]'
    ]
}

# 正则表达式备选
REGEX_PATTERNS = [
    r'主题[:\s]+(\d+)',
    r'发帖[:\s]+(\d+)',
    r'Posts[:\s]+(\d+)'
]
```

### B. 配置项完整列表

```yaml
advanced:
  # 现有配置
  max_concurrent: 5
  download_retry: 3
  download_timeout: 30
  rate_limit_delay: 0.5
  page_load_timeout: 60
  wait_until: domcontentloaded

  # 新增配置
  refresh_forum_stats: true       # 是否自动刷新
  forum_stats_refresh_days: 7     # 刷新间隔（天）
  forum_stats_timeout: 30         # 获取超时（秒）
```

### C. 数据结构JSON Schema

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "url": {"type": "string"},
    "added_date": {"type": "string", "pattern": "\\d{4}-\\d{2}-\\d{2}"},
    "last_update": {"type": ["string", "null"]},
    "total_posts": {"type": "integer", "minimum": 0},
    "forum_total_posts": {"type": ["integer", "null"], "minimum": 0},
    "forum_stats_updated": {"type": ["string", "null"]},
    "tags": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["name", "url", "added_date", "total_posts", "tags"]
}
```

---

**文档版本**: v1.0
**最后更新**: 2026-02-12
**状态**: 待审批
**预计实施时间**: 2-3小时
**预计完成日期**: 2026-02-12

---

## 🚀 准备就绪

本设计文档提供了完整的实施指南，包括：
- ✅ 详细的步骤说明
- ✅ 清晰的验收标准
- ✅ 完整的测试计划
- ✅ 风险评估和缓解措施
- ✅ 回滚方案

**等待审批后即可开始实施！**
