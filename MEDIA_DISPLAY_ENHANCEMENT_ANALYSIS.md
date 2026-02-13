# 媒体显示增强分析

**日期**: 2026-02-12
**需求来源**: 用户反馈
**优先级**: P1（用户体验改进）

---

## 📋 需求概述

**用户需求**：
```
在下载整理的统一页面中，我要显示照片和视频，而不只是做个链接
```

**当前问题**：
- 归档页面（`content.html`）只显示图片和视频的文件链接
- 用户需要点击链接才能查看图片/视频
- 无法在同一页面中快速浏览所有媒体内容

**用户期望**：
- 图片直接显示在页面中（使用 `<img>` 标签）
- 视频可以在页面中播放（使用 `<video>` 标签）
- 提供更好的浏览体验

---

## 🔍 当前实现分析

### 当前模板代码 (post.html)

#### 图片部分 (Line 94-105)
```html
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
```

**问题**：
- ❌ 只有链接 `<a href="...">`
- ❌ 没有 `<img>` 标签
- ❌ 无法直接看到图片内容

#### 视频部分 (Line 107-119)
```html
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
```

**问题**：
- ❌ 只有链接 `<a href="...">`
- ❌ 没有 `<video>` 标签
- ❌ 无法直接播放视频

---

## 💡 解决方案设计

### 方案 1: 完全替换为嵌入显示（推荐）⭐⭐⭐⭐⭐

**实现方式**：直接使用 `<img>` 和 `<video>` 标签嵌入媒体

#### 图片部分
```html
{% if images %}
<section>
    <h2>📷 图片 ({{ images|length }})</h2>
    {% for img in images %}
    <div class="media-item">
        <p><strong>图片 [{{ loop.index }}]</strong></p>
        <img src="photo/{{ img.filename }}"
             alt="{{ title }} - 图片 {{ loop.index }}"
             loading="lazy"
             style="max-width: 100%; height: auto; margin: 10px 0; border: 1px solid #ddd;">
        <p class="media-info">
            <a href="photo/{{ img.filename }}" download>下载原图</a>
            {% if img.size %}| {{ img.size }}{% endif %}
        </p>
    </div>
    {% endfor %}
</section>
{% endif %}
```

#### 视频部分
```html
{% if videos %}
<section>
    <h2>🎬 视频 ({{ videos|length }})</h2>
    {% for vid in videos %}
    <div class="media-item">
        <p><strong>视频 [{{ loop.index }}]</strong></p>
        <video controls
               preload="metadata"
               style="max-width: 100%; height: auto; margin: 10px 0; border: 1px solid #ddd;">
            <source src="video/{{ vid.filename }}" type="video/mp4">
            您的浏览器不支持视频播放。<a href="video/{{ vid.filename }}">下载视频</a>
        </video>
        <p class="media-info">
            <a href="video/{{ vid.filename }}" download>下载视频</a>
            {% if vid.size %}| {{ vid.size }}{% endif %}
        </p>
    </div>
    {% endfor %}
</section>
{% endif %}
```

**优点**：
- ✅ 直接显示图片和视频
- ✅ 现代浏览器完美支持
- ✅ 用户体验极佳（不需要点击）
- ✅ 支持懒加载（`loading="lazy"`）
- ✅ 保留下载链接

**缺点**：
- ⚠️ w3m 文本浏览器无法显示图片/视频（只显示替代文本）
- ⚠️ 页面加载时间可能变长（如果图片/视频很多）

---

### 方案 2: 混合模式（链接 + 嵌入）⭐⭐⭐⭐

**实现方式**：同时提供链接和嵌入显示

```html
{% if images %}
<section>
    <h2>📷 图片 ({{ images|length }})</h2>

    <!-- 快速预览：缩略图网格 -->
    <div class="thumbnail-grid">
        {% for img in images %}
        <a href="#img-{{ loop.index }}" title="查看图片 {{ loop.index }}">
            <img src="photo/{{ img.filename }}"
                 alt="缩略图 {{ loop.index }}"
                 style="width: 100px; height: 100px; object-fit: cover; margin: 5px;">
        </a>
        {% endfor %}
    </div>

    <!-- 详细显示 -->
    {% for img in images %}
    <div id="img-{{ loop.index }}" class="media-item">
        <p><strong>图片 [{{ loop.index }}]</strong></p>
        <img src="photo/{{ img.filename }}"
             alt="{{ title }} - 图片 {{ loop.index }}"
             loading="lazy"
             style="max-width: 100%; height: auto;">
        <p class="media-info">
            <a href="photo/{{ img.filename }}">photo/{{ img.filename }}</a>
            {% if img.size %}({{ img.size }}){% endif %}
        </p>
    </div>
    {% endfor %}
</section>
{% endif %}
```

**优点**：
- ✅ 提供缩略图网格预览
- ✅ 保留链接方式
- ✅ 灵活性高

**缺点**：
- ⚠️ 页面结构更复杂
- ⚠️ 缩略图可能占用存储空间

---

### 方案 3: 可切换模式（最灵活）⭐⭐⭐

**实现方式**：使用 JavaScript 切换显示模式

```html
<section>
    <h2>
        📷 图片 ({{ images|length }})
        <button onclick="toggleMediaDisplay('image')" style="float: right;">
            切换显示模式
        </button>
    </h2>

    <!-- 链接模式 -->
    <div id="image-links" class="display-mode">
        {% for img in images %}
        <div class="file">
            <strong>[{{ loop.index }}]</strong>
            <a href="photo/{{ img.filename }}">photo/{{ img.filename }}</a>
            {% if img.size %}({{ img.size }}){% endif %}
        </div>
        {% endfor %}
    </div>

    <!-- 嵌入模式 -->
    <div id="image-embed" class="display-mode" style="display: none;">
        {% for img in images %}
        <div class="media-item">
            <p><strong>图片 [{{ loop.index }}]</strong></p>
            <img src="photo/{{ img.filename }}"
                 alt="{{ title }} - 图片 {{ loop.index }}"
                 style="max-width: 100%; height: auto;">
        </div>
        {% endfor %}
    </div>
</section>

<script>
function toggleMediaDisplay(type) {
    const links = document.getElementById(type + '-links');
    const embed = document.getElementById(type + '-embed');

    if (links.style.display === 'none') {
        links.style.display = 'block';
        embed.style.display = 'none';
    } else {
        links.style.display = 'none';
        embed.style.display = 'block';
    }
}
</script>
```

**优点**：
- ✅ 用户可以自由选择
- ✅ 兼容性最好
- ✅ 适合不同网络环境

**缺点**：
- ⚠️ 需要 JavaScript（w3m 不支持）
- ⚠️ 页面体积增大

---

## 🎨 CSS 样式增强

### 新增 CSS (添加到 post.html)

```css
/* 媒体项容器 */
.media-item {
    margin: 20px 0;
    padding: 15px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: #fafafa;
}

/* 图片样式 */
.media-item img {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 10px 0;
    border: 1px solid #ddd;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* 视频样式 */
.media-item video {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 10px 0;
    background-color: #000;
    border: 1px solid #ddd;
}

/* 媒体信息 */
.media-info {
    margin: 5px 0;
    color: #666;
    font-size: 0.9em;
}

.media-info a {
    color: #06c;
    text-decoration: none;
}

.media-info a:hover {
    text-decoration: underline;
}

/* 缩略图网格（方案2） */
.thumbnail-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin: 15px 0;
}

.thumbnail-grid img {
    cursor: pointer;
    border: 2px solid #ddd;
    transition: border-color 0.2s;
}

.thumbnail-grid img:hover {
    border-color: #06c;
}

/* 响应式设计 */
@media (max-width: 600px) {
    .media-item img,
    .media-item video {
        border-radius: 0;
    }
}
```

---

## 📊 方案对比

| 方案 | 用户体验 | 兼容性 | 实现难度 | 页面性能 | 推荐度 |
|------|---------|--------|---------|---------|--------|
| **方案1: 完全嵌入** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ✅ 强烈推荐 |
| 方案2: 混合模式 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 可选 |
| 方案3: 可切换 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 可选优化 |

**推荐选择**：**方案 1（完全嵌入显示）**

**理由**：
1. 现代浏览器是主要使用场景
2. w3m 用户可以通过链接下载后查看（保留下载链接）
3. 实现简单，维护成本低
4. 用户体验最好（不需要额外操作）

---

## 🔧 技术实现细节

### HTML5 图片标签最佳实践

```html
<img src="photo/img_1.jpg"
     alt="描述性文本"           <!-- 无障碍访问 -->
     loading="lazy"             <!-- 懒加载，提升性能 -->
     width="800"                <!-- 可选：指定尺寸避免布局跳动 -->
     height="600"
     style="max-width: 100%; height: auto;">  <!-- 响应式 -->
```

### HTML5 视频标签最佳实践

```html
<video controls                <!-- 显示控制条 -->
       preload="metadata"      <!-- 只预加载元数据 -->
       poster="thumbnail.jpg"  <!-- 可选：封面图 -->
       style="max-width: 100%; height: auto;">
    <source src="video/vid_1.mp4" type="video/mp4">
    <source src="video/vid_1.webm" type="video/webm">  <!-- 可选：多格式支持 -->
    您的浏览器不支持视频播放。<a href="video/vid_1.mp4">下载视频</a>
</video>
```

**关键属性说明**：

| 属性 | 说明 | 推荐值 |
|------|------|--------|
| `controls` | 显示播放控制条 | 必需 |
| `preload` | 预加载策略 | `metadata` (只加载元数据) |
| `loading` | 图片懒加载 | `lazy` (延迟加载) |
| `alt` | 替代文本 | 描述性文本 |
| `max-width` | 最大宽度 | `100%` (响应式) |

---

## 🧪 测试计划

### 测试用例 1: 图片显示
```
步骤：
1. 归档包含图片的帖子
2. 用浏览器打开 content.html
3. 检查图片是否直接显示在页面中

预期结果：
✅ 图片以 <img> 标签嵌入显示
✅ 图片宽度自适应页面
✅ 图片下方有文件名和大小信息
✅ "下载原图"链接可用
```

### 测试用例 2: 视频播放
```
步骤：
1. 归档包含视频的帖子
2. 用浏览器打开 content.html
3. 点击视频播放按钮

预期结果：
✅ 视频以 <video> 标签嵌入显示
✅ 视频控制条正常工作（播放/暂停/进度条/音量）
✅ 视频宽度自适应页面
✅ "下载视频"链接可用
```

### 测试用例 3: 多媒体混合
```
步骤：
1. 归档包含多张图片和多个视频的帖子
2. 用浏览器打开 content.html
3. 向下滚动浏览所有媒体

预期结果：
✅ 图片和视频交替显示正常
✅ 页面布局不混乱
✅ 滚动流畅（懒加载生效）
```

### 测试用例 4: 性能测试
```
步骤：
1. 归档包含 50+ 图片的帖子
2. 用浏览器打开 content.html
3. 检查页面加载时间和内存占用

预期结果：
✅ 初始加载时间 < 3 秒
✅ 图片懒加载正常（滚动到可见区域才加载）
✅ 内存占用合理
```

### 测试用例 5: w3m 兼容性
```
步骤：
1. 用 w3m 打开 content.html
   $ w3m content.html

预期结果：
✅ 显示 [IMAGE] 占位符
✅ 显示图片/视频的下载链接
✅ 可以通过链接下载媒体文件
```

### 测试用例 6: 响应式设计
```
步骤：
1. 在不同屏幕尺寸下查看 content.html
   - 手机 (320px)
   - 平板 (768px)
   - 桌面 (1920px)

预期结果：
✅ 图片和视频自适应屏幕宽度
✅ 布局不溢出
✅ 文字可读性良好
```

---

## 📝 实施清单

### 阶段 1: 修改模板 (30分钟)
- [ ] 修改 `python/src/templates/post.html`
  - [ ] 更新图片部分（Line 94-105）
  - [ ] 更新视频部分（Line 107-119）
  - [ ] 添加新的 CSS 样式
- [ ] 保持向后兼容（保留下载链接）

### 阶段 2: 测试验证 (30分钟)
- [ ] 测试用例 1-3（功能测试）
- [ ] 测试用例 4（性能测试）
- [ ] 测试用例 5（w3m 兼容性）
- [ ] 测试用例 6（响应式设计）

### 阶段 3: 优化调整 (可选，30分钟)
- [ ] 根据测试结果调整样式
- [ ] 优化图片尺寸（如果需要）
- [ ] 添加缩略图预览（如果采用方案2）

### 总预计时间: 1-1.5 小时

---

## 🎯 预期效果

### 修改前
```
📷 图片 (23)
[1] photo/img_1.jpg (2.3 MB)
[2] photo/img_2.jpg (1.8 MB)
[3] photo/img_3.jpg (2.1 MB)
...

🎬 视频 (5)
[1] video/video_1.mp4 (15.2 MB)
[2] video/video_2.mp4 (12.8 MB)
...
```
**问题**：需要点击每个链接才能查看

### 修改后
```
📷 图片 (23)

图片 [1]
[图片直接显示在这里，尺寸自适应]
下载原图 | 2.3 MB

图片 [2]
[图片直接显示在这里，尺寸自适应]
下载原图 | 1.8 MB

...

🎬 视频 (5)

视频 [1]
[视频播放器直接显示在这里，带控制条]
下载视频 | 15.2 MB

视频 [2]
[视频播放器直接显示在这里，带控制条]
下载视频 | 12.8 MB

...
```
**改进**：所有媒体直接显示，用户体验极佳

---

## 🔐 安全考虑

### XSS 防护
- ✅ `alt` 属性使用安全的变量（`{{ title }}`）
- ✅ 文件路径使用相对路径（`photo/`, `video/`）
- ✅ 不允许外部 URL（避免混合内容）

### 文件类型验证
- ✅ 图片：只支持常见格式（jpg, png, gif, webp）
- ✅ 视频：只支持常见格式（mp4, webm, ogg）
- ⚠️ 建议：添加文件类型检查（在 archiver.py 中）

---

## 🚀 进阶增强：图片灯箱功能

### 📋 功能需求

**用户追加需求**：
```
可以点击图片查看大图吗？
```

**功能描述**：
- 点击页面中的图片，弹出全屏灯箱查看大图
- 支持关闭返回原页面
- 支持键盘操作（ESC 关闭，← → 切换图片）
- 支持上一张/下一张切换
- 显示图片信息（编号、文件名、大小）

---

### 灯箱方案对比

#### 方案 A: 纯 CSS 实现 ⭐⭐⭐

**原理**：使用 CSS `:target` 伪类

**优点**：
- ✅ 无需 JavaScript
- ✅ 实现简单
- ✅ 兼容性好

**缺点**：
- ❌ 不支持键盘切换图片
- ❌ 不支持图片缩放拖动
- ❌ URL 会改变（添加 #锚点）

---

#### 方案 B: 原生 JavaScript 实现（推荐）⭐⭐⭐⭐⭐

**原理**：使用原生 JavaScript 控制灯箱显示

**核心功能**：
- ✅ 点击图片打开灯箱
- ✅ 关闭方式：关闭按钮 / 点击背景 / ESC 键
- ✅ 图片切换：左右箭头按钮 / ← → 键
- ✅ 循环浏览（最后一张 → 第一张）
- ✅ 图片信息显示
- ✅ 禁止背景滚动（打开灯箱时）

**HTML 结构**：
```html
<!-- 图片列表（添加点击事件）-->
{% for img in images %}
<div class="media-item">
    <p><strong>图片 [{{ loop.index }}]</strong></p>
    <img src="photo/{{ img.filename }}"
         alt="{{ title }} - 图片 {{ loop.index }}"
         data-index="{{ loop.index }}"
         onclick="openLightbox({{ loop.index - 1 }})"
         loading="lazy"
         style="max-width: 100%; height: auto; cursor: pointer;">
    <p class="media-info">
        <a href="photo/{{ img.filename }}" download>下载原图</a>
        {% if img.size %}| {{ img.size }}{% endif %}
    </p>
</div>
{% endfor %}

<!-- 灯箱容器（在 </body> 前添加）-->
<div id="lightbox" class="lightbox" onclick="closeLightbox()">
    <span class="lightbox-close" onclick="closeLightbox()">&times;</span>
    <span class="lightbox-prev" onclick="event.stopPropagation(); changeImage(-1)">&#10094;</span>
    <span class="lightbox-next" onclick="event.stopPropagation(); changeImage(1)">&#10095;</span>

    <div class="lightbox-content" onclick="event.stopPropagation()">
        <img id="lightbox-img" src="" alt="">
        <p id="lightbox-caption" class="lightbox-caption"></p>
    </div>
</div>
```

**CSS 样式（添加到 `<style>` 中）**：
```css
/* 灯箱容器 */
.lightbox {
    display: none;
    position: fixed;
    z-index: 9999;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.95);
    justify-content: center;
    align-items: center;
}

/* 灯箱内容 */
.lightbox-content {
    position: relative;
    max-width: 90vw;
    max-height: 90vh;
    text-align: center;
}

/* 灯箱图片 */
.lightbox-content img {
    max-width: 100%;
    max-height: 80vh;
    width: auto;
    height: auto;
    object-fit: contain;
    border: 2px solid #fff;
    box-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}

/* 关闭按钮 */
.lightbox-close {
    position: absolute;
    top: 15px;
    right: 35px;
    color: #fff;
    font-size: 50px;
    font-weight: bold;
    cursor: pointer;
    z-index: 10001;
    transition: 0.3s;
}

.lightbox-close:hover {
    color: #ff0000;
}

/* 上一张/下一张按钮 */
.lightbox-prev,
.lightbox-next {
    cursor: pointer;
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    padding: 16px;
    color: white;
    font-weight: bold;
    font-size: 30px;
    user-select: none;
    background-color: rgba(0, 0, 0, 0.5);
    border-radius: 3px;
    z-index: 10001;
    transition: background-color 0.3s;
}

.lightbox-prev:hover,
.lightbox-next:hover {
    background-color: rgba(0, 0, 0, 0.8);
}

.lightbox-prev {
    left: 20px;
}

.lightbox-next {
    right: 20px;
}

/* 图片说明 */
.lightbox-caption {
    color: #fff;
    padding: 15px;
    text-align: center;
    font-size: 1em;
}

/* 缩略图悬停效果 */
img[onclick]:hover {
    opacity: 0.85;
    transform: scale(1.02);
    transition: all 0.2s ease;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
```

**JavaScript 代码（在 `</body>` 前添加）**：
```javascript
<script>
// 图片数据（Jinja2 生成）
const images = [
    {% for img in images %}
    {
        filename: 'photo/{{ img.filename }}',
        title: '图片 [{{ loop.index }}]',
        info: '{{ img.filename }}{% if img.size %} ({{ img.size }}){% endif %}'
    }{% if not loop.last %},{% endif %}
    {% endfor %}
];

let currentIndex = 0;

// 打开灯箱
function openLightbox(index) {
    currentIndex = index;
    updateLightboxImage();
    document.getElementById('lightbox').style.display = 'flex';
    document.body.style.overflow = 'hidden'; // 禁止背景滚动
}

// 关闭灯箱
function closeLightbox() {
    document.getElementById('lightbox').style.display = 'none';
    document.body.style.overflow = 'auto'; // 恢复滚动
}

// 切换图片
function changeImage(direction) {
    currentIndex += direction;

    // 循环切换
    if (currentIndex < 0) {
        currentIndex = images.length - 1;
    } else if (currentIndex >= images.length) {
        currentIndex = 0;
    }

    updateLightboxImage();
}

// 更新灯箱显示的图片
function updateLightboxImage() {
    if (images.length === 0) return;

    const img = images[currentIndex];
    document.getElementById('lightbox-img').src = img.filename;
    document.getElementById('lightbox-img').alt = img.title;
    document.getElementById('lightbox-caption').textContent =
        img.title + ' - ' + img.info + ' (' + (currentIndex + 1) + '/' + images.length + ')';
}

// 键盘支持
document.addEventListener('keydown', function(e) {
    const lightbox = document.getElementById('lightbox');
    if (lightbox.style.display === 'flex') {
        if (e.key === 'Escape') {
            closeLightbox();
        } else if (e.key === 'ArrowLeft') {
            changeImage(-1);
        } else if (e.key === 'ArrowRight') {
            changeImage(1);
        }
    }
});
</script>
```

**优点**：
- ✅ 支持键盘操作（ESC、← →）
- ✅ 单个灯箱容器（性能好）
- ✅ 可以切换上一张/下一张
- ✅ 不改变 URL
- ✅ 体验流畅
- ✅ 离线可用（无外部依赖）

**缺点**：
- ⚠️ 需要 JavaScript（w3m 不支持，但仍可通过下载链接查看）
- ⚠️ 代码稍复杂（但完全可控）

---

#### 方案 C: 第三方库 ⭐⭐⭐⭐

**使用库**：GLightbox、Lightbox2、PhotoSwipe

**优点**：
- ✅ 功能强大（缩放、拖动、手势）
- ✅ 动画流畅
- ✅ 支持触摸屏
- ✅ 专业级体验

**缺点**：
- ❌ 依赖外部库（需要网络或本地部署）
- ❌ 增加页面体积
- ❌ 归档离线使用需要打包库文件

---

### 灯箱功能测试计划

#### 测试用例 7: 灯箱基本功能
```
步骤：
1. 打开包含多张图片的归档页面
2. 点击任意图片
3. 检查灯箱是否弹出

预期结果：
✅ 灯箱弹出全屏显示
✅ 图片居中显示
✅ 背景变暗（半透明黑色）
✅ 显示关闭按钮和切换按钮
✅ 显示图片信息（编号/文件名/大小）
```

#### 测试用例 8: 灯箱关闭功能
```
步骤：
1. 打开灯箱
2. 分别测试：
   a. 点击关闭按钮（×）
   b. 点击背景区域
   c. 按 ESC 键

预期结果：
✅ 所有方式都能关闭灯箱
✅ 关闭后恢复页面滚动
✅ 返回原页面位置
```

#### 测试用例 9: 图片切换功能
```
步骤：
1. 打开灯箱
2. 点击右箭头按钮（或按 → 键）
3. 点击左箭头按钮（或按 ← 键）
4. 在第一张时按 ← 键
5. 在最后一张时按 → 键

预期结果：
✅ 图片正确切换
✅ 图片信息同步更新
✅ 支持循环切换（第一张 ↔ 最后一张）
✅ 切换流畅无卡顿
```

#### 测试用例 10: 灯箱响应式
```
步骤：
1. 在不同屏幕尺寸下打开灯箱
   - 桌面（1920px）
   - 平板（768px）
   - 手机（375px）

预期结果：
✅ 图片自适应屏幕大小
✅ 按钮位置合理可见
✅ 不溢出屏幕
✅ 触摸操作正常（移动端）
```

---

### 🎨 可选增强功能（移动端优化）

#### 触摸手势支持
```javascript
// 添加到 JavaScript 中
let touchStartX = 0;
let touchEndX = 0;

document.getElementById('lightbox-img').addEventListener('touchstart', e => {
    touchStartX = e.changedTouches[0].screenX;
});

document.getElementById('lightbox-img').addEventListener('touchend', e => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
});

function handleSwipe() {
    if (touchEndX < touchStartX - 50) {
        // 向左滑动 - 下一张
        changeImage(1);
    }
    if (touchEndX > touchStartX + 50) {
        // 向右滑动 - 上一张
        changeImage(-1);
    }
}
```

---

### 📊 灯箱方案对比

| 方案 | 复杂度 | 功能丰富度 | 性能 | 离线可用 | 推荐度 |
|------|--------|-----------|------|---------|--------|
| 方案A: 纯CSS | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 适合简单需求 |
| **方案B: 原生JS** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | ✅ **强烈推荐** |
| 方案C: 第三方库 | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | 可选（在线环境） |

**推荐选择**：**方案 B（原生 JavaScript）**

---

## 💡 其他增强建议（P2优先级）

### 可选功能
1. ~~**图片灯箱效果**：点击图片放大查看~~ ✅ 已纳入主方案
2. **视频封面图**：自动生成视频缩略图作为 poster
3. **图片懒加载增强**：添加加载占位符和骨架屏
4. **批量下载**：提供"下载所有图片"按钮
5. **图片排序**：按尺寸、名称、时间排序
6. **图片缩放**：灯箱中支持鼠标滚轮缩放
7. **图片拖动**：放大后支持拖动查看
8. **全屏模式**：F11 或按钮进入全屏查看
9. **幻灯片播放**：自动播放所有图片

---

## 📚 相关文档

- **PHASE2_5_DESIGN.md** - HTML 模板设计文档
- **PHASE2_5_PROGRESS.md** - Phase 2.5 进度记录
- **templates/post.html** - 当前模板文件

---

## 🎓 总结

### 推荐方案：方案 1（完全嵌入显示）

**实施内容**：
1. 图片部分：使用 `<img>` 标签直接显示
2. 视频部分：使用 `<video>` 标签直接播放
3. 添加 CSS 样式优化显示效果
4. 保留下载链接以兼容文本浏览器

**优势**：
- ✅ 用户体验最佳
- ✅ 实现简单
- ✅ 维护成本低
- ✅ 符合现代 Web 标准

**工作量**：1-1.5 小时

---

**分析完成，等待用户确认后开始实施！** 📋
