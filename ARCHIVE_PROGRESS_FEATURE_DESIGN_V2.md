# 归档进度显示功能 - 详细设计文档 v2.0

**功能代号**: FEAT-ARCHIVE-PROGRESS
**版本**: v2.0（重大修订）
**创建日期**: 2026-02-12
**修订日期**: 2026-02-12
**设计者**: Claude AI
**审批状态**: 待审批

---

## 📝 版本历史

| 版本 | 日期 | 主要变更 | 原因 |
|------|------|---------|------|
| v1.0 | 2026-02-12 | 初始版本 | 基于时间间隔刷新统计 |
| **v2.0** | 2026-02-12 | **策略重大调整** | **基于新帖子检测，消除阻塞问题** |

### v2.0 重大变更

**变更原因**:
1. **用户担心阻塞**: v1.0设计会在更新前独立刷新统计，可能阻塞30-60秒
2. **用户建议更合理**: 应该在归档时顺便获取论坛总数，而不是独立刷新
3. **技术洞察**: 归档流程本来就要访问作者主页，顺便获取总数零额外开销

**核心变更**:
- ❌ 删除：独立的"刷新论坛统计"步骤
- ✅ 改为：归档时顺便从HTML获取论坛总数
- ✅ 结果：完全无阻塞，逻辑更简单

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

---

## 🏗️ 技术架构（v2.0）

### 核心策略：归档时顺便获取

```
用户操作: 更新作者
  ↓
显示作者列表（使用现有数据）← 无阻塞
  ↓
选择作者
  ↓
归档流程:
  1. 访问作者主页第1页
     ├─ 提取该页的帖子URL
     └─ 从HTML读取论坛总数 ← 顺便做，零额外开销
  2. 访问第2页...
  3. 收集完所有帖子URL
  4. 检测新帖子
  5. 更新配置（包括论坛总数）
  6. 归档新帖子
```

### 关键改进

**v1.0 (旧)**:
```python
# 独立刷新（阻塞）
await refresh_forum_stats()  # 可能阻塞30秒
  ↓
显示列表
  ↓
归档帖子
```

**v2.0 (新)**:
```python
# 归档时顺便获取（零额外开销）
显示列表
  ↓
归档帖子:
  - 访问作者主页（本来就要访问）
  - 顺便从HTML读取论坛总数 ← 零额外开销
  - 继续归档
```

---

## 📊 获取论坛总数的两种方式

### 方式1: 从HTML直接读取（主要方式）⭐⭐⭐⭐⭐

**原理**: 作者主页通常会显示总帖子数

```html
<!-- 假设的HTML结构（需要Step 0确认） -->
<div class="author-info">
    <span>主题数: <strong>120</strong></span>
</div>
```

**实现**:
```python
async def get_forum_total_from_html(self, page) -> Optional[int]:
    """从当前页面HTML中提取论坛总数

    Returns:
        int: 论坛总数，失败返回None
    """
    try:
        # 使用Step 0探测到的选择器
        element = await page.query_selector(FORUM_TOTAL_SELECTOR)
        if element:
            text = await element.inner_text()
            # 移除逗号等格式化字符
            text = text.replace(',', '').strip()
            return int(text)
    except Exception as e:
        self.logger.warning(f"从HTML提取总数失败: {e}")
        return None
```

**优点**:
- ✅ 快速：< 0.1秒
- ✅ 零额外开销：访问页面时顺便读取
- ✅ 准确：显示的就是论坛总数

**缺点**:
- ⚠️ 依赖HTML结构：如果论坛改版，选择器可能失效

---

### 方式2: 统计收集的URL数量（Fallback）

**原理**: 归档流程会收集所有帖子URL，列表长度就是总数

```python
# 归档流程
post_urls = await collect_post_urls(author_url)
# post_urls = [url1, url2, ..., url120]

forum_total = len(post_urls)  # 120
```

**优点**:
- ✅ 100%可靠：不依赖HTML结构
- ✅ 准确：实际收集到的数量

**缺点**:
- ⚠️ 慢：需要遍历所有分页才能知道总数

---

### 组合策略（推荐）

```python
async def archive_author(self, author_name: str, author_url: str) -> dict:
    """归档作者的所有帖子"""

    # 访问作者主页第1页
    await self.page.goto(author_url)

    # 尝试从HTML读取论坛总数（方式1）
    forum_total = await self.get_forum_total_from_html(self.page)

    # 收集所有帖子URL
    post_urls = await self.collect_post_urls(author_url)

    # 如果方式1失败，使用方式2作为fallback
    if forum_total is None:
        forum_total = len(post_urls)
        self.logger.info(f"使用fallback方式，统计得到总数: {forum_total}")

    # 验证（可选）
    if abs(forum_total - len(post_urls)) > 5:
        self.logger.warning(
            f"论坛总数({forum_total})与实际收集数({len(post_urls)})差异较大"
        )

    # 检测新帖子
    new_post_urls = [url for url in post_urls if not self._is_archived(url)]

    # 归档新帖子...

    return {
        'total': len(post_urls),
        'new': len(new_post_urls),
        'skipped': len(post_urls) - len(new_post_urls),
        'forum_total': forum_total  # 返回论坛总数
    }
```

---

## 📁 数据结构设计

### 配置文件结构（与v1.0相同）

```yaml
followed_authors:
  - name: "独醉笑清风"
    url: "https://t66y.com/htm_data/7/2402/..."
    added_date: "2026-02-11"
    last_update: "2026-02-11 22:58:01"
    total_posts: 80                        # 已归档数
    forum_total_posts: 120                 # 论坛总帖子数
    forum_stats_updated: "2026-02-12"      # 论坛数据获取时间
    tags: ["synced_from_nodejs"]
```

**字段定义**（与v1.0相同）:

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `forum_total_posts` | integer | ❌ | null | 论坛总帖子数 |
| `forum_stats_updated` | string | ❌ | null | 论坛数据获取时间 |

**向下兼容**:
- 旧数据：`forum_total_posts` 为 `null`
- 显示逻辑：只显示已归档数
- 首次归档：自动获取并更新

---

## 🔧 实施步骤（v2.0 - 简化版）

### 与v1.0的对比

| 步骤 | v1.0（旧） | v2.0（新） | 变化 |
|------|-----------|-----------|------|
| Step 0 | 探测HTML结构 | 探测HTML结构 | ✅ 相同 |
| Step 1 | 修改数据结构 | 修改数据结构 | ✅ 相同 |
| Step 2 | 实现独立爬取方法 | 实现HTML读取方法 | ⚠️ 简化 |
| Step 3 | 修改显示逻辑 | 修改显示逻辑 | ✅ 相同 |
| Step 4 | **菜单集成（复杂）** | **归档集成（简单）** | ✅ 简化 |
| Step 5 | 配置文件更新 | ~~删除~~（不需要） | ✅ 删除 |
| Step 6 | 测试验证 | 测试验证 | ✅ 相同 |

**总结**: v2.0实施更简单，耗时更短（1.5小时 → 1小时）

---

### Step 0: 探测HTML结构（与v1.0相同）

**目标**: 确定论坛HTML中显示总帖子数的位置

**操作**:
1. 访问一个作者主页
2. 查看HTML源码或使用浏览器开发者工具
3. 找到显示"主题: 120"或类似文本的元素
4. 确定CSS选择器

**输出**:
```python
# 记录到代码中
FORUM_TOTAL_SELECTOR = '.author-stats .post-count'  # 示例

# 或者多个候选
FORUM_TOTAL_SELECTORS = [
    '.author-info .total',
    '.post-count',
    '[data-posts]'
]
```

**验收标准**:
- [ ] 至少在2个不同作者页面上验证选择器有效
- [ ] 记录了fallback选择器（如果主选择器失败）

---

### Step 1: 修改数据结构（与v1.0相同）

**文件**: `python/src/config/manager.py`

**修改**: 参见v1.0设计文档

---

### Step 2: 实现HTML读取方法（v2.0 - 简化）

**目标**: 实现从HTML读取论坛总数的方法

**文件**: `python/src/scraper/extractor.py`

**新增方法**:

```python
# 在文件顶部定义选择器（Step 0的结果）
FORUM_TOTAL_SELECTORS = [
    '.author-stats .post-count',  # 主选择器
    '.user-info .total',          # 备用1
    '[data-total-posts]'          # 备用2
]

class PostExtractor:
    async def get_forum_total_from_html(self, page=None) -> Optional[int]:
        """从HTML中提取论坛总帖子数

        Args:
            page: Playwright页面对象，如果为None则使用self.page

        Returns:
            int: 论坛总数，失败返回None

        Implementation:
            1. 尝试多个选择器
            2. 提取文本并清理
            3. 转换为整数
            4. 失败返回None（不抛出异常）
        """
        target_page = page or self.page

        if not target_page:
            self.logger.error("页面对象为None")
            return None

        # 尝试每个选择器
        for selector in FORUM_TOTAL_SELECTORS:
            try:
                element = await target_page.query_selector(selector)
                if element:
                    text = await element.inner_text()

                    # 清理文本（移除逗号、空格等）
                    text = text.replace(',', '').replace(' ', '').strip()

                    # 提取数字（可能格式为"主题: 120"）
                    import re
                    match = re.search(r'\d+', text)
                    if match:
                        total = int(match.group())
                        self.logger.info(f"从HTML提取论坛总数: {total} (选择器: {selector})")
                        return total

            except Exception as e:
                self.logger.debug(f"选择器 {selector} 失败: {e}")
                continue

        # 所有选择器都失败
        self.logger.warning("所有选择器都无法提取论坛总数")
        return None
```

**验收标准**:
- [ ] 能够成功从HTML提取论坛总数
- [ ] 支持多个候选选择器（fallback）
- [ ] 失败时返回None，不抛出异常
- [ ] 记录了适当的日志

**预计耗时**: 20分钟

---

### Step 3: 修改显示逻辑（与v1.0相同）

**文件**: `python/src/utils/display.py`

**修改**: 参见v1.0设计文档

---

### Step 4: 归档流程集成（v2.0 - 核心变更）

**目标**: 在归档流程中顺便获取论坛总数

**文件**: `python/src/scraper/archiver.py`

**修改位置**: `archive_author()` 方法

**当前代码**（简化）:
```python
async def archive_author(self, author_name: str, author_url: str) -> dict:
    """归档作者的所有帖子"""

    # 阶段一：收集所有帖子 URL
    post_urls = await self.extractor.collect_post_urls(author_url)
    total_posts = len(post_urls)

    # 阶段二：逐个处理帖子
    new_posts = 0
    for post_url in post_urls:
        if should_archive(...):
            # 归档帖子
            new_posts += 1

    return {
        'total': total_posts,
        'new': new_posts,
        'skipped': total_posts - new_posts,
        'failed': 0
    }
```

**修改为**:
```python
async def archive_author(self, author_name: str, author_url: str) -> dict:
    """归档作者的所有帖子"""

    self.logger.info(f"开始归档作者: {author_name}")

    # 阶段一：收集所有帖子 URL
    self.logger.info("【阶段 1】收集帖子列表...")

    # 访问作者主页（collect_post_urls内部会访问）
    post_urls = await self.extractor.collect_post_urls(author_url)
    total_posts = len(post_urls)

    # 新增：从HTML获取论坛总数
    # 注意：此时已经访问过作者主页了，如果页面还在可以直接读取
    forum_total = await self.extractor.get_forum_total_from_html()

    # 如果获取失败，使用收集到的URL数量作为fallback
    if forum_total is None:
        forum_total = total_posts
        self.logger.info(f"使用fallback方式，论坛总数: {forum_total}")
    else:
        self.logger.info(f"从HTML获取论坛总数: {forum_total}")

        # 验证差异（可选）
        if abs(forum_total - total_posts) > 5:
            self.logger.warning(
                f"论坛总数({forum_total})与实际收集数({total_posts})差异较大"
            )

    # 阶段二：逐个处理帖子
    self.logger.info(f"【阶段 2】处理 {total_posts} 篇帖子...")

    new_posts = 0
    skipped_posts = 0
    failed_posts = 0

    for idx, post_url in enumerate(post_urls, 1):
        self.logger.info(f"处理帖子 {idx}/{total_posts}")

        # 计算目录路径
        # 提取帖子详情
        # 检查是否需要归档
        # 归档...

        if should_archive(...):
            new_posts += 1
        else:
            skipped_posts += 1

    # 返回结果（新增forum_total字段）
    return {
        'total': total_posts,
        'new': new_posts,
        'skipped': skipped_posts,
        'failed': failed_posts,
        'forum_total': forum_total  # 新增
    }
```

**关键点**:
- ✅ 在收集帖子URL后，顺便从HTML读取论坛总数
- ✅ 零额外开销（访问已经完成了）
- ✅ 使用fallback确保可靠性
- ✅ 返回值中包含 `forum_total` 字段

**验收标准**:
- [ ] 归档后返回结果包含 `forum_total` 字段
- [ ] HTML读取失败时使用fallback
- [ ] 记录了适当的日志

**预计耗时**: 20分钟

---

### Step 5: 菜单更新配置（v2.0 - 简化）

**目标**: 归档完成后更新配置文件中的论坛总数

**文件**: `python/src/menu/main_menu.py`

**修改位置**: `_run_update()` 方法中，归档完成后更新配置的部分

**当前代码**（约第470行）:
```python
result = await archiver.archive_author(author_name, author_url)

# 更新配置中的统计信息
author['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
author['total_posts'] = author.get('total_posts', 0) + result['new']
```

**修改为**:
```python
result = await archiver.archive_author(author_name, author_url)

# 更新配置中的统计信息
author['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
author['total_posts'] = author.get('total_posts', 0) + result['new']

# 新增：更新论坛总数（如果归档流程中获取到了）
if result.get('forum_total'):
    author['forum_total_posts'] = result['forum_total']
    author['forum_stats_updated'] = datetime.now().strftime('%Y-%m-%d')
    self.logger.info(f"已更新论坛总数: {result['forum_total']}")
```

**验收标准**:
- [ ] 归档后配置文件中 `forum_total_posts` 被更新
- [ ] `forum_stats_updated` 记录为当前日期
- [ ] 如果获取失败（None），不更新这两个字段

**预计耗时**: 10分钟

---

### Step 6: 关注新作者时获取（可选）

**目标**: 关注新作者时也获取论坛总数

**文件**: `python/src/menu/main_menu.py`

**修改位置**: `_follow_author()` 方法

**这是可选的**，因为：
- 首次归档时会自动获取
- 但在关注时获取可以让用户立即看到论坛总数

**实现**（可选）:
```python
async def _follow_author(self) -> None:
    """关注新作者"""

    # ... 获取作者名和URL ...

    # 可选：获取论坛总数
    forum_total = None
    try:
        self.console.print("[dim]正在获取作者信息...[/dim]")

        from ..scraper.extractor import PostExtractor
        from pathlib import Path

        extractor = PostExtractor(self.config['forum']['url'], Path('logs'))
        await extractor.start()

        # 访问作者主页
        await extractor.page.goto(author_url, wait_until='domcontentloaded')

        # 从HTML读取总数
        forum_total = await extractor.get_forum_total_from_html()

        await extractor.close()

        if forum_total:
            self.console.print(f"[green]✓ 检测到该作者共有 {forum_total} 篇帖子[/green]")

    except Exception as e:
        self.console.print(f"[yellow]⚠️  获取信息失败，将在首次归档时获取[/yellow]")

    # 保存作者信息
    success = self.config_manager.follow_author(
        author_name,
        author_url,
        forum_total_posts=forum_total
    )
```

**验收标准**:
- [ ] 关注成功后配置中包含 `forum_total_posts`（如果获取成功）
- [ ] 获取失败不影响关注功能

**预计耗时**: 15分钟（可选）

---

### Step 7: 测试验证

**测试场景**: 与v1.0类似，但更简单

#### 测试1: 归档新作者

**操作**:
1. 归档一个作者（有新帖子）
2. 检查配置文件

**期望**:
```yaml
- name: "测试作者"
  total_posts: 10           # 新归档的帖子数
  forum_total_posts: 50     # 从HTML读取的总数
  forum_stats_updated: "2026-02-12"
```

#### 测试2: 显示进度

**操作**:
1. 查看关注列表

**期望**:
```
┃ 归档进度         ┃
│ 10/50 (20%)      │  ← 显示正确的进度
```

#### 测试3: HTML读取失败

**操作**:
1. 修改选择器为无效值
2. 归档一个作者

**期望**:
- 使用fallback方式（`len(post_urls)`）
- 仍然能获取到论坛总数
- 日志显示"使用fallback方式"

---

## 📊 v1.0 vs v2.0 对比

### 实施复杂度

| 项目 | v1.0 | v2.0 | 变化 |
|------|------|------|------|
| 需要修改的文件 | 5个 | 3个 | ✅ 减少 |
| 新增方法 | 3个 | 1个 | ✅ 减少 |
| 新增配置项 | 3个 | 0个 | ✅ 删除 |
| 测试场景 | 6个 | 3个 | ✅ 简化 |
| **预计耗时** | **2-3小时** | **1-1.5小时** | ✅ **减少50%** |

### 阻塞问题

| 场景 | v1.0 | v2.0 | 改进 |
|------|------|------|------|
| 更新前刷新统计 | 阻塞30秒 | **无阻塞** | ✅ 完美 |
| 关注新作者 | 阻塞8秒 | 阻塞8秒（可选） | - |
| 归档流程 | 不变 | 不变 | - |

### 用户体验

| 方面 | v1.0 | v2.0 | 改进 |
|------|------|------|------|
| 更新速度 | 慢（需要先刷新） | 快（直接开始） | ✅ 更快 |
| 数据准确性 | 可能过时（7天刷新） | 实时（每次归档更新） | ✅ 更准 |
| 操作复杂度 | 需要选择是否刷新 | 无需选择 | ✅ 更简单 |

---

## ✅ v2.0 优势总结

### 1. 无阻塞

- ❌ v1.0: 更新前独立刷新统计，阻塞30秒
- ✅ v2.0: 归档时顺便获取，零额外开销

### 2. 更精确

- ❌ v1.0: 基于时间间隔，可能不准确
- ✅ v2.0: 每次归档后更新，实时准确

### 3. 更简单

- ❌ v1.0: 需要"刷新统计"独立步骤，逻辑复杂
- ✅ v2.0: 集成到归档流程，逻辑简单

### 4. 实施更快

- ❌ v1.0: 2-3小时
- ✅ v2.0: 1-1.5小时

---

## 🚀 推荐实施

### 理由

1. **用户担心正确**: v1.0确实有阻塞问题
2. **用户建议合理**: 归档时顺便获取更自然
3. **技术上可行**: 访问页面时顺便读取HTML，零开销
4. **实施更简单**: 减少50%工作量

### 下一步

1. 审批v2.0设计
2. 执行Step 0（探测HTML结构）
3. 按顺序实施Steps 1-7
4. 测试验证

---

**文档版本**: v2.0
**最后更新**: 2026-02-12
**状态**: 待审批
**预计实施时间**: 1-1.5小时
**推荐度**: ⭐⭐⭐⭐⭐ 强烈推荐
