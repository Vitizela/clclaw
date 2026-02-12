# Phase 2.5: HTML 模板统一优化

> **版本**: v2.5
> **状态**: 🔴 待开始
> **创建日期**: 2026-02-12
> **预计工期**: 1 小时
> **优先级**: P1（用户体验提升 + 简化 Phase 3）

---

## 📋 目录

- [一、概述](#一概述)
- [二、问题分析](#二问题分析)
- [三、解决方案](#三解决方案)
- [四、详细实施步骤](#四详细实施步骤)
- [五、验收标准](#五验收标准)
- [六、测试清单](#六测试清单)
- [七、对后续 Phase 的影响](#七对后续-phase-的影响)
- [八、回滚方案](#八回滚方案)

---

## 一、概述

### 1.1 目标

**核心目标**：统一所有归档帖子的 `content.html` 格式，优化终端浏览体验

**具体目标**：
1. ✅ 统一 HTML 模板（单一标准格式）
2. ✅ 优化 w3m 终端浏览器支持
3. ✅ 元数据可见化（从注释移到页面）
4. ✅ 媒体文件清单化（图片/视频列表）
5. ✅ 简化 Phase 3 数据库导入

### 1.2 背景

**当前状态**（Phase 2 完成后）：
- ✅ Python 爬虫已实现并启用（`use_python_scraper: true`）
- ✅ 已归档 278 篇测试帖子（7 位作者）
- ❌ content.html 格式不统一（纯文本/图片/视频各不相同）
- ❌ w3m 浏览体验差（缺少结构、元数据隐藏）

**简化前提**：
- 🗑️ 测试数据可删除（无需向后兼容）
- ✅ 从零开始采用最优方案
- ✅ 无历史包袱，无技术债

### 1.3 收益

**用户体验**：
- ✅ w3m 终端浏览体验优化（清晰结构、易于导航）
- ✅ 元数据可见（标题、作者、时间、URL）
- ✅ 本地文件清单（photo/img_1.jpg, video/video_1.mp4）

**开发效率**：
- ✅ Phase 3 开发时间节省 **2 小时**（无需解析多种格式）
- ✅ 历史数据导入工具不需要（测试数据已删除）
- ✅ 测试验证简化（单一格式，无混合）

**代码质量**：
- ✅ 格式统一，易于维护
- ✅ 零技术债，无兼容逻辑
- ✅ 模板化设计，扩展方便

---

## 二、问题分析

### 2.1 当前 content.html 格式问题

#### 问题 1: 格式严重不统一

**纯文本帖子**：
```html
<!-- 帖子元数据
标题: 揭秘河南地产王的起伏人生
作者: 独醉笑清风
时间: 2022-08-29 06:53
URL: https://t66y.com/htm_data/2208/7/5254402.html
-->

谨慎半生...<br><br><br><br>"我已经快70岁了..."<br><br><br>01.<br>中原第一枪<br><br>...
```

**图片帖子**：
```html
<!-- 帖子元数据... -->

五点半的早晨，<br>周围乌漆嘛黑，<br>...<br>
<div class="image-big">
  <img iyl-data="..." ess-data="..." src="..." style="...">
  <div class="image-big-text">链接</div>
</div><br>
<div class="image-big">...</div><br>
...
```

**视频帖子**：
```html
<!-- 帖子元数据... -->

<video src="https://..." controls="controls" style="..." loop="true">
  您的浏览器不支持 video 标签。
</video><br>
<video src="..."></video><br>
...
```

**问题总结**：
- ❌ 三种完全不同的 HTML 结构
- ❌ 没有统一的页面框架
- ❌ 内联样式混乱（`style="..."` 到处都是）

#### 问题 2: 关键信息隐藏或缺失

- ❌ **元数据在注释中**：用户在浏览器/w3m 中看不到标题、作者、时间
- ❌ **没有本地文件清单**：不知道 `photo/` 目录下有哪些图片
- ❌ **没有归档统计**：不知道本帖共多少张图片、多少个视频
- ❌ **没有归档时间**：不知道何时抓取的

#### 问题 3: w3m 浏览器兼容性差

- ❌ **缺少完整 HTML 结构**：无 `<!DOCTYPE>`, `<head>`, `<body>`
- ❌ **复杂的 div 嵌套**：`<div class="image-big">` w3m 渲染混乱
- ❌ **缺少语义化标签**：没有 `<article>`, `<header>`, `<section>`
- ❌ **图片/视频无本地链接**：只能在线查看，不能点击本地文件

#### 问题 4: 排版不美观

- ❌ **连续多个 `<br>`**：`<br><br><br><br>` 空白过多
- ❌ **没有段落结构**：应该用 `<p>` 而非 `<br>`
- ❌ **标题不突出**：章节标题（如 "01. 中原第一枪"）是普通文本
- ❌ **媒体资源无组织**：图片/视频混在正文中

### 2.2 w3m 浏览效果对比

#### 当前效果（问题）
```
谨慎半生...(大段文本无结构)

01.(标题不突出)
中原第一枪(没有分隔)

(连续空行)(连续空行)(连续空行)

胡葆森搞房地产...(段落不清晰)

[image-big](div标签显示为文本)
[链接](无法点击)
```

#### 期望效果（优化后）
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
揭秘河南地产王的起伏人生
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
作者: 独醉笑清风 | 发布: 2022-08-29 06:53 | 归档: 2026-02-12

  谨慎半生，坐地称王的河南地产一哥、建业董事长胡葆森，
30年来躲过数波大风大浪...

01. 中原第一枪
───────────────────────────────────────────────

  胡葆森搞房地产的想法，是在1992年春天迸发的...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📷 图片 (22)
[1] photo/img_1.jpg (可点击)
[2] photo/img_2.jpg (可点击)
...
```

---

## 三、解决方案

### 3.1 技术选型

#### 模板引擎：Jinja2

**选择理由**：
- ✅ Python 生态标准（Flask, Django 都使用）
- ✅ 语法简洁（`{{ var }}`, `{% if %}`, `{% for %}`）
- ✅ 功能强大（过滤器、继承、宏）
- ✅ 已在 requirements.txt 中（无需额外安装）

**替代方案对比**：
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **Jinja2** | 标准、强大、易用 | - | ✅ 采用 |
| f-string | 简单、无依赖 | 复杂模板难维护 | ❌ 不适合 |
| string.Template | 无依赖 | 功能太弱 | ❌ 不适合 |
| 手写拼接 | 灵活 | 代码混乱 | ❌ 不适合 |

#### HTML 设计原则

1. **语义化标签优先**：`<article>`, `<header>`, `<section>`, `<footer>`
2. **w3m 友好 CSS**：只使用 w3m 支持的基础样式
3. **纯文本可读**：即使没有 CSS 也结构清晰
4. **单文件完整**：无外部 CSS/JS 依赖

### 3.2 架构设计

#### 文件结构

```
python/src/templates/
  ├── __init__.py                 # 空文件
  ├── post.html                   # 主模板（80 行）
  └── filters.py                  # 内容清理过滤器（60 行）

python/src/scraper/
  └── archiver.py                 # 修改保存逻辑（30 行改动）
```

#### 数据流

```
帖子原始数据 (dict)
    ↓
内容清理 (filters.clean_html_content)
    ↓
模板渲染 (Jinja2)
    ↓
生成 HTML (post.html)
    ↓
保存文件 (content.html)
```

#### 模板变量

```python
template_data = {
    # 元数据
    'title': str,              # 帖子标题
    'author': str,             # 作者名
    'publish_time': str,       # 发布时间 (YYYY-MM-DD HH:MM)
    'archive_time': str,       # 归档时间 (YYYY-MM-DD HH:MM:SS)
    'url': str,                # 原始 URL

    # 正文
    'content': str,            # HTML 内容（会通过 filter 清理）
    'content_length': int,     # 字符数

    # 媒体
    'images': List[dict],      # [{'filename': 'img_1.jpg', 'url': '...'}, ...]
    'videos': List[dict],      # [{'filename': 'video_1.mp4', 'url': '...'}, ...]
}
```

---

## 四、详细实施步骤

### Step 1: 创建模板文件（15 分钟）

#### 1.1 创建目录结构

```bash
mkdir -p python/src/templates
touch python/src/templates/__init__.py
```

#### 1.2 创建主模板 `python/src/templates/post.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ author }}</title>
    <style>
        /* 极简 CSS，w3m 友好 */
        body {
            max-width: 800px;
            margin: 20px auto;
            padding: 0 15px;
            line-height: 1.6;
            font-family: monospace;
        }
        h1 {
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        .meta {
            color: #666;
            margin: 5px 0;
            font-size: 0.95em;
        }
        .meta b {
            color: #000;
        }
        article {
            margin: 30px 0;
        }
        article p {
            margin: 10px 0;
            text-indent: 2em;
        }
        article h2 {
            font-size: 1.3em;
            margin: 25px 0 15px 0;
            border-bottom: 1px solid #999;
            padding-bottom: 5px;
        }
        section {
            margin: 30px 0;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }
        section h2 {
            font-size: 1.2em;
            border-bottom: none;
        }
        .file {
            margin: 5px 0;
            padding: 5px;
            border-left: 3px solid #ccc;
            padding-left: 10px;
        }
        .file a {
            color: #06c;
            text-decoration: none;
        }
        .file a:hover {
            text-decoration: underline;
        }
        footer {
            border-top: 1px solid #ccc;
            margin-top: 30px;
            padding-top: 10px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>

<!-- 头部：元数据 -->
<header>
    <h1>{{ title }}</h1>
    <div class="meta">
        <b>作者:</b> {{ author }} |
        <b>发布:</b> {{ publish_time }} |
        <b>归档:</b> {{ archive_time }}
    </div>
    <div class="meta">
        <b>原文:</b> <a href="{{ url }}">{{ url }}</a>
    </div>
</header>

<!-- 正文 -->
<article>
    {{ content|safe }}
</article>

<!-- 图片列表 -->
{% if images %}
<section>
    <h2>📷 图片 ({{ images|length }})</h2>
    {% for img in images %}
    <div class="file">
        <strong>[{{ loop.index }}]</strong>
        <a href="photo/{{ img.filename }}">photo/{{ img.filename }}</a>
        {% if img.size %}({{ img.size }}){% endif %}
    </div>
    {% endfor %}
</section>
{% endif %}

<!-- 视频列表 -->
{% if videos %}
<section>
    <h2>🎬 视频 ({{ videos|length }})</h2>
    {% for vid in videos %}
    <div class="file">
        <strong>[{{ loop.index }}]</strong>
        <a href="video/{{ vid.filename }}">video/{{ vid.filename }}</a>
        {% if vid.size %}({{ vid.size }}){% endif %}
    </div>
    {% endfor %}
</section>
{% endif %}

<!-- 页脚：统计 -->
<footer>
    <p>
        <b>统计:</b> {{ content_length }} 字符 |
        {{ images|length }} 图片 |
        {{ videos|length }} 视频
    </p>
    <p>
        <b>归档:</b> {{ archive_time }} |
        <b>生成器:</b> Python Scraper v2.5 (Playwright + Jinja2)
    </p>
    <p>
        <b>终端浏览:</b> <code>w3m content.html</code>
    </p>
</footer>

</body>
</html>
```

**验证**：
```bash
wc -l python/src/templates/post.html
# 应输出约 80 行
```

---

### Step 2: 创建过滤器（15 分钟）

#### 2.1 创建 `python/src/templates/filters.py`

```python
"""HTML 内容清理和格式化

功能：
1. 移除复杂的 div 嵌套
2. 转换连续 <br> 为段落
3. 提取章节标题
4. 移除图片/视频标签（单独列表展示）
5. 优化 w3m 浏览体验
"""
import re


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

    # 1. 移除图片 div（会在底部单独列出）
    html = re.sub(
        r'<div\s+class="image-big">.*?</div>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 2. 移除视频标签（会在底部单独列出）
    html = re.sub(
        r'<video.*?</video>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 3. 移除点赞按钮等无关元素
    html = re.sub(
        r'<div\s+onclick="clickLike.*?</div>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 4. 转换连续 <br> 为段落分隔
    html = re.sub(r'(<br\s*/?>){2,}', '</p>\n<p>', html, flags=re.IGNORECASE)

    # 5. 移除剩余的单个 <br>（段落内换行）
    html = re.sub(r'<br\s*/?>', ' ', html, flags=re.IGNORECASE)

    # 6. 识别章节标题（如 "01." "一、" 开头）
    html = re.sub(
        r'<p>\s*(\d+\.|\d+、|[一二三四五六七八九十]+、)\s*([^<]+?)\s*</p>',
        r'<h2>\1 \2</h2>',
        html
    )

    # 7. 包裹段落（如果还没有）
    if not html.strip().startswith('<p>') and not html.strip().startswith('<h'):
        html = f'<p>{html}</p>'

    # 8. 清理多余空行
    html = re.sub(r'\n{3,}', '\n\n', html)

    # 9. 清理空段落
    html = re.sub(r'<p>\s*</p>', '', html)

    # 10. 去除首尾空白
    html = html.strip()

    return html


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化字符串（如 "1.2 MB"）
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
```

**验证**：
```bash
python3 -c "from src.templates.filters import clean_html_content; print('✓ 导入成功')"
```

---

### Step 3: 修改 Archiver（20 分钟）

#### 3.1 在 `python/src/scraper/archiver.py` 顶部添加导入

```python
# 在文件开头添加
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime
import sys

# 在其他导入之后添加
sys.path.insert(0, str(Path(__file__).parent.parent))
from templates.filters import clean_html_content, format_file_size
```

#### 3.2 修改 `__init__` 方法

```python
class ForumArchiver:
    def __init__(self, config: dict):
        # ... 现有代码 ...

        # 初始化模板引擎
        template_dir = Path(__file__).parent.parent / 'templates'
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

        # 注册自定义过滤器
        self.jinja_env.filters['clean'] = clean_html_content
        self.jinja_env.filters['size'] = format_file_size

        self.logger.info("模板引擎已初始化")
```

#### 3.3 添加新方法：准备媒体列表

在 `ForumArchiver` 类中添加以下方法：

```python
def _prepare_media_list(self, media_urls: list, media_type: str, post_dir: Path) -> list:
    """
    准备媒体文件列表（用于模板）

    Args:
        media_urls: 原始 URL 列表
        media_type: 'image' 或 'video'
        post_dir: 帖子目录

    Returns:
        [{'filename': 'img_1.jpg', 'url': '...', 'size': '1.2 MB'}, ...]
    """
    media_list = []

    # 确定子目录和文件前缀
    if media_type == 'image':
        subdir = post_dir / 'photo'
        prefix = 'img_'
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    else:  # video
        subdir = post_dir / 'video'
        prefix = 'video_'
        extensions = ['.mp4', '.avi', '.mkv', '.webm', '.mov']

    if not subdir.exists():
        return []

    # 遍历原始 URL，匹配本地文件
    for idx, url in enumerate(media_urls, 1):
        # 尝试找到对应的本地文件
        filename = None
        file_size = None

        # 方法1：按索引匹配（img_1.jpg, img_2.jpg...）
        for ext in extensions:
            candidate = subdir / f"{prefix}{idx}{ext}"
            if candidate.exists():
                filename = f"{prefix}{idx}{ext}"
                file_size = candidate.stat().st_size
                break

        # 如果找不到，使用占位
        if not filename:
            filename = f"{prefix}{idx}.unknown"

        media_list.append({
            'filename': filename,
            'url': url,
            'size': format_file_size(file_size) if file_size else None
        })

    return media_list
```

#### 3.4 修改保存内容的方法

找到原来保存 content.html 的地方（可能在 `_archive_post` 或类似方法中），替换为：

```python
def _save_content_html(self, post_data: dict, post_dir: Path):
    """
    使用模板生成并保存 content.html

    Args:
        post_data: 帖子数据（包含 title, author, time, content, images, videos, url）
        post_dir: 帖子目录
    """
    try:
        # 准备模板数据
        template_data = {
            'title': post_data.get('title', '无标题'),
            'author': post_data.get('author', '未知作者'),
            'publish_time': post_data.get('time', 'N/A'),
            'archive_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': post_data.get('url', ''),
            'content': clean_html_content(post_data.get('content', '')),
            'content_length': len(post_data.get('content', '')),
            'images': self._prepare_media_list(
                post_data.get('images', []),
                'image',
                post_dir
            ),
            'videos': self._prepare_media_list(
                post_data.get('videos', []),
                'video',
                post_dir
            )
        }

        # 加载模板
        template = self.jinja_env.get_template('post.html')

        # 渲染 HTML
        html = template.render(**template_data)

        # 保存文件
        content_file = post_dir / 'content.html'
        content_file.write_text(html, encoding='utf-8')

        self.logger.info(f"已生成 content.html: {template_data['title']}")

    except Exception as e:
        self.logger.error(f"生成 content.html 失败: {str(e)}", exc_info=True)
        raise
```

#### 3.5 在归档流程中调用

确保在归档流程中调用 `_save_content_html`：

```python
# 在 archive_author 或类似方法中，下载完成后：

# 下载图片和视频（现有逻辑）
# ...

# 使用新模板生成 content.html
self._save_content_html(post_data, post_dir)

# 标记完成
mark_complete(post_dir, post_url)
```

**验证**：
```bash
python3 -c "from src.scraper.archiver import ForumArchiver; print('✓ 导入成功')"
```

---

### Step 4: 测试与验证（10 分钟）

#### 4.1 归档测试帖子

```bash
cd python
python main.py

# 选择 [3] 立即更新
# 选择 1-2 位作者
# 设置下载 1 页（测试）

# 等待归档完成
```

#### 4.2 检查生成的 HTML

```bash
# 查找最新归档的帖子
LATEST=$(find /home/ben/Download/t66y -name "content.html" -type f -printf '%T+ %p\n' | sort -r | head -1 | cut -d' ' -f2-)

# 查看文件
cat "$LATEST"

# 预期：看到完整的 HTML 结构（<!DOCTYPE>, <html>, <head>, <body>）
# 预期：看到元数据在 <header> 中
# 预期：看到正文在 <article> 中
# 预期：看到图片/视频列表在 <section> 中
```

#### 4.3 w3m 浏览测试

```bash
# 使用 w3m 浏览
w3m "$LATEST"

# 预期效果：
# - 标题大而清晰
# - 元数据可见（作者、发布、归档时间）
# - 正文段落分明
# - 章节标题突出
# - 图片/视频列表清晰
# - 可以用方向键导航
# - 链接可以点击（Enter 键）
```

#### 4.4 浏览器查看测试

```bash
# 在浏览器中打开
firefox "$LATEST"

# 预期效果：
# - 排版美观
# - 样式正常
# - 链接可点击
```

---

### Step 5: 清理测试数据（5 分钟）

#### 5.1 备份配置（可选）

```bash
cp python/config.yaml python/config.yaml.backup
cp config.json config.json.backup
```

#### 5.2 清空归档数据

```bash
# 删除所有测试归档
rm -rf /home/ben/Download/t66y/*

# 验证
ls -la /home/ben/Download/t66y/
# 应该是空的（或只有 .gitkeep 之类的文件）
```

#### 5.3 验证配置完整

```bash
# 确认 config.yaml 中的关注列表还在
cat python/config.yaml | grep -A 10 "followed_authors:"

# 确认数据库路径等配置正常
cat python/config.yaml | grep "database_path"
```

---

## 五、验收标准

### 5.1 P0 标准（必须通过）

- [ ] **模板文件创建成功**
  - `python/src/templates/post.html` 存在且约 80 行
  - `python/src/templates/filters.py` 存在且约 60 行
  - `python/src/templates/__init__.py` 存在

- [ ] **Archiver 修改成功**
  - 导入 Jinja2 无错误
  - 模板引擎初始化成功
  - 可以生成 content.html

- [ ] **新归档使用新模板**
  - 归档 1 个帖子后，content.html 包含 `<!DOCTYPE html>`
  - 包含完整的 `<html>`, `<head>`, `<body>` 结构
  - 元数据在 `<header>` 中可见

- [ ] **w3m 浏览正常**
  - `w3m content.html` 可以打开
  - 标题、作者、时间可见
  - 正文段落清晰
  - 链接可以点击（Enter 键）

### 5.2 P1 标准（强烈建议）

- [ ] **正文格式正确**
  - 段落用 `<p>` 标签包裹
  - 章节标题识别为 `<h2>`（如 "01. xxx"）
  - 连续 `<br>` 已转换为段落分隔

- [ ] **媒体列表完整**
  - 图片列表显示所有图片文件名
  - 视频列表显示所有视频文件名
  - 本地文件链接可点击

- [ ] **统计信息正确**
  - 页脚显示字符数、图片数、视频数
  - 归档时间格式正确（YYYY-MM-DD HH:MM:SS）

### 5.3 P2 标准（可选优化）

- [ ] **浏览器显示美观**
  - Firefox/Chrome 中打开排版正常
  - CSS 样式生效
  - 字体、颜色、间距合理

- [ ] **文件大小显示**
  - 图片/视频显示文件大小（如 "1.2 MB"）

---

## 六、测试清单

### 6.1 单元测试

#### 测试 1: 过滤器功能

```bash
cd python

# 测试内容清理
python3 << 'EOF'
from src.templates.filters import clean_html_content

# 测试1: 转换连续 <br> 为段落
html = "第一段<br><br>第二段<br><br><br>第三段"
result = clean_html_content(html)
assert '<p>' in result
assert '</p>' in result
print("✓ 测试1通过: 段落转换")

# 测试2: 识别章节标题
html = "<p>01. 第一章</p><p>正文...</p>"
result = clean_html_content(html)
assert '<h2>01. 第一章</h2>' in result
print("✓ 测试2通过: 章节识别")

# 测试3: 移除图片 div
html = '<div class="image-big"><img src="..."></div>正文'
result = clean_html_content(html)
assert 'image-big' not in result
print("✓ 测试3通过: 图片移除")

# 测试4: 移除视频标签
html = '<video src="..."></video>正文'
result = clean_html_content(html)
assert '<video' not in result
print("✓ 测试4通过: 视频移除")

print("\n✅ 所有单元测试通过")
EOF
```

#### 测试 2: 模板渲染

```bash
cd python

python3 << 'EOF'
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# 加载模板
template_dir = Path('src/templates')
env = Environment(loader=FileSystemLoader(str(template_dir)))
template = env.get_template('post.html')

# 测试数据
data = {
    'title': '测试标题',
    'author': '测试作者',
    'publish_time': '2026-02-12 10:00',
    'archive_time': '2026-02-12 10:05',
    'url': 'https://example.com/test',
    'content': '<p>测试内容</p>',
    'content_length': 100,
    'images': [
        {'filename': 'img_1.jpg', 'url': 'https://...', 'size': '1.2 MB'},
        {'filename': 'img_2.jpg', 'url': 'https://...', 'size': '800 KB'}
    ],
    'videos': []
}

# 渲染
html = template.render(**data)

# 验证
assert '<!DOCTYPE html>' in html
assert '<title>测试标题 - 测试作者</title>' in html
assert '作者: 测试作者' in html
assert '📷 图片 (2)' in html
assert 'img_1.jpg' in html

print("✅ 模板渲染测试通过")
EOF
```

### 6.2 集成测试

#### 测试 3: 完整归档流程

```bash
cd python

# 1. 归档一个纯文本帖子
python main.py
# 手动操作：
# - 选择 [3] 立即更新
# - 选择一个作者（如"独醉笑清风"，纯文本帖子多）
# - 设置 1 页

# 2. 检查生成的文件
TEXT_POST=$(find /home/ben/Download/t66y -name "content.html" -type f | head -1)
echo "检查文件: $TEXT_POST"

# 验证 HTML 结构
grep -q "<!DOCTYPE html>" "$TEXT_POST" && echo "✓ DOCTYPE 存在"
grep -q "<h1>" "$TEXT_POST" && echo "✓ 标题存在"
grep -q "作者:" "$TEXT_POST" && echo "✓ 元数据可见"
grep -q "<article>" "$TEXT_POST" && echo "✓ 正文结构正确"

# 3. w3m 查看（手动）
w3m "$TEXT_POST"
```

#### 测试 4: 图片帖子

```bash
# 归档一个包含图片的帖子
python main.py
# 选择有图片的作者（如"厦门一只狼"）

# 检查
IMG_POST=$(find /home/ben/Download/t66y -type d -name "*\[*P\]" | head -1)/content.html
echo "检查文件: $IMG_POST"

# 验证图片列表
grep -q "📷 图片" "$IMG_POST" && echo "✓ 图片列表存在"
grep -q "photo/" "$IMG_POST" && echo "✓ 本地文件链接存在"
grep -q "<section>" "$IMG_POST" && echo "✓ 区域结构正确"

# w3m 查看
w3m "$IMG_POST"
```

#### 测试 5: 视频帖子

```bash
# 归档一个包含视频的帖子
python main.py
# 选择有视频的作者（如"我是抵触情绪"）

# 检查
VID_POST=$(find /home/ben/Download/t66y -type d -name "*\[*V\]" | head -1)/content.html
echo "检查文件: $VID_POST"

# 验证视频列表
grep -q "🎬 视频" "$VID_POST" && echo "✓ 视频列表存在"
grep -q "video/" "$VID_POST" && echo "✓ 本地文件链接存在"

# w3m 查看
w3m "$VID_POST"
```

### 6.3 回归测试

#### 测试 6: 确保其他功能未受影响

```bash
cd python

# 1. 测试菜单系统
python main.py
# 手动验证：
# - [1] 关注新作者 - 正常
# - [2] 查看关注列表 - 正常
# - [3] 立即更新 - 正常（已测试）
# - [4] 取消关注 - 正常
# - [5] 系统设置 - 正常

# 2. 测试配置加载
python3 -c "from src.config.manager import ConfigManager; cm = ConfigManager(); config = cm.load(); print('✓ 配置加载正常')"

# 3. 测试爬虫功能（不含模板）
python3 -c "from src.scraper.extractor import PostExtractor; print('✓ 提取器正常')"
python3 -c "from src.scraper.downloader import MediaDownloader; print('✓ 下载器正常')"
```

---

## 七、对后续 Phase 的影响

### 7.1 Phase 3: 数据库 + 统计

#### 影响分析

**简化前（未做 Phase 2.5）**：
```python
# Phase 3 需要解析多种格式
def parse_content_html(html_file: Path) -> dict:
    content = html_file.read_text()

    # 复杂：需要区分三种格式
    if '<!-- 帖子元数据' in content:
        # 旧格式：从注释提取
        metadata = extract_from_comment(content)
    elif '<header>' in content:
        # 新格式：从结构提取
        metadata = extract_from_structure(content)
    else:
        # 其他格式：猜测
        metadata = guess_metadata(content)

    return metadata
```

**简化后（做了 Phase 2.5）**：
```python
# Phase 3 只需解析统一格式
def parse_content_html(html_file: Path) -> dict:
    soup = BeautifulSoup(html_file.read_text(), 'html.parser')

    # 简单：直接提取
    return {
        'title': soup.find('h1').text,
        'author': soup.find('div', class_='meta').find('b', text='作者:').next_sibling.strip(),
        'publish_time': extract_meta_value(soup, '发布:'),
        'archive_time': extract_meta_value(soup, '归档:'),
        'url': soup.find('div', class_='meta').find('a')['href'],
        'content_length': int(soup.find('footer').text.split('字符')[0].split()[-1]),
        'image_count': len(soup.find_all('section')[0].find_all('div', class_='file')) if soup.find_all('section') else 0,
        'video_count': len(soup.find_all('section')[1].find_all('div', class_='file')) if len(soup.find_all('section')) > 1 else 0
    }
```

#### 节省时间

| 任务 | 简化前 | 简化后 | 节省 |
|------|--------|--------|------|
| 历史数据导入工具 | 2 小时 | 0 小时 | 2 小时 |
| 解析逻辑实现 | 1 小时 | 0.5 小时 | 0.5 小时 |
| 测试验证 | 1 小时 | 0.5 小时 | 0.5 小时 |
| **总计** | **4 小时** | **1 小时** | **3 小时** |

**Phase 3 总工期**：3-4 天 → **2-3 天**

### 7.2 Phase 4: 数据分析 + 可视化

#### 影响

- ✅ 词云生成：直接从数据库读取正文（统一格式）
- ✅ 时间分析：发布时间格式统一，解析简单
- ✅ 报告生成：可以直接链接到 content.html（格式美观）

### 7.3 长期维护

- ✅ **扩展性强**：添加新字段只需修改模板
- ✅ **易于调试**：HTML 结构清晰，问题容易定位
- ✅ **零技术债**：无历史包袱，无兼容逻辑

---

## 八、回滚方案

### 8.1 回滚场景

如果 Phase 2.5 出现严重问题需要回滚：

#### 场景 1: 模板渲染错误

**症状**：生成的 HTML 格式错误、无法打开

**回滚步骤**：
```bash
# 1. 回退代码
git checkout v2.0  # 回到 Phase 2 版本

# 2. 删除新归档的数据（如果有）
rm -rf /home/ben/Download/t66y/*

# 3. 重新归档
cd python
python main.py
```

#### 场景 2: Jinja2 依赖问题

**症状**：`ModuleNotFoundError: No module named 'jinja2'`

**解决方案**：
```bash
# 安装依赖
pip install jinja2

# 或回滚到 Phase 2
git checkout v2.0
```

### 8.2 回滚风险评估

| 风险 | 可能性 | 影响 | 对策 |
|------|--------|------|------|
| 模板语法错误 | 低 | 中 | 单元测试覆盖 |
| Jinja2 依赖问题 | 极低 | 低 | 已在 requirements.txt |
| w3m 不兼容 | 低 | 低 | 已用基础 CSS |
| 数据丢失 | 极低 | 高 | 测试数据可删除 |

**结论**：回滚风险极低，即使回滚也不影响功能（Phase 2 仍可用）

---

## 九、Git 提交策略

### 9.1 分支管理

```bash
# 创建开发分支
git checkout -b phase2.5-html-template

# 开发过程中定期提交
git add python/src/templates/
git commit -m "feat(phase2.5): add Jinja2 templates"

git add python/src/scraper/archiver.py
git commit -m "feat(phase2.5): integrate template rendering in archiver"

# 测试通过后合并
git checkout main
git merge phase2.5-html-template --no-ff

# 打标签
git tag -a v2.5 -m "Phase 2.5: HTML Template Optimization

- Unified content.html format
- w3m terminal browser optimization
- Visible metadata in header
- Local media file listing
- Simplified Phase 3 implementation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 推送
git push origin main --tags
```

### 9.2 提交信息规范

**格式**：`<type>(phase2.5): <subject>`

**类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `refactor`: 重构
- `test`: 测试
- `docs`: 文档

**示例**：
```
feat(phase2.5): add Jinja2 templates for unified HTML
feat(phase2.5): add content cleaning filters
feat(phase2.5): integrate template rendering in archiver
test(phase2.5): add unit tests for filters
docs(phase2.5): add Phase 2.5 design document
```

---

## 十、总结

### 10.1 核心价值

1. **用户体验** - w3m 终端浏览体验大幅提升
2. **代码质量** - 统一格式，易于维护
3. **开发效率** - Phase 3 节省 3 小时开发时间
4. **零技术债** - 无历史包袱，无兼容逻辑

### 10.2 工作量

| 任务 | 预计时间 | 实际时间 |
|------|---------|---------|
| 创建模板 | 15 分钟 | - |
| 创建过滤器 | 15 分钟 | - |
| 修改 Archiver | 20 分钟 | - |
| 测试验证 | 10 分钟 | - |
| 清理测试数据 | 5 分钟 | - |
| **总计** | **65 分钟** | - |

### 10.3 验收清单

**P0（必须）**：
- [ ] 模板文件创建成功（post.html, filters.py）
- [ ] Archiver 修改成功（导入 Jinja2, 渲染模板）
- [ ] 新归档使用新模板（包含 <!DOCTYPE html>）
- [ ] w3m 浏览正常（标题、正文、链接可点击）

**P1（建议）**：
- [ ] 正文格式正确（段落、章节标题）
- [ ] 媒体列表完整（图片、视频文件名）
- [ ] 统计信息正确（字符数、图片数、视频数）

**P2（可选）**：
- [ ] 浏览器显示美观
- [ ] 文件大小显示

### 10.4 下一步

完成 Phase 2.5 后：
1. ✅ 清理测试数据（`rm -rf /home/ben/Download/t66y/*`）
2. ✅ 更新 MIGRATION_PROGRESS.md（标记 Phase 2.5 完成）
3. ✅ 启动 Phase 3 数据库开发（2-3 天）

---

**Phase 2.5 设计文档完成！**

**预计工期**：1 小时
**建议优先级**：P1（高）
**验收标准**：4 项 P0 + 3 项 P1
**对 Phase 3 影响**：节省 3 小时开发时间

**准备就绪，等待用户批准后开始实施！**
