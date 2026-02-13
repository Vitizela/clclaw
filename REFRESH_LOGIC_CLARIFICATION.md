# 刷新逻辑澄清文档

**创建日期**: 2026-02-12
**问题**: "检测到需要刷新"的具体含义

---

## 🤔 用户的疑问

> 检测到需要刷新，是指检测到比最后一次下载帖子日期更新的帖子吗？

**这是一个很好的问题**，涉及两个不同的概念需要区分。

---

## 📊 两个不同的概念

### 概念1: 刷新论坛统计（`forum_total_posts`）

**目的**: 更新"论坛总帖子数"字段，用于显示归档进度

**场景**:
```
作者A在论坛有 100 篇帖子
  ↓
我们关注时获取了这个数字: forum_total_posts = 100
  ↓
7天后，作者A又发了 20 篇新帖子，现在有 120 篇
  ↓
但我们的配置文件里还是: forum_total_posts = 100 ← 需要刷新
  ↓
刷新后更新为: forum_total_posts = 120
```

**刷新触发条件**（原设计）:
- ✅ 基于**时间间隔**：距离上次刷新超过7天
- ❌ 不是基于新帖子检测

**为什么这样设计？**
- 简单：不需要爬取论坛就能判断
- 避免频繁请求：7天刷新一次
- 论坛总数是用于显示进度的"参考数据"，不需要实时准确

---

### 概念2: 检测并归档新帖子

**目的**: 下载作者新发布的帖子到本地

**场景**:
```
上次归档: 2026-02-10
  ↓
作者A在 2026-02-11 发了新帖
  ↓
今天（2026-02-12）执行更新
  ↓
归档流程会:
  1. 爬取作者主页，获取所有帖子列表
  2. 检查哪些帖子是新的（URL不在本地）
  3. 下载新帖子
```

**检测逻辑**:
- ✅ 基于**帖子URL**：本地没有的就是新帖子
- ✅ 基于**完成标记**：没有 `.complete` 文件的目录
- ❌ 不是基于发布日期对比

**为什么这样设计？**
- 可靠：URL是唯一标识
- 增量：自动跳过已归档的帖子
- 断点续传：未完成的帖子会重新归档

---

## 🔄 刷新论坛统计的两种策略

### 策略A: 基于时间间隔（原设计）

**逻辑**:
```python
if last_refresh is None:
    需要刷新  # 从未获取过
elif (today - last_refresh_date).days >= 7:
    需要刷新  # 超过7天
else:
    不需要刷新
```

**优点**:
- ✅ 实现简单
- ✅ 不需要额外的网络请求
- ✅ 可以提前判断（不用访问论坛）

**缺点**:
- ⚠️ 可能浪费：7天内作者没发新帖，刷新了也是原来的数字
- ⚠️ 可能不准：7天内作者发了很多新帖，但没刷新

**适用场景**:
- 论坛总数是"参考数据"，不要求实时准确
- 减少网络请求，避免被封IP

---

### 策略B: 基于新帖子检测（用户建议）

**逻辑**:
```python
# 归档流程中
collected_post_urls = 爬取作者主页获取帖子列表
new_posts = [url for url in collected_post_urls if not exists_locally(url)]

if len(new_posts) > 0:
    # 检测到新帖子，顺便更新论坛总数
    forum_total_posts = len(collected_post_urls)
    需要刷新论坛统计
```

**优点**:
- ✅ 精确：只在有新帖子时才刷新
- ✅ 不浪费：没新帖子就不刷新
- ✅ 实时：论坛总数始终是最新的

**缺点**:
- ⚠️ 复杂：需要在归档流程中集成
- ⚠️ 依赖：必须执行归档才能刷新
- ⚠️ 时机：只在"更新"时刷新，"查看列表"时不刷新

**适用场景**:
- 论坛总数要求实时准确
- 用户经常执行更新操作

---

## 🎯 策略对比

### 场景1: 用户每天都更新

| 天数 | 作者新帖 | 策略A（时间） | 策略B（新帖） |
|------|---------|--------------|--------------|
| Day 1 | 发了5篇 | 不刷新（<7天） | ✅ 刷新（有新帖） |
| Day 2 | 没发帖 | 不刷新（<7天） | ✅ 不刷新（无新帖） |
| Day 3 | 发了3篇 | 不刷新（<7天） | ✅ 刷新（有新帖） |
| Day 7 | 没发帖 | ✅ 刷新（>=7天） | ✅ 不刷新（无新帖） |
| Day 8 | 发了2篇 | 不刷新（<7天） | ✅ 刷新（有新帖） |

**结论**: 策略B更精确，不浪费

---

### 场景2: 用户每周更新一次

| 周数 | 作者新帖 | 策略A（时间） | 策略B（新帖） |
|------|---------|--------------|--------------|
| Week 1 | 发了10篇 | ✅ 刷新（>=7天） | ✅ 刷新（有新帖） |
| Week 2 | 发了8篇 | ✅ 刷新（>=7天） | ✅ 刷新（有新帖） |
| Week 3 | 没发帖 | ✅ 刷新（>=7天） | ✅ 不刷新（无新帖） |

**结论**: 策略B避免了Week 3的浪费刷新

---

### 场景3: 只查看列表，不更新

| 操作 | 策略A（时间） | 策略B（新帖） |
|------|--------------|--------------|
| 查看关注列表 | ✅ 检查是否需要刷新 | ❌ 不检查（因为没有归档流程） |
| 查看关注列表 | ✅ 如果>7天，可以刷新 | ❌ 不刷新 |

**结论**: 策略B在"只查看不更新"时无法刷新

---

## 💡 推荐方案

### 方案: 策略B（基于新帖子）+ 回退到策略A

**核心思路**: 结合两种策略的优点

#### 实现逻辑

```python
async def _run_update(self):
    """更新作者内容"""

    # 不在更新前刷新统计（删除原来的逻辑）
    # await self._refresh_forum_stats_if_needed()  # 删除

    # 显示作者列表（使用现有数据）
    show_author_table(self.config['followed_authors'])

    # 选择作者...
    selected_authors = ...

    # 开始归档
    for author in selected_authors:
        # 阶段1: 收集帖子URL
        post_urls = await extractor.collect_post_urls(author['url'])

        # 检测新帖子
        new_post_urls = [url for url in post_urls if not is_archived(url)]

        if len(new_post_urls) > 0:
            # 有新帖子，顺便更新论坛总数
            author['forum_total_posts'] = len(post_urls)
            author['forum_stats_updated'] = today

            self.logger.info(f"检测到 {len(new_post_urls)} 篇新帖子，论坛总数: {len(post_urls)}")

        # 阶段2: 归档新帖子
        for post_url in new_post_urls:
            await archive_post(post_url)
```

#### 回退机制

如果用户只查看列表不更新，提供手动刷新：

```python
# 主菜单新增选项
[6] 手动刷新论坛统计

async def _manual_refresh_stats(self):
    """手动刷新统计（使用策略A的逻辑）"""
    # 让用户选择要刷新的作者
    # 刷新论坛总数
    # 保存配置
```

---

## 📋 对比总结

### 原设计（策略A）

```
更新作者
  ↓
检查是否>7天 → 是 → 刷新统计（可能阻塞30秒） ← 用户担心阻塞
  ↓
显示列表
  ↓
归档新帖子
```

**问题**:
- ❌ 可能阻塞用户操作
- ⚠️ 可能浪费刷新（没有新帖子也刷新）

---

### 推荐方案（策略B）

```
更新作者
  ↓
显示列表（使用现有数据）
  ↓
选择作者
  ↓
归档流程:
  1. 收集帖子URL（需要爬取）
  2. 检测新帖子
  3. 如果有新帖子 → 顺便更新论坛总数 ← 不阻塞，因为归档本来就要爬取
  4. 归档新帖子
```

**优点**:
- ✅ 不阻塞：刷新统计不是独立操作，而是归档流程的一部分
- ✅ 精确：只在有新帖子时才更新论坛总数
- ✅ 不浪费：没有新帖子就不刷新
- ✅ 实时：论坛总数始终反映最新状态

---

## 🔧 实施建议

### 修改点1: 删除独立的刷新统计步骤

```python
# 原代码（删除）
async def _run_update(self):
    await self._refresh_forum_stats_if_needed()  # 删除这行

    show_author_table(...)
    # ...
```

### 修改点2: 在归档流程中集成

**文件**: `python/src/scraper/archiver.py`

```python
async def archive_author(self, author_name: str, author_url: str) -> dict:
    """归档作者的所有帖子"""

    # 阶段一：收集所有帖子 URL
    post_urls = await self.extractor.collect_post_urls(author_url)
    total_posts = len(post_urls)

    # 新增：更新论坛总数（基于实际爬取的结果）
    self.logger.info(f"论坛总帖子数: {total_posts}")
    # 返回给调用者，让调用者更新配置

    # 阶段二：逐个处理帖子
    new_posts = 0
    skipped_posts = 0

    for post_url in post_urls:
        post_dir = self._get_post_directory(author_name, post_data)

        if not should_archive(post_dir, post_url):
            skipped_posts += 1
            continue  # 跳过已归档的

        # 归档新帖子
        # ...
        new_posts += 1

    return {
        'total': total_posts,
        'new': new_posts,
        'skipped': skipped_posts,
        'forum_total': total_posts,  # 新增：返回论坛总数
    }
```

### 修改点3: 更新配置

**文件**: `python/src/menu/main_menu.py`

```python
result = await archiver.archive_author(author_name, author_url)

# 更新配置
author['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
author['total_posts'] = author.get('total_posts', 0) + result['new']

# 新增：更新论坛总数（基于归档流程中爬取的结果）
if result.get('forum_total'):
    author['forum_total_posts'] = result['forum_total']
    author['forum_stats_updated'] = datetime.now().strftime('%Y-%m-%d')
```

---

## ✅ 优点总结

采用策略B（基于新帖子检测）的优点：

1. **无独立阻塞**:
   - 不再有"刷新统计"的独立步骤
   - 论坛总数的更新融入到归档流程中
   - 归档本来就要爬取作者主页，顺便获取总数

2. **精确且不浪费**:
   - 有新帖子才更新论坛总数
   - 没有新帖子就不更新（论坛总数也没变）

3. **实时准确**:
   - 每次归档后，论坛总数都是最新的
   - 进度百分比更准确

4. **简化逻辑**:
   - 不需要"检查是否需要刷新"的复杂逻辑
   - 不需要配置刷新间隔天数
   - 不需要用户选择"跳过刷新"

---

## 🎯 结论

**回答用户的问题**:

> 检测到需要刷新，是指检测到比最后一次下载帖子日期更新的帖子吗？

**我的原设计**: 不是，是基于时间间隔（7天）

**更好的设计**: 是的，应该基于新帖子检测（策略B）

**推荐方案**: 采用策略B，在归档流程中顺便更新论坛总数，这样：
- ✅ 不会阻塞（因为归档本来就要爬取）
- ✅ 精确且不浪费
- ✅ 逻辑更简单

---

**文档状态**: 已完成
**推荐**: 采用策略B（基于新帖子检测）
**下一步**: 更新设计文档，采用新策略
