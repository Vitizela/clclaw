# 媒体显示增强实施方案（JS 灯箱方案）

**创建日期**: 2026-02-12
**预计工期**: 2-3 小时
**优先级**: P1（用户体验增强）
**方案选择**: 原生 JavaScript 灯箱（推荐方案 ⭐⭐⭐⭐⭐）

---

## 📋 实施目标

基于 `MEDIA_DISPLAY_ENHANCEMENT_ANALYSIS.md` 的分析，实现以下两个核心功能：

### 阶段 1：媒体嵌入显示（必须）
- ✅ 图片直接显示在页面中（使用 `<img>` 标签）
- ✅ 视频直接嵌入播放器（使用 `<video>` 标签）
- ✅ 保留下载链接（向下兼容）
- ✅ 响应式设计（移动端友好）
- ✅ 懒加载优化（`loading="lazy"`）

### 阶段 2：图片灯箱功能（增强）
- ✅ 点击图片查看大图
- ✅ 键盘导航（ESC 关闭，← → 切换）
- ✅ 点击背景或关闭按钮关闭
- ✅ 显示图片序号和信息
- ✅ 平滑动画效果
- ✅ 触摸手势支持（可选）

---

## 🎯 关键成功标准

### P0 要求（必须满足）
1. **图片显示**: 所有图片能直接在页面中显示
2. **视频播放**: 视频能直接在页面中播放
3. **灯箱基础功能**: 点击图片能打开灯箱查看大图
4. **键盘操作**: ESC 关闭灯箱，← → 切换图片
5. **兼容性保持**: w3m 终端浏览器仍然可用

### P1 要求（强烈建议）
- 响应式设计（移动端正常显示）
- 懒加载优化（性能提升）
- 平滑动画效果
- 点击背景关闭灯箱

### P2 要求（可选优化）
- 触摸手势支持（左右滑动切换）
- 图片预加载（提升切换速度）
- 加载动画

---

## 📁 文件清单

### 需要修改的文件（1 个）

#### `python/src/templates/post.html` 🔴 P0
**当前状态**: 只显示图片/视频的下载链接
**修改目标**:
- 添加图片嵌入显示
- 添加视频播放器
- 添加灯箱 HTML 结构
- 添加灯箱 CSS 样式（约 80 行）
- 添加灯箱 JavaScript 代码（约 70 行）

**预计修改量**: +200 行（CSS 80 + JS 70 + HTML 50）

---

## 📐 详细实施步骤

### Step 0: 备份当前模板

```bash
cp python/src/templates/post.html python/src/templates/post.html.backup
```

---

### Step 1: 修改图片部分 - 嵌入显示（30 分钟）

#### 1.1 修改图片 CSS 样式

在 `<style>` 标签内（第 7-71 行）添加：

```css
/* ============ 媒体显示增强 ============ */

/* 图片容器 */
.images-gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
    margin: 20px 0;
}

.image-item {
    position: relative;
    border: 1px solid #ddd;
    border-radius: 4px;
    overflow: hidden;
    background: #f9f9f9;
    transition: transform 0.2s, box-shadow 0.2s;
}

.image-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    cursor: pointer;
}

/* 图片本体 */
.image-item img {
    width: 100%;
    height: 200px;
    object-fit: cover;
    display: block;
}

/* 图片信息条 */
.image-info {
    padding: 8px;
    font-size: 0.85em;
    background: white;
    border-top: 1px solid #eee;
}

.image-info .index {
    font-weight: bold;
    color: #06c;
}

.image-info .size {
    color: #666;
    float: right;
}

/* 下载链接 */
.download-link {
    display: block;
    text-align: center;
    padding: 5px;
    margin-top: 5px;
    background: #f0f0f0;
    color: #06c;
    text-decoration: none;
    font-size: 0.85em;
    border-radius: 3px;
}

.download-link:hover {
    background: #e0e0e0;
    text-decoration: underline;
}

/* 响应式：移动端单列 */
@media (max-width: 600px) {
    .images-gallery {
        grid-template-columns: 1fr;
    }

    .image-item img {
        height: auto;
        max-height: 300px;
    }
}
```

#### 1.2 修改图片 HTML 结构

将第 93-105 行替换为：

```html
<!-- 图片列表 -->
{% if images %}
<section>
    <h2>📷 图片 ({{ images|length }})</h2>
    <div class="images-gallery">
        {% for img in images %}
        <div class="image-item" onclick="openLightbox({{ loop.index0 }})">
            <img
                src="photo/{{ img.filename }}"
                alt="图片 {{ loop.index }}"
                loading="lazy"
                onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0ibW9ub3NwYWNlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5Ij7liqDovb3lpLHotKU8L3RleHQ+PC9zdmc+'"
            >
            <div class="image-info">
                <span class="index">[{{ loop.index }}]</span>
                {% if img.size %}
                <span class="size">{{ img.size }}</span>
                {% endif %}
            </div>
            <a href="photo/{{ img.filename }}" class="download-link" download onclick="event.stopPropagation()">
                ⬇ 下载
            </a>
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}
```

**关键点说明**:
- `onclick="openLightbox({{ loop.index0 }})"`: 点击图片时打开灯箱（索引从 0 开始）
- `loading="lazy"`: 懒加载优化
- `onerror`: 图片加载失败时显示占位符（Base64 编码的 SVG）
- `onclick="event.stopPropagation()"`: 下载链接点击时不触发灯箱

---

### Step 2: 修改视频部分 - 嵌入播放器（20 分钟）

#### 2.1 添加视频 CSS 样式

在 `<style>` 标签内继续添加：

```css
/* 视频容器 */
.videos-gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.video-item {
    border: 1px solid #ddd;
    border-radius: 4px;
    overflow: hidden;
    background: #000;
}

/* 视频播放器 */
.video-item video {
    width: 100%;
    height: auto;
    display: block;
    background: #000;
}

/* 视频信息 */
.video-info {
    padding: 8px;
    background: white;
    border-top: 1px solid #eee;
    font-size: 0.85em;
}

.video-info .index {
    font-weight: bold;
    color: #06c;
}

.video-info .size {
    color: #666;
    float: right;
}

/* 响应式：移动端单列 */
@media (max-width: 600px) {
    .videos-gallery {
        grid-template-columns: 1fr;
    }
}
```

#### 2.2 修改视频 HTML 结构

将第 107-119 行替换为：

```html
<!-- 视频列表 -->
{% if videos %}
<section>
    <h2>🎬 视频 ({{ videos|length }})</h2>
    <div class="videos-gallery">
        {% for vid in videos %}
        <div class="video-item">
            <video
                controls
                preload="metadata"
                poster="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjM2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjQwIiBoZWlnaHQ9IjM2MCIgZmlsbD0iIzAwMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0ibW9ub3NwYWNlIiBmb250LXNpemU9IjI0IiBmaWxsPSIjZmZmIj7igLbvuI8g54K55Ye75pKt5pS+PC90ZXh0Pjwvc3ZnPg=="
            >
                <source src="video/{{ vid.filename }}" type="video/mp4">
                <source src="video/{{ vid.filename }}" type="video/webm">
                您的浏览器不支持视频播放。
            </video>
            <div class="video-info">
                <span class="index">[{{ loop.index }}]</span>
                <span>{{ vid.filename }}</span>
                {% if vid.size %}
                <span class="size">{{ vid.size }}</span>
                {% endif %}
            </div>
            <a href="video/{{ vid.filename }}" class="download-link" download>
                ⬇ 下载视频
            </a>
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}
```

**关键点说明**:
- `controls`: 显示播放控件
- `preload="metadata"`: 只预加载元数据（优化性能）
- `poster`: 视频封面（Base64 占位符）
- `<source>`: 支持多种视频格式

---

### Step 3: 添加灯箱功能（60 分钟）

#### 3.1 添加灯箱 HTML 结构

在 `</body>` 标签之前（第 137 行）添加：

```html
<!-- 图片灯箱 -->
<div id="lightbox" class="lightbox" onclick="closeLightbox()">
    <span class="lightbox-close" onclick="closeLightbox()">&times;</span>

    <button class="lightbox-prev" onclick="changeImage(-1); event.stopPropagation()">
        &#10094;
    </button>

    <div class="lightbox-content" onclick="event.stopPropagation()">
        <img id="lightbox-img" src="" alt="灯箱图片">
        <div class="lightbox-info">
            <span id="lightbox-caption">图片 1 / 1</span>
        </div>
    </div>

    <button class="lightbox-next" onclick="changeImage(1); event.stopPropagation()">
        &#10095;
    </button>
</div>
```

#### 3.2 添加灯箱 CSS 样式

在 `<style>` 标签内继续添加（约 80 行）：

```css
/* ============ 图片灯箱 ============ */

/* 灯箱容器（全屏遮罩） */
.lightbox {
    display: none; /* 默认隐藏 */
    position: fixed;
    z-index: 9999;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.95);
    justify-content: center;
    align-items: center;
    animation: fadeIn 0.3s ease;
}

.lightbox.active {
    display: flex;
}

/* 淡入动画 */
@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

/* 缩放动画 */
@keyframes zoomIn {
    from {
        transform: scale(0.8);
        opacity: 0;
    }
    to {
        transform: scale(1);
        opacity: 1;
    }
}

/* 关闭按钮（右上角 X） */
.lightbox-close {
    position: absolute;
    top: 20px;
    right: 40px;
    font-size: 40px;
    font-weight: bold;
    color: white;
    cursor: pointer;
    z-index: 10001;
    transition: color 0.3s;
}

.lightbox-close:hover {
    color: #f44;
}

/* 灯箱内容容器 */
.lightbox-content {
    max-width: 90%;
    max-height: 90%;
    display: flex;
    flex-direction: column;
    align-items: center;
    animation: zoomIn 0.3s ease;
}

/* 灯箱图片 */
.lightbox-content img {
    max-width: 100%;
    max-height: 80vh;
    object-fit: contain;
    border-radius: 4px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

/* 图片信息栏 */
.lightbox-info {
    margin-top: 15px;
    padding: 10px 20px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    color: white;
    font-size: 0.9em;
    backdrop-filter: blur(10px);
}

/* 前一张按钮（左侧 <） */
.lightbox-prev,
.lightbox-next {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    font-size: 30px;
    font-weight: bold;
    color: white;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    padding: 15px 20px;
    cursor: pointer;
    border-radius: 4px;
    transition: background 0.3s, transform 0.2s;
    z-index: 10001;
    backdrop-filter: blur(5px);
}

.lightbox-prev {
    left: 40px;
}

.lightbox-next {
    right: 40px;
}

.lightbox-prev:hover,
.lightbox-next:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-50%) scale(1.1);
}

.lightbox-prev:active,
.lightbox-next:active {
    transform: translateY(-50%) scale(0.95);
}

/* 移动端优化 */
@media (max-width: 600px) {
    .lightbox-close {
        top: 10px;
        right: 20px;
        font-size: 30px;
    }

    .lightbox-prev,
    .lightbox-next {
        font-size: 24px;
        padding: 10px 15px;
    }

    .lightbox-prev {
        left: 10px;
    }

    .lightbox-next {
        right: 10px;
    }

    .lightbox-content {
        max-width: 95%;
    }

    .lightbox-info {
        font-size: 0.8em;
        padding: 8px 15px;
    }
}

/* w3m 终端浏览器兼容 */
@media (max-width: 1px) {
    .lightbox {
        display: none !important;
    }
}
```

#### 3.3 添加灯箱 JavaScript 代码

在 `</body>` 标签之前（灯箱 HTML 之后）添加：

```html
<script>
// ============ 图片灯箱功能 ============

// 全局变量
let currentImageIndex = 0;
const images = [
    {% for img in images %}
    {
        src: 'photo/{{ img.filename }}',
        alt: '图片 {{ loop.index }}',
        caption: '[{{ loop.index }}] {{ img.filename }}{% if img.size %} ({{ img.size }}){% endif %}'
    }{% if not loop.last %},{% endif %}
    {% endfor %}
];
const totalImages = images.length;

/**
 * 打开灯箱
 * @param {number} index - 图片索引（从 0 开始）
 */
function openLightbox(index) {
    if (totalImages === 0) return;

    currentImageIndex = index;
    const lightbox = document.getElementById('lightbox');
    lightbox.classList.add('active');

    updateLightboxImage();

    // 禁止页面滚动
    document.body.style.overflow = 'hidden';
}

/**
 * 关闭灯箱
 */
function closeLightbox() {
    const lightbox = document.getElementById('lightbox');
    lightbox.classList.remove('active');

    // 恢复页面滚动
    document.body.style.overflow = 'auto';
}

/**
 * 切换图片
 * @param {number} direction - 方向（-1 = 上一张，1 = 下一张）
 */
function changeImage(direction) {
    if (totalImages === 0) return;

    currentImageIndex += direction;

    // 循环切换
    if (currentImageIndex < 0) {
        currentImageIndex = totalImages - 1;
    } else if (currentImageIndex >= totalImages) {
        currentImageIndex = 0;
    }

    updateLightboxImage();
}

/**
 * 更新灯箱图片
 */
function updateLightboxImage() {
    const img = document.getElementById('lightbox-img');
    const caption = document.getElementById('lightbox-caption');

    const currentImage = images[currentImageIndex];

    img.src = currentImage.src;
    img.alt = currentImage.alt;
    caption.textContent = currentImage.caption;
}

/**
 * 键盘事件监听
 */
document.addEventListener('keydown', function(event) {
    const lightbox = document.getElementById('lightbox');

    // 只在灯箱打开时响应
    if (!lightbox.classList.contains('active')) return;

    switch(event.key) {
        case 'Escape':
            closeLightbox();
            break;
        case 'ArrowLeft':
            changeImage(-1);
            break;
        case 'ArrowRight':
            changeImage(1);
            break;
    }
});

// ============ 可选：触摸手势支持（移动端） ============

let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', function(event) {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox.classList.contains('active')) return;

    touchStartX = event.changedTouches[0].screenX;
}, false);

document.addEventListener('touchend', function(event) {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox.classList.contains('active')) return;

    touchEndX = event.changedTouches[0].screenX;
    handleSwipe();
}, false);

function handleSwipe() {
    const swipeThreshold = 50; // 最小滑动距离

    if (touchEndX < touchStartX - swipeThreshold) {
        // 向左滑动 → 下一张
        changeImage(1);
    }

    if (touchEndX > touchStartX + swipeThreshold) {
        // 向右滑动 → 上一张
        changeImage(-1);
    }
}
</script>
```

**关键点说明**:
- `images` 数组：使用 Jinja2 模板动态生成图片列表
- `openLightbox(index)`: 打开灯箱并显示指定图片
- `closeLightbox()`: 关闭灯箱
- `changeImage(direction)`: 切换图片（支持循环）
- 键盘事件：ESC 关闭，← → 切换
- 触摸手势：左右滑动切换（移动端）

---

### Step 4: 更新模板注释和元数据（5 分钟）

#### 4.1 修改页脚统计信息

将第 128-130 行的版本号更新：

```html
<p>
    <b>归档:</b> {{ archive_time }} |
    <b>生成器:</b> Python Scraper v2.6 (Playwright + Jinja2 + JS Lightbox)
</p>
```

#### 4.2 添加模板顶部注释

在第 1 行之前添加：

```html
<!--
    模板版本: v2.6
    更新日期: 2026-02-12
    新增功能:
    - ✅ 图片嵌入显示（<img> 标签）
    - ✅ 视频嵌入播放（<video> 标签）
    - ✅ 图片灯箱功能（原生 JS）
    - ✅ 键盘导航支持（ESC, ← →）
    - ✅ 触摸手势支持（移动端）
    - ✅ 响应式设计
    - ✅ w3m 终端浏览器兼容
-->
```

---

## ✅ 验收标准

### 基础功能测试（P0）

#### Test 1: 图片显示测试
```bash
# 前置条件：归档一个包含至少 3 张图片的帖子
cd python
python main.py
# 选择 [3] 立即更新，选择作者，限制 1 页

# 验证步骤：
1. 打开生成的 content.html
2. 检查图片是否直接显示（不只是链接）
3. 检查图片懒加载（滚动时才加载）
4. 检查图片加载失败时的占位符

# 预期结果：
✅ 所有图片正常显示
✅ 图片布局整齐（网格布局）
✅ 显示图片序号和文件大小
✅ 下载链接正常工作
```

#### Test 2: 视频播放测试
```bash
# 前置条件：归档一个包含视频的帖子

# 验证步骤：
1. 打开生成的 content.html
2. 检查视频播放器是否显示
3. 点击播放按钮测试视频播放
4. 测试视频控件（播放、暂停、音量、全屏）

# 预期结果：
✅ 视频播放器正常显示
✅ 视频能正常播放
✅ 视频控件功能完整
✅ 下载链接正常工作
```

#### Test 3: 灯箱基础功能测试
```bash
# 验证步骤：
1. 打开包含多张图片的 content.html
2. 点击任意一张图片
3. 检查灯箱是否打开
4. 检查图片是否放大显示
5. 检查图片序号信息

# 预期结果：
✅ 点击图片能打开灯箱
✅ 灯箱显示大图
✅ 显示图片序号和文件名
✅ 背景半透明（黑色遮罩）
```

#### Test 4: 键盘导航测试
```bash
# 验证步骤：
1. 打开灯箱
2. 按 → 键
3. 按 ← 键
4. 按 ESC 键

# 预期结果：
✅ → 键切换到下一张（循环）
✅ ← 键切换到上一张（循环）
✅ ESC 键关闭灯箱
✅ 关闭灯箱后页面滚动恢复
```

#### Test 5: 关闭灯箱测试
```bash
# 验证步骤：
1. 打开灯箱
2. 点击右上角 X 按钮
3. 重新打开灯箱
4. 点击背景黑色区域

# 预期结果：
✅ 点击 X 按钮能关闭
✅ 点击背景能关闭
✅ 关闭后页面状态正常
```

### 高级功能测试（P1）

#### Test 6: 响应式设计测试
```bash
# 验证步骤：
1. 打开 content.html
2. 调整浏览器窗口到不同宽度：
   - 桌面端：1200px
   - 平板：768px
   - 手机：375px
3. 检查图片和视频的布局

# 预期结果：
✅ 桌面端：多列网格布局
✅ 平板：2 列布局
✅ 手机：单列布局
✅ 所有尺寸下灯箱正常显示
```

#### Test 7: 移动端触摸手势测试（可选）
```bash
# 验证步骤：
1. 使用手机或浏览器开发者工具模拟触摸设备
2. 打开灯箱
3. 在图片上向左滑动
4. 在图片上向右滑动

# 预期结果：
✅ 向左滑动切换到下一张
✅ 向右滑动切换到上一张
✅ 滑动距离不足时不触发切换
```

#### Test 8: 性能测试
```bash
# 验证步骤：
1. 归档一个包含 50+ 图片的帖子
2. 打开 content.html
3. 检查页面加载速度
4. 检查图片懒加载是否生效
5. 打开浏览器开发者工具查看网络请求

# 预期结果：
✅ 页面初始加载时间 < 2 秒
✅ 图片按需加载（滚动到视口内才加载）
✅ 网络请求数量合理
```

### 兼容性测试（P0）

#### Test 9: w3m 终端浏览器兼容测试
```bash
# 验证步骤：
w3m content.html

# 预期结果：
✅ 能正常查看标题、作者、时间
✅ 能正常查看正文内容
✅ 能看到图片下载链接
✅ 能看到视频下载链接
✅ 不会因 JavaScript 报错
```

#### Test 10: 多浏览器测试
```bash
# 验证步骤：
在以下浏览器中打开 content.html：
- Chrome/Edge
- Firefox
- Safari（如有 Mac）
- 移动端浏览器（Android/iOS）

# 预期结果：
✅ 所有浏览器中功能正常
✅ CSS 样式一致
✅ JavaScript 功能正常
```

---

## 🔒 风险控制

### 备份策略
```bash
# 实施前备份
cp python/src/templates/post.html python/src/templates/post.html.backup

# 如需回滚
cp python/src/templates/post.html.backup python/src/templates/post.html
```

### 灰度发布策略
1. **阶段 1**: 只修改测试环境模板
2. **阶段 2**: 使用测试配置归档 1-2 个作者
3. **阶段 3**: 确认无问题后全量发布

### 降级方案
如果灯箱功能有严重 Bug，可以快速降级：
1. 注释掉灯箱 JavaScript 代码
2. 移除 `onclick="openLightbox()"` 事件
3. 保留图片和视频的嵌入显示

---

## 📊 预计工作量

| 任务 | 预计时间 | 难度 |
|------|---------|------|
| Step 1: 图片嵌入显示 | 30 分钟 | ⭐⭐ |
| Step 2: 视频嵌入播放 | 20 分钟 | ⭐ |
| Step 3: 灯箱功能实现 | 60 分钟 | ⭐⭐⭐ |
| Step 4: 元数据更新 | 5 分钟 | ⭐ |
| 测试验证 | 30 分钟 | ⭐⭐ |
| **总计** | **2-3 小时** | **⭐⭐⭐** |

---

## 📚 参考资源

### 相关文档
- `MEDIA_DISPLAY_ENHANCEMENT_ANALYSIS.md` - 详细分析文档
- `python/src/templates/post.html` - 当前模板
- `python/src/templates/filters.py` - Jinja2 过滤器

### 技术参考
- [MDN: \<img\> 标签](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/img)
- [MDN: \<video\> 标签](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/video)
- [MDN: CSS Grid 布局](https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_Grid_Layout)
- [MDN: 键盘事件](https://developer.mozilla.org/zh-CN/docs/Web/API/KeyboardEvent)
- [MDN: 触摸事件](https://developer.mozilla.org/zh-CN/docs/Web/API/Touch_events)

---

## 📝 提交检查清单

实施完成后，确认以下事项：

- [ ] `post.html` 备份已创建
- [ ] 图片嵌入显示功能完成
- [ ] 视频嵌入播放功能完成
- [ ] 灯箱 HTML 结构添加完成
- [ ] 灯箱 CSS 样式添加完成（约 80 行）
- [ ] 灯箱 JavaScript 代码添加完成（约 70 行）
- [ ] 模板版本号更新为 v2.6
- [ ] 所有 P0 测试通过（Test 1-5）
- [ ] w3m 兼容性测试通过（Test 9）
- [ ] 至少完成一次完整归档测试
- [ ] 代码格式整洁，注释清晰
- [ ] 准备好 Git 提交信息

### Git 提交信息模板
```bash
git add python/src/templates/post.html
git commit -m "feat(templates): add media display and JS lightbox

- 图片嵌入显示（<img> 标签 + 网格布局）
- 视频嵌入播放（<video> 标签）
- 图片灯箱功能（原生 JS）
- 键盘导航支持（ESC, ← →）
- 触摸手势支持（移动端滑动）
- 响应式设计（移动端友好）
- w3m 终端浏览器兼容

模板版本: v2.5 → v2.6
代码量: +200 行（CSS 80 + JS 70 + HTML 50）
测试状态: ✅ 所有 P0 测试通过

参考: MEDIA_DISPLAY_IMPLEMENTATION_PLAN.md
"
```

---

## 🎯 最终验收标准

Phase 2.6 完成的判定标准：

- [ ] **P0 功能**: 图片显示、视频播放、灯箱基础功能、键盘导航、关闭灯箱
- [ ] **P0 测试**: Test 1-5 全部通过
- [ ] **兼容性**: w3m 终端浏览器正常使用（Test 9）
- [ ] **响应式**: 移动端显示正常（Test 6）
- [ ] **性能**: 懒加载生效，页面加载流畅（Test 8）
- [ ] **无严重 Bug**: 不影响正常归档和浏览
- [ ] **文档更新**: 提交信息清晰，包含变更说明

---

**准备就绪，等待执行实施！**

建议实施流程：
1. ✅ 阅读本文档（您正在做）
2. ⏳ 备份当前模板
3. ⏳ 按步骤修改 post.html
4. ⏳ 测试归档一个作者（1-2 页）
5. ⏳ 验证所有 P0 测试
6. ⏳ Git 提交并标记版本
