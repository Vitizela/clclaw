# 故障排查指南

本文档记录项目开发中遇到的关键问题和解决方案，帮助快速定位和修复类似问题。

---

## 数据库同步问题

### 问题：Media 记录为 0，EXIF 数据未提取

**症状：**
```bash
./verify_exif.sh
# 输出：
# ✓ 帖子已入库: XXX
# ✓ 图片记录: 0 张  ← 问题！
# ❌ 图片记录为 0，数据库同步失败！
```

**可能原因及解决方案：**

#### 1. 变量未定义

**错误信息：** `name 'author_name' is not defined`

**原因：** 函数内部使用了外部作用域的变量

**定位：**
```bash
# 查看归档日志
grep "数据库同步失败" logs/scraper.log
# 输出：WARNING - ⚠️  数据库同步失败: name 'author_name' is not defined
```

**修复：**
```python
# ❌ 错误
sync_archived_post(author_name=author_name, ...)

# ✅ 正确
sync_archived_post(author_name=post_data.get('author', 'Unknown'), ...)
```

**相关文件：** `python/src/scraper/archiver.py`
**提交：** 779976c

---

#### 2. 路径类型不匹配

**错误信息：** Media 记录为 0，但无明显错误

**原因：** 传递的是 URL 列表，而非文件路径

**定位：**
```bash
# 检查传递的数据
python3 -c "
import sys
sys.path.insert(0, 'python')
from pathlib import Path

post_dir = Path('/path/to/post')
# 检查 metadata['images'] 的值
print(metadata.get('images', []))
# 如果输出 ['https://...', 'https://...'] → 错误
# 应该输出 ['photo/img_1.jpg', 'photo/img_2.jpg'] → 正确
"
```

**修复：**
```python
# ❌ 错误：传递 URL
'images': post_data.get('images', [])  # ['https://...']

# ✅ 正确：扫描实际文件
image_files = []
photo_dir = post_dir / 'photo'
if photo_dir.exists():
    for pattern in ['img_*.jpg', 'img_*.png', 'img_*.jpeg', 'img_*.webp']:
        for img_file in sorted(photo_dir.glob(pattern)):
            image_files.append(f'photo/{img_file.name}')
'images': image_files  # ['photo/img_1.jpg', ...]
```

**相关文件：** `python/src/scraper/archiver.py`
**提交：** 91d8069

---

#### 3. Early Return 跳过逻辑

**错误信息：** 重新归档后 Media 仍为 0

**原因：** Post 已存在时直接返回，跳过 Media 同步

**定位：**
```bash
# 检查数据库
python3 -c "
import sys
sys.path.insert(0, 'python')
from src.database.models import Post

Post._db = get_default_connection()
post = Post.get_by_url('https://...')
print(f'Post 存在: {post is not None}')
print(f'Post ID: {post.id if post else None}')
# 如果 Post 存在但 Media 为 0 → 触发此问题
"
```

**修复：**
```python
# ❌ 错误：提前返回
if Post.exists(post_url):
    post.update(...)
    return True  # ← 跳过 Media 同步

# ✅ 正确：继续执行
if Post.exists(post_url):
    post.update(...)
    # 继续执行 Media 同步
else:
    post = Post.create(...)
# Media 同步代码（两个分支都会执行）
```

**相关文件：** `python/src/database/sync.py`
**提交：** a4bfcb5

---

#### 4. 变量作用域错误

**错误信息：** `cannot access local variable 'archived_date' where it is not associated with a value`

**原因：** 变量定义在 if/else 分支内，另一分支无法访问

**定位：**
```bash
# 手动测试同步
python3 -c "
from src.database.sync import sync_archived_post
result = sync_archived_post(...)
# 如果报错提到 archived_date → 触发此问题
"
```

**修复：**
```python
# ❌ 错误：定义在分支内
if condition:
    ...
else:
    archived_date = datetime.now().strftime("%Y-%m-%d")

# 后续使用
Media.create(..., download_date=archived_date)  # ← if 分支会报错

# ✅ 正确：提前定义
archived_date = datetime.now().strftime("%Y-%m-%d")
if condition:
    ...
else:
    ...
```

**相关文件：** `python/src/database/sync.py`
**提交：** 5de8f26

---

#### 5. 方法签名缺少参数

**错误信息：** `Media.create() got an unexpected keyword argument 'exif_make'`

**原因：** 添加了新字段，但忘记更新 `create()` 方法

**定位：**
```bash
# 检查方法签名
grep -A 20 "def create" python/src/database/models.py | grep -A 20 "class Media"
# 如果没有 exif_* 参数 → 触发此问题
```

**修复：**
```python
# ❌ 错误：缺少参数
def create(cls, post_id, type, url, ...):
    pass

# ✅ 正确：添加所有参数
def create(cls, post_id, type, url, ...,
    exif_make=None, exif_model=None, exif_datetime=None,
    exif_iso=None, exif_aperture=None, exif_shutter_speed=None,
    exif_focal_length=None, exif_gps_lat=None, exif_gps_lng=None, exif_location=None
):
    cursor = conn.execute("""
        INSERT INTO media (..., exif_make, exif_model, ...)
        VALUES (?, ?, ...)
    """, (..., exif_make, exif_model, ...))
```

**相关文件：** `python/src/database/models.py`
**提交：** 5de8f26

---

### 诊断流程

遇到 Media 记录为 0 时，按以下顺序检查：

1. **检查归档日志**
   ```bash
   grep "数据库同步" logs/scraper.log
   # 查看是否有 "✓ 已同步到数据库" 或错误信息
   ```

2. **检查数据库记录**
   ```bash
   ./verify_exif.sh
   # 确认 Post 和 Media 的状态
   ```

3. **手动测试同步**
   ```bash
   python3 -c "
   from src.database.sync import sync_archived_post
   from pathlib import Path

   post_dir = Path('/path/to/post')
   image_files = [f'photo/{f.name}' for f in (post_dir/'photo').glob('img_*.jpg')]

   metadata = {
       'title': '标题',
       'image_count': len(image_files),
       'images': image_files,
       'videos': [],
   }

   result = sync_archived_post('作者名', 'URL', post_dir, metadata)
   print(f'同步结果: {result}')
   "
   ```

4. **检查文件路径**
   ```bash
   # 确认图片文件存在
   ls -lh "/path/to/post/photo/"
   ```

5. **清理重试**
   ```bash
   ./clean_test_post.sh  # 清理旧数据
   # 重新归档
   ```

---

## EXIF 显示问题

### 问题：HTML 中看不到 EXIF 信息

**症状：** 打开 HTML，图片下方没有灰色背景的 EXIF 信息

**可能原因及解决方案：**

#### 1. 数据库中无 EXIF

**定位：**
```bash
./verify_exif.sh
# 输出：
# ✓ Media: 2 张
# ❌ 无 EXIF 数据  ← 问题
```

**原因：** 数据库同步时未提取 EXIF（参考上一节）

**修复：** 先解决数据库同步问题

---

#### 2. 模板版本过旧

**定位：**
```bash
# 检查 HTML 头部
head -20 "/path/to/post/content.html"
# 查看 "模板版本: v2.X"
# 如果 < v2.7 → 使用了旧模板
```

**原因：** Jinja2 模板缓存

**修复：**
```bash
# 重新生成 HTML
python3 python/regenerate_html.py "https://..."
```

---

#### 3. 模板未传递 EXIF 数据

**定位：**
```bash
# 检查 HTML 源码
grep -o "exif.*null" "/path/to/post/content.html"
# 如果找到 "exif: null" → EXIF 数据未传递给模板
```

**原因：** `archiver.py` 未调用 `_get_exif_data_for_post()`

**修复：**
```python
# 在 _prepare_media_list() 中
exif_data_map = {}
if media_type == 'image' and post_url:
    exif_data_map = self._get_exif_data_for_post(post_url)

# 添加到 media_item
if filename in exif_data_map:
    media_item['exif'] = exif_data_map[filename]
```

**相关文件：** `python/src/scraper/archiver.py`

---

#### 4. 图片本身无 EXIF

**定位：**
```bash
# 检查图片文件
python3 -c "
from PIL import Image
img = Image.open('/path/to/img.jpg')
exif = img.getexif()
print(f'EXIF 字段数: {len(exif)}')
# 如果为 0 → 图片无 EXIF
"
```

**原因：** 网络图片通常被剥离 EXIF

**解决：** 正常现象，无需修复

---

## 模板缓存问题

### 问题：修改模板后，HTML 仍使用旧版本

**症状：**
- 修改了 `post.html` 模板
- 重新归档后，生成的 HTML 仍然是旧版本

**原因：** Jinja2 默认缓存已编译的模板

**修复：**
```python
# python/src/scraper/archiver.py
self.jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    auto_reload=True,  # ← 添加：自动重新加载
    cache_size=0       # ← 添加：禁用缓存
)
```

**相关文件：** `python/src/scraper/archiver.py`
**提交：** 376d265

---

## sqlite3.Row 兼容性问题

### 问题：`'sqlite3.Row' object has no attribute 'get'`

**错误位置：** `python/src/database/models.py` - `Media.from_row()`

**原因：** `sqlite3.Row` 不支持 `.get()` 方法

**修复：**
```python
# ❌ 错误
def from_row(cls, row):
    return cls(
        exif_make=row.get('exif_make'),  # ← 报错
        ...
    )

# ✅ 正确：使用 safe_get() 辅助函数
def from_row(cls, row):
    def safe_get(key):
        try:
            return row[key]
        except (KeyError, IndexError):
            return None

    return cls(
        exif_make=safe_get('exif_make'),
        ...
    )
```

**相关文件：** `python/src/database/models.py`
**提交：** ed1f552

---

## 常用调试命令

### 检查数据库状态

```bash
# 查看帖子列表
python3 -c "
import sys
sys.path.insert(0, 'python')
from src.database.connection import get_default_connection

db = get_default_connection()
conn = db.get_connection()
cursor = conn.execute('SELECT id, title, image_count FROM posts ORDER BY id DESC LIMIT 10')
for row in cursor:
    print(f'{row[0]}: {row[1]} ({row[2]} 张图片)')
"

# 查看 Media 记录
python3 -c "
import sys
sys.path.insert(0, 'python')
from src.database.connection import get_default_connection

db = get_default_connection()
conn = db.get_connection()
cursor = conn.execute('SELECT post_id, COUNT(*) FROM media GROUP BY post_id ORDER BY post_id DESC LIMIT 10')
for row in cursor:
    print(f'Post {row[0]}: {row[1]} 个媒体文件')
"

# 查看 EXIF 统计
python3 -c "
import sys
sys.path.insert(0, 'python')
from src.database.connection import get_default_connection

db = get_default_connection()
conn = db.get_connection()
cursor = conn.execute('SELECT exif_make, exif_model, COUNT(*) FROM media WHERE exif_make IS NOT NULL GROUP BY exif_make, exif_model')
for row in cursor:
    print(f'{row[0]} {row[1]}: {row[2]} 张')
"
```

### 清理测试数据

```bash
# 删除指定帖子的数据库记录
python3 -c "
import sys
sys.path.insert(0, 'python')
from src.database.connection import get_default_connection

db = get_default_connection()
conn = db.get_connection()
conn.execute('DELETE FROM posts WHERE url = ?', ('https://...',))
conn.commit()
print('✓ 已删除')
"

# 删除帖子目录
rm -rf "/path/to/post/directory"
```

### 手动提取 EXIF

```bash
# 批量提取
python3 -m src.database.migrate_exif --limit 100

# 检查单张图片
python3 -c "
from PIL import Image
from PIL.ExifTags import TAGS

img = Image.open('/path/to/img.jpg')
exif = img.getexif()
print(f'EXIF 字段数: {len(exif)}')

for tag_id, value in exif.items():
    tag_name = TAGS.get(tag_id, tag_id)
    print(f'{tag_name}: {value}')
"
```

### 重新生成 HTML

```bash
# 自动查找有 EXIF 的帖子
python3 python/regenerate_html.py

# 指定帖子 URL
python3 python/regenerate_html.py "https://..."

# 一键测试
python3 python/test_exif_display.py
```

---

## 预防措施

### 代码审查检查清单

当添加新功能或修改数据流时，检查：

- [ ] **变量作用域**：共享变量是否在正确的作用域定义？
- [ ] **Early Return**：提前返回是否会跳过必要的逻辑？
- [ ] **数据类型**：函数间传递的数据类型是否一致？
- [ ] **方法签名**：数据库 schema 变更后，是否同步更新 `create()` 方法？
- [ ] **错误处理**：异常是否被正确捕获和记录？
- [ ] **日志输出**：关键步骤是否有日志？便于调试

### 测试流程

修改数据库同步逻辑后：

1. **单元测试**：手动调用 `sync_archived_post()` 验证
2. **集成测试**：完整归档流程测试
3. **数据验证**：运行 `./verify_exif.sh` 检查结果
4. **显示验证**：运行 `python3 python/test_exif_display.py` 查看 HTML

### 日志建议

在关键位置添加日志：

```python
# 数据库同步开始
self.logger.info("  → 同步到数据库...")

# 关键数据
self.logger.debug(f"    author_name: {author_name}")
self.logger.debug(f"    image_files: {len(image_files)}")

# 成功/失败
self.logger.info("  ✓ 已同步到数据库")
# 或
self.logger.warning(f"  ⚠️  数据库同步失败: {e}")
```

---

## 参考文档

- **MEMORY.md** - 项目记忆（关键技术决策、常见陷阱）
- **EXIF_STATIC_DISPLAY.md** - EXIF 功能说明
- **PHASE4_DETAILED_PLAN.md** - Phase 4 详细计划
- **python/src/database/README.md** - 数据库模块文档

---

## 版本历史

- **v1.0** (2026-02-15) - 初始版本，记录 Phase 4 Week 1 调试经验
