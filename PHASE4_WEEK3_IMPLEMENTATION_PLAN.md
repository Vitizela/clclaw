# Phase 4 Week 3 实施计划：相机使用分析

## 执行摘要

**目标**: 实现相机使用分析功能，统计相机型号被哪些作者使用，在哪些日期的帖子中使用

**工期**: 3 天（Day 11-13）核心功能 + 1 天（Day 14）测试

**优先级**: P1（必做）

**前置依赖**: ✅ Phase 4 Week 1 完成（EXIF 提取功能已实现）

**核心产出**:
- 3 个数据库视图
- 3 个查询函数
- 相机使用分析菜单
- Rich Table 格式化显示

**关键特性**:
- ✅ 数据已具备（Week 1 EXIF 提取完成）
- ✅ 索引已优化（idx_media_exif_make/model）
- ✅ 性能预估良好（<200ms）

---

## 1. 背景与需求

### 1.1 用户需求（2026-02-16）

用户希望了解：
1. **某个相机型号** → 被哪些作者使用
2. **某个相机型号** → 在哪些日期的帖子中使用
3. **某个作者** → 使用了哪些相机型号
4. **整体概览** → 相机型号的使用排行

### 1.2 使用场景

- **摄影爱好者**: 了解某款相机的实际使用情况
- **内容分析**: 研究作者的器材偏好和更新情况
- **趋势分析**: 观察相机流行程度随时间的变化
- **设备研究**: 对比不同作者使用的相机型号

### 1.3 数据基础

**已有数据**（Week 1 完成）:
- `media` 表包含 10 个 EXIF 字段
- `exif_make`: 相机制造商（如 vivo, Canon）
- `exif_model`: 相机型号（如 X Fold3 Pro）
- `exif_datetime`: 拍摄时间
- 其他 EXIF 参数（ISO, 光圈, 快门, 焦距等）

**已有索引**:
```sql
CREATE INDEX idx_media_exif_make ON media(exif_make);
CREATE INDEX idx_media_exif_model ON media(exif_model);
CREATE INDEX idx_media_type_camera ON media(type, exif_make, exif_model);
```

**三表关联**:
```
media (exif_make, exif_model, post_id)
  → posts (author_id, publish_date)
    → authors (name)
```

---

## 2. 核心功能设计

### 2.1 功能清单

| 功能 | 描述 | 优先级 |
|------|------|--------|
| **相机型号排行** | 显示所有相机的使用统计 | P0 |
| **相机→作者查询** | 查询指定相机被哪些作者使用 | P0 |
| **作者→相机查询** | 查询指定作者使用了哪些相机 | P0 |
| **相机使用时间线** | 查询相机在不同日期的使用情况 | P1 |

### 2.2 显示效果

#### 示例 1: 相机 → 作者使用

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

#### 示例 2: 作者 → 相机使用

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

#### 示例 3: 相机使用时间线

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

## 3. 数据库设计

### 3.1 新增视图（3 个）

#### 视图 1: v_camera_author_usage（相机→作者关联）

**用途**: 查询相机被哪些作者使用

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

**查询示例**:
```sql
-- 查询 vivo X Fold3 Pro 被哪些作者使用
SELECT * FROM v_camera_author_usage
WHERE make = 'vivo' AND model = 'X Fold3 Pro';

-- 查询某作者使用的所有相机
SELECT * FROM v_camera_author_usage
WHERE author_name = '同花顺心'
ORDER BY photo_count DESC;
```

#### 视图 2: v_camera_daily_usage（相机→日期关联）

**用途**: 查询相机使用的时间线

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

**查询示例**:
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

#### 视图 3: v_author_camera_summary（作者→相机汇总）

**用途**: 查询作者使用的相机统计

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

**查询示例**:
```sql
-- 查询所有作者的相机使用汇总
SELECT * FROM v_author_camera_summary;

-- 查询某作者的相机统计
SELECT * FROM v_author_camera_summary
WHERE author_name = '同花顺心';
```

---

### 3.2 查询函数（3 个）

#### 函数 1: get_camera_usage_by_authors()

**文件**: `python/src/database/query.py`

**功能**: 查询相机被哪些作者使用（支持过滤）

**函数签名**:
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
```

**实现要点**:
- 使用 `v_camera_author_usage` 视图
- 支持动态 WHERE 条件
- 支持 LIMIT 分页

#### 函数 2: get_camera_usage_timeline()

**文件**: `python/src/database/query.py`

**功能**: 查询相机使用的时间线

**函数签名**:
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
```

**实现要点**:
- 使用 `v_camera_daily_usage` 视图
- 支持年月过滤
- 按日期降序排列

#### 函数 3: get_author_camera_usage()

**文件**: `python/src/database/query.py`

**功能**: 查询作者使用的所有相机型号

**函数签名**:
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
```

**实现要点**:
- 查询 `v_camera_author_usage` 视图
- 计算使用百分比
- 按照片数降序排列

---

## 4. 菜单界面设计

### 4.1 菜单结构

**位置**: 主菜单 → 查看统计 → 相机使用分析

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

**子菜单**:
```
📷 相机使用分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 查看所有相机型号排行
  2. 查询相机被哪些作者使用
  3. 查询作者使用了哪些相机
  4. 查看相机使用时间线
  0. 返回上级菜单
```

### 4.2 交互流程

#### 流程 1: 查看相机型号排行

```
1. 用户选择"1. 查看所有相机型号排行"
2. 系统查询 v_camera_stats 视图
3. 显示 Rich Table：
   - 列：相机型号、照片数、帖子数、作者数、首次使用
   - 排序：按照片数降序
4. 提示：按 Enter 返回上级菜单
```

#### 流程 2: 查询相机→作者

```
1. 用户选择"2. 查询相机被哪些作者使用"
2. 显示相机型号列表供选择（从 v_camera_stats）
3. 用户选择相机（如 vivo X Fold3 Pro）
4. 系统调用 get_camera_usage_by_authors()
5. 显示 Rich Table：
   - 作者列表、照片数、帖子数、使用期间
   - EXIF 统计摘要
6. 提示：按 Enter 返回相机列表
```

#### 流程 3: 查询作者→相机

```
1. 用户选择"3. 查询作者使用了哪些相机"
2. 显示作者列表供选择（从 authors 表）
3. 用户选择作者（如 同花顺心）
4. 系统调用 get_author_camera_usage()
5. 显示 Rich Table：
   - 相机列表、照片数、占比、使用期间
   - 总结：X 种相机，共 Y 张照片
6. 提示：按 Enter 返回作者列表
```

#### 流程 4: 查看使用时间线

```
1. 用户选择"4. 查看相机使用时间线"
2. 显示相机型号列表供选择
3. 用户选择相机（如 vivo X Fold3 Pro）
4. 可选：输入年份过滤（如 2024）
5. 系统调用 get_camera_usage_timeline()
6. 显示简单的文本图表：
   - 按月或日聚合
   - ASCII 条形图
   - 显示作者名称
7. 提示：按 Enter 返回相机列表
```

### 4.3 Rich Table 样式

**基础配置**:
```python
from rich.table import Table
from rich.console import Console

table = Table(
    title="相机使用统计",
    show_header=True,
    header_style="bold cyan",
    border_style="blue",
    expand=False
)

table.add_column("作者", justify="left", style="green")
table.add_column("照片数", justify="right", style="yellow")
table.add_column("帖子数", justify="right", style="yellow")
table.add_column("首次使用", justify="center", style="cyan")
table.add_column("最后使用", justify="center", style="cyan")
```

---

## 5. 实施步骤

### Day 11: 数据库设计（0.75 天）

#### Task #45: 创建相机使用视图（0.5 天）

**步骤**:
1. 创建文件 `python/src/database/schema_camera_usage.sql`
2. 编写 3 个视图的 CREATE VIEW 语句
3. 添加注释说明每个视图的用途

**验收**:
```bash
# 执行 SQL
sqlite3 python/data/forum_data.db < python/src/database/schema_camera_usage.sql

# 测试查询
sqlite3 python/data/forum_data.db "SELECT * FROM v_camera_author_usage LIMIT 5;"
```

**预期输出**:
```
vivo|X Fold3 Pro|vivo X Fold3 Pro|1|同花顺心|300|20|2024-01-15|2024-12-20|400|2.2|50
```

#### Task #46: 测试视图性能（0.25 天）

**步骤**:
1. 创建测试脚本 `test_camera_views.py`
2. 测试各视图查询耗时
3. 验证数据准确性

**验收**:
```bash
python python/test_camera_views.py
```

**预期输出**:
```
✓ v_camera_author_usage: 45ms (100 行)
✓ v_camera_daily_usage: 38ms (150 行)
✓ v_author_camera_summary: 52ms (14 行)
```

---

### Day 12: 查询函数实现（1.5 天）

#### Task #47: 实现 get_camera_usage_by_authors()（0.5 天）

**步骤**:
1. 在 `python/src/database/query.py` 末尾添加函数
2. 实现动态 WHERE 条件构建
3. 编写 docstring 和类型注解

**验收**:
```python
result = get_camera_usage_by_authors(
    camera_make='vivo',
    camera_model='X Fold3 Pro'
)
assert len(result) > 0
assert result[0]['author_name'] is not None
```

#### Task #48: 实现 get_camera_usage_timeline()（0.5 天）

**步骤**:
1. 在 `python/src/database/query.py` 添加函数
2. 实现年月过滤逻辑
3. 按日期降序排列

**验收**:
```python
result = get_camera_usage_timeline(
    camera_make='vivo',
    camera_model='X Fold3 Pro',
    year=2024
)
assert len(result) > 0
assert 'date' in result[0]
```

#### Task #49: 实现 get_author_camera_usage()（0.5 天）

**步骤**:
1. 在 `python/src/database/query.py` 添加函数
2. 实现使用百分比计算
3. 按照片数降序排列

**验收**:
```python
result = get_author_camera_usage('同花顺心')
assert result['total_cameras'] > 0
assert len(result['cameras']) > 0
assert 'usage_percent' in result['cameras'][0]
```

---

### Day 13: 菜单界面实现（1 天）

#### Task #50: 创建 camera_usage_menu.py（0.5 天）

**步骤**:
1. 创建文件 `python/src/menu/camera_usage_menu.py`（可选独立文件）
2. 定义 `CameraUsageMenu` 类
3. 实现 4 个菜单选项方法

**代码框架**:
```python
class CameraUsageMenu:
    def __init__(self, config, db_connection):
        self.config = config
        self.db = db_connection
        self.console = Console()

    def show(self):
        """显示相机使用分析菜单"""
        while True:
            choice = self._show_menu()
            if choice == '1':
                self._show_camera_ranking()
            elif choice == '2':
                self._query_camera_to_authors()
            elif choice == '3':
                self._query_author_to_cameras()
            elif choice == '4':
                self._show_camera_timeline()
            elif choice == '0':
                break

    def _show_camera_ranking(self):
        """显示相机型号排行"""
        # 查询 v_camera_stats
        # Rich Table 显示

    def _query_camera_to_authors(self):
        """查询相机→作者"""
        # 1. 显示相机列表
        # 2. 用户选择相机
        # 3. 调用 get_camera_usage_by_authors()
        # 4. Rich Table 显示

    def _query_author_to_cameras(self):
        """查询作者→相机"""
        # 1. 显示作者列表
        # 2. 用户选择作者
        # 3. 调用 get_author_camera_usage()
        # 4. Rich Table 显示

    def _show_camera_timeline(self):
        """显示相机使用时间线"""
        # 1. 显示相机列表
        # 2. 用户选择相机
        # 3. 调用 get_camera_usage_timeline()
        # 4. 文本图表显示
```

**验收**:
- 菜单显示正常
- 可选择各选项
- 按 0 返回上级

#### Task #51: 实现 Rich Table 显示（0.5 天）

**步骤**:
1. 实现 `_format_camera_author_table()` 方法
2. 实现 `_format_author_camera_table()` 方法
3. 实现 `_format_camera_ranking_table()` 方法

**代码示例**:
```python
def _format_camera_author_table(self, data, camera_name):
    """格式化相机→作者表格"""
    table = Table(
        title=f"相机型号: {camera_name}",
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("作者", justify="left", style="green")
    table.add_column("照片数", justify="right", style="yellow")
    table.add_column("帖子数", justify="right", style="yellow")
    table.add_column("首次使用", justify="center")
    table.add_column("最后使用", justify="center")

    for row in data:
        table.add_row(
            row['author_name'],
            str(row['photo_count']),
            str(row['post_count']),
            row['first_use_date'][:10],
            row['last_use_date'][:10]
        )

    return table
```

#### Task #52: 集成到主菜单（0.25 天）

**步骤**:
1. 修改 `python/src/menu/main_menu.py`
2. 在 `_show_statistics()` 方法添加选项
3. 添加调用 `CameraUsageMenu` 的代码

**代码修改**:
```python
def _show_statistics(self):
    """显示统计菜单"""
    choices = [
        "1. 全局统计",
        "2. 作者排行榜",
        "3. 月度发帖趋势",
        "4. 时间分布分析",
        "5. 相机使用分析",  # ← 新增
        "6. 数据完整性检查",
        "0. 返回主菜单"
    ]

    choice = select_with_keybindings(...)

    if choice == "5. 相机使用分析":
        from .camera_usage_menu import CameraUsageMenu
        camera_menu = CameraUsageMenu(self.config, self.db)
        camera_menu.show()
```

**验收**:
- 统计菜单显示新选项
- 选择后进入相机使用菜单
- 返回后回到统计菜单

---

### Day 14: 测试与优化（0.5 天）

#### Task #53: 编写单元测试（0.25 天）

**步骤**:
1. 创建文件 `python/test_camera_usage.py`
2. 编写 3 个查询函数的测试用例
3. 运行测试并验证

**测试代码**:
```python
def test_get_camera_usage_by_authors():
    """测试相机作者查询"""
    result = get_camera_usage_by_authors(
        camera_make='vivo',
        camera_model='X Fold3 Pro'
    )
    assert len(result) > 0
    assert result[0]['author_name'] is not None
    assert result[0]['photo_count'] > 0

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

**验收**:
```bash
pytest python/test_camera_usage.py -v
```

**预期输出**:
```
test_camera_usage.py::test_get_camera_usage_by_authors PASSED
test_camera_usage.py::test_get_camera_usage_timeline PASSED
test_camera_usage.py::test_get_author_camera_usage PASSED

3 passed in 0.5s
```

#### Task #54: 集成测试（0.25 天）

**步骤**:
1. 手动测试完整菜单流程
2. 验证 Rich Table 显示效果
3. 测试边界情况（无数据、大量数据）

**测试清单**:
- [ ] 菜单显示正常
- [ ] 相机排行显示正确
- [ ] 相机→作者查询正常
- [ ] 作者→相机查询正常
- [ ] 时间线显示正确
- [ ] 无数据时提示友好
- [ ] 返回逻辑正确

---

## 6. 文件清单

### 新建文件

```
python/src/database/
├── schema_camera_usage.sql       (~150 行，3 个视图定义)

python/src/menu/
├── camera_usage_menu.py          (~400 行，相机使用菜单，可选独立)

python/
├── test_camera_usage.py          (~150 行，单元测试)
└── test_camera_views.py          (~100 行，视图性能测试)
```

### 修改文件

```
python/src/database/query.py      (+150 行，3 个查询函数)
python/src/menu/main_menu.py      (+20 行，菜单集成)
```

---

## 7. 性能预估

### 查询性能（基于 1000 张图片）

| 查询类型 | 预估耗时 | 说明 |
|----------|----------|------|
| 相机排行（视图） | <50ms | 已有索引优化 |
| 相机→作者（3表JOIN） | <100ms | 复合索引支持 |
| 作者→相机 | <80ms | 外键优化 |
| 时间线查询 | <100ms | 日期聚合 |

### 优化措施

1. **已有优化**:
   - 索引：`idx_media_exif_make`, `idx_media_exif_model`
   - 外键索引：`posts.author_id`, `media.post_id`

2. **可选优化**（如查询慢）:
   - 物化视图缓存
   - 结果缓存（`@lru_cache`）
   - 分页加载（LIMIT + OFFSET）

---

## 8. 风险与缓解

### 风险 1: 数据量过大导致查询慢

**症状**: 查询响应时间 > 1 秒

**缓解**:
1. 检查索引是否存在：`EXPLAIN QUERY PLAN`
2. 添加复合索引：`CREATE INDEX idx_post_author_date ON posts(author_id, publish_date)`
3. 使用物化视图缓存

### 风险 2: 部分照片无 EXIF 数据

**症状**: 查询结果为空或数据不完整

**缓解**:
1. 检查 EXIF 提取覆盖率：
   ```sql
   SELECT
       COUNT(*) as total,
       SUM(CASE WHEN exif_make IS NOT NULL THEN 1 ELSE 0 END) as has_exif
   FROM media WHERE type = 'image';
   ```
2. 运行历史数据迁移：`python python/src/database/migrate_exif.py`

### 风险 3: 菜单交互复杂导致用户困惑

**症状**: 用户不知道如何使用

**缓解**:
1. 添加清晰的提示文本
2. 提供示例操作流程
3. 更新用户指南文档

---

## 9. 验收标准

### 功能验收

- ✅ 能查询相机被哪些作者使用
- ✅ 能查询作者使用了哪些相机
- ✅ 能查看相机使用时间线
- ✅ 显示准确的统计数据
- ✅ Rich Table 格式美观

### 性能验收

- ✅ 查询响应时间 < 200ms
- ✅ 支持 1000+ 照片数据集
- ✅ 菜单切换无延迟

### 用户体验验收

- ✅ 菜单交互流畅
- ✅ 数据易于理解
- ✅ 错误提示友好
- ✅ 返回逻辑清晰

### 代码质量验收

- ✅ 所有函数有类型注解
- ✅ 所有函数有 docstring
- ✅ 单元测试 100% 通过
- ✅ 代码符合 PEP 8 规范

---

## 10. 文档更新

### 需要更新的文档

1. **PHASE4_FEATURE_PLAN.md** ✅ 已更新
   - 添加 F 模块：相机使用分析

2. **PHASE4_TASK_TRACKER.md** ✅ 已更新
   - Week 3 任务清单

3. **用户指南** 待更新
   - 添加相机使用分析章节
   - 示例查询和截图

4. **数据库文档** 待更新
   - 新增视图说明
   - 查询性能指标

5. **API 文档** 待更新
   - 3 个查询函数签名
   - 参数说明和返回值

---

## 11. 后续扩展（可选）

### Phase 4.5 可能的增强

1. **图表可视化**:
   - matplotlib 相机使用时间线图
   - matplotlib 作者相机使用饼图

2. **高级统计**:
   - 相机流行度趋势分析
   - 相机更新频率统计

3. **导出功能**:
   - CSV 导出
   - Excel 导出（openpyxl）

4. **报告生成**:
   - HTML 相机使用报告
   - 包含图表和详细统计

---

## 12. 总结

### 核心价值

1. **数据洞察**: 深入了解相机使用情况
2. **器材研究**: 对比不同相机的实际使用
3. **作者分析**: 了解作者的器材偏好
4. **趋势发现**: 观察相机流行度变化

### 技术亮点

1. **视图优化**: 3 个视图预聚合，查询性能好
2. **灵活查询**: 3 个函数支持动态过滤
3. **用户友好**: Rich Table 美化显示
4. **性能优秀**: 查询响应 <200ms

### 实施效率

- **总工作量**: 3.5 天（Day 11-14）
- **核心功能**: 3 天
- **测试优化**: 0.5 天
- **代码量**: ~850 行（含测试）

---

**文档版本**: v1.0
**创建日期**: 2026-02-16
**作者**: Claude Sonnet 4.5
**状态**: ✅ **设计完成，待用户审核后实施**
