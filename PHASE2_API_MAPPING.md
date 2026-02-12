# Phase 2: Node.js 到 Python Playwright API 映射表

> **用途**: Phase 2 实施时的快速参考指南
> **创建日期**: 2026-02-11
> **适用版本**: Playwright Node.js 1.42.x → Playwright Python 1.42.x

---

## 📋 目录

- [基础 API 对照](#基础-api-对照)
- [元素查询](#元素查询)
- [页面操作](#页面操作)
- [等待机制](#等待机制)
- [内容提取](#内容提取)
- [完整示例对比](#完整示例对比)
- [常见陷阱](#常见陷阱)

---

## 基础 API 对照

### 浏览器启动

| Node.js | Python | 说明 |
|---------|--------|------|
| `const browser = await chromium.launch()` | `browser = await p.chromium.launch()` | 需要在 `async_playwright()` 上下文中 |
| `const context = await browser.newContext()` | `context = await browser.new_context()` | 驼峰 → 下划线 |
| `const page = await context.newPage()` | `page = await context.new_page()` | 驼峰 → 下划线 |
| `await browser.close()` | `await browser.close()` | 相同 |

**Python 完整上下文示例**：
```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    # ... 操作
    await browser.close()
```

---

## 元素查询

### 查询单个元素

| Node.js | Python | 说明 |
|---------|--------|------|
| `const el = await page.$(selector)` | `el = await page.query_selector(selector)` | `$` → `query_selector` |
| `const el = await page.waitForSelector(sel)` | `el = await page.wait_for_selector(sel)` | 驼峰 → 下划线 |
| `const text = await el.textContent()` | `text = await el.text_content()` | 驼峰 → 下划线 |
| `const attr = await el.getAttribute('href')` | `attr = await el.get_attribute('href')` | 驼峰 → 下划线 |

### 查询多个元素

| Node.js | Python | 说明 |
|---------|--------|------|
| `const els = await page.$$(selector)` | `els = await page.query_selector_all(selector)` | `$$` → `query_selector_all` |
| `const count = els.length` | `count = len(els)` | JS 属性 → Python 内置函数 |

### 元素评估（Evaluate）

| Node.js | Python | 说明 |
|---------|--------|------|
| `await page.$eval(sel, el => el.textContent)` | `await page.eval_on_selector(sel, 'el => el.textContent')` | **注意**：Python 需要字符串形式的 JS 代码 |
| `await page.$$eval(sel, els => els.map(...))` | `await page.eval_on_selector_all(sel, 'els => ...')` | 同上 |

**重要差异示例**：

Node.js:
```javascript
const titles = await page.$$eval('h3 > a', links => {
    return links.map(link => link.textContent.trim());
});
```

Python:
```python
titles = await page.eval_on_selector_all('h3 > a', '''
    links => links.map(link => link.textContent.trim())
''')
```

---

## 页面操作

### 导航

| Node.js | Python | 说明 |
|---------|--------|------|
| `await page.goto(url)` | `await page.goto(url)` | 相同 |
| `await page.goto(url, { waitUntil: 'domcontentloaded' })` | `await page.goto(url, wait_until='domcontentloaded')` | 选项参数：驼峰 → 下划线 |
| `await page.reload()` | `await page.reload()` | 相同 |
| `await page.goBack()` | `await page.go_back()` | 驼峰 → 下划线 |

### 交互操作

| Node.js | Python | 说明 |
|---------|--------|------|
| `await page.click(selector)` | `await page.click(selector)` | 相同 |
| `await page.fill(selector, text)` | `await page.fill(selector, text)` | 相同 |
| `await page.type(selector, text)` | `await page.type(selector, text)` | 相同 |
| `await page.screenshot({ path: 'pic.png' })` | `await page.screenshot(path='pic.png')` | 对象参数 → 关键字参数 |

---

## 等待机制

### 等待导航

| Node.js | Python | 说明 |
|---------|--------|------|
| `await page.waitForNavigation()` | `await page.wait_for_load_state('networkidle')` | **API 变化** |
| `await page.waitForNavigation({ waitUntil: 'domcontentloaded' })` | `await page.wait_for_load_state('domcontentloaded')` | 更明确的语义 |

**重要**：Python 中没有 `wait_for_navigation()`，使用 `wait_for_load_state()` 替代。

### 等待元素/条件

| Node.js | Python | 说明 |
|---------|--------|------|
| `await page.waitForSelector(sel)` | `await page.wait_for_selector(sel)` | 驼峰 → 下划线 |
| `await page.waitForTimeout(1000)` | `await page.wait_for_timeout(1000)` | 驼峰 → 下划线 |
| `await page.waitForFunction(fn)` | `await page.wait_for_function(fn)` | 驼峰 → 下划线 |

### 选项参数差异

Node.js:
```javascript
await page.waitForSelector('#tbody', {
    timeout: 60000,
    state: 'visible'
});
```

Python:
```python
await page.wait_for_selector('#tbody',
    timeout=60000,
    state='visible'
)
```

---

## 内容提取

### 获取文本内容

| 操作 | Node.js | Python |
|------|---------|--------|
| 单个元素文本 | `const text = await page.$eval('h4', el => el.textContent)` | `text = await page.eval_on_selector('h4', 'el => el.textContent')` |
| 或直接获取 | `const el = await page.$('h4');`<br>`const text = await el.textContent();` | `el = await page.query_selector('h4')`<br>`text = await el.text_content()` |
| 多个元素文本 | `const texts = await page.$$eval('a', els => els.map(e => e.textContent))` | `texts = await page.eval_on_selector_all('a', 'els => els.map(e => e.textContent)')` |

### 获取属性

| 操作 | Node.js | Python |
|------|---------|--------|
| href 属性 | `const href = await page.$eval('a', el => el.href)` | `href = await page.eval_on_selector('a', 'el => el.href')` |
| 或直接获取 | `const el = await page.$('a');`<br>`const href = await el.getAttribute('href');` | `el = await page.query_selector('a')`<br>`href = await el.get_attribute('href')` |
| data 属性 | `await el.getAttribute('data-timestamp')` | `await el.get_attribute('data-timestamp')` |

### innerHTML / innerText

| Node.js | Python |
|---------|--------|
| `const html = await page.$eval('#content', el => el.innerHTML)` | `html = await page.eval_on_selector('#content', 'el => el.innerHTML')` |
| `const text = await page.$eval('#content', el => el.innerText)` | `text = await page.eval_on_selector('#content', 'el => el.innerText')` |

---

## 完整示例对比

### 示例 1: 收集帖子链接（archive_posts.js 核心逻辑）

**Node.js 版本**:
```javascript
const pagePostInfos = await page.$$eval('#tbody tr', (rows, authors) => {
    return rows.map(row => {
        const authorElement = row.querySelector('.bl');
        const titleElement = row.querySelector('h3 > a');
        if (authorElement && titleElement && authors.includes(authorElement.textContent.trim())) {
            return {
                author: authorElement.textContent.trim(),
                url: titleElement.href
            };
        }
        return null;
    }).filter(Boolean);
}, authorsToScrape);
```

**Python 等价版本**:
```python
page_post_infos = await page.eval_on_selector_all(
    '#tbody tr',
    '''(rows, authors) => {
        return rows.map(row => {
            const authorElement = row.querySelector('.bl');
            const titleElement = row.querySelector('h3 > a');
            if (authorElement && titleElement && authors.includes(authorElement.textContent.trim())) {
                return {
                    author: authorElement.textContent.trim(),
                    url: titleElement.href
                };
            }
            return null;
        }).filter(Boolean);
    }''',
    authors_to_scrape
)
```

**替代方案（更 Pythonic）**:
```python
# 获取所有行
rows = await page.query_selector_all('#tbody tr')

page_post_infos = []
for row in rows:
    author_el = await row.query_selector('.bl')
    title_el = await row.query_selector('h3 > a')

    if author_el and title_el:
        author_name = (await author_el.text_content()).strip()
        if author_name in authors_to_scrape:
            page_post_infos.append({
                'author': author_name,
                'url': await title_el.get_attribute('href')
            })
```

---

### 示例 2: 提取帖子内容（archive_posts.js）

**Node.js 版本**:
```javascript
const title = await page.$eval('h4.f16', el => el.textContent.trim());
const timestamp = await page.$eval('span[data-timestamp]', el => el.getAttribute('data-timestamp'));

// 提取内容
const rawContent = await page.$eval('.tpc_content', el => el.innerHTML);
```

**Python 等价版本**:
```python
title = await page.eval_on_selector('h4.f16', 'el => el.textContent.trim()')
timestamp = await page.eval_on_selector('span[data-timestamp]', 'el => el.getAttribute("data-timestamp")')

# 提取内容
raw_content = await page.eval_on_selector('.tpc_content', 'el => el.innerHTML')
```

**或使用直接 API（推荐）**:
```python
title_el = await page.wait_for_selector('h4.f16')
title = (await title_el.text_content()).strip()

timestamp_el = await page.wait_for_selector('span[data-timestamp]')
timestamp = await timestamp_el.get_attribute('data-timestamp')

content_el = await page.wait_for_selector('.tpc_content')
raw_content = await content_el.inner_html()
```

---

### 示例 3: 页面翻页逻辑

**Node.js 版本**:
```javascript
const nextPageButton = await page.$('a:has-text("下一頁")');
if (nextPageButton && !(await nextPageButton.evaluate(node => node.classList.contains('gray')))) {
    await nextPageButton.click();
    await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 60000 });
    currentPage++;
} else {
    break;
}
```

**Python 等价版本**:
```python
next_page_button = await page.query_selector('a:has-text("下一頁")')
if next_page_button:
    is_disabled = await next_page_button.evaluate('node => node.classList.contains("gray")')
    if not is_disabled:
        await next_page_button.click()
        await page.wait_for_load_state('domcontentloaded', timeout=60000)
        current_page += 1
    else:
        break
else:
    break
```

---

## 常见陷阱

### 1. 驼峰命名 vs 下划线命名

❌ **错误**:
```python
await page.waitForSelector('#tbody')  # AttributeError
```

✅ **正确**:
```python
await page.wait_for_selector('#tbody')
```

---

### 2. 对象参数 vs 关键字参数

❌ **错误**:
```python
await page.goto(url, { 'waitUntil': 'domcontentloaded' })  # SyntaxError
```

✅ **正确**:
```python
await page.goto(url, wait_until='domcontentloaded')
```

---

### 3. waitForNavigation 已废弃

❌ **错误**:
```python
await page.wait_for_navigation()  # AttributeError: 不存在此方法
```

✅ **正确**:
```python
await page.wait_for_load_state('networkidle')
# 或
await page.wait_for_load_state('domcontentloaded')
```

---

### 4. eval 函数需要字符串形式

❌ **错误**:
```python
# 尝试传递 Python lambda
titles = await page.eval_on_selector_all('a', lambda els: [e.text_content for e in els])
```

✅ **正确**:
```python
# 传递 JavaScript 代码字符串
titles = await page.eval_on_selector_all('a', 'els => els.map(e => e.textContent)')
```

---

### 5. 数组访问

❌ **错误**:
```python
elements = await page.query_selector_all('a')
first = elements[0]  # ElementHandle 对象，可以直接索引
```

✅ **正确**:
```python
elements = await page.query_selector_all('a')
first = elements[0]  # 实际上这是正确的！Python 列表可以索引
```

---

## 快速查询表

| 类别 | Node.js 关键词 | Python 关键词 |
|------|---------------|--------------|
| 命名风格 | camelCase | snake_case |
| 查询单个 | `$()` | `query_selector()` |
| 查询多个 | `$$()` | `query_selector_all()` |
| 单个 eval | `$eval()` | `eval_on_selector()` |
| 多个 eval | `$$eval()` | `eval_on_selector_all()` |
| 等待元素 | `waitForSelector()` | `wait_for_selector()` |
| 等待导航 | `waitForNavigation()` | `wait_for_load_state()` |
| 获取文本 | `textContent()` | `text_content()` |
| 获取属性 | `getAttribute()` | `get_attribute()` |
| HTML 内容 | `innerHTML()` | `inner_html()` |
| 参数传递 | `{ key: value }` | `key=value` |

---

## 实用技巧

### 技巧 1: 复杂 JS 代码使用三引号字符串

```python
result = await page.eval_on_selector_all('.post', '''
    posts => {
        return posts
            .filter(p => p.textContent.length > 100)
            .map(p => ({
                title: p.querySelector('h3')?.textContent,
                author: p.querySelector('.author')?.textContent
            }));
    }
''')
```

### 技巧 2: 优先使用直接 API 而非 eval

```python
# 不推荐（虽然可行）
text = await page.eval_on_selector('h1', 'el => el.textContent')

# 推荐（更清晰，类型安全）
el = await page.query_selector('h1')
text = await el.text_content()
```

### 技巧 3: 批量操作使用列表推导

```python
rows = await page.query_selector_all('tr')

# 并发提取所有行的文本
texts = await asyncio.gather(*[
    row.text_content() for row in rows
])
```

---

## 参考资源

- **Playwright Python 官方文档**: https://playwright.dev/python/docs/intro
- **API 参考**: https://playwright.dev/python/docs/api/class-page
- **Node.js 到 Python 迁移指南**: https://playwright.dev/python/docs/languages

---

**文档版本**: 1.0
**最后更新**: 2026-02-11
**下一步**: 参考 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) Phase 2 章节开始实施
