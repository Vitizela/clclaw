# 反爬虫问题分析报告

**日期：** 2026-02-13
**问题：** 刷新检测新帖功能无法统计论坛帖子总数
**状态：** 已识别，暂不修复

---

## 问题描述

用户选择作者"清风皓月"和"独醉笑清风"后，返回操作菜单并选择"刷新检测新帖"，期望看到这两个作者的论坛帖子总数（forum_total_posts），但实际没有显示。

## 根本原因

**不是 URL 格式错误，而是论坛的反爬虫机制阻止了 Playwright 访问。**

### 证据

从 `logs/extractor.log` 发现：

```log
2026-02-13 22:46:02 - extractor - INFO - 开始收集帖子列表: https://t66y.com/@独醉笑清风
2026-02-13 22:46:02 - extractor - INFO - 限制: 最多收集 3 页
2026-02-13 22:46:02 - extractor - INFO - 检测到作者主页格式，跳过作者过滤
2026-02-13 22:46:02 - extractor - INFO - 正在抓取第 1 页...
2026-02-13 22:46:02 - extractor - ERROR - 第 1 页提取失败: net::ERR_ABORTED at https://t66y.com/@%E7%8B%AC%E9%86%89%E7%AC%91%E6%B8%85%E9%A3%8E
2026-02-13 22:46:02 - extractor - INFO - 收集完成，共 0 篇帖子
```

**所有作者**的扫描都出现了 `net::ERR_ABORTED` 错误，包括：
- 独醉笑清风
- 清风皓月
- 同花顺心
- 厦门一只狼
- 我是抵触情绪

### URL 格式验证

用户确认 `https://t66y.com/@作者名` 在浏览器中手动访问是**可以正常工作的**，可以看到作者在所有版块的帖子。

这证明：
- ✅ URL 格式本身是正确的
- ❌ 问题不是 URL 错误
- ⚠️ 问题是自动化工具被检测和阻止

---

## 反爬虫检测机制

论坛可能使用以下方式检测 Playwright：

### 1. navigator.webdriver 检测
```javascript
if (navigator.webdriver === true) {
  // 检测到自动化工具，阻止访问
}
```

### 2. User-Agent 识别
Playwright 的默认 User-Agent 可能被识别为爬虫。

### 3. 行为模式分析
- 缺少鼠标移动
- 缺少滚动事件
- 访问速度过于规律
- 没有停留时间

### 4. JavaScript 挑战
- 页面可能执行 JS 代码检测自动化特征
- 可能使用 Cloudflare 或类似服务

### 5. Cookie/Session 检测
- `@作者名` URL 可能需要先访问主页建立有效 session
- 直接访问会被拒绝

---

## 数据流分析

### 刷新检测流程（失败）

```
用户: 刷新检测新帖
  ↓
_refresh_check_new_posts()
  ↓
checker.batch_check_authors(authors, max_pages=3)
  ↓
对每个作者: checker.check_new_posts(author_name, author_url)
  ↓
extractor.collect_post_urls("https://t66y.com/@作者名", max_pages=3)
  ↓
page.goto(url) → 论坛检测到 Playwright
  ↓
net::ERR_ABORTED（连接被中止）
  ↓
返回空列表: []
  ↓
tracker.check_new_posts(author_name, [])
  ↓
返回: {'total_forum': 0, 'has_new': False, ...}
  ↓
回到 _refresh_check_new_posts()
  ↓
检查: if result.get('total_forum'):  → False（0 是 falsy）
  ↓
❌ 不执行更新 forum_total_posts 的逻辑
```

### 为什么部分作者有 forum_total_posts？

查看配置文件 `python/config.yaml`：

```yaml
- name: 同花顺心
  forum_total_posts: 60
  forum_stats_updated: '2026-02-13'

- name: cyruscc
  forum_total_posts: 2
  forum_stats_updated: '2026-02-13'
```

这些作者有 `forum_total_posts`，可能因为：

1. **在归档流程中获得**
   - 归档时可能使用了不同的 URL 格式（搜索 URL）
   - 搜索 URL: `thread0806.php?fid=7&search=作者名`
   - 反爬虫检测可能较松

2. **更早时间获得**
   - 那时论坛的反爬虫规则还不严格
   - 或者首次访问时被允许（建立 session）

3. **使用了不同的访问方式**
   - 通过版块搜索而不是直接访问 `@作者名` URL

---

## 代码缺陷

### main_menu.py:957

```python
if result.get('total_forum'):
    old_total = author.get('forum_total_posts', 0)
    new_total = result['total_forum']
    author['forum_total_posts'] = max(old_total, new_total)
```

**问题：** 当 `total_forum = 0` 时，`result.get('total_forum')` 返回 0，在 if 判断中被视为 `False`，导致更新逻辑不执行。

**应该改为：**
```python
if 'total_forum' in result:
    # 或者
if result.get('total_forum') is not None:
```

但这只是次要问题，主要问题还是扫描被论坛阻止。

---

## 解决方案方向

### 方案 A: 绕过反爬虫检测

#### 1. 隐藏 webdriver 属性
```python
await page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    })
""")
```

#### 2. 设置真实 User-Agent
```python
await browser.new_context(
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...'
)
```

#### 3. 添加人类行为
- 随机延迟（0.5-2秒）
- 模拟鼠标移动
- 滚动页面

#### 4. 先访问主页建立 session
```python
await page.goto('https://t66y.com/')
await asyncio.sleep(2)
await page.goto(author_url)
```

#### 5. 使用 stealth plugin
```python
from playwright_stealth import stealth_async
await stealth_async(page)
```

### 方案 B: 使用搜索 URL

改为使用版块搜索 URL 而不是 `@作者名` URL：

```python
# 当前
author_url = "https://t66y.com/@作者名"

# 改为
author_url = "https://t66y.com/thread0806.php?fid=7&search=作者名"
```

**优势：**
- 搜索 URL 反爬虫检测可能较松
- 已有作者过滤逻辑（extractor.py:140-153）

**劣势：**
- 只能搜索特定版块（fid=7）
- 无法获取作者在所有版块的帖子

### 方案 C: API 或 RSS

如果论坛提供 API 或 RSS：
- 使用官方接口
- 避免反爬虫问题

### 方案 D: 降低频率

- 减少并发请求（max_concurrent=1）
- 增加延迟（rate_limit_delay=2.0）
- 每次只刷新部分作者

---

## 用户决策

**2026-02-13：** 用户决定暂时保持当前设计，不立即修复反爬虫问题。

**理由：**
- 刷新功能是辅助功能，不影响核心归档
- 修复需要较多工作量
- Phase 2 开发优先级更高

**未来可能行动：**
- 等待 Phase 2 完成后再考虑
- 或者用户反馈需要时再处理
- 或者采用方案 B（搜索 URL）作为折中方案

---

## 相关文件

- `python/src/scraper/extractor.py` - collect_post_urls() 方法
- `python/src/scraper/checker.py` - check_new_posts() 方法
- `python/src/menu/main_menu.py` - _refresh_check_new_posts() 方法
- `logs/extractor.log` - 错误日志记录

---

## 参考文档

- [Playwright Stealth](https://github.com/AtuboDad/playwright_stealth)
- [反爬虫检测绕过技术](https://scrapfly.io/blog/playwright-stealth-mode/)
- [网页自动化最佳实践](https://playwright.dev/python/docs/auth)
