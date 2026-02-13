# 正文内容清理问题修复

**问题**: 生成的 content.html 正文中有孤立的 `</div>` 标签和格式不统一

**日期**: 2026-02-12

---

## 🔍 问题表现

### 现象
用户报告：
> 新下载整理的页面，并没有符合统一的格式，页面前半部分还是自由摆放，后半部分是统一的

### 实际问题（第 392 行）
```html
<article>
    <p>经过几天几夜的偷摸查探，最终还是被我发现了证据。 </div> </div> 看着聊天记录...
    偷偷发两张她的身材照 </div> </div> 敬请期待下一期</p>
</article>
```

**问题点**:
- ❌ 孤立的 `</div>` 标签（共 4 个）
- ❌ HTML 结构不完整
- ❌ 可能还有图片标签残留

---

## 🔎 根因分析

### 当前的 `clean_html_content` 函数（filters.py）

```python
# 1. 移除图片 div（会在底部单独列出）
html = re.sub(
    r'<div\s+class="image-big">.*?</div>',
    '',
    html,
    flags=re.DOTALL | re.IGNORECASE
)
```

**问题**:
1. **正则表达式不够全面**：
   - 只匹配 `<div class="image-big">...</div>`
   - 如果图片在其他容器中（如 `<div class="image">` 或 `<a><img></a>`），不会被移除

2. **残留结束标签**：
   - 如果 HTML 嵌套复杂（如 `<div><div><img></div></div>`），正则可能只匹配内层，留下外层的 `</div>`

3. **没有移除 `<img>` 标签本身**：
   - 如果正文中有裸的 `<img>` 标签（没有 div 包裹），不会被移除

### 原始 HTML 可能的结构

```html
<!-- 可能的图片 HTML 格式 -->
<div class="image-big">
    <div>
        <img src="photo/xxx.jpg" />
    </div>
</div>

<!-- 或者 -->
<a href="photo/xxx.jpg">
    <img src="photo/xxx.jpg" />
</a>

<!-- 或者裸标签 -->
<img src="photo/xxx.jpg" />
```

---

## 💡 解决方案

### 方案 A: 改进正则表达式（推荐） ⭐⭐⭐⭐⭐

**修改 `filters.py` 中的 `clean_html_content` 函数**：

```python
def clean_html_content(raw_html: str) -> str:
    """
    清理原始 HTML，转换为适合阅读的格式

    Args:
        raw_html: 从网页提取的原始 HTML

    Returns:
        清理后的 HTML（段落结构、章节标题）
    """
    if not raw_html or not raw_html.strip():
        return '<p>（无内容）</p>'

    html = raw_html

    # ========== 新增：更彻底的图片/视频清理 ==========

    # 1. 移除所有 <img> 标签（不管是否有包裹）
    html = re.sub(
        r'<img[^>]*>',
        '',
        html,
        flags=re.IGNORECASE
    )

    # 2. 移除图片链接（<a href="xxx.jpg"><img></a> 或 <a href="xxx.jpg">查看图片</a>）
    html = re.sub(
        r'<a\s+[^>]*href=["\'][^"\']*\.(jpg|jpeg|png|gif|webp|bmp)["\'][^>]*>.*?</a>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 3. 移除图片 div 容器（各种可能的 class 名称）
    html = re.sub(
        r'<div\s+class=["\']?(image-big|image|img-container|pic)["\']?[^>]*>.*?</div>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 4. 移除视频标签（会在底部单独列出）
    html = re.sub(
        r'<video[^>]*>.*?</video>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 5. 移除 <source> 标签（视频源）
    html = re.sub(
        r'<source[^>]*>',
        '',
        html,
        flags=re.IGNORECASE
    )

    # ========== 新增：清理残留标签 ==========

    # 6. 移除孤立的 </div> 标签
    html = re.sub(r'</div>\s*', ' ', html, flags=re.IGNORECASE)

    # 7. 移除孤立的 <div> 开始标签（没有对应的结束标签）
    html = re.sub(r'<div[^>]*>\s*', ' ', html, flags=re.IGNORECASE)

    # 8. 移除空的 <a> 标签
    html = re.sub(r'<a[^>]*>\s*</a>', '', html, flags=re.IGNORECASE)

    # ========== 原有逻辑 ==========

    # 9. 移除点赞按钮等无关元素
    html = re.sub(
        r'<div\s+onclick="clickLike.*?</div>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 10. 转换连续 <br> 为段落分隔
    html = re.sub(r'(<br\s*/?>){2,}', '</p>\n<p>', html, flags=re.IGNORECASE)

    # 11. 移除剩余的单个 <br>（段落内换行）
    html = re.sub(r'<br\s*/?>', ' ', html, flags=re.IGNORECASE)

    # 12. 识别章节标题（如 "01." "一、" 开头）
    html = re.sub(
        r'<p>\s*(\d+\.|\d+、|[一二三四五六七八九十]+、)\s*([^<]+?)\s*</p>',
        r'<h2>\1 \2</h2>',
        html
    )

    # 13. 包裹段落（如果还没有）
    if not html.strip().startswith('<p>') and not html.strip().startswith('<h'):
        html = f'<p>{html}</p>'

    # 14. 清理多余空格
    html = re.sub(r'\s{2,}', ' ', html)

    # 15. 清理多余空行
    html = re.sub(r'\n{3,}', '\n\n', html)

    # 16. 清理空段落
    html = re.sub(r'<p>\s*</p>', '', html)

    # 17. 去除首尾空白
    html = html.strip()

    return html
```

### 关键改进点

| 改进项 | 旧版 | 新版 |
|--------|------|------|
| 移除 `<img>` | ❌ 只移除特定 div 中的 | ✅ 移除所有 `<img>` 标签 |
| 图片链接 | ❌ 不处理 | ✅ 移除 `<a href="xxx.jpg">` |
| 孤立标签 | ❌ 留下 `</div>` | ✅ 清理所有孤立的 `<div>` 和 `</div>` |
| 视频标签 | ✅ 已处理 | ✅ 增强（包括 `<source>`） |
| 空格清理 | ❌ 不完善 | ✅ 清理多余空格 |

---

## 📋 实施步骤

### Step 1: 备份当前文件
```bash
cp python/src/templates/filters.py python/src/templates/filters.py.backup
```

### Step 2: 修改 `filters.py`
替换 `clean_html_content` 函数为上述新版本

### Step 3: 测试修复效果
```bash
# 重新生成测试帖子
cd /home/ben/gemini-work/gemini-t66y
python test_template.py
```

### Step 4: 验证结果
打开生成的 content.html，检查：
- [ ] 正文中没有孤立的 `</div>` 标签
- [ ] 正文中没有 `<img>` 标签
- [ ] 图片只在底部的"图片列表"部分显示
- [ ] 正文格式整洁，段落清晰

---

## 🧪 测试用例

### Test 1: 孤立标签清理
**输入**:
```html
<p>文本内容 </div> </div> 更多文本</p>
```

**预期输出**:
```html
<p>文本内容 更多文本</p>
```

### Test 2: 图片标签移除
**输入**:
```html
<p>文本 <img src="photo/1.jpg"> 更多文本</p>
```

**预期输出**:
```html
<p>文本 更多文本</p>
```

### Test 3: 图片容器移除
**输入**:
```html
<div class="image-big"><img src="1.jpg"></div>
```

**预期输出**:
```html
（空字符串）
```

### Test 4: 图片链接移除
**输入**:
```html
<p>文本 <a href="photo/1.jpg">查看图片</a> 更多文本</p>
```

**预期输出**:
```html
<p>文本 更多文本</p>
```

---

## 🎯 预期效果

**修复前**:
```html
<article>
    <p>文本 </div> </div> <img src="1.jpg"> 更多文本</p>
</article>
```

**修复后**:
```html
<article>
    <p>文本 更多文本</p>
</article>
```

---

**推荐行动**: 立即实施方案 A，预计 5 分钟完成。
