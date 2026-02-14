# Phase 3 详细实施计划：数据库 + 基础统计

**文档版本**: v1.0
**创建日期**: 2026-02-13
**预计工期**: 3-4 天
**优先级**: P0（核心功能）
**前置依赖**: Phase 1 ✅ + Phase 2 ✅

---

## 📑 目录

1. [现状分析](#1-现状分析)
2. [设计目标](#2-设计目标)
3. [数据库架构设计](#3-数据库架构设计)
4. [模块架构设计](#4-模块架构设计)
5. [数据迁移策略](#5-数据迁移策略)
6. [功能设计](#6-功能设计)
7. [实施步骤](#7-实施步骤)
8. [测试策略](#8-测试策略)
9. [风险评估](#9-风险评估)
10. [验收标准](#10-验收标准)

---

## 1. 现状分析

### 1.1 当前数据存储方式

**文件系统结构**:
```
论坛存档/
├── 独醉笑清风/
│   ├── 2025/
│   │   └── 01/
│   │       └── 帖子标题1/
│   │           ├── content.html
│   │           ├── photo/
│   │           │   ├── img_1.jpg
│   │           │   └── img_2.jpg
│   │           └── video/
│   │               └── video_1.mp4
│   └── 2026/
│       └── 02/
│           └── 帖子标题2/
│               └── ...
├── 清风皓月/
└── ...
```

**配置文件数据** (`python/config.yaml`):
```yaml
followed_authors:
  - name: "独醉笑清风"
    added_date: "2026-02-11"
    last_update: "2026-02-11 22:58:52"
    total_posts: 80
    total_images: 0
    total_videos: 0
    forum_total_posts: 120
    tags: ["synced_from_nodejs"]
```

**URL Hash 追踪数据** (`python/data/archived_posts.json`):
```json
{
  "独醉笑清风": {
    "hashes": ["a3f5b2c1", "7d8e9f0a", ...],
    "last_check": "2026-02-13 18:30:00",
    "total_count": 80
  }
}
```

### 1.2 当前限制

1. **查询效率低**: 统计需要遍历整个文件系统
2. **数据分散**: 元数据分布在多个地方（config.yaml、archived_posts.json、文件系统）
3. **难以分析**: 无法快速查询时间分布、内容统计等
4. **扩展性差**: 添加新的统计维度需要重新扫描所有文件

### 1.3 数据量估算

根据当前配置文件：
- 关注作者: 9 位
- 总归档帖子: ~350 篇（估算）
- 总图片: ~1,000 张（估算）
- 总视频: ~50 个（估算）
- 归档目录大小: ~2-3 GB

**预期增长**:
- 未来 1 年: 作者 20 位，帖子 2,000 篇
- SQLite 完全适用（<10GB 数据）

---

## 2. 设计目标

### 2.1 核心目标

1. **建立数据持久化层**: 使用 SQLite 存储所有归档元数据
2. **历史数据导入**: 将现有文件系统数据导入数据库
3. **实时同步**: 归档新帖时自动更新数据库
4. **快速统计**: 支持 <1 秒查询响应
5. **数据一致性**: 数据库与文件系统保持同步

### 2.2 非目标（Phase 4）

- ❌ 复杂分析（词云、趋势图）
- ❌ 全文搜索
- ❌ 内容存储（content.html 仍保存在文件系统）
- ❌ 图片/视频存储（仍保存在文件系统）

### 2.3 设计原则

1. **最小侵入**: 不改变现有文件组织方式
2. **向后兼容**: 支持没有数据库时的降级运行
3. **性能优先**: 查询效率 > 写入效率（读多写少）
4. **数据冗余**: 允许适度冗余以加速查询
5. **可观测性**: 提供数据一致性检查工具

---

## 3. 数据库架构设计

### 3.1 表结构设计

#### 表 1: `authors` - 作者表

**用途**: 存储关注的作者基本信息

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| `name` | TEXT | UNIQUE NOT NULL | 作者名（唯一） |
| `added_date` | TEXT | NOT NULL | 关注日期（YYYY-MM-DD） |
| `last_update` | TEXT | | 最后更新时间（YYYY-MM-DD HH:MM:SS） |
| `url` | TEXT | | 作者 URL |
| `total_posts` | INTEGER | DEFAULT 0 | 已归档帖子数 |
| `forum_total_posts` | INTEGER | DEFAULT 0 | 论坛总帖子数 |
| `total_images` | INTEGER | DEFAULT 0 | 总图片数 |
| `total_videos` | INTEGER | DEFAULT 0 | 总视频数 |
| `total_size_bytes` | INTEGER | DEFAULT 0 | 总占用空间（字节） |
| `tags` | TEXT | | 标签（JSON 数组字符串） |
| `notes` | TEXT | | 备注 |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 记录创建时间 |
| `updated_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 记录更新时间 |

**索引**:
```sql
CREATE UNIQUE INDEX idx_authors_name ON authors(name);
```

**设计决策**:
- ✅ 使用 TEXT 存储日期（与 config.yaml 格式一致，易于读写）
- ✅ tags 存储为 JSON 字符串（简化设计，避免关联表）
- ✅ 冗余统计字段（避免频繁聚合查询）

---

#### 表 2: `posts` - 帖子表

**用途**: 存储每篇帖子的元数据

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| `author_id` | INTEGER | NOT NULL | 作者 ID（外键） |
| `url` | TEXT | UNIQUE NOT NULL | 帖子 URL（唯一标识） |
| `url_hash` | TEXT | NOT NULL | URL 的 MD5 hash（8 位） |
| `title` | TEXT | NOT NULL | 帖子标题 |
| `publish_date` | TEXT | | 发布日期（YYYY-MM-DD HH:MM:SS） |
| `publish_year` | INTEGER | | 发布年份（冗余，加速查询） |
| `publish_month` | INTEGER | | 发布月份（1-12，冗余） |
| `publish_hour` | INTEGER | | 发布小时（0-23，冗余） |
| `publish_weekday` | INTEGER | | 星期几（0=周一，冗余） |
| `content_length` | INTEGER | DEFAULT 0 | 内容长度（字符数） |
| `word_count` | INTEGER | DEFAULT 0 | 字数统计（分词后） |
| `image_count` | INTEGER | DEFAULT 0 | 图片数量 |
| `video_count` | INTEGER | DEFAULT 0 | 视频数量 |
| `file_path` | TEXT | NOT NULL | 归档目录路径 |
| `archived_date` | TEXT | NOT NULL | 归档日期 |
| `file_size_bytes` | INTEGER | DEFAULT 0 | 目录占用空间 |
| `is_complete` | BOOLEAN | DEFAULT 1 | 是否完整归档 |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 记录创建时间 |
| `updated_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 记录更新时间 |

**索引**:
```sql
-- 关键索引
CREATE UNIQUE INDEX idx_posts_url ON posts(url);
CREATE INDEX idx_posts_url_hash ON posts(url_hash);
CREATE INDEX idx_posts_author ON posts(author_id);

-- 时间查询索引
CREATE INDEX idx_posts_publish_date ON posts(publish_date);
CREATE INDEX idx_posts_year_month ON posts(publish_year, publish_month);

-- 统计查询索引
CREATE INDEX idx_posts_author_date ON posts(author_id, publish_date);
```

**外键约束**:
```sql
FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
```

**设计决策**:
- ✅ `url_hash` 与 `archived_posts.json` 保持一致（新帖检测）
- ✅ 冗余时间字段（year/month/hour/weekday）加速 Phase 4 分析
- ✅ `file_path` 存储相对路径（便于归档目录迁移）
- ✅ `is_complete` 标记归档完整性（支持断点续传检查）
- ❌ 不存储 `content`（保持文件系统存储，避免数据库膨胀）

---

#### 表 3: `media` - 媒体文件表

**用途**: 存储图片和视频的详细信息

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| `post_id` | INTEGER | NOT NULL | 帖子 ID（外键） |
| `type` | TEXT | NOT NULL | 类型：'image' 或 'video' |
| `url` | TEXT | NOT NULL | 原始 URL |
| `file_name` | TEXT | NOT NULL | 文件名（如 img_1.jpg） |
| `file_path` | TEXT | NOT NULL | 文件相对路径 |
| `file_size_bytes` | INTEGER | DEFAULT 0 | 文件大小 |
| `width` | INTEGER | | 图片宽度（可选） |
| `height` | INTEGER | | 图片高度（可选） |
| `duration` | INTEGER | | 视频时长（秒，可选） |
| `is_downloaded` | BOOLEAN | DEFAULT 1 | 是否已下载 |
| `download_date` | TEXT | | 下载日期 |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 记录创建时间 |

**索引**:
```sql
CREATE INDEX idx_media_post ON media(post_id);
CREATE INDEX idx_media_type ON media(type);
CREATE INDEX idx_media_post_type ON media(post_id, type);
```

**外键约束**:
```sql
FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
```

**设计决策**:
- ✅ 支持查询"每篇帖子的媒体数量"
- ✅ 支持统计"总图片/视频数"
- ✅ 为 Phase 4 可视化预留维度字段（width/height/duration）
- ✅ `is_downloaded` 支持断点续传检查

---

#### 表 4: `sync_history` - 同步历史表

**用途**: 记录数据库同步操作历史（可选，便于调试）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| `sync_type` | TEXT | NOT NULL | 类型：'import', 'archive', 'check' |
| `author_name` | TEXT | | 相关作者 |
| `posts_added` | INTEGER | DEFAULT 0 | 新增帖子数 |
| `posts_updated` | INTEGER | DEFAULT 0 | 更新帖子数 |
| `errors` | INTEGER | DEFAULT 0 | 错误数 |
| `duration_seconds` | REAL | | 耗时（秒） |
| `status` | TEXT | NOT NULL | 状态：'success', 'failed', 'partial' |
| `error_message` | TEXT | | 错误信息 |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | 同步时间 |

**索引**:
```sql
CREATE INDEX idx_sync_history_type ON sync_history(sync_type);
CREATE INDEX idx_sync_history_date ON sync_history(created_at);
```

**设计决策**:
- ✅ 辅助调试（查看历史同步记录）
- ✅ 监控数据质量（错误统计）
- ⚠️ 可选实现（优先级较低）

---

### 3.2 数据库视图设计

#### 视图 1: `v_author_stats` - 作者统计视图

**用途**: 快速查询每个作者的统计信息

```sql
CREATE VIEW v_author_stats AS
SELECT
    a.id,
    a.name,
    a.added_date,
    a.last_update,
    COUNT(DISTINCT p.id) as post_count,
    SUM(p.image_count) as image_count,
    SUM(p.video_count) as video_count,
    SUM(p.file_size_bytes) as total_size_bytes,
    MIN(p.publish_date) as first_post_date,
    MAX(p.publish_date) as latest_post_date
FROM authors a
LEFT JOIN posts p ON a.id = p.author_id
GROUP BY a.id;
```

**优势**:
- ✅ 封装复杂聚合查询
- ✅ 提供一致的统计接口
- ✅ 可作为 API 返回格式的基础

---

#### 视图 2: `v_monthly_stats` - 月度统计视图

**用途**: 为 Phase 4 趋势分析预留

```sql
CREATE VIEW v_monthly_stats AS
SELECT
    a.name as author_name,
    p.publish_year,
    p.publish_month,
    COUNT(*) as post_count,
    SUM(p.image_count) as image_count,
    SUM(p.video_count) as video_count
FROM posts p
JOIN authors a ON p.author_id = a.id
GROUP BY a.name, p.publish_year, p.publish_month
ORDER BY p.publish_year DESC, p.publish_month DESC;
```

---

### 3.3 触发器设计

#### 触发器 1: 自动更新作者统计

**目的**: 当帖子插入/更新/删除时，自动更新 `authors` 表的冗余统计字段

```sql
-- 插入帖子时
CREATE TRIGGER trg_posts_insert_update_author
AFTER INSERT ON posts
FOR EACH ROW
BEGIN
    UPDATE authors SET
        total_posts = (SELECT COUNT(*) FROM posts WHERE author_id = NEW.author_id),
        total_images = (SELECT SUM(image_count) FROM posts WHERE author_id = NEW.author_id),
        total_videos = (SELECT SUM(video_count) FROM posts WHERE author_id = NEW.author_id),
        total_size_bytes = (SELECT SUM(file_size_bytes) FROM posts WHERE author_id = NEW.author_id),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.author_id;
END;

-- 删除帖子时（类似逻辑）
CREATE TRIGGER trg_posts_delete_update_author
AFTER DELETE ON posts
FOR EACH ROW
BEGIN
    UPDATE authors SET
        total_posts = (SELECT COUNT(*) FROM posts WHERE author_id = OLD.author_id),
        total_images = (SELECT SUM(image_count) FROM posts WHERE author_id = OLD.author_id),
        total_videos = (SELECT SUM(video_count) FROM posts WHERE author_id = OLD.author_id),
        total_size_bytes = (SELECT SUM(file_size_bytes) FROM posts WHERE author_id = OLD.author_id),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.author_id;
END;
```

**优势**:
- ✅ 自动维护冗余统计字段
- ✅ 保证数据一致性
- ✅ 查询时无需 JOIN + GROUP BY（性能提升）

**风险**:
- ⚠️ 批量导入时可能影响性能（解决：导入时禁用触发器）

---

### 3.4 数据库配置

#### SQLite 优化参数

```sql
-- 性能优化
PRAGMA journal_mode = WAL;           -- 写入优化
PRAGMA synchronous = NORMAL;         -- 平衡安全性和性能
PRAGMA cache_size = 10000;           -- 增大缓存（~40MB）
PRAGMA temp_store = MEMORY;          -- 临时表存储在内存

-- 外键约束
PRAGMA foreign_keys = ON;            -- 启用外键
```

**设计决策**:
- ✅ WAL 模式：支持并发读写
- ✅ NORMAL 同步：降低写入延迟，容忍极少数据丢失风险
- ✅ 启用外键：保证数据完整性

---

## 4. 模块架构设计

### 4.1 模块划分

```
src/database/
├── __init__.py           # 模块初始化
├── schema.sql            # 数据库结构定义
├── connection.py         # 数据库连接管理 ⭐
├── models.py             # 数据模型（ORM 风格）⭐
├── query.py              # 查询辅助函数 ⭐
├── migrate.py            # 历史数据导入工具 ⭐
├── sync.py               # 数据同步工具 ⭐
└── integrity.py          # 数据一致性检查 ⭐
```

### 4.2 模块职责

#### 4.2.1 `connection.py` - 数据库连接管理

**职责**:
- 创建和管理数据库连接
- 初始化数据库（执行 schema.sql）
- 提供连接单例（避免重复连接）
- 配置 SQLite 参数

**关键接口**:
```python
class DatabaseConnection:
    def __init__(self, db_path: str)
    def get_connection() -> sqlite3.Connection
    def initialize_database() -> None
    def close() -> None
```

**设计决策**:
- ✅ 单例模式：全局共享一个连接
- ✅ 懒加载：首次使用时才创建
- ✅ 自动初始化：如果数据库不存在则创建

---

#### 4.2.2 `models.py` - 数据模型

**职责**:
- 提供对象化的数据库访问（类似 ORM）
- 封装 CRUD 操作
- 数据验证

**核心类**:

**类 1: `Author` - 作者模型**
```python
class Author:
    # 属性
    id: int
    name: str
    added_date: str
    last_update: str
    url: str
    total_posts: int
    # ... 其他字段

    # 方法
    @classmethod
    def get_by_name(name: str) -> Optional[Author]

    @classmethod
    def get_all() -> List[Author]

    @classmethod
    def create(name: str, added_date: str, ...) -> Author

    def update(self, **kwargs) -> None

    def delete(self) -> None

    def get_posts(self) -> List[Post]

    def get_stats(self) -> dict
```

**类 2: `Post` - 帖子模型**
```python
class Post:
    # 属性
    id: int
    author_id: int
    url: str
    title: str
    publish_date: str
    # ... 其他字段

    # 方法
    @classmethod
    def get_by_url(url: str) -> Optional[Post]

    @classmethod
    def get_by_author(author_id: int) -> List[Post]

    @classmethod
    def create(author_id: int, url: str, ...) -> Post

    def update(self, **kwargs) -> None

    def delete(self) -> None

    def get_media(self) -> List[Media]

    @staticmethod
    def exists(url: str) -> bool
```

**类 3: `Media` - 媒体模型**
```python
class Media:
    # 属性
    id: int
    post_id: int
    type: str  # 'image' or 'video'
    file_path: str
    # ... 其他字段

    # 方法
    @classmethod
    def get_by_post(post_id: int) -> List[Media]

    @classmethod
    def create(post_id: int, type: str, ...) -> Media

    def update(self, **kwargs) -> None

    def delete(self) -> None
```

**设计决策**:
- ✅ 轻量级 ORM（不使用 SQLAlchemy，避免依赖）
- ✅ 类方法提供查询接口
- ✅ 实例方法提供修改接口
- ✅ 返回对象而非字典（类型安全）

---

#### 4.2.3 `query.py` - 查询辅助函数

**职责**:
- 提供高级查询功能（统计、聚合、排行）
- 封装复杂的 SQL 查询
- 为菜单系统提供数据接口

**关键函数**:

**函数 1: 总体统计**
```python
def get_global_stats() -> dict:
    """
    返回全局统计信息

    Returns:
        {
            'total_authors': 7,
            'total_posts': 245,
            'total_images': 1245,
            'total_videos': 67,
            'total_size_gb': 2.3,
            'latest_update': '2026-02-13 16:30:00'
        }
    """
```

**函数 2: 作者排行榜**
```python
def get_author_ranking(order_by: str = 'posts', limit: int = 10) -> List[dict]:
    """
    获取作者排行榜

    Args:
        order_by: 排序字段 ('posts', 'images', 'videos', 'size')
        limit: 返回数量

    Returns:
        [
            {'name': '独醉笑清风', 'posts': 80, 'images': 245, ...},
            {'name': '清风皓月', 'posts': 77, 'images': 189, ...},
            ...
        ]
    """
```

**函数 3: 月度统计**
```python
def get_monthly_stats(
    author_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]:
    """
    获取月度发帖统计（为 Phase 4 趋势分析准备）

    Returns:
        [
            {'year': 2026, 'month': 2, 'post_count': 15, ...},
            {'year': 2026, 'month': 1, 'post_count': 22, ...},
            ...
        ]
    """
```

**函数 4: 时间分布统计**
```python
def get_hourly_distribution(author_name: str) -> dict:
    """
    获取作者发帖的小时分布（为 Phase 4 热力图准备）

    Returns:
        {
            0: 2,   # 凌晨 0 点发了 2 篇
            1: 0,
            2: 1,
            ...
            23: 5
        }
    """
```

**函数 5: 数据完整性检查**
```python
def check_data_integrity() -> dict:
    """
    检查数据库与文件系统的一致性

    Returns:
        {
            'total_checked': 245,
            'missing_in_db': 3,      # 文件存在但数据库缺失
            'missing_files': 1,      # 数据库有记录但文件缺失
            'inconsistent': 2,       # 元数据不一致
            'details': [...]
        }
    """
```

**设计决策**:
- ✅ 函数式接口（简单易用）
- ✅ 返回字典或列表（便于 JSON 序列化）
- ✅ 预留 Phase 4 分析接口
- ✅ 提供数据质量检查功能

---

#### 4.2.4 `migrate.py` - 历史数据导入工具

**职责**:
- 扫描文件系统归档数据
- 解析元数据并导入数据库
- 提供增量导入和全量重建功能
- 显示导入进度

**核心流程**:

```
1. 扫描归档目录
   ↓
2. 遍历每个作者目录
   ↓
3. 遍历每个帖子目录
   ↓
4. 读取 content.html 提取元数据
   ↓
5. 扫描 photo/ 和 video/ 目录
   ↓
6. 写入数据库（authors + posts + media）
   ↓
7. 更新统计信息
```

**关键函数**:

**函数 1: 全量导入**
```python
def import_all_data(
    archive_path: str,
    config: dict,
    force_rebuild: bool = False,
    show_progress: bool = True
) -> dict:
    """
    导入所有历史数据

    Args:
        archive_path: 归档目录路径
        config: 配置字典（用于读取作者 URL、tags 等）
        force_rebuild: 是否强制重建（清空数据库重新导入）
        show_progress: 是否显示进度条

    Returns:
        {
            'authors_added': 7,
            'posts_added': 245,
            'media_added': 1312,
            'duration_seconds': 12.5,
            'errors': []
        }
    """
```

**函数 2: 单作者导入**
```python
def import_author_data(
    author_name: str,
    archive_path: str,
    config: dict
) -> dict:
    """
    导入单个作者的数据

    用于增量添加新作者后的数据导入
    """
```

**函数 3: 元数据提取**
```python
def extract_post_metadata(post_dir: Path) -> dict:
    """
    从帖子目录提取元数据

    Args:
        post_dir: 帖子目录路径（如 论坛存档/作者/2026/02/标题/）

    Returns:
        {
            'title': '帖子标题',
            'publish_date': '2026-02-11 10:30:00',
            'content_length': 1234,
            'image_count': 5,
            'video_count': 1,
            'images': ['photo/img_1.jpg', ...],
            'videos': ['video/video_1.mp4', ...],
            'file_size_bytes': 12345678
        }
    """
```

**元数据提取策略**:

1. **从目录结构提取**:
   - 作者名: 父目录名
   - 年份/月份: 路径中的 `2026/02/`
   - 标题: 目录名（可能被安全化）

2. **从 content.html 提取**:
   - 发布时间: HTML 中的时间戳
   - 内容长度: HTML 文件大小或纯文本长度
   - 原始标题: HTML 标题（未被安全化）

3. **从文件系统扫描**:
   - 图片/视频列表: 遍历 photo/ 和 video/
   - 文件大小: 递归计算目录大小

4. **从 config.yaml 补充**:
   - 作者 URL
   - 作者 tags
   - 关注日期

5. **从 archived_posts.json 补充**:
   - URL hash（用于新帖检测）

**设计决策**:
- ✅ 支持全量重建（测试和修复数据）
- ✅ 支持增量导入（只导入新增数据）
- ✅ 使用 tqdm 显示进度（用户友好）
- ✅ 错误容忍（单个帖子失败不影响整体）
- ✅ 事务批处理（提高导入性能）

**性能优化**:
- 批量插入（每 100 条 commit 一次）
- 导入时禁用触发器（导入完成后手动更新统计）
- 使用事务（减少磁盘 I/O）

---

#### 4.2.5 `sync.py` - 数据同步工具

**职责**:
- 在归档新帖时同步更新数据库
- 在删除作者时同步删除数据库记录
- 在配置变更时同步更新数据库

**核心函数**:

**函数 1: 同步新归档的帖子**
```python
def sync_archived_post(
    author_name: str,
    post_url: str,
    post_dir: Path,
    metadata: dict
) -> None:
    """
    归档完成后调用，将帖子信息写入数据库

    Args:
        author_name: 作者名
        post_url: 帖子 URL
        post_dir: 帖子目录路径
        metadata: 帖子元数据（由 archiver 提供）
    """
```

**函数 2: 同步删除作者**
```python
def sync_delete_author(author_name: str) -> None:
    """
    取消关注作者时调用，删除数据库中的记录

    注意：不删除文件系统中的归档数据
    """
```

**函数 3: 同步配置变更**
```python
def sync_config_to_db(config: dict) -> None:
    """
    配置文件变更后同步到数据库

    同步内容：
    - 作者 tags 变更
    - 作者 notes 变更
    - 作者 URL 变更
    """
```

**集成点**:

在 `archiver.py` 中：
```python
# 归档完成后
await archiver.archive_post(post_info)
# ↓ 新增：同步到数据库
from database.sync import sync_archived_post
sync_archived_post(author_name, post_url, post_dir, metadata)
```

在 `main_menu.py` 中：
```python
# 取消关注作者后
self.config_manager.remove_author(author_name)
# ↓ 新增：同步到数据库
from database.sync import sync_delete_author
sync_delete_author(author_name)
```

**设计决策**:
- ✅ 最小侵入（只需在关键点调用同步函数）
- ✅ 同步失败不影响归档（记录错误日志但继续）
- ✅ 提供手动修复工具（migrate.py 重新导入）

---

#### 4.2.6 `integrity.py` - 数据一致性检查

**职责**:
- 检查数据库与文件系统的一致性
- 检测缺失、重复、损坏的数据
- 提供自动修复功能

**核心函数**:

**函数 1: 全面检查**
```python
def check_all(archive_path: str, fix: bool = False) -> dict:
    """
    执行全面的数据一致性检查

    检查项：
    1. 数据库中的帖子在文件系统中是否存在
    2. 文件系统中的帖子在数据库中是否存在
    3. 统计字段是否准确
    4. 外键关系是否完整

    Args:
        archive_path: 归档目录
        fix: 是否自动修复（慎用）

    Returns:
        {
            'total_checked': 245,
            'issues': [
                {'type': 'missing_file', 'post_id': 123, 'url': '...'},
                {'type': 'missing_in_db', 'path': '...'},
                {'type': 'stat_mismatch', 'author': '...', 'field': 'total_posts'},
                ...
            ],
            'fixed': 5  # 如果 fix=True
        }
    """
```

**函数 2: 修复统计字段**
```python
def fix_statistics() -> None:
    """
    重新计算并更新所有作者的统计字段
    """
```

**函数 3: 检测孤立记录**
```python
def check_orphaned_records() -> dict:
    """
    检测孤立的数据库记录

    Returns:
        {
            'orphaned_posts': [...],   # 作者不存在的帖子
            'orphaned_media': [...]    # 帖子不存在的媒体
        }
    """
```

**使用场景**:
- 导入数据后验证
- 定期维护（每月运行一次）
- 修复数据错误
- 调试数据同步问题

**菜单集成**:
```
[6] 查看统计
    ↓
    [高级] → [数据完整性检查]
```

---

## 5. 数据迁移策略

### 5.1 迁移流程

```
阶段 1: 准备
├─ 备份现有数据
├─ 创建数据库
└─ 验证依赖

阶段 2: 作者数据导入
├─ 从 config.yaml 读取作者列表
├─ 写入 authors 表
└─ 验证作者记录

阶段 3: 帖子数据扫描
├─ 遍历归档目录
├─ 提取每篇帖子的元数据
├─ 批量写入 posts 表
└─ 显示进度条

阶段 4: 媒体数据扫描
├─ 扫描每篇帖子的 photo/ 和 video/
├─ 批量写入 media 表
└─ 更新统计

阶段 5: 验证
├─ 运行完整性检查
├─ 修复统计字段
└─ 生成导入报告
```

### 5.2 性能优化策略

**问题**: 导入 350 篇帖子 + 1,000 张图片 = ~1,350 条记录

**优化手段**:

1. **批量插入**
   - 每 100 条记录 commit 一次
   - 使用 `executemany()` 而非循环 `execute()`

2. **禁用约束**
   ```python
   # 导入前
   PRAGMA foreign_keys = OFF;
   DROP TRIGGER trg_posts_insert_update_author;

   # ... 导入数据 ...

   # 导入后
   PRAGMA foreign_keys = ON;
   CREATE TRIGGER ...;
   # 手动更新统计
   ```

3. **使用事务**
   ```python
   conn.execute("BEGIN TRANSACTION")
   # ... 插入数据 ...
   conn.execute("COMMIT")
   ```

4. **并行处理**
   - 作者级别并行（每个作者独立扫描）
   - 使用 `ProcessPoolExecutor`

**预期性能**:
- 扫描速度: ~50 篇/秒
- 导入 350 篇帖子: ~7 秒
- 导入 1,350 条媒体: ~3 秒
- **总计: <15 秒**

### 5.3 错误处理

**常见错误**:

1. **目录缺失**
   - 问题: `content.html` 不存在
   - 处理: 跳过该帖子，记录警告

2. **日期解析失败**
   - 问题: 无法从 HTML 提取发布时间
   - 处理: 使用归档日期作为替代

3. **编码问题**
   - 问题: 文件名包含特殊字符
   - 处理: 使用 `errors='ignore'` 读取

4. **重复 URL**
   - 问题: 同一 URL 出现多次
   - 处理: 跳过重复项，使用 `INSERT OR IGNORE`

**错误日志**:
```python
{
    'timestamp': '2026-02-13 16:30:00',
    'level': 'WARNING',
    'author': '独醉笑清风',
    'post_dir': '论坛存档/独醉笑清风/2026/02/标题/',
    'error': 'content.html not found',
    'action': 'skipped'
}
```

### 5.4 回滚策略

如果导入失败：

1. **删除数据库**
   ```bash
   rm python/data/forum_data.db
   ```

2. **重新导入**
   ```python
   python main.py
   # 选择 [高级] → [重新导入数据库]
   ```

3. **验证配置**
   - 检查 `config.yaml` 是否完整
   - 检查归档目录是否可访问

---

## 6. 功能设计

### 6.1 菜单集成

#### 6.1.1 主菜单改动

**现有菜单**:
```
[1] 关注新作者
[2] 查看关注列表
[3] 立即更新所有作者
[4] 取消关注作者
[5] 系统设置
[6] 查看统计（Phase 3 后可用）← 当前不可用
[7] 数据分析（Phase 4 后可用）← 灰色
[8] 退出
```

**Phase 3 改动**:
```
[6] 查看统计 ← 变为可用，绿色高亮
```

#### 6.1.2 统计菜单设计

**入口**: 主菜单 → [6] 查看统计

**子菜单**:
```
╔════════════════════════════════════════╗
║            📊 统计信息                  ║
╠════════════════════════════════════════╣
║  总关注作者: 7                         ║
║  总归档帖子: 245                       ║
║  总下载图片: 1,245                     ║
║  总下载视频: 67                        ║
║  占用空间: 2.3 GB                      ║
║  最后更新: 2026-02-13 16:30           ║
╚════════════════════════════════════════╝

作者排行榜（按帖子数）
─────────────────────────────────────
1. 独醉笑清风       80 篇   245 图   8 视频
2. 清风皓月         77 篇   189 图   5 视频
3. 厦门一只狼       70 篇   301 图   12 视频
4. 纯情母老虎       18 篇   45 图    3 视频
...

请选择操作：
  [1] 查看详细统计（选择作者）
  [2] 导出统计报告（CSV）
  [3] 数据完整性检查
  [0] 返回主菜单
```

#### 6.1.3 详细统计页面

**入口**: 统计菜单 → [1] 查看详细统计 → 选择作者

**显示内容**:
```
作者: 独醉笑清风
────────────────────────────────────────
基本信息:
  关注日期: 2026-02-11
  最后更新: 2026-02-11 22:58:52
  作者 URL: https://t66y.com/@独醉笑清风

归档统计:
  总帖子数: 80 篇
  总图片数: 245 张
  总视频数: 8 个
  总字数: 105,678 字
  平均帖子长度: 1,321 字
  平均图片/帖: 3.1
  平均视频/帖: 0.1

空间占用:
  总大小: 856 MB
  平均每帖: 10.7 MB

时间跨度:
  最早帖子: 2025-01-15 10:30
  最新帖子: 2026-02-10 18:45
  活跃天数: 391 天

按任意键返回...
```

### 6.2 首次运行流程

**场景**: 用户首次启用 Phase 3 功能

**流程**:
```
1. 用户运行 python main.py

2. 系统检测到数据库不存在
   ↓
   提示: "检测到首次使用统计功能，需要导入历史数据"

3. 询问用户
   ┌─────────────────────────────────────┐
   │ 是否立即导入历史归档数据到数据库？   │
   │                                     │
   │ 预计时间: ~15 秒                    │
   │ 数据量: 约 350 篇帖子               │
   │                                     │
   │ [Y] 立即导入  [N] 稍后导入          │
   └─────────────────────────────────────┘

4. 如果选择 [Y]:
   ┌─────────────────────────────────────┐
   │ 正在导入历史数据...                 │
   │ ████████████████░░░░ 80%            │
   │ 已处理: 280/350 篇帖子              │
   └─────────────────────────────────────┘

5. 导入完成
   ┌─────────────────────────────────────┐
   │ ✓ 导入完成！                        │
   │                                     │
   │ 作者数: 7                           │
   │ 帖子数: 350                         │
   │ 媒体数: 1,312                       │
   │ 用时: 12.5 秒                       │
   │                                     │
   │ 按任意键继续...                     │
   └─────────────────────────────────────┘

6. 进入主菜单（[6] 查看统计 变为可用）
```

### 6.3 数据完整性检查流程

**入口**: 统计菜单 → [3] 数据完整性检查

**流程**:
```
1. 扫描数据库和文件系统
   ┌─────────────────────────────────────┐
   │ 正在检查数据完整性...               │
   │ ████████████████████ 100%           │
   │ 已检查: 350/350 篇帖子              │
   └─────────────────────────────────────┘

2. 显示结果
   ╔════════════════════════════════════════╗
   ║        数据完整性检查报告               ║
   ╠════════════════════════════════════════╣
   ║  检查项目: 350 篇帖子                  ║
   ║  通过: 347 项                          ║
   ║  问题: 3 项                            ║
   ╚════════════════════════════════════════╝

   发现的问题:
   ────────────────────────────────────────
   [1] 数据库缺失
       - 帖子: 论坛存档/作者A/2026/01/标题X/
       - 建议: 重新导入该作者

   [2] 文件缺失
       - URL: https://...
       - 数据库记录存在但文件不存在
       - 建议: 删除数据库记录或重新归档

   [3] 统计不一致
       - 作者: 独醉笑清风
       - total_posts: 数据库=80, 实际=82
       - 建议: 修复统计字段

3. 提供操作选项
   请选择操作：
     [1] 自动修复（慎用）
     [2] 导出详细报告（CSV）
     [3] 重新导入所有数据
     [0] 返回
```

---

## 7. 实施步骤

### 7.1 总体时间线（3-4 天）

```
Day 1: 数据库设计与基础模块（6-8 小时）
├─ Morning: schema.sql + connection.py
├─ Afternoon: models.py 基础实现
└─ Evening: 单元测试

Day 2: 数据迁移工具（6-8 小时）
├─ Morning: migrate.py 核心逻辑
├─ Afternoon: 测试导入功能
└─ Evening: 性能优化

Day 3: 查询与同步（6-8 小时）
├─ Morning: query.py 统计函数
├─ Afternoon: sync.py 同步逻辑
└─ Evening: 集成到 archiver

Day 4: 菜单集成与测试（4-6 小时）
├─ Morning: 菜单集成
├─ Afternoon: 完整性检查工具
└─ Evening: 综合测试与文档
```

### 7.2 Day 1: 数据库设计与基础模块

#### 任务 1.1: 编写 schema.sql（1 小时）

**步骤**:
1. 创建文件 `src/database/schema.sql`
2. 定义 4 个表（authors, posts, media, sync_history）
3. 创建索引（7 个关键索引）
4. 创建视图（v_author_stats, v_monthly_stats）
5. 创建触发器（2 个自动更新触发器）
6. 添加注释

**验证**:
```bash
# 手动测试 SQL 语法
sqlite3 test.db < src/database/schema.sql
sqlite3 test.db ".schema"
```

#### 任务 1.2: 实现 connection.py（1 小时）

**步骤**:
1. 创建 `DatabaseConnection` 类
2. 实现单例模式
3. 实现 `initialize_database()` 方法
4. 配置 SQLite 参数（WAL, PRAGMA）
5. 添加错误处理

**验证**:
```python
# 测试脚本
from database.connection import DatabaseConnection

db = DatabaseConnection('test.db')
db.initialize_database()
conn = db.get_connection()
print("Tables:", conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
```

#### 任务 1.3: 实现 models.py 基础版（3 小时）

**步骤**:
1. 创建 `Author` 类
   - 实现 `create()`, `get_by_name()`, `get_all()`
2. 创建 `Post` 类
   - 实现 `create()`, `get_by_url()`, `exists()`
3. 创建 `Media` 类
   - 实现 `create()`, `get_by_post()`
4. 添加数据验证
5. 编写 docstring

**验证**:
```python
# 单元测试
from database.models import Author, Post, Media

# 创建作者
author = Author.create(name="测试作者", added_date="2026-02-13")
assert author.id > 0

# 查询作者
found = Author.get_by_name("测试作者")
assert found.name == "测试作者"

# 创建帖子
post = Post.create(
    author_id=author.id,
    url="https://test.com/1.html",
    title="测试标题",
    ...
)
assert post.id > 0
```

#### 任务 1.4: 单元测试（1 小时）

**步骤**:
1. 创建 `tests/test_database_models.py`
2. 测试 Author CRUD
3. 测试 Post CRUD
4. 测试外键约束
5. 测试触发器

---

### 7.3 Day 2: 数据迁移工具

#### 任务 2.1: 实现元数据提取（2 小时）

**步骤**:
1. 在 `migrate.py` 中实现 `extract_post_metadata()`
2. 从目录结构提取信息
3. 解析 `content.html`
4. 扫描媒体文件
5. 计算目录大小

**测试**:
```python
from database.migrate import extract_post_metadata
from pathlib import Path

post_dir = Path("论坛存档/独醉笑清风/2026/02/测试帖子")
metadata = extract_post_metadata(post_dir)
print(metadata)
```

#### 任务 2.2: 实现导入逻辑（3 小时）

**步骤**:
1. 实现 `import_all_data()`
2. 遍历归档目录
3. 批量插入数据（100 条/批）
4. 添加进度条（tqdm）
5. 错误处理和日志

**测试**:
```python
from database.migrate import import_all_data

result = import_all_data(
    archive_path="论坛存档",
    config=config,
    force_rebuild=True,
    show_progress=True
)

print(f"导入完成: {result}")
```

#### 任务 2.3: 性能优化（1 小时）

**步骤**:
1. 禁用触发器和外键
2. 使用事务批处理
3. 测量导入速度
4. 优化瓶颈

**目标**:
- 350 篇帖子 < 15 秒

---

### 7.4 Day 3: 查询与同步

#### 任务 3.1: 实现查询函数（2 小时）

**步骤**:
1. 在 `query.py` 实现：
   - `get_global_stats()`
   - `get_author_ranking()`
   - `get_monthly_stats()`
2. 测试查询性能（< 1 秒）

#### 任务 3.2: 实现同步逻辑（2 小时）

**步骤**:
1. 在 `sync.py` 实现：
   - `sync_archived_post()`
   - `sync_delete_author()`
2. 在 `archiver.py` 中集成
3. 在 `main_menu.py` 中集成

#### 任务 3.3: 实现完整性检查（2 小时）

**步骤**:
1. 在 `integrity.py` 实现：
   - `check_all()`
   - `fix_statistics()`
2. 测试检查功能

---

### 7.5 Day 4: 菜单集成与测试

#### 任务 4.1: 菜单集成（2 小时）

**步骤**:
1. 修改 `main_menu.py`：
   - 添加统计菜单
   - 首次运行检测和导入流程
2. 修改 `_show_statistics()` 方法
3. 添加数据完整性检查入口

#### 任务 4.2: 综合测试（2 小时）

**测试清单**:
- [ ] 首次运行自动导入
- [ ] 统计菜单显示正确
- [ ] 作者排行榜准确
- [ ] 新归档帖子自动同步
- [ ] 取消关注作者同步删除
- [ ] 数据完整性检查工作
- [ ] 查询性能 < 1 秒

#### 任务 4.3: 文档更新（1 小时）

**步骤**:
1. 更新 `README.md`
2. 更新 `MIGRATION_PROGRESS.md`
3. 创建 `PHASE3_COMPLETION_REPORT.md`
4. 更新 `FEATURES_DESIGN_OVERVIEW.md`

---

## 8. 测试策略

### 8.1 单元测试

**测试文件**: `tests/test_database.py`

**测试覆盖**:
```python
# 测试 connection.py
def test_database_initialization()
def test_singleton_pattern()

# 测试 models.py
def test_author_crud()
def test_post_crud()
def test_media_crud()
def test_foreign_key_constraints()
def test_triggers()

# 测试 query.py
def test_global_stats()
def test_author_ranking()
def test_monthly_stats()

# 测试 migrate.py
def test_metadata_extraction()
def test_import_author_data()
def test_batch_import()

# 测试 sync.py
def test_sync_archived_post()
def test_sync_delete_author()

# 测试 integrity.py
def test_check_all()
def test_fix_statistics()
```

### 8.2 集成测试

**场景 1: 全量导入**
```
1. 准备测试数据（3 个作者，10 篇帖子）
2. 运行 import_all_data()
3. 验证数据库记录数
4. 验证统计字段准确性
5. 验证查询结果正确
```

**场景 2: 增量同步**
```
1. 导入初始数据
2. 使用 archiver 归档新帖
3. 验证数据库自动更新
4. 验证统计字段自动更新
```

**场景 3: 数据一致性**
```
1. 导入数据
2. 手动删除一个文件
3. 运行完整性检查
4. 验证检测到缺失文件
```

### 8.3 性能测试

**测试指标**:

| 操作 | 数据量 | 目标时间 | 测试结果 |
|------|--------|---------|---------|
| 全量导入 | 350 篇帖子 | < 15 秒 | ⏳ 待测 |
| 查询全局统计 | 全部数据 | < 1 秒 | ⏳ 待测 |
| 查询作者排行 | 全部数据 | < 1 秒 | ⏳ 待测 |
| 同步单篇帖子 | 1 篇帖子 | < 0.1 秒 | ⏳ 待测 |
| 完整性检查 | 350 篇帖子 | < 10 秒 | ⏳ 待测 |

**测试工具**:
```python
import time

start = time.time()
import_all_data(archive_path, config)
duration = time.time() - start
print(f"导入耗时: {duration:.2f} 秒")
```

### 8.4 用户验收测试

**测试场景**:

1. **首次使用**
   - [ ] 提示导入历史数据
   - [ ] 进度条显示正常
   - [ ] 导入结果准确

2. **查看统计**
   - [ ] 全局统计正确
   - [ ] 作者排行榜正确
   - [ ] 详细统计页面正确

3. **新归档同步**
   - [ ] 归档新帖后统计自动更新
   - [ ] 数据库记录正确

4. **数据维护**
   - [ ] 完整性检查工作
   - [ ] 修复功能工作

---

## 9. 风险评估

### 9.1 技术风险

#### 风险 1: 导入性能不达标

**描述**: 大量数据导入超过 15 秒

**可能性**: 中等

**影响**: 中等（用户体验差，但不影响功能）

**缓解措施**:
- 使用批量插入
- 禁用触发器和外键
- 使用事务
- 并行处理作者

**应急方案**:
- 提供后台导入选项
- 分批导入（每次导入一个作者）

---

#### 风险 2: 元数据提取失败

**描述**: 无法从 content.html 提取发布时间等元数据

**可能性**: 高（不同时期的归档格式可能不同）

**影响**: 中等（部分统计功能受限）

**缓解措施**:
- 提供多种解析策略（尝试多种选择器）
- 使用文件修改时间作为后备
- 允许部分数据缺失

**应急方案**:
- 提供手动补充元数据的工具

---

#### 风险 3: 数据一致性问题

**描述**: 数据库与文件系统不同步

**可能性**: 中等

**影响**: 高（统计不准确）

**缓解措施**:
- 提供完整性检查工具
- 提供自动修复功能
- 定期运行一致性检查

**应急方案**:
- 提供重新导入功能（force_rebuild）

---

### 9.2 项目风险

#### 风险 4: 时间超支

**描述**: 实施超过预计的 3-4 天

**可能性**: 中等

**影响**: 低（不影响核心功能）

**缓解措施**:
- 优先实现核心功能（P0）
- 推迟次要功能（P1, P2）
- 分阶段交付

**优先级划分**:
- P0: schema.sql, models.py, migrate.py, query.py（核心）
- P1: sync.py, integrity.py（重要）
- P2: 菜单美化、导出 CSV（可延后）

---

#### 风险 5: 与现有代码冲突

**描述**: 数据库模块与现有代码集成困难

**可能性**: 低

**影响**: 中等

**缓解措施**:
- 最小侵入设计
- 向后兼容（支持无数据库运行）
- 充分测试集成点

**应急方案**:
- 提供配置开关（experimental.enable_database）
- 支持回退到无数据库模式

---

## 10. 验收标准

### 10.1 功能验收

**P0 必须满足**:

- [ ] **数据库创建成功**
  - schema.sql 执行无错误
  - 所有表、索引、视图、触发器创建成功

- [ ] **历史数据导入成功**
  - 所有作者导入数据库
  - 所有帖子导入数据库（>90%）
  - 所有媒体文件导入数据库（>90%）

- [ ] **统计功能正常**
  - 全局统计数字准确
  - 作者排行榜正确
  - 详细统计页面正确

- [ ] **数据同步正常**
  - 新归档帖子自动写入数据库
  - 取消关注作者自动删除记录

- [ ] **菜单集成完成**
  - [6] 查看统计菜单可用
  - 首次运行提示导入
  - 用户界面友好

**P1 强烈建议**:

- [ ] **数据完整性检查**
  - 检测缺失记录
  - 检测统计不一致
  - 提供修复功能

- [ ] **性能达标**
  - 导入 350 篇帖子 < 20 秒
  - 查询统计 < 2 秒

- [ ] **错误处理健壮**
  - 导入失败不影响系统
  - 同步失败记录日志
  - 提供回滚机制

**P2 可选**:

- [ ] 导出统计报告（CSV）
- [ ] 后台导入模式
- [ ] 数据备份功能

---

### 10.2 质量验收

**代码质量**:
- [ ] 所有函数有 docstring
- [ ] 关键逻辑有注释
- [ ] 命名清晰一致
- [ ] 无明显代码重复

**测试覆盖**:
- [ ] 单元测试覆盖核心函数
- [ ] 集成测试覆盖主要场景
- [ ] 性能测试通过

**文档完整**:
- [ ] 本设计文档完整
- [ ] 代码注释充分
- [ ] 用户文档更新（README）
- [ ] 完成报告编写

---

### 10.3 用户验收

**用户测试清单**:

1. **首次使用流程**
   - [ ] 启动系统提示导入
   - [ ] 导入进度清晰
   - [ ] 导入结果准确

2. **统计查看**
   - [ ] 全局统计易于理解
   - [ ] 排行榜信息完整
   - [ ] 详细统计有价值

3. **日常使用**
   - [ ] 归档新帖统计自动更新
   - [ ] 查询响应快速
   - [ ] 无明显错误

4. **数据维护**
   - [ ] 完整性检查易于使用
   - [ ] 修复功能可靠

---

## 11. 附录

### 11.1 参考文档

- [ADR-002: Python 迁移方案](./ADR-002_Python_Migration_Plan.md) - 第 5.3 节
- [SQLite 官方文档](https://www.sqlite.org/docs.html)
- [Python sqlite3 模块](https://docs.python.org/3/library/sqlite3.html)

### 11.2 SQL 速查

**常用查询**:

```sql
-- 查询全局统计
SELECT
    COUNT(DISTINCT author_id) as author_count,
    COUNT(*) as post_count,
    SUM(image_count) as image_count,
    SUM(video_count) as video_count
FROM posts;

-- 查询作者排行（按帖子数）
SELECT a.name, COUNT(p.id) as post_count
FROM authors a
LEFT JOIN posts p ON a.id = p.author_id
GROUP BY a.id
ORDER BY post_count DESC;

-- 查询月度统计
SELECT
    publish_year,
    publish_month,
    COUNT(*) as post_count
FROM posts
GROUP BY publish_year, publish_month
ORDER BY publish_year DESC, publish_month DESC;

-- 查询孤立记录
SELECT * FROM posts WHERE author_id NOT IN (SELECT id FROM authors);
SELECT * FROM media WHERE post_id NOT IN (SELECT id FROM posts);
```

### 11.3 配置变更

**config.yaml 新增配置项**:

```yaml
# Phase 3 新增
database:
  enabled: true                           # 是否启用数据库
  path: ./python/data/forum_data.db       # 数据库路径
  auto_sync: true                         # 归档时自动同步
  auto_import_on_first_run: true          # 首次运行自动导入

statistics:
  enabled: true                           # 是否启用统计功能
  cache_duration_seconds: 300             # 统计缓存时长（5分钟）
```

---

## 📊 实施检查清单

### Day 1: 数据库设计与基础模块
- [ ] schema.sql 编写完成
- [ ] connection.py 实现完成
- [ ] models.py 基础版实现
- [ ] 单元测试通过

### Day 2: 数据迁移工具
- [ ] extract_post_metadata() 实现
- [ ] import_all_data() 实现
- [ ] 导入测试通过（测试数据）
- [ ] 性能优化完成

### Day 3: 查询与同步
- [ ] query.py 统计函数实现
- [ ] sync.py 同步逻辑实现
- [ ] archiver.py 集成同步
- [ ] main_menu.py 集成同步

### Day 4: 菜单集成与测试
- [ ] 统计菜单实现
- [ ] 首次运行流程实现
- [ ] 完整性检查实现
- [ ] 综合测试通过
- [ ] 文档更新完成

---

**Phase 3 设计完成！准备开始实施时请告知。**

---

**文档版本**: v1.0
**创建日期**: 2026-02-13
**状态**: ✅ 设计完成，待用户批准
