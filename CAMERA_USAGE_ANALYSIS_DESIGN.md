# 相机使用分析功能设计文档

**需求**: 统计相机型号被哪些作者使用，在哪个日期的帖子中使用
**功能类型**: 数据分析增强（Phase 4 扩展）
**优先级**: P2（增强功能）
**创建日期**: 2026-02-16

---

## 📋 需求分析

### 用户需求

用户希望了解：
1. **某个相机型号** → 被哪些作者使用
2. **某个相机型号** → 在哪些日期的帖子中使用
3. **某个作者** → 使用了哪些相机型号（反向查询）
4. **整体概览** → 相机型号的使用分布

### 使用场景

1. **摄影爱好者**：想知道某款相机的实际使用情况
2. **内容分析**：了解作者的器材偏好和更新情况
3. **趋势分析**：某款相机的流行程度随时间的变化
4. **设备研究**：对比不同作者使用的相机型号

---

## 🗄️ 数据库现状

### 现有表结构

#### 1. media 表（包含 EXIF 数据）

```sql
CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,           -- 关联帖子
    type TEXT NOT NULL,                 -- 'image' 或 'video'
    url TEXT NOT NULL,
    file_name TEXT,
    file_path TEXT,

    -- EXIF 数据（Phase 4 已实现）
    exif_make TEXT,                     -- 相机制造商（如 vivo, Canon）
    exif_model TEXT,                    -- 相机型号（如 X Fold3 Pro）
    exif_datetime TEXT,                 -- 拍摄时间
    exif_iso INTEGER,                   -- ISO 感光度
    exif_aperture REAL,                 -- 光圈值
    exif_shutter_speed TEXT,            -- 快门速度
    exif_focal_length REAL,             -- 焦距
    exif_gps_lat REAL,                  -- GPS 纬度
    exif_gps_lng REAL,                  -- GPS 经度
    exif_location TEXT,                 -- 地理位置

    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);
```

#### 2. posts 表（关联帖子信息）

```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    author_id INTEGER NOT NULL,         -- 关联作者
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    publish_date TEXT,                  -- 发布日期（YYYY-MM-DD HH:MM:SS）
    publish_year INTEGER,               -- 冗余字段：年份
    publish_month INTEGER,              -- 冗余字段：月份
    file_path TEXT NOT NULL,            -- 归档路径
    archived_date TEXT NOT NULL,        -- 归档日期

    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
);
```

#### 3. authors 表（作者信息）

```sql
CREATE TABLE authors (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    total_posts INTEGER DEFAULT 0,      -- 触发器自动维护
    total_images INTEGER DEFAULT 0,     -- 触发器自动维护
    ...
);
```

### 现有索引

```sql
-- 相机查询优化索引（已存在）
CREATE INDEX idx_media_exif_make ON media(exif_make);
CREATE INDEX idx_media_exif_model ON media(exif_model);
CREATE INDEX idx_media_type_camera ON media(type, exif_make, exif_model);

-- 时间查询优化索引（已存在）
CREATE INDEX idx_media_exif_datetime ON media(exif_datetime);
```

### 现有视图

#### v_camera_stats（已存在，但不够用）

```sql
CREATE VIEW v_camera_stats AS
SELECT
    exif_make as make,
    exif_model as model,
    COUNT(*) as photo_count,
    COUNT(DISTINCT post_id) as post_count,
    MIN(exif_datetime) as first_use,
    MAX(exif_datetime) as last_use,
    ROUND(AVG(exif_iso), 0) as avg_iso,
    ROUND(AVG(exif_aperture), 1) as avg_aperture,
    ROUND(AVG(exif_focal_length), 0) as avg_focal_length
FROM media
WHERE type = 'image'
  AND exif_make IS NOT NULL
  AND exif_model IS NOT NULL
GROUP BY exif_make, exif_model
ORDER BY photo_count DESC;
```

**问题**：缺少作者信息和帖子日期信息

---

## 🎯 解决方案设计

### 方案 A：创建新视图（推荐）

#### 优点
- ✅ 查询性能好（预聚合）
- ✅ 代码简洁（直接 SELECT）
- ✅ 易于维护
- ✅ 支持复杂统计

#### 缺点
- ⚠️ 灵活性较低（需要预定义统计维度）
- ⚠️ 视图数量可能增多

#### 实施方案

##### 视图 1: v_camera_author_usage（相机 → 作者）

```sql
CREATE VIEW IF NOT EXISTS v_camera_author_usage AS
SELECT
    -- 相机信息
    m.exif_make as make,
    m.exif_model as model,
    m.exif_make || ' ' || m.exif_model as camera_full,

    -- 作者信息
    a.id as author_id,
    a.name as author_name,

    -- 使用统计
    COUNT(DISTINCT m.id) as photo_count,
    COUNT(DISTINCT p.id) as post_count,

    -- 时间范围
    MIN(p.publish_date) as first_use_date,
    MAX(p.publish_date) as last_use_date,

    -- EXIF 统计
    ROUND(AVG(m.exif_iso), 0) as avg_iso,
    ROUND(AVG(m.exif_aperture), 1) as avg_aperture,
    ROUND(AVG(m.exif_focal_length), 0) as avg_focal_length

FROM media m
JOIN posts p ON m.post_id = p.id
JOIN authors a ON p.author_id = a.id
WHERE m.type = 'image'
  AND m.exif_make IS NOT NULL
  AND m.exif_model IS NOT NULL
GROUP BY m.exif_make, m.exif_model, a.id
ORDER BY camera_full, photo_count DESC;
```

**查询示例**：
```sql
-- 查询 vivo X Fold3 Pro 被哪些作者使用
SELECT * FROM v_camera_author_usage
WHERE make = 'vivo' AND model = 'X Fold3 Pro';

-- 查询某作者使用的所有相机
SELECT * FROM v_camera_author_usage
WHERE author_name = '同花顺心'
ORDER BY photo_count DESC;
```

##### 视图 2: v_camera_daily_usage（相机 → 日期）

```sql
CREATE VIEW IF NOT EXISTS v_camera_daily_usage AS
SELECT
    -- 相机信息
    m.exif_make as make,
    m.exif_model as model,
    m.exif_make || ' ' || m.exif_model as camera_full,

    -- 日期信息
    DATE(p.publish_date) as date,
    p.publish_year as year,
    p.publish_month as month,

    -- 使用统计
    COUNT(DISTINCT m.id) as photo_count,
    COUNT(DISTINCT p.id) as post_count,

    -- 作者列表（去重）
    GROUP_CONCAT(DISTINCT a.name) as authors

FROM media m
JOIN posts p ON m.post_id = p.id
JOIN authors a ON p.author_id = a.id
WHERE m.type = 'image'
  AND m.exif_make IS NOT NULL
  AND m.exif_model IS NOT NULL
GROUP BY m.exif_make, m.exif_model, DATE(p.publish_date)
ORDER BY camera_full, date DESC;
```

**查询示例**：
```sql
-- 查询 vivo X Fold3 Pro 的使用时间线
SELECT date, photo_count, post_count, authors
FROM v_camera_daily_usage
WHERE make = 'vivo' AND model = 'X Fold3 Pro'
ORDER BY date DESC;

-- 查询某月所有相机使用情况
SELECT camera_full, SUM(photo_count) as total_photos
FROM v_camera_daily_usage
WHERE year = 2024 AND month = 12
GROUP BY camera_full
ORDER BY total_photos DESC;
```

##### 视图 3: v_author_camera_summary（作者 → 相机汇总）

```sql
CREATE VIEW IF NOT EXISTS v_author_camera_summary AS
SELECT
    -- 作者信息
    a.id as author_id,
    a.name as author_name,

    -- 相机统计
    COUNT(DISTINCT m.exif_make || '-' || m.exif_model) as camera_count,
    GROUP_CONCAT(DISTINCT m.exif_make || ' ' || m.exif_model) as camera_list,

    -- 最常用相机
    (
        SELECT m2.exif_make || ' ' || m2.exif_model
        FROM media m2
        JOIN posts p2 ON m2.post_id = p2.id
        WHERE p2.author_id = a.id
          AND m2.type = 'image'
          AND m2.exif_make IS NOT NULL
        GROUP BY m2.exif_make, m2.exif_model
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ) as most_used_camera,

    -- 总照片数
    COUNT(DISTINCT m.id) as total_photos,
    COUNT(DISTINCT p.id) as total_posts_with_exif

FROM authors a
LEFT JOIN posts p ON a.id = p.author_id
LEFT JOIN media m ON p.id = m.post_id AND m.type = 'image'
WHERE m.exif_make IS NOT NULL
GROUP BY a.id
ORDER BY total_photos DESC;
```

---

### 方案 B：扩展查询函数（灵活性高）

在 `python/src/database/query.py` 中添加新函数。

#### 优点
- ✅ 灵活性高（可动态过滤）
- ✅ 支持复杂参数组合
- ✅ 代码可读性好

#### 缺点
- ⚠️ 每次查询都执行 JOIN（性能略低）
- ⚠️ 代码量较大

#### 实施方案

##### 函数 1: get_camera_usage_by_authors()

```python
def get_camera_usage_by_authors(
    camera_make: Optional[str] = None,
    camera_model: Optional[str] = None,
    author_name: Optional[str] = None,
    limit: int = 50,
    db: Optional[DatabaseConnection] = None
) -> List[Dict]:
    """
    查询相机被哪些作者使用

    Args:
        camera_make: 相机制造商（如 'vivo'），None 表示全部
        camera_model: 相机型号（如 'X Fold3 Pro'），None 表示全部
        author_name: 作者名称（用于反向查询），None 表示全部
        limit: 返回结果数量限制
        db: 数据库连接

    Returns:
        [
            {
                'camera_full': 'vivo X Fold3 Pro',
                'make': 'vivo',
                'model': 'X Fold3 Pro',
                'author_name': '同花顺心',
                'photo_count': 150,
                'post_count': 10,
                'first_use_date': '2024-01-15',
                'last_use_date': '2024-12-20',
                'avg_iso': 400,
                'avg_aperture': 2.2,
                'avg_focal_length': 50
            },
            ...
        ]
    """
    if db is None:
        db = _get_db()

    conn = db.get_connection()

    # 构建动态 WHERE 条件
    conditions = ["m.type = 'image'", "m.exif_make IS NOT NULL", "m.exif_model IS NOT NULL"]
    params = []

    if camera_make:
        conditions.append("m.exif_make = ?")
        params.append(camera_make)

    if camera_model:
        conditions.append("m.exif_model = ?")
        params.append(camera_model)

    if author_name:
        conditions.append("a.name = ?")
        params.append(author_name)

    where_clause = " AND ".join(conditions)

    # 执行查询
    cursor = conn.execute(f"""
        SELECT
            m.exif_make || ' ' || m.exif_model as camera_full,
            m.exif_make as make,
            m.exif_model as model,
            a.name as author_name,
            COUNT(DISTINCT m.id) as photo_count,
            COUNT(DISTINCT p.id) as post_count,
            MIN(p.publish_date) as first_use_date,
            MAX(p.publish_date) as last_use_date,
            ROUND(AVG(m.exif_iso), 0) as avg_iso,
            ROUND(AVG(m.exif_aperture), 1) as avg_aperture,
            ROUND(AVG(m.exif_focal_length), 0) as avg_focal_length
        FROM media m
        JOIN posts p ON m.post_id = p.id
        JOIN authors a ON p.author_id = a.id
        WHERE {where_clause}
        GROUP BY m.exif_make, m.exif_model, a.id
        ORDER BY camera_full, photo_count DESC
        LIMIT ?
    """, params + [limit])

    return [dict(row) for row in cursor.fetchall()]
```

##### 函数 2: get_camera_usage_timeline()

```python
def get_camera_usage_timeline(
    camera_make: str,
    camera_model: str,
    author_name: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Optional[DatabaseConnection] = None
) -> List[Dict]:
    """
    查询相机使用的时间线（按日期聚合）

    Args:
        camera_make: 相机制造商（必填）
        camera_model: 相机型号（必填）
        author_name: 作者名称（可选，用于过滤）
        year: 年份过滤（可选）
        month: 月份过滤（可选）
        db: 数据库连接

    Returns:
        [
            {
                'date': '2024-12-20',
                'year': 2024,
                'month': 12,
                'photo_count': 15,
                'post_count': 1,
                'authors': '同花顺心'
            },
            ...
        ]
    """
    if db is None:
        db = _get_db()

    conn = db.get_connection()

    # 构建动态 WHERE 条件
    conditions = [
        "m.type = 'image'",
        "m.exif_make = ?",
        "m.exif_model = ?"
    ]
    params = [camera_make, camera_model]

    if author_name:
        conditions.append("a.name = ?")
        params.append(author_name)

    if year:
        conditions.append("p.publish_year = ?")
        params.append(year)

    if month:
        conditions.append("p.publish_month = ?")
        params.append(month)

    where_clause = " AND ".join(conditions)

    # 执行查询
    cursor = conn.execute(f"""
        SELECT
            DATE(p.publish_date) as date,
            p.publish_year as year,
            p.publish_month as month,
            COUNT(DISTINCT m.id) as photo_count,
            COUNT(DISTINCT p.id) as post_count,
            GROUP_CONCAT(DISTINCT a.name) as authors
        FROM media m
        JOIN posts p ON m.post_id = p.id
        JOIN authors a ON p.author_id = a.id
        WHERE {where_clause}
        GROUP BY DATE(p.publish_date)
        ORDER BY date DESC
    """, params)

    return [dict(row) for row in cursor.fetchall()]
```

##### 函数 3: get_author_camera_usage()

```python
def get_author_camera_usage(
    author_name: str,
    db: Optional[DatabaseConnection] = None
) -> Dict:
    """
    查询作者使用的所有相机型号

    Args:
        author_name: 作者名称
        db: 数据库连接

    Returns:
        {
            'author_name': '同花顺心',
            'total_cameras': 3,
            'total_photos': 450,
            'cameras': [
                {
                    'camera_full': 'vivo X Fold3 Pro',
                    'make': 'vivo',
                    'model': 'X Fold3 Pro',
                    'photo_count': 300,
                    'post_count': 20,
                    'first_use': '2024-01-15',
                    'last_use': '2024-12-20',
                    'usage_percent': 66.7
                },
                ...
            ]
        }
    """
    if db is None:
        db = _get_db()

    conn = db.get_connection()

    # 查询作者的所有相机使用情况
    cursor = conn.execute("""
        SELECT
            m.exif_make || ' ' || m.exif_model as camera_full,
            m.exif_make as make,
            m.exif_model as model,
            COUNT(DISTINCT m.id) as photo_count,
            COUNT(DISTINCT p.id) as post_count,
            MIN(p.publish_date) as first_use,
            MAX(p.publish_date) as last_use
        FROM media m
        JOIN posts p ON m.post_id = p.id
        JOIN authors a ON p.author_id = a.id
        WHERE a.name = ?
          AND m.type = 'image'
          AND m.exif_make IS NOT NULL
          AND m.exif_model IS NOT NULL
        GROUP BY m.exif_make, m.exif_model
        ORDER BY photo_count DESC
    """, (author_name,))

    cameras = []
    total_photos = 0

    for row in cursor.fetchall():
        row_dict = dict(row)
        cameras.append(row_dict)
        total_photos += row_dict['photo_count']

    # 计算使用百分比
    for camera in cameras:
        camera['usage_percent'] = round(camera['photo_count'] / total_photos * 100, 1) if total_photos > 0 else 0

    return {
        'author_name': author_name,
        'total_cameras': len(cameras),
        'total_photos': total_photos,
        'cameras': cameras
    }
```

---

### 方案 C：创建专门的分析类（高级）

创建 `python/src/analysis/camera_usage_analyzer.py`。

#### 优点
- ✅ 封装性好
- ✅ 支持复杂分析逻辑
- ✅ 易于扩展

#### 缺点
- ⚠️ 代码量最大
- ⚠️ 需要额外的类设计

#### 实施方案

```python
class CameraUsageAnalyzer:
    """相机使用分析器"""

    def __init__(self, db_connection=None):
        self.db = db_connection or get_default_connection()

    def analyze_camera_by_author(
        self,
        camera_make: str,
        camera_model: str
    ) -> Dict:
        """分析指定相机被哪些作者使用"""
        ...

    def analyze_camera_timeline(
        self,
        camera_make: str,
        camera_model: str
    ) -> pd.DataFrame:
        """分析相机使用时间线（支持可视化）"""
        ...

    def analyze_author_cameras(
        self,
        author_name: str
    ) -> Dict:
        """分析作者使用的所有相机"""
        ...

    def generate_usage_report(
        self,
        output_format: str = 'markdown'
    ) -> str:
        """生成完整的相机使用报告"""
        ...
```

---

## 🎨 用户界面设计

### 统计菜单新增选项

```
📊 查看统计（Phase 3 后可用）
  1. 全局统计
  2. 作者排行榜
  3. 月度发帖趋势
  4. 时间分布分析
  5. 相机使用分析  ← 新增
  6. 数据完整性检查
  0. 返回主菜单
```

### 相机使用分析子菜单

```
📷 相机使用分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 查看所有相机型号排行
  2. 查询相机被哪些作者使用
  3. 查询作者使用了哪些相机
  4. 查看相机使用时间线
  5. 生成相机使用报告
  0. 返回上级菜单
```

### 显示效果示例

#### 示例 1: 相机型号排行

```
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ 相机型号          ┃ 照片数 ┃ 帖子数 ┃ 作者数   ┃ 首次使用 ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ vivo X Fold3 Pro  │  450  │   30  │    3    │2024-01-15│
│ Canon EOS 5D      │  320  │   25  │    2    │2024-02-10│
│ iPhone 15 Pro     │  280  │   18  │    4    │2024-03-01│
└───────────────────┴───────┴───────┴─────────┴──────────┘
```

#### 示例 2: 相机 → 作者使用

```
相机型号: vivo X Fold3 Pro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ 作者     ┃ 照片数 ┃ 帖子数 ┃ 首次使用 ┃ 最后使用 ┃
┡━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 同花顺心  │  300  │   20  │2024-01-15│2024-12-20│
│ cyruscc  │  100  │    8  │2024-03-10│2024-11-30│
│ 其他作者  │   50  │    2  │2024-06-01│2024-09-15│
└──────────┴───────┴───────┴──────────┴──────────┘

EXIF 参数统计：
  平均 ISO: 400
  平均光圈: f/2.2
  平均焦距: 50mm
```

#### 示例 3: 作者 → 相机使用

```
作者: 同花顺心
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

使用了 3 种相机型号，共 450 张照片

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ 相机型号          ┃ 照片数 ┃ 占比   ┃ 使用期间 ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ vivo X Fold3 Pro  │  300  │ 66.7% │2024-01至今│
│ Canon EOS 5D      │  100  │ 22.2% │2024-03-06│
│ iPhone 14 Pro     │   50  │ 11.1% │2023-12-01│
└───────────────────┴───────┴────────┴──────────┘
```

#### 示例 4: 相机使用时间线

```
相机型号: vivo X Fold3 Pro
时间线: 2024-01-01 至 2024-12-31
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2024-12 ████████████████ 60 张 (同花顺心)
2024-11 ████████████     45 张 (同花顺心, cyruscc)
2024-10 ████████         30 张 (cyruscc)
2024-09 ████             15 张 (其他作者)
2024-08 ██               10 张 (同花顺心)
...

总计: 450 张照片，30 篇帖子，3 位作者
```

---

## 🔧 实施建议

### 推荐方案：**方案 A（视图）+ 方案 B（查询函数）混合**

#### 阶段 1：创建视图（必需）
1. `v_camera_author_usage` - 相机与作者关联
2. `v_camera_daily_usage` - 相机与日期关联
3. `v_author_camera_summary` - 作者相机汇总

#### 阶段 2：添加查询函数（必需）
1. `get_camera_usage_by_authors()` - 灵活查询
2. `get_camera_usage_timeline()` - 时间线查询
3. `get_author_camera_usage()` - 作者相机详情

#### 阶段 3：创建菜单界面（必需）
1. 在 `main_menu.py` 的统计菜单添加入口
2. 创建 `camera_usage_menu.py`（可选独立文件）
3. 使用 Rich Table 美化显示

#### 阶段 4：可视化（可选）
1. 使用 matplotlib 绘制时间线图表
2. 使用 matplotlib 绘制作者相机使用饼图
3. 生成 HTML 报告

---

## 📊 性能考虑

### 查询性能评估

#### 测试场景
- 数据量：1,000 张图片，50 篇帖子，5 位作者

#### 预期性能
| 查询类型 | 预估耗时 | 优化措施 |
|----------|----------|----------|
| 相机排行（视图） | <50ms | 已有索引 |
| 相机 → 作者（3-表 JOIN） | <100ms | 复合索引 |
| 相机时间线 | <100ms | 日期索引 |
| 作者 → 相机 | <80ms | 已有外键索引 |

### 优化建议

#### 1. 确保索引完整
```sql
-- 检查现有索引
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='media';

-- 如需补充复合索引
CREATE INDEX IF NOT EXISTS idx_media_post_type_camera
ON media(post_id, type, exif_make, exif_model);
```

#### 2. 视图物化（如果查询慢）
```python
# 定期更新缓存表
def materialize_camera_usage():
    conn.execute("DROP TABLE IF EXISTS cache_camera_usage")
    conn.execute("""
        CREATE TABLE cache_camera_usage AS
        SELECT * FROM v_camera_author_usage
    """)
```

#### 3. 结果缓存
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_camera_usage_by_authors_cached(...):
    ...
```

---

## 🧪 测试计划

### 单元测试

```python
# test_camera_usage_queries.py

def test_get_camera_usage_by_authors():
    """测试相机作者查询"""
    result = get_camera_usage_by_authors(
        camera_make='vivo',
        camera_model='X Fold3 Pro'
    )
    assert len(result) > 0
    assert result[0]['author_name'] is not None

def test_get_camera_usage_timeline():
    """测试时间线查询"""
    result = get_camera_usage_timeline(
        camera_make='vivo',
        camera_model='X Fold3 Pro'
    )
    assert len(result) > 0
    assert 'date' in result[0]

def test_get_author_camera_usage():
    """测试作者相机查询"""
    result = get_author_camera_usage('同花顺心')
    assert result['total_cameras'] > 0
    assert len(result['cameras']) > 0
```

### 集成测试

```python
def test_camera_usage_menu_flow():
    """测试菜单流程"""
    # 1. 显示相机排行
    # 2. 选择相机查看作者
    # 3. 返回上级菜单
    ...
```

---

## 📝 文档更新

### 需要更新的文档

1. **用户指南**
   - 添加相机使用分析章节
   - 示例查询和截图

2. **数据库文档**
   - 新增视图说明
   - 查询性能指标

3. **API 文档**
   - 新增查询函数签名
   - 参数说明和返回值

---

## 🎯 验收标准

### 功能验收
- ✅ 能查询相机被哪些作者使用
- ✅ 能查询作者使用了哪些相机
- ✅ 能查看相机使用时间线
- ✅ 显示准确的统计数据

### 性能验收
- ✅ 查询响应时间 < 200ms
- ✅ 支持 1000+ 照片数据集

### 用户体验验收
- ✅ 菜单交互流畅
- ✅ 表格显示美观
- ✅ 数据易于理解

---

## 📅 实施时间线

### 阶段 1：数据库（1 小时）
- 创建 3 个新视图
- 测试视图查询

### 阶段 2：查询函数（2 小时）
- 实现 3 个查询函数
- 编写单元测试

### 阶段 3：菜单界面（2 小时）
- 创建相机使用菜单
- Rich Table 显示

### 阶段 4：测试与文档（1 小时）
- 集成测试
- 更新文档

**总计**: 6 小时

---

## 🔗 相关文件

### 需要修改的文件
- `python/src/database/schema_v2.sql` - 添加视图
- `python/src/database/query.py` - 添加查询函数
- `python/src/menu/main_menu.py` - 添加菜单入口

### 需要创建的文件
- `python/src/menu/camera_usage_menu.py` - 相机使用菜单（可选）
- `test_camera_usage.py` - 测试文件

---

**设计完成日期**: 2026-02-16
**设计者**: Claude Sonnet 4.5
**状态**: 📋 **设计完成，待用户审核**
