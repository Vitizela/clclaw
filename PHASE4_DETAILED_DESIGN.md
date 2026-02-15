# Phase 4 详细设计文档：数据分析 + 可视化

**文档版本**: v1.0
**创建日期**: 2026-02-14
**目标受众**: AI 编程实施
**实施工期**: 3 周（15 个工作日）
**前置依赖**: Phase 3 完成 ✅

---

## 📑 目录

1. [设计总览](#1-设计总览)
2. [数据库设计](#2-数据库设计)
3. [模块详细设计](#3-模块详细设计)
4. [接口规范](#4-接口规范)
5. [配置设计](#5-配置设计)
6. [测试设计](#6-测试设计)
7. [实施任务清单](#7-实施任务清单)
8. [验收标准](#8-验收标准)

---

## 1. 设计总览

### 1.1 目标与范围

**Phase 4 目标**：将 Phase 3 采集的数据转化为可视化洞察和分析报告

**核心功能（5 个模块）**：
1. ✅ **图片元数据分析**：EXIF 提取、水印显示、GPS 分析
2. ✅ **文本分析**：词云生成、关键词提取
3. ✅ **时间分析**：趋势图、热力图、活跃度分析
4. ✅ **可视化增强**：图表美化、中文支持
5. ✅ **报告生成**：HTML 报告自动生成

**非目标（Phase 5）**：
- ❌ 交互式可视化（plotly）
- ❌ PDF 导出
- ❌ Web 界面

### 1.2 技术栈

**核心依赖**：
```python
# requirements.txt 新增
Pillow>=10.0.0        # 图片处理、EXIF 提取
jieba>=0.42.0         # 中文分词
wordcloud>=1.9.0      # 词云生成
matplotlib>=3.7.0     # 图表绘制
seaborn>=0.12.0       # 高级可视化（热力图）
pandas>=2.0.0         # 数据处理
jinja2>=3.1.0         # HTML 模板
geopy>=2.3.0          # GPS 反查
```

**字体依赖**（必需）：
- Linux: `apt install fonts-wqy-zenhei`
- macOS: 系统自带黑体
- Windows: 系统自带微软雅黑

### 1.3 模块架构

```
python/src/
├── analysis/                    # 新增：分析模块
│   ├── __init__.py             # 模块导出
│   ├── exif_analyzer.py        # EXIF 分析器（新增）
│   ├── text_analyzer.py        # 文本分析器（新增）
│   ├── time_analyzer.py        # 时间分析器（新增）
│   ├── visualizer.py           # 可视化器（新增）
│   └── report_generator.py     # 报告生成器（新增）
│
├── database/                    # 扩展：数据库模块
│   ├── schema_v2.sql           # Schema 扩展脚本（新增）
│   ├── migrate_exif.py         # EXIF 数据迁移（新增）
│   └── models.py               # 扩展 Media 模型
│
├── scraper/                     # 扩展：爬虫模块
│   ├── downloader.py           # 扩展：下载时提取 EXIF
│   └── archiver.py             # 扩展：HTML 生成添加水印
│
├── menu/                        # 扩展：菜单模块
│   ├── main_menu.py            # 扩展：添加分析菜单入口
│   └── analysis_menu.py        # 分析菜单（新增）
│
└── utils/                       # 扩展：工具模块
    ├── exif_utils.py           # EXIF 工具函数（新增）
    ├── font_config.py          # 字体配置（新增）
    └── stopwords.txt           # 停用词表（新增）
```

**输出目录**：
```
分析报告/
├── wordcloud/                  # 词云图
│   ├── 独醉笑清风_wordcloud.png
│   ├── 清风皓月_wordcloud.png
│   └── 全局_wordcloud.png
│
├── charts/                     # 统计图表
│   ├── monthly_trend.png
│   ├── time_heatmap.png
│   └── camera_ranking.png
│
└── reports/                    # HTML 报告
    ├── index.html              # 概览页
    ├── author_独醉笑清风.html
    └── author_清风皓月.html
```

---

## 2. 数据库设计

### 2.1 Schema 扩展

**文件**: `python/src/database/schema_v2.sql`

```sql
-- Phase 4: 扩展 media 表，添加 EXIF 字段
-- 执行时机：Phase 4 启动时自动检测并执行

-- 检查是否已扩展
-- SELECT COUNT(*) FROM pragma_table_info('media') WHERE name = 'exif_make';

-- EXIF 基础信息
ALTER TABLE media ADD COLUMN exif_make TEXT;           -- 相机品牌
ALTER TABLE media ADD COLUMN exif_model TEXT;          -- 相机型号
ALTER TABLE media ADD COLUMN exif_datetime TEXT;       -- 拍摄时间

-- EXIF 拍摄参数
ALTER TABLE media ADD COLUMN exif_iso INTEGER;         -- ISO 感光度
ALTER TABLE media ADD COLUMN exif_aperture REAL;       -- 光圈值
ALTER TABLE media ADD COLUMN exif_shutter_speed TEXT;  -- 快门速度
ALTER TABLE media ADD COLUMN exif_focal_length REAL;   -- 焦距

-- GPS 信息
ALTER TABLE media ADD COLUMN exif_gps_lat REAL;        -- GPS 纬度
ALTER TABLE media ADD COLUMN exif_gps_lng REAL;        -- GPS 经度
ALTER TABLE media ADD COLUMN exif_location TEXT;       -- 地理位置（反查）

-- 创建索引（优化查询）
CREATE INDEX IF NOT EXISTS idx_media_exif_make ON media(exif_make);
CREATE INDEX IF NOT EXISTS idx_media_exif_model ON media(exif_model);
CREATE INDEX IF NOT EXISTS idx_media_exif_datetime ON media(exif_datetime);
CREATE INDEX IF NOT EXISTS idx_media_gps ON media(exif_gps_lat, exif_gps_lng);

-- 创建视图：相机使用统计
CREATE VIEW IF NOT EXISTS v_camera_stats AS
SELECT
    exif_make,
    exif_model,
    COUNT(*) as photo_count,
    COUNT(DISTINCT post_id) as post_count,
    MIN(exif_datetime) as first_use,
    MAX(exif_datetime) as last_use
FROM media
WHERE media_type = 'image'
  AND exif_make IS NOT NULL
  AND exif_model IS NOT NULL
GROUP BY exif_make, exif_model
ORDER BY photo_count DESC;

-- 创建视图：拍摄地点统计
CREATE VIEW IF NOT EXISTS v_location_stats AS
SELECT
    exif_location,
    COUNT(*) as photo_count,
    COUNT(DISTINCT post_id) as post_count,
    AVG(exif_gps_lat) as avg_lat,
    AVG(exif_gps_lng) as avg_lng
FROM media
WHERE media_type = 'image'
  AND exif_location IS NOT NULL
GROUP BY exif_location
ORDER BY photo_count DESC;
```

### 2.2 数据迁移策略

**目标**：扫描已有图片，提取 EXIF 元数据并写入数据库

**流程**：
1. 查询所有 `media_type='image'` 且 `exif_make IS NULL` 的记录
2. 按 `file_path` 读取图片文件
3. 提取 EXIF 数据
4. 批量更新数据库（100 条/批次）
5. 显示进度条

**性能要求**：
- 扫描速度：> 10 张/秒
- 1,000 张图片：< 2 分钟

**容错处理**：
- 文件不存在：记录日志，跳过
- EXIF 数据缺失：字段设为 NULL，不报错
- GPS 反查失败：保存坐标，location 为 NULL

---

## 3. 模块详细设计

### 3.1 EXIF 分析器（exif_analyzer.py）

**职责**：提取和分析图片 EXIF 元数据

#### 3.1.1 核心类设计

```python
"""
EXIF 分析器模块

功能：
1. 提取图片 EXIF 元数据
2. GPS 坐标反查地理位置
3. 统计相机使用情况
4. 分析拍摄参数分布

依赖：
- Pillow (PIL)
- geopy

作者: Claude Sonnet 4.5
日期: 2026-02-14
"""

from typing import Dict, Optional, Tuple, List
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

logger = logging.getLogger(__name__)


class ExifAnalyzer:
    """EXIF 数据分析器"""

    def __init__(self, db_connection=None):
        """
        初始化 EXIF 分析器

        Args:
            db_connection: 数据库连接（可选）
        """
        self.db = db_connection
        self.geolocator = Nominatim(
            user_agent="t66y-forum-archiver/1.0",
            timeout=10
        )
        # GPS 反查缓存（避免重复查询）
        self._location_cache: Dict[Tuple[float, float], str] = {}

    def extract_exif(self, image_path: str) -> Dict[str, any]:
        """
        提取图片 EXIF 元数据

        Args:
            image_path: 图片文件路径

        Returns:
            dict: EXIF 数据字典
            {
                'make': 'Canon',
                'model': 'EOS R5',
                'datetime': '2026:02:14 14:30:00',
                'iso': 400,
                'aperture': 2.8,
                'shutter_speed': '1/1000',
                'focal_length': 50.0,
                'gps_lat': 39.9042,
                'gps_lng': 116.4074
            }

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件不是有效图片
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        try:
            img = Image.open(image_path)
            exif_data = img.getexif()

            if not exif_data:
                logger.debug(f"图片无 EXIF 数据: {image_path}")
                return {}

            # 提取基础信息
            result = {
                'make': self._get_exif_tag(exif_data, 'Make'),
                'model': self._get_exif_tag(exif_data, 'Model'),
                'datetime': self._get_exif_tag(exif_data, 'DateTimeOriginal'),
                'iso': self._get_exif_tag(exif_data, 'ISOSpeedRatings'),
                'aperture': self._parse_aperture(exif_data),
                'shutter_speed': self._parse_shutter_speed(exif_data),
                'focal_length': self._parse_focal_length(exif_data),
            }

            # 提取 GPS 信息
            gps_info = self._extract_gps(exif_data)
            if gps_info:
                result['gps_lat'] = gps_info['latitude']
                result['gps_lng'] = gps_info['longitude']

            # 清理 None 值
            result = {k: v for k, v in result.items() if v is not None}

            return result

        except Exception as e:
            logger.error(f"提取 EXIF 失败: {image_path}, 错误: {e}")
            return {}

    def _get_exif_tag(self, exif_data, tag_name: str) -> Optional[any]:
        """获取 EXIF 标签值"""
        for tag_id, value in exif_data.items():
            if TAGS.get(tag_id) == tag_name:
                return value
        return None

    def _parse_aperture(self, exif_data) -> Optional[float]:
        """
        解析光圈值

        EXIF FNumber 格式：(280, 100) 表示 f/2.8
        """
        f_number = self._get_exif_tag(exif_data, 'FNumber')
        if f_number and isinstance(f_number, tuple) and len(f_number) == 2:
            return round(f_number[0] / f_number[1], 1)
        return None

    def _parse_shutter_speed(self, exif_data) -> Optional[str]:
        """
        解析快门速度

        EXIF ExposureTime 格式：(1, 1000) 表示 1/1000s
        """
        exposure_time = self._get_exif_tag(exif_data, 'ExposureTime')
        if exposure_time and isinstance(exposure_time, tuple) and len(exposure_time) == 2:
            numerator, denominator = exposure_time
            if numerator == 1:
                return f"1/{denominator}"
            else:
                return f"{numerator}/{denominator}"
        return None

    def _parse_focal_length(self, exif_data) -> Optional[float]:
        """
        解析焦距

        EXIF FocalLength 格式：(500, 10) 表示 50.0mm
        """
        focal_length = self._get_exif_tag(exif_data, 'FocalLength')
        if focal_length and isinstance(focal_length, tuple) and len(focal_length) == 2:
            return round(focal_length[0] / focal_length[1], 1)
        return None

    def _extract_gps(self, exif_data) -> Optional[Dict[str, float]]:
        """
        提取 GPS 坐标

        Returns:
            dict: {'latitude': 39.9042, 'longitude': 116.4074}
        """
        gps_info = self._get_exif_tag(exif_data, 'GPSInfo')
        if not gps_info:
            return None

        try:
            # 解析纬度
            lat = self._parse_gps_coordinate(
                gps_info.get(2),  # GPSLatitude
                gps_info.get(1)   # GPSLatitudeRef (N/S)
            )

            # 解析经度
            lng = self._parse_gps_coordinate(
                gps_info.get(4),  # GPSLongitude
                gps_info.get(3)   # GPSLongitudeRef (E/W)
            )

            if lat is not None and lng is not None:
                return {'latitude': lat, 'longitude': lng}

        except Exception as e:
            logger.warning(f"解析 GPS 失败: {e}")

        return None

    def _parse_gps_coordinate(self, coord, ref) -> Optional[float]:
        """
        解析 GPS 坐标

        Args:
            coord: ((度, 1), (分, 1), (秒, 100))
            ref: 'N'/'S'/'E'/'W'

        Returns:
            float: 十进制坐标
        """
        if not coord or not ref:
            return None

        try:
            degrees = coord[0][0] / coord[0][1]
            minutes = coord[1][0] / coord[1][1]
            seconds = coord[2][0] / coord[2][1]

            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

            # 南纬和西经为负值
            if ref in ['S', 'W']:
                decimal = -decimal

            return round(decimal, 6)

        except Exception as e:
            logger.warning(f"解析坐标失败: {e}")
            return None

    def reverse_geocode(
        self,
        latitude: float,
        longitude: float,
        language: str = 'zh-CN'
    ) -> Optional[str]:
        """
        GPS 坐标反查地理位置

        Args:
            latitude: 纬度
            longitude: 经度
            language: 语言（默认中文）

        Returns:
            str: 地理位置（例如：北京市朝阳区）
            None: 查询失败

        示例：
            >>> analyzer.reverse_geocode(39.9042, 116.4074)
            '北京市朝阳区'
        """
        # 检查缓存
        cache_key = (round(latitude, 4), round(longitude, 4))
        if cache_key in self._location_cache:
            return self._location_cache[cache_key]

        try:
            location = self.geolocator.reverse(
                f"{latitude}, {longitude}",
                language=language,
                timeout=10
            )

            if location and location.address:
                # 提取简化地址（城市 + 区）
                address = self._simplify_address(location.address)
                self._location_cache[cache_key] = address
                return address

        except GeocoderTimedOut:
            logger.warning(f"GPS 反查超时: ({latitude}, {longitude})")
        except GeocoderServiceError as e:
            logger.warning(f"GPS 反查失败: {e}")
        except Exception as e:
            logger.error(f"GPS 反查异常: {e}")

        return None

    def _simplify_address(self, full_address: str) -> str:
        """
        简化地址（提取城市 + 区）

        Args:
            full_address: "朝阳区, 北京市, 100000, 中国"

        Returns:
            str: "北京市朝阳区"
        """
        # 简单处理：提取前两个逗号分隔的部分
        parts = full_address.split(',')
        if len(parts) >= 2:
            return f"{parts[1].strip()}{parts[0].strip()}"
        return full_address

    def get_camera_stats(self) -> List[Dict]:
        """
        获取相机使用统计

        Returns:
            list: 相机统计列表
            [
                {
                    'make': 'Canon',
                    'model': 'EOS R5',
                    'photo_count': 120,
                    'post_count': 15
                },
                ...
            ]
        """
        if not self.db:
            raise ValueError("需要数据库连接")

        conn = self.db.get_connection()
        cursor = conn.execute("""
            SELECT
                exif_make as make,
                exif_model as model,
                COUNT(*) as photo_count,
                COUNT(DISTINCT post_id) as post_count
            FROM media
            WHERE media_type = 'image'
              AND exif_make IS NOT NULL
              AND exif_model IS NOT NULL
            GROUP BY exif_make, exif_model
            ORDER BY photo_count DESC
            LIMIT 10
        """)

        return [dict(row) for row in cursor.fetchall()]

    def get_shooting_params_distribution(self) -> Dict[str, Dict]:
        """
        获取拍摄参数分布

        Returns:
            dict: 参数分布统计
            {
                'iso': {100: 20, 400: 35, 800: 15, ...},
                'aperture': {1.8: 10, 2.8: 25, 5.6: 30, ...},
                'focal_length': {24: 15, 50: 40, 85: 20, ...}
            }
        """
        if not self.db:
            raise ValueError("需要数据库连接")

        conn = self.db.get_connection()

        # ISO 分布
        cursor = conn.execute("""
            SELECT exif_iso, COUNT(*) as count
            FROM media
            WHERE exif_iso IS NOT NULL
            GROUP BY exif_iso
            ORDER BY exif_iso
        """)
        iso_dist = {row[0]: row[1] for row in cursor.fetchall()}

        # 光圈分布
        cursor = conn.execute("""
            SELECT exif_aperture, COUNT(*) as count
            FROM media
            WHERE exif_aperture IS NOT NULL
            GROUP BY exif_aperture
            ORDER BY exif_aperture
        """)
        aperture_dist = {row[0]: row[1] for row in cursor.fetchall()}

        # 焦距分布
        cursor = conn.execute("""
            SELECT exif_focal_length, COUNT(*) as count
            FROM media
            WHERE exif_focal_length IS NOT NULL
            GROUP BY exif_focal_length
            ORDER BY exif_focal_length
        """)
        focal_length_dist = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            'iso': iso_dist,
            'aperture': aperture_dist,
            'focal_length': focal_length_dist
        }

    def batch_extract_exif(
        self,
        media_records: List[Dict],
        show_progress: bool = True
    ) -> Dict[str, int]:
        """
        批量提取 EXIF 数据

        Args:
            media_records: Media 记录列表
                [{'media_id': 1, 'file_path': '/path/to/img.jpg'}, ...]
            show_progress: 是否显示进度条

        Returns:
            dict: 统计结果
            {
                'total': 100,
                'success': 85,
                'failed': 15,
                'has_gps': 20
            }
        """
        from rich.progress import Progress, TaskID

        total = len(media_records)
        success = 0
        failed = 0
        has_gps = 0

        if show_progress:
            with Progress() as progress:
                task = progress.add_task(
                    "[cyan]提取 EXIF 数据...",
                    total=total
                )

                for record in media_records:
                    self._process_single_media(record)
                    progress.update(task, advance=1)
        else:
            for record in media_records:
                result = self._process_single_media(record)
                if result:
                    success += 1
                    if result.get('gps_lat'):
                        has_gps += 1
                else:
                    failed += 1

        return {
            'total': total,
            'success': success,
            'failed': failed,
            'has_gps': has_gps
        }

    def _process_single_media(self, record: Dict) -> Optional[Dict]:
        """处理单个 Media 记录"""
        try:
            exif_data = self.extract_exif(record['file_path'])

            if exif_data:
                # GPS 反查（如果有坐标）
                if 'gps_lat' in exif_data and 'gps_lng' in exif_data:
                    location = self.reverse_geocode(
                        exif_data['gps_lat'],
                        exif_data['gps_lng']
                    )
                    if location:
                        exif_data['location'] = location

                # 更新数据库
                if self.db:
                    self._update_media_exif(record['media_id'], exif_data)

                return exif_data

        except Exception as e:
            logger.error(f"处理失败: {record['file_path']}, 错误: {e}")

        return None

    def _update_media_exif(self, media_id: int, exif_data: Dict):
        """更新 Media 表的 EXIF 字段"""
        if not self.db:
            return

        conn = self.db.get_connection()

        # 构建 UPDATE 语句
        fields = []
        values = []

        field_mapping = {
            'make': 'exif_make',
            'model': 'exif_model',
            'datetime': 'exif_datetime',
            'iso': 'exif_iso',
            'aperture': 'exif_aperture',
            'shutter_speed': 'exif_shutter_speed',
            'focal_length': 'exif_focal_length',
            'gps_lat': 'exif_gps_lat',
            'gps_lng': 'exif_gps_lng',
            'location': 'exif_location'
        }

        for key, db_field in field_mapping.items():
            if key in exif_data:
                fields.append(f"{db_field} = ?")
                values.append(exif_data[key])

        if fields:
            values.append(media_id)
            sql = f"UPDATE media SET {', '.join(fields)} WHERE media_id = ?"
            conn.execute(sql, values)
            conn.commit()
```

#### 3.1.2 使用示例

```python
from database import get_default_connection
from analysis import ExifAnalyzer

# 初始化
db = get_default_connection()
analyzer = ExifAnalyzer(db)

# 单张图片 EXIF 提取
exif = analyzer.extract_exif('/path/to/photo.jpg')
print(exif)
# {'make': 'Canon', 'model': 'EOS R5', 'iso': 400, ...}

# GPS 反查
location = analyzer.reverse_geocode(39.9042, 116.4074)
print(location)  # "北京市朝阳区"

# 相机统计
stats = analyzer.get_camera_stats()
print(stats)
# [{'make': 'Canon', 'model': 'EOS R5', 'photo_count': 120}, ...]

# 批量提取（历史数据迁移）
from database import Media
media_list = Media.get_all_images_without_exif()
result = analyzer.batch_extract_exif(media_list, show_progress=True)
print(result)
# {'total': 1000, 'success': 950, 'failed': 50, 'has_gps': 200}
```

#### 3.1.3 测试用例

**文件**: `test_exif_analyzer.py`

```python
import pytest
from analysis.exif_analyzer import ExifAnalyzer

def test_extract_exif_basic():
    """测试基础 EXIF 提取"""
    analyzer = ExifAnalyzer()
    exif = analyzer.extract_exif('test_data/photo_with_exif.jpg')

    assert 'make' in exif
    assert 'model' in exif
    assert isinstance(exif.get('iso'), int)

def test_extract_exif_no_exif():
    """测试无 EXIF 数据的图片"""
    analyzer = ExifAnalyzer()
    exif = analyzer.extract_exif('test_data/photo_no_exif.jpg')

    assert exif == {}

def test_extract_gps():
    """测试 GPS 提取"""
    analyzer = ExifAnalyzer()
    exif = analyzer.extract_exif('test_data/photo_with_gps.jpg')

    assert 'gps_lat' in exif
    assert 'gps_lng' in exif
    assert -90 <= exif['gps_lat'] <= 90
    assert -180 <= exif['gps_lng'] <= 180

def test_reverse_geocode():
    """测试 GPS 反查"""
    analyzer = ExifAnalyzer()
    location = analyzer.reverse_geocode(39.9042, 116.4074)

    assert location is not None
    assert '北京' in location

def test_parse_aperture():
    """测试光圈解析"""
    # 实现细节测试
    pass

def test_camera_stats():
    """测试相机统计"""
    # 需要数据库连接
    pass
```

---

### 3.2 文本分析器（text_analyzer.py）

#### 3.2.1 核心类设计

```python
"""
文本分析器模块

功能：
1. 中文分词（jieba）
2. 词频统计
3. 词云生成
4. 关键词提取（可选）

依赖：
- jieba
- wordcloud
- matplotlib

作者: Claude Sonnet 4.5
日期: 2026-02-14
"""

from typing import List, Dict, Optional
from pathlib import Path
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """文本分析器"""

    def __init__(self, db_connection=None, stopwords_path: str = None):
        """
        初始化文本分析器

        Args:
            db_connection: 数据库连接（可选）
            stopwords_path: 停用词表路径（可选）
        """
        self.db = db_connection

        # 加载停用词
        if stopwords_path and Path(stopwords_path).exists():
            self.stopwords = self._load_stopwords(stopwords_path)
        else:
            self.stopwords = self._default_stopwords()

        # 配置 jieba
        jieba.setLogLevel(logging.INFO)

    def _load_stopwords(self, path: str) -> set:
        """加载停用词表"""
        with open(path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())

    def _default_stopwords(self) -> set:
        """默认停用词"""
        return {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '个', '们'
        }

    def segment(self, text: str, min_length: int = 2) -> List[str]:
        """
        中文分词

        Args:
            text: 待分词文本
            min_length: 最小词长（默认 2）

        Returns:
            list: 分词结果
        """
        words = jieba.cut(text)
        words_filtered = [
            w for w in words
            if len(w) >= min_length and w not in self.stopwords
        ]
        return words_filtered

    def calculate_word_freq(
        self,
        text: str,
        top_n: int = 100
    ) -> Dict[str, int]:
        """
        计算词频

        Args:
            text: 文本
            top_n: 返回 Top N 个词

        Returns:
            dict: 词频字典 {'词': 频次}
        """
        words = self.segment(text)

        # 统计词频
        freq = {}
        for word in words:
            freq[word] = freq.get(word, 0) + 1

        # 排序并取 Top N
        sorted_freq = sorted(
            freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return dict(sorted_freq)

    def generate_wordcloud(
        self,
        text: str = None,
        author_name: str = None,
        output_path: str = None,
        width: int = 1920,
        height: int = 1080,
        background_color: str = 'white',
        font_path: str = None
    ) -> str:
        """
        生成词云图

        Args:
            text: 文本（与 author_name 二选一）
            author_name: 作者名（从数据库读取所有帖子标题）
            output_path: 输出路径（默认：分析报告/wordcloud/作者_wordcloud.png）
            width: 宽度（默认 1920）
            height: 高度（默认 1080）
            background_color: 背景色（默认白色）
            font_path: 字体路径（默认自动检测）

        Returns:
            str: 输出文件路径

        Raises:
            ValueError: text 和 author_name 都未提供
        """
        # 获取文本
        if text is None and author_name is None:
            raise ValueError("必须提供 text 或 author_name")

        if text is None:
            text = self._get_author_text(author_name)

        # 分词
        words = self.segment(text)
        words_joined = ' '.join(words)

        # 自动检测字体
        if font_path is None:
            font_path = self._detect_chinese_font()

        # 生成词云
        wordcloud = WordCloud(
            font_path=font_path,
            width=width,
            height=height,
            background_color=background_color,
            max_words=200,
            relative_scaling=0.5,
            colormap='viridis'
        ).generate(words_joined)

        # 保存文件
        if output_path is None:
            name = author_name if author_name else '全局'
            output_path = f"分析报告/wordcloud/{name}_wordcloud.png"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"词云已生成: {output_path}")
        return output_path

    def _get_author_text(self, author_name: str) -> str:
        """从数据库获取作者所有帖子标题"""
        if not self.db:
            raise ValueError("需要数据库连接")

        from database import Post
        posts = Post.get_by_author_name(author_name)

        # 合并所有标题
        titles = [post.title for post in posts if post.title]
        return ' '.join(titles)

    def _detect_chinese_font(self) -> str:
        """自动检测中文字体"""
        import platform
        import os

        system = platform.system()

        # Linux
        if system == 'Linux':
            fonts = [
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            ]
            for font in fonts:
                if os.path.exists(font):
                    return font

        # macOS
        elif system == 'Darwin':
            return '/System/Library/Fonts/PingFang.ttc'

        # Windows
        elif system == 'Windows':
            return 'C:/Windows/Fonts/msyh.ttc'

        # 默认（可能失败）
        logger.warning("未找到中文字体，可能出现乱码")
        return None

    def generate_multi_author_wordcloud(
        self,
        author_names: List[str],
        output_dir: str = "分析报告/wordcloud/"
    ) -> List[str]:
        """
        批量生成多个作者的词云

        Args:
            author_names: 作者名列表
            output_dir: 输出目录

        Returns:
            list: 生成的文件路径列表
        """
        output_paths = []

        for author_name in author_names:
            try:
                output_path = f"{output_dir}/{author_name}_wordcloud.png"
                path = self.generate_wordcloud(
                    author_name=author_name,
                    output_path=output_path
                )
                output_paths.append(path)
            except Exception as e:
                logger.error(f"生成词云失败: {author_name}, 错误: {e}")

        return output_paths

    def extract_keywords(
        self,
        text: str,
        top_n: int = 10,
        method: str = 'tfidf'
    ) -> List[tuple]:
        """
        提取关键词（可选功能）

        Args:
            text: 文本
            top_n: 返回 Top N 个关键词
            method: 提取方法（'tfidf' 或 'textrank'）

        Returns:
            list: [(关键词, 权重), ...]
        """
        import jieba.analyse

        if method == 'tfidf':
            keywords = jieba.analyse.extract_tags(
                text,
                topK=top_n,
                withWeight=True
            )
        elif method == 'textrank':
            keywords = jieba.analyse.textrank(
                text,
                topK=top_n,
                withWeight=True
            )
        else:
            raise ValueError(f"不支持的方法: {method}")

        return keywords
```

#### 3.2.2 使用示例

```python
from database import get_default_connection
from analysis import TextAnalyzer

# 初始化
db = get_default_connection()
analyzer = TextAnalyzer(db, stopwords_path='python/src/utils/stopwords.txt')

# 单个作者词云
wordcloud_path = analyzer.generate_wordcloud(author_name="独醉笑清风")
print(f"词云已生成: {wordcloud_path}")

# 批量生成
authors = ['独醉笑清风', '清风皓月', '同花顺心']
paths = analyzer.generate_multi_author_wordcloud(authors)

# 全局词云（所有作者）
all_text = "从数据库获取所有标题..."
analyzer.generate_wordcloud(text=all_text, output_path="全局_wordcloud.png")

# 词频统计
freq = analyzer.calculate_word_freq(all_text, top_n=20)
print(freq)
# {'美女': 120, '性感': 95, '诱惑': 80, ...}

# 关键词提取
keywords = analyzer.extract_keywords(all_text, top_n=10)
print(keywords)
# [('美女', 0.85), ('性感', 0.72), ...]
```

---

### 3.3 时间分析器（time_analyzer.py）

#### 3.3.1 核心类设计

```python
"""
时间分析器模块

功能：
1. 月度趋势分析
2. 时间热力图（小时 x 星期）
3. 活跃度分析

依赖：
- matplotlib
- seaborn
- pandas

作者: Claude Sonnet 4.5
日期: 2026-02-14
"""

from typing import Dict, List, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class TimeAnalyzer:
    """时间分析器"""

    def __init__(self, db_connection=None, font_config=None):
        """
        初始化时间分析器

        Args:
            db_connection: 数据库连接
            font_config: 字体配置（FontConfig 实例）
        """
        self.db = db_connection

        # 配置中文字体
        if font_config:
            font_config.setup_matplotlib_font()
        else:
            self._setup_default_font()

    def _setup_default_font(self):
        """配置默认中文字体"""
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

    def get_monthly_trend(
        self,
        author_name: str = None
    ) -> pd.DataFrame:
        """
        获取月度趋势数据

        Args:
            author_name: 作者名（None 表示全局）

        Returns:
            DataFrame: 月度数据
            columns: ['year_month', 'post_count', 'image_count', 'video_count']
        """
        if not self.db:
            raise ValueError("需要数据库连接")

        conn = self.db.get_connection()

        if author_name:
            sql = """
                SELECT
                    publish_year || '-' || printf('%02d', publish_month) as year_month,
                    COUNT(*) as post_count,
                    SUM(image_count) as image_count,
                    SUM(video_count) as video_count
                FROM posts
                WHERE author_id = (SELECT author_id FROM authors WHERE name = ?)
                  AND publish_year IS NOT NULL
                  AND publish_month IS NOT NULL
                GROUP BY publish_year, publish_month
                ORDER BY publish_year, publish_month
            """
            df = pd.read_sql_query(sql, conn, params=(author_name,))
        else:
            sql = """
                SELECT
                    publish_year || '-' || printf('%02d', publish_month) as year_month,
                    COUNT(*) as post_count,
                    SUM(image_count) as image_count,
                    SUM(video_count) as video_count
                FROM posts
                WHERE publish_year IS NOT NULL
                  AND publish_month IS NOT NULL
                GROUP BY publish_year, publish_month
                ORDER BY publish_year, publish_month
            """
            df = pd.read_sql_query(sql, conn)

        return df

    def plot_monthly_trend(
        self,
        author_name: str = None,
        output_path: str = None,
        figsize: tuple = (14, 6),
        dpi: int = 300
    ) -> str:
        """
        绘制月度趋势图

        Args:
            author_name: 作者名
            output_path: 输出路径
            figsize: 图表大小
            dpi: 分辨率

        Returns:
            str: 输出文件路径
        """
        df = self.get_monthly_trend(author_name)

        if df.empty:
            logger.warning("无数据，无法生成趋势图")
            return None

        # 绘图
        fig, ax = plt.subplots(figsize=figsize)

        ax.plot(
            df['year_month'],
            df['post_count'],
            marker='o',
            linewidth=2,
            markersize=6,
            label='帖子数'
        )

        # 标题
        title = f"{author_name} 发帖月度趋势" if author_name else "全局发帖月度趋势"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('帖子数', fontsize=12)

        # 旋转 x 轴标签
        plt.xticks(rotation=45, ha='right')

        # 网格
        ax.grid(True, alpha=0.3, linestyle='--')

        # 图例
        ax.legend(fontsize=10)

        plt.tight_layout()

        # 保存
        if output_path is None:
            name = author_name if author_name else '全局'
            output_path = f"分析报告/charts/{name}_monthly_trend.png"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"月度趋势图已生成: {output_path}")
        return output_path

    def get_time_heatmap_data(
        self,
        author_name: str = None
    ) -> pd.DataFrame:
        """
        获取时间热力图数据

        Args:
            author_name: 作者名

        Returns:
            DataFrame: 热力图数据
            index: weekday (0-6)
            columns: hour (0-23)
            values: post_count
        """
        if not self.db:
            raise ValueError("需要数据库连接")

        conn = self.db.get_connection()

        if author_name:
            sql = """
                SELECT
                    publish_weekday,
                    publish_hour,
                    COUNT(*) as post_count
                FROM posts
                WHERE author_id = (SELECT author_id FROM authors WHERE name = ?)
                  AND publish_weekday IS NOT NULL
                  AND publish_hour IS NOT NULL
                GROUP BY publish_weekday, publish_hour
            """
            df = pd.read_sql_query(sql, conn, params=(author_name,))
        else:
            sql = """
                SELECT
                    publish_weekday,
                    publish_hour,
                    COUNT(*) as post_count
                FROM posts
                WHERE publish_weekday IS NOT NULL
                  AND publish_hour IS NOT NULL
                GROUP BY publish_weekday, publish_hour
            """
            df = pd.read_sql_query(sql, conn)

        # 转换为 pivot 表
        pivot = df.pivot(
            index='publish_weekday',
            columns='publish_hour',
            values='post_count'
        ).fillna(0)

        return pivot

    def plot_time_heatmap(
        self,
        author_name: str = None,
        output_path: str = None,
        figsize: tuple = (16, 8),
        dpi: int = 300
    ) -> str:
        """
        绘制时间热力图

        Args:
            author_name: 作者名
            output_path: 输出路径
            figsize: 图表大小
            dpi: 分辨率

        Returns:
            str: 输出文件路径
        """
        pivot = self.get_time_heatmap_data(author_name)

        if pivot.empty:
            logger.warning("无数据，无法生成热力图")
            return None

        # 绘图
        fig, ax = plt.subplots(figsize=figsize)

        # 星期标签
        weekday_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

        sns.heatmap(
            pivot,
            cmap='YlOrRd',
            annot=True,
            fmt='.0f',
            linewidths=0.5,
            cbar_kws={'label': '帖子数'},
            yticklabels=weekday_labels,
            ax=ax
        )

        # 标题
        title = f"{author_name} 发帖时间热力图" if author_name else "全局发帖时间热力图"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        ax.set_xlabel('小时', fontsize=12)
        ax.set_ylabel('星期', fontsize=12)

        plt.tight_layout()

        # 保存
        if output_path is None:
            name = author_name if author_name else '全局'
            output_path = f"分析报告/charts/{name}_time_heatmap.png"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"时间热力图已生成: {output_path}")
        return output_path

    def analyze_active_patterns(
        self,
        author_name: str = None
    ) -> Dict:
        """
        分析活跃模式

        Args:
            author_name: 作者名

        Returns:
            dict: 活跃模式分析
            {
                'most_active_hour': 14,           # 最活跃小时
                'most_active_weekday': 2,         # 最活跃星期（0=周一）
                'weekday_vs_weekend': {
                    'weekday': 80,                # 工作日帖子数
                    'weekend': 20                 # 周末帖子数
                },
                'peak_hours': [14, 15, 20],       # 高峰时段
                'active_pattern': 'night_owl'     # 活跃模式：night_owl/early_bird/balanced
            }
        """
        if not self.db:
            raise ValueError("需要数据库连接")

        conn = self.db.get_connection()

        # 小时分布
        if author_name:
            cursor = conn.execute("""
                SELECT publish_hour, COUNT(*) as count
                FROM posts
                WHERE author_id = (SELECT author_id FROM authors WHERE name = ?)
                  AND publish_hour IS NOT NULL
                GROUP BY publish_hour
                ORDER BY count DESC
            """, (author_name,))
        else:
            cursor = conn.execute("""
                SELECT publish_hour, COUNT(*) as count
                FROM posts
                WHERE publish_hour IS NOT NULL
                GROUP BY publish_hour
                ORDER BY count DESC
            """)

        hour_dist = {row[0]: row[1] for row in cursor.fetchall()}
        most_active_hour = max(hour_dist, key=hour_dist.get) if hour_dist else None

        # 星期分布
        if author_name:
            cursor = conn.execute("""
                SELECT publish_weekday, COUNT(*) as count
                FROM posts
                WHERE author_id = (SELECT author_id FROM authors WHERE name = ?)
                  AND publish_weekday IS NOT NULL
                GROUP BY publish_weekday
                ORDER BY count DESC
            """, (author_name,))
        else:
            cursor = conn.execute("""
                SELECT publish_weekday, COUNT(*) as count
                FROM posts
                WHERE publish_weekday IS NOT NULL
                GROUP BY publish_weekday
                ORDER BY count DESC
            """)

        weekday_dist = {row[0]: row[1] for row in cursor.fetchall()}
        most_active_weekday = max(weekday_dist, key=weekday_dist.get) if weekday_dist else None

        # 工作日 vs 周末
        weekday_count = sum(weekday_dist.get(i, 0) for i in range(5))  # 周一到周五
        weekend_count = sum(weekday_dist.get(i, 0) for i in [5, 6])    # 周六、周日

        # 高峰时段（Top 3 小时）
        sorted_hours = sorted(hour_dist.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [hour for hour, _ in sorted_hours[:3]]

        # 活跃模式判断
        active_pattern = self._determine_active_pattern(most_active_hour)

        return {
            'most_active_hour': most_active_hour,
            'most_active_weekday': most_active_weekday,
            'weekday_vs_weekend': {
                'weekday': weekday_count,
                'weekend': weekend_count
            },
            'peak_hours': peak_hours,
            'active_pattern': active_pattern
        }

    def _determine_active_pattern(self, most_active_hour: int) -> str:
        """判断活跃模式"""
        if most_active_hour is None:
            return 'unknown'

        if 6 <= most_active_hour <= 11:
            return 'early_bird'      # 早起鸟
        elif 22 <= most_active_hour or most_active_hour <= 2:
            return 'night_owl'       # 夜猫子
        else:
            return 'balanced'        # 均衡型
```

#### 3.3.2 使用示例

```python
from database import get_default_connection
from analysis import TimeAnalyzer

# 初始化
db = get_default_connection()
analyzer = TimeAnalyzer(db)

# 月度趋势图
trend_path = analyzer.plot_monthly_trend(author_name="独醉笑清风")
print(f"趋势图已生成: {trend_path}")

# 时间热力图
heatmap_path = analyzer.plot_time_heatmap(author_name="独醉笑清风")
print(f"热力图已生成: {heatmap_path}")

# 活跃度分析
patterns = analyzer.analyze_active_patterns(author_name="独醉笑清风")
print(patterns)
# {
#     'most_active_hour': 14,
#     'most_active_weekday': 2,
#     'weekday_vs_weekend': {'weekday': 80, 'weekend': 20},
#     'peak_hours': [14, 15, 20],
#     'active_pattern': 'balanced'
# }
```

---

由于文档太长，我将分成两部分。这是第一部分（EXIF 分析器 + 文本分析器 + 时间分析器）。

第二部分将包含：
- 3.4 可视化器
- 3.5 报告生成器
- 4. 接口规范
- 5. 配置设计
- 6. 测试设计
- 7. 实施任务清单
- 8. 验收标准

是否继续创建第二部分？
# Phase 4 详细设计文档（第二部分）

**续接**: PHASE4_DETAILED_DESIGN.md

---

## 3.4 可视化器（visualizer.py）

### 3.4.1 核心类设计

```python
"""
可视化器模块

功能：
1. 统一图表样式配置
2. 各类图表绘制（柱状图、饼图、热力图等）
3. 中文字体配置
4. 高清图片输出

依赖：
- matplotlib
- seaborn

作者: Claude Sonnet 4.5
日期: 2026-02-14
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logger = logging.getLogger(__name__)


class Visualizer:
    """可视化器"""

    def __init__(self, font_config=None, style: str = 'seaborn-v0_8'):
        """
        初始化可视化器

        Args:
            font_config: 字体配置
            style: matplotlib 样式
        """
        self.font_config = font_config

        # 配置样式
        plt.style.use(style)

        # 配置中文字体
        if font_config:
            font_config.setup_matplotlib_font()
        else:
            self._setup_default_font()

        # 配置默认参数
        self._setup_defaults()

    def _setup_default_font(self):
        """配置默认中文字体"""
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

    def _setup_defaults(self):
        """配置默认参数"""
        import matplotlib
        matplotlib.rcParams['figure.dpi'] = 100
        matplotlib.rcParams['savefig.dpi'] = 300
        matplotlib.rcParams['savefig.bbox'] = 'tight'
        matplotlib.rcParams['figure.figsize'] = (12, 6)

    def plot_bar_chart(
        self,
        data: Dict[str, int],
        title: str,
        xlabel: str,
        ylabel: str,
        output_path: str,
        figsize: Tuple[int, int] = (12, 6),
        color: str = '#3498db',
        top_n: int = None
    ) -> str:
        """
        绘制柱状图

        Args:
            data: 数据字典 {'标签': 数值}
            title: 标题
            xlabel: X 轴标签
            ylabel: Y 轴标签
            output_path: 输出路径
            figsize: 图表大小
            color: 柱子颜色
            top_n: 只显示 Top N（可选）

        Returns:
            str: 输出文件路径
        """
        # 排序并取 Top N
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
        if top_n:
            sorted_data = sorted_data[:top_n]

        labels, values = zip(*sorted_data)

        # 绘图
        fig, ax = plt.subplots(figsize=figsize)

        bars = ax.bar(labels, values, color=color, alpha=0.8)

        # 在柱子上显示数值
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f'{int(height)}',
                ha='center',
                va='bottom',
                fontsize=10
            )

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)

        # 旋转 x 轴标签
        plt.xticks(rotation=45, ha='right')

        # 网格
        ax.grid(True, axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()

        # 保存
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"柱状图已生成: {output_path}")
        return output_path

    def plot_pie_chart(
        self,
        data: Dict[str, int],
        title: str,
        output_path: str,
        figsize: Tuple[int, int] = (10, 10),
        colors: List[str] = None,
        explode: List[float] = None
    ) -> str:
        """
        绘制饼图

        Args:
            data: 数据字典
            title: 标题
            output_path: 输出路径
            figsize: 图表大小
            colors: 颜色列表（可选）
            explode: 突出显示（可选）

        Returns:
            str: 输出文件路径
        """
        labels, values = zip(*data.items())

        # 默认颜色
        if colors is None:
            colors = plt.cm.Set3.colors

        # 绘图
        fig, ax = plt.subplots(figsize=figsize)

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            colors=colors,
            explode=explode,
            startangle=90
        )

        # 美化文本
        for text in texts:
            text.set_fontsize(12)

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        plt.tight_layout()

        # 保存
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"饼图已生成: {output_path}")
        return output_path

    def plot_line_chart(
        self,
        data: Dict[str, List],
        title: str,
        xlabel: str,
        ylabel: str,
        output_path: str,
        figsize: Tuple[int, int] = (14, 6),
        markers: bool = True
    ) -> str:
        """
        绘制折线图（支持多条线）

        Args:
            data: 数据字典
                {
                    '系列1': {'x': [1, 2, 3], 'y': [10, 20, 15]},
                    '系列2': {'x': [1, 2, 3], 'y': [5, 15, 10]}
                }
            title: 标题
            xlabel: X 轴标签
            ylabel: Y 轴标签
            output_path: 输出路径
            figsize: 图表大小
            markers: 是否显示标记点

        Returns:
            str: 输出文件路径
        """
        fig, ax = plt.subplots(figsize=figsize)

        for label, values in data.items():
            marker = 'o' if markers else None
            ax.plot(
                values['x'],
                values['y'],
                label=label,
                marker=marker,
                linewidth=2,
                markersize=6
            )

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)

        # 网格
        ax.grid(True, alpha=0.3, linestyle='--')

        # 图例
        ax.legend(fontsize=10, loc='best')

        plt.tight_layout()

        # 保存
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"折线图已生成: {output_path}")
        return output_path

    def plot_heatmap(
        self,
        data: List[List[float]],
        row_labels: List[str],
        col_labels: List[str],
        title: str,
        output_path: str,
        figsize: Tuple[int, int] = (14, 8),
        cmap: str = 'YlOrRd',
        annot: bool = True
    ) -> str:
        """
        绘制热力图

        Args:
            data: 数据矩阵
            row_labels: 行标签
            col_labels: 列标签
            title: 标题
            output_path: 输出路径
            figsize: 图表大小
            cmap: 颜色映射
            annot: 是否显示数值

        Returns:
            str: 输出文件路径
        """
        fig, ax = plt.subplots(figsize=figsize)

        sns.heatmap(
            data,
            cmap=cmap,
            annot=annot,
            fmt='.0f',
            linewidths=0.5,
            cbar_kws={'label': '数值'},
            xticklabels=col_labels,
            yticklabels=row_labels,
            ax=ax
        )

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        plt.tight_layout()

        # 保存
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"热力图已生成: {output_path}")
        return output_path
```

---

## 3.5 报告生成器（report_generator.py）

### 3.5.1 核心类设计

```python
"""
报告生成器模块

功能：
1. HTML 报告生成
2. Markdown 报告生成（可选）
3. 模板渲染
4. 图表嵌入

依赖：
- jinja2

作者: Claude Sonnet 4.5
日期: 2026-02-14
"""

from typing import Dict, List, Optional
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader
import base64
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(self, template_dir: str = None):
        """
        初始化报告生成器

        Args:
            template_dir: 模板目录路径
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / 'templates'

        self.template_dir = Path(template_dir)

        # 创建 Jinja2 环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

    def generate_html_report(
        self,
        data: Dict,
        output_path: str = "分析报告/reports/index.html",
        embed_images: bool = True
    ) -> str:
        """
        生成 HTML 报告

        Args:
            data: 报告数据
                {
                    'title': '论坛归档分析报告',
                    'global_stats': {...},
                    'authors': [...],
                    'charts': {...},
                    'wordclouds': {...}
                }
            output_path: 输出路径
            embed_images: 是否嵌入图片（base64）

        Returns:
            str: 输出文件路径
        """
        # 加载模板
        template = self.env.get_template('report.html')

        # 图片处理
        if embed_images:
            data = self._embed_images(data)

        # 渲染
        html = template.render(**data)

        # 保存
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"HTML 报告已生成: {output_path}")
        return output_path

    def _embed_images(self, data: Dict) -> Dict:
        """将图片转为 base64 嵌入"""
        # 处理 charts
        if 'charts' in data:
            for key, path in data['charts'].items():
                if path and Path(path).exists():
                    data['charts'][key] = self._image_to_base64(path)

        # 处理 wordclouds
        if 'wordclouds' in data:
            for key, path in data['wordclouds'].items():
                if path and Path(path).exists():
                    data['wordclouds'][key] = self._image_to_base64(path)

        return data

    def _image_to_base64(self, image_path: str) -> str:
        """图片转 base64"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
            b64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/png;base64,{b64_data}"

    def generate_markdown_report(
        self,
        data: Dict,
        output_path: str = "分析报告/reports/report.md"
    ) -> str:
        """
        生成 Markdown 报告（可选）

        Args:
            data: 报告数据
            output_path: 输出路径

        Returns:
            str: 输出文件路径
        """
        # 加载模板
        template = self.env.get_template('report.md')

        # 渲染
        markdown = template.render(**data)

        # 保存
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        logger.info(f"Markdown 报告已生成: {output_path}")
        return output_path

    def generate_author_report(
        self,
        author_name: str,
        data: Dict,
        output_path: str = None
    ) -> str:
        """
        生成单个作者的详细报告

        Args:
            author_name: 作者名
            data: 作者数据
            output_path: 输出路径

        Returns:
            str: 输出文件路径
        """
        if output_path is None:
            output_path = f"分析报告/reports/author_{author_name}.html"

        # 加载模板
        template = self.env.get_template('author_report.html')

        # 渲染
        html = template.render(author_name=author_name, **data)

        # 保存
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"作者报告已生成: {output_path}")
        return output_path
```

### 3.5.2 HTML 模板设计

**文件**: `python/src/analysis/templates/report.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        h1 {
            font-size: 36px;
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 16px;
            opacity: 0.9;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 14px;
            color: #666;
        }

        .section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }

        .chart-container {
            margin: 20px 0;
            text-align: center;
        }

        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .author-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .author-card {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }

        .author-name {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .author-stats {
            font-size: 14px;
            color: #666;
        }

        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }

        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            h1 {
                font-size: 28px;
            }

            .author-grid {
                grid-template-columns: 1fr;
            }
        }

        @media print {
            body {
                background: white;
            }

            .container {
                max-width: 100%;
            }

            .section {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <h1>{{ title }}</h1>
            <div class="subtitle">生成时间: {{ generation_time }}</div>
        </header>

        <!-- Global Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ global_stats.total_authors }}</div>
                <div class="stat-label">关注作者</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ global_stats.total_posts }}</div>
                <div class="stat-label">归档帖子</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ global_stats.total_images }}</div>
                <div class="stat-label">图片总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ global_stats.total_videos }}</div>
                <div class="stat-label">视频总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ global_stats.total_size_gb }}</div>
                <div class="stat-label">总存储空间(GB)</div>
            </div>
        </div>

        <!-- Monthly Trend -->
        <div class="section">
            <h2 class="section-title">📈 发帖月度趋势</h2>
            <div class="chart-container">
                {% if charts.monthly_trend %}
                <img src="{{ charts.monthly_trend }}" alt="月度趋势图">
                {% else %}
                <p>暂无数据</p>
                {% endif %}
            </div>
        </div>

        <!-- Time Heatmap -->
        <div class="section">
            <h2 class="section-title">🌡️ 发帖时间热力图</h2>
            <div class="chart-container">
                {% if charts.time_heatmap %}
                <img src="{{ charts.time_heatmap }}" alt="时间热力图">
                {% else %}
                <p>暂无数据</p>
                {% endif %}
            </div>
        </div>

        <!-- Wordcloud -->
        <div class="section">
            <h2 class="section-title">☁️ 内容词云</h2>
            <div class="chart-container">
                {% if wordclouds.global %}
                <img src="{{ wordclouds.global }}" alt="全局词云">
                {% else %}
                <p>暂无数据</p>
                {% endif %}
            </div>
        </div>

        <!-- Camera Stats -->
        {% if charts.camera_ranking %}
        <div class="section">
            <h2 class="section-title">📷 相机使用统计</h2>
            <div class="chart-container">
                <img src="{{ charts.camera_ranking }}" alt="相机排行">
            </div>
        </div>
        {% endif %}

        <!-- Author List -->
        <div class="section">
            <h2 class="section-title">👥 作者详情</h2>
            <div class="author-grid">
                {% for author in authors %}
                <div class="author-card">
                    <div class="author-name">{{ author.name }}</div>
                    <div class="author-stats">
                        📝 帖子: {{ author.total_posts }} |
                        🖼️ 图片: {{ author.total_images }} |
                        🎬 视频: {{ author.total_videos }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Footer -->
        <footer>
            <p>🤖 由 T66Y 论坛归档系统自动生成</p>
            <p>Powered by Claude Sonnet 4.5</p>
        </footer>
    </div>
</body>
</html>
```

---

## 4. 接口规范

### 4.1 模块导出接口

**文件**: `python/src/analysis/__init__.py`

```python
"""
分析模块

Phase 4: 数据分析 + 可视化

模块结构:
- exif_analyzer.py: EXIF 分析器
- text_analyzer.py: 文本分析器
- time_analyzer.py: 时间分析器
- visualizer.py: 可视化器
- report_generator.py: 报告生成器

作者: Claude Sonnet 4.5
日期: 2026-02-14
"""

from .exif_analyzer import ExifAnalyzer
from .text_analyzer import TextAnalyzer
from .time_analyzer import TimeAnalyzer
from .visualizer import Visualizer
from .report_generator import ReportGenerator

__all__ = [
    'ExifAnalyzer',
    'TextAnalyzer',
    'TimeAnalyzer',
    'Visualizer',
    'ReportGenerator',
]

__version__ = '1.0.0'
```

### 4.2 高层API设计

```python
"""
高层 API（可选）

简化常用操作的接口

文件: python/src/analysis/api.py
"""

from typing import List, Dict, Optional
from database import get_default_connection
from .exif_analyzer import ExifAnalyzer
from .text_analyzer import TextAnalyzer
from .time_analyzer import TimeAnalyzer
from .visualizer import Visualizer
from .report_generator import ReportGenerator


def analyze_all(
    output_dir: str = "分析报告",
    authors: List[str] = None
) -> Dict[str, str]:
    """
    一键生成所有分析报告

    Args:
        output_dir: 输出目录
        authors: 作者列表（None = 全部）

    Returns:
        dict: 生成的文件路径
        {
            'wordclouds': [...],
            'charts': [...],
            'reports': [...]
        }
    """
    db = get_default_connection()

    # 初始化分析器
    exif_analyzer = ExifAnalyzer(db)
    text_analyzer = TextAnalyzer(db)
    time_analyzer = TimeAnalyzer(db)
    visualizer = Visualizer()
    report_gen = ReportGenerator()

    results = {
        'wordclouds': [],
        'charts': [],
        'reports': []
    }

    # 1. 词云
    if authors:
        for author in authors:
            path = text_analyzer.generate_wordcloud(author_name=author)
            results['wordclouds'].append(path)
    else:
        path = text_analyzer.generate_wordcloud()
        results['wordclouds'].append(path)

    # 2. 趋势图
    path = time_analyzer.plot_monthly_trend()
    results['charts'].append(path)

    # 3. 热力图
    path = time_analyzer.plot_time_heatmap()
    results['charts'].append(path)

    # 4. 相机统计
    camera_stats = exif_analyzer.get_camera_stats()
    if camera_stats:
        data = {item['model']: item['photo_count'] for item in camera_stats}
        path = visualizer.plot_bar_chart(
            data,
            "相机使用排行",
            "相机型号",
            "照片数",
            f"{output_dir}/charts/camera_ranking.png"
        )
        results['charts'].append(path)

    # 5. HTML 报告
    report_data = {
        'title': '论坛归档分析报告',
        'generation_time': '2026-02-14',
        'global_stats': {},  # 从数据库获取
        'authors': [],       # 从数据库获取
        'charts': {},
        'wordclouds': {}
    }
    path = report_gen.generate_html_report(report_data)
    results['reports'].append(path)

    return results


def analyze_author(author_name: str, output_dir: str = "分析报告") -> Dict[str, str]:
    """
    分析单个作者

    Args:
        author_name: 作者名
        output_dir: 输出目录

    Returns:
        dict: 生成的文件路径
    """
    db = get_default_connection()

    results = {}

    # 词云
    text_analyzer = TextAnalyzer(db)
    results['wordcloud'] = text_analyzer.generate_wordcloud(author_name=author_name)

    # 趋势图
    time_analyzer = TimeAnalyzer(db)
    results['trend'] = time_analyzer.plot_monthly_trend(author_name=author_name)

    # 热力图
    results['heatmap'] = time_analyzer.plot_time_heatmap(author_name=author_name)

    # 活跃度分析
    results['active_patterns'] = time_analyzer.analyze_active_patterns(author_name=author_name)

    return results
```

---

## 5. 配置设计

### 5.1 字体配置模块

**文件**: `python/src/utils/font_config.py`

```python
"""
字体配置模块

功能：
1. 自动检测系统中文字体
2. 配置 matplotlib 中文显示
3. 提供字体路径查询

作者: Claude Sonnet 4.5
日期: 2026-02-14
"""

import platform
import os
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class FontConfig:
    """字体配置器"""

    # 字体路径映射
    FONT_PATHS = {
        'Linux': [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/arphic/uming.ttc',
        ],
        'Darwin': [  # macOS
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
        ],
        'Windows': [
            'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',  # 黑体
            'C:/Windows/Fonts/simsun.ttc',  # 宋体
        ]
    }

    def __init__(self):
        """初始化字体配置"""
        self.system = platform.system()
        self.font_path = self.detect_chinese_font()

    def detect_chinese_font(self) -> Optional[str]:
        """
        自动检测系统中文字体

        Returns:
            str: 字体文件路径
            None: 未找到字体
        """
        paths = self.FONT_PATHS.get(self.system, [])

        for path in paths:
            if os.path.exists(path):
                logger.info(f"找到中文字体: {path}")
                return path

        logger.warning(f"未找到中文字体（系统: {self.system}）")
        return None

    def setup_matplotlib_font(self) -> bool:
        """
        配置 matplotlib 中文字体

        Returns:
            bool: 配置成功
        """
        import matplotlib
        import matplotlib.font_manager as fm

        if self.font_path:
            # 添加字体
            fm.fontManager.addfont(self.font_path)

            # 获取字体名称
            font_prop = fm.FontProperties(fname=self.font_path)
            font_name = font_prop.get_name()

            # 配置 matplotlib
            matplotlib.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
            matplotlib.rcParams['axes.unicode_minus'] = False

            logger.info(f"matplotlib 中文字体配置成功: {font_name}")
            return True
        else:
            # 降级配置
            matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
            matplotlib.rcParams['axes.unicode_minus'] = False

            logger.warning("使用降级配置，中文可能显示为方框")
            return False

    def get_font_path(self) -> Optional[str]:
        """获取字体路径"""
        return self.font_path

    def test_chinese_display(self) -> bool:
        """
        测试中文显示

        Returns:
            bool: 中文显示正常
        """
        import matplotlib.pyplot as plt

        try:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, '测试中文显示', fontsize=20, ha='center', va='center')
            ax.set_title('中文字体测试')

            test_path = 'test_chinese_font.png'
            plt.savefig(test_path, dpi=100)
            plt.close()

            # 检查文件
            if os.path.exists(test_path):
                logger.info("中文显示测试通过")
                os.remove(test_path)
                return True

        except Exception as e:
            logger.error(f"中文显示测试失败: {e}")

        return False
```

### 5.2 停用词表

**文件**: `python/src/utils/stopwords.txt`

```
# 中文停用词表
# 用于词云生成时过滤无意义词汇

# 代词
的
了
在
是
我
你
他
她
它
们
这
那
哪
谁
什么

# 动词
有
和
就
不
都
会
要
去
说
看
做

# 副词
也
很
还
又
再
更
最
只
才
能
可以

# 连词
与
或
但是
然后
因为
所以
虽然
如果

# 量词
一
一个
一些
几个

# 其他
上
下
中
里
外
前
后
左
右
```

---

## 6. 测试设计

### 6.1 单元测试

**文件**: `test_phase4_analysis.py`

```python
"""
Phase 4 分析模块单元测试

运行: pytest test_phase4_analysis.py -v

作者: Claude Sonnet 4.5
日期: 2026-02-14
"""

import pytest
from pathlib import Path
from analysis import (
    ExifAnalyzer,
    TextAnalyzer,
    TimeAnalyzer,
    Visualizer,
    ReportGenerator
)


class TestExifAnalyzer:
    """EXIF 分析器测试"""

    def test_extract_exif_basic(self):
        """测试基础 EXIF 提取"""
        analyzer = ExifAnalyzer()
        # 需要准备测试图片
        # exif = analyzer.extract_exif('test_data/photo_with_exif.jpg')
        # assert 'make' in exif

    def test_extract_gps(self):
        """测试 GPS 提取"""
        pass

    def test_reverse_geocode(self):
        """测试 GPS 反查"""
        analyzer = ExifAnalyzer()
        location = analyzer.reverse_geocode(39.9042, 116.4074)
        assert location is not None
        assert '北京' in location


class TestTextAnalyzer:
    """文本分析器测试"""

    def test_segment(self):
        """测试中文分词"""
        analyzer = TextAnalyzer()
        text = "这是一个测试文本"
        words = analyzer.segment(text)
        assert len(words) > 0

    def test_calculate_word_freq(self):
        """测试词频统计"""
        analyzer = TextAnalyzer()
        text = "美女 美女 性感 性感 性感"
        freq = analyzer.calculate_word_freq(text)
        assert freq['性感'] > freq['美女']

    def test_generate_wordcloud(self):
        """测试词云生成"""
        # 需要文本数据
        pass


class TestTimeAnalyzer:
    """时间分析器测试"""

    def test_get_monthly_trend(self):
        """测试获取月度趋势"""
        # 需要数据库连接
        pass

    def test_analyze_active_patterns(self):
        """测试活跃度分析"""
        # 需要数据库连接
        pass


class TestVisualizer:
    """可视化器测试"""

    def test_plot_bar_chart(self):
        """测试柱状图"""
        vis = Visualizer()
        data = {'A': 10, 'B': 20, 'C': 15}
        output = 'test_output/bar_chart.png'
        path = vis.plot_bar_chart(
            data,
            '测试柱状图',
            'X轴',
            'Y轴',
            output
        )
        assert Path(path).exists()

    def test_plot_pie_chart(self):
        """测试饼图"""
        pass


class TestReportGenerator:
    """报告生成器测试"""

    def test_generate_html_report(self):
        """测试 HTML 报告生成"""
        gen = ReportGenerator()
        data = {
            'title': '测试报告',
            'generation_time': '2026-02-14',
            'global_stats': {
                'total_authors': 9,
                'total_posts': 350
            },
            'authors': [],
            'charts': {},
            'wordclouds': {}
        }
        output = 'test_output/test_report.html'
        path = gen.generate_html_report(data, output)
        assert Path(path).exists()


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

---

## 7. 实施任务清单

### 7.1 任务分解（Week 1-3，共35个任务）

**格式**: `[Task #XX] 任务名称（工作量）`

#### Week 1: 图片元数据（5 天）

**Day 1: 数据库扩展（0.5 天）**
- [Task #26] 创建 `schema_v2.sql`（0.5 天）

**Day 2: EXIF 分析器（1 天）**
- [Task #27] 创建 `exif_analyzer.py` 基础框架（0.5 天）
- [Task #28] 实现 `extract_exif()` 方法（0.5 天）

**Day 3: EXIF 提取集成（1 天）**
- [Task #29] 修改 `downloader.py` 下载时提取 EXIF（0.5 天）
- [Task #30] 实现 GPS 提取和反查（0.5 天）

**Day 4: 历史数据迁移（1 天）**
- [Task #31] 创建 `migrate_exif.py`（0.5 天）
- [Task #32] 实现批量 EXIF 扫描（0.5 天）

**Day 5: 照片水印显示（1 天）**
- [Task #33] 修改 `archiver.py` HTML 生成（0.5 天）
- [Task #34] 设计水印 CSS 样式（0.5 天）

---

#### Week 2: 文本与时间分析（5 天）

**Day 6: 文本分析器基础（1 天）**
- [Task #35] 创建 `text_analyzer.py`（0.5 天）
- [Task #36] 实现中文分词和词频统计（0.5 天）

**Day 7: 词云生成（1 天）**
- [Task #37] 实现词云生成器（0.5 天）
- [Task #38] 配置中文字体（`font_config.py`）（0.5 天）

**Day 8: 时间分析器基础（1 天）**
- [Task #39] 创建 `time_analyzer.py`（0.5 天）
- [Task #40] 实现月度趋势分析（0.5 天）

**Day 9: 时间热力图（1 天）**
- [Task #41] 实现时间热力图（0.5 天）
- [Task #42] 实现活跃度分析（0.5 天）

**Day 10: 相机统计（1 天）**
- [Task #43] 实现相机统计查询（0.5 天）
- [Task #44] 绘制相机排行图表（0.5 天）

---

#### Week 3: 可视化与报告（5 天）

**Day 11: 可视化器（1 天）**
- [Task #45] 创建 `visualizer.py`（0.5 天）
- [Task #46] 实现各类图表方法（0.5 天）

**Day 12: 图表美化（1 天）**
- [Task #47] 统一图表样式配置（0.5 天）
- [Task #48] 高清输出配置（0.5 天）

**Day 13: 报告生成器（1 天）**
- [Task #49] 创建 `report_generator.py`（0.5 天）
- [Task #50] 设计 HTML 模板（0.5 天）

**Day 14: 报告集成（1 天）**
- [Task #51] 实现报告数据准备（0.5 天）
- [Task #52] 实现图片嵌入（0.5 天）

**Day 15: 菜单集成与测试（1 天）**
- [Task #53] 创建 `analysis_menu.py`（0.5 天）
- [Task #54] 集成到主菜单（0.5 天）

---

### 7.2 任务依赖关系

```
Task #26 (schema_v2.sql)
  ├─> Task #27 (exif_analyzer基础)
  │     ├─> Task #28 (extract_exif)
  │     │     ├─> Task #29 (downloader集成)
  │     │     └─> Task #30 (GPS提取)
  │     └─> Task #31 (migrate_exif)
  │           └─> Task #32 (批量扫描)
  │
  ├─> Task #35 (text_analyzer)
  │     ├─> Task #36 (分词)
  │     └─> Task #37 (词云)
  │           └─> Task #38 (字体配置)
  │
  ├─> Task #39 (time_analyzer)
  │     ├─> Task #40 (月度趋势)
  │     ├─> Task #41 (热力图)
  │     └─> Task #42 (活跃度)
  │
  ├─> Task #43 (相机统计)
  │     └─> Task #44 (相机图表)
  │
  ├─> Task #45 (visualizer)
  │     ├─> Task #46 (图表方法)
  │     ├─> Task #47 (样式配置)
  │     └─> Task #48 (高清输出)
  │
  └─> Task #49 (report_generator)
        ├─> Task #50 (HTML模板)
        ├─> Task #51 (数据准备)
        └─> Task #52 (图片嵌入)
              └─> Task #53 (analysis_menu)
                    └─> Task #54 (菜单集成)
```

---

## 8. 验收标准

### 8.1 功能验收

| 验收项 | 标准 | 测试方法 | 优先级 |
|--------|------|----------|--------|
| **EXIF 提取** | 所有图片 EXIF 数据完整 | 随机抽查 100 张 | P0 |
| **照片水印** | 归档页面正确显示水印 | 浏览器测试 | P0 |
| **GPS 反查** | 成功率 > 90% | 统计反查结果 | P1 |
| **词云生成** | 中文无乱码，词云清晰 | 视觉检查 | P0 |
| **时间热力图** | 数据准确，颜色区分清晰 | 对比数据库 | P0 |
| **月度趋势图** | 折线清晰，标签完整 | 视觉检查 | P0 |
| **相机统计** | 数据准确，Top 10 排行正确 | 对比数据库 | P1 |
| **HTML 报告** | 包含所有分析内容，样式美观 | 多浏览器测试 | P0 |
| **响应式设计** | 手机/平板/桌面适配 | 多设备测试 | P1 |

### 8.2 性能验收

| 指标 | 目标 | 测试方法 | 优先级 |
|------|------|----------|--------|
| EXIF 提取速度 | > 10 张/秒 | 批量提取 100 张计时 | P0 |
| GPS 反查速度 | < 2 秒/次 | 单次反查计时 | P1 |
| 词云生成时间 | < 5 秒 | 单作者词云计时 | P0 |
| 热力图生成时间 | < 2 秒 | 全局热力图计时 | P0 |
| HTML 报告生成 | < 10 秒 | 完整报告计时 | P0 |
| 报告文件大小 | < 10 MB | 检查文件大小 | P1 |

### 8.3 质量验收

| 指标 | 目标 | 测试方法 | 优先级 |
|------|------|----------|--------|
| 代码覆盖率 | > 80% | pytest --cov | P1 |
| 单元测试通过率 | 100% | pytest | P0 |
| 中文显示 | 无乱码 | 多平台测试 | P0 |
| 图表质量 | DPI 300，清晰 | 视觉检查 | P0 |
| 报告美观度 | 符合设计规范 | 设计师审查 | P1 |

### 8.4 验收测试用例

**测试用例 1：EXIF 提取完整性**
```
前置条件：数据库中有 1,000 张图片记录
测试步骤：
1. 运行 EXIF 批量扫描
2. 统计提取成功率
3. 检查字段完整性
预期结果：
- 成功率 > 95%
- 主要字段（make/model/datetime）完整率 > 90%
```

**测试用例 2：词云中文显示**
```
前置条件：已有帖子标题数据
测试步骤：
1. 生成单作者词云
2. 生成全局词云
3. 在多个平台查看（Linux/macOS/Windows）
预期结果：
- 所有平台中文显示正常，无乱码
- 词云图清晰，DPI 300
```

**测试用例 3：HTML 报告功能**
```
前置条件：已生成所有图表
测试步骤：
1. 生成 HTML 报告
2. 在多个浏览器打开（Chrome/Firefox/Safari）
3. 测试响应式设计（调整窗口大小）
4. 测试打印功能
预期结果：
- 所有浏览器显示正常
- 响应式布局正确
- 打印格式友好
```

**测试用例 4：照片水印显示**
```
前置条件：已归档帖子包含图片
测试步骤：
1. 打开归档页面
2. 查看图片水印
3. 测试多种设备（手机/平板/桌面）
预期结果：
- 水印信息完整（相机/时间/地点）
- 样式美观
- 多设备适配
```

---

## 9. 实施检查清单

### 9.1 环境准备

- [ ] 安装依赖库（`pip install -r requirements.txt`）
- [ ] 安装中文字体（Linux: `apt install fonts-wqy-zenhei`）
- [ ] 测试中文显示（运行 `font_config.test_chinese_display()`）
- [ ] 准备测试数据（EXIF 图片、文本数据）

### 9.2 Week 1 检查清单

- [ ] Task #26: schema_v2.sql 创建
- [ ] Task #27-28: exif_analyzer.py 基础功能
- [ ] Task #29-30: downloader.py 集成 + GPS
- [ ] Task #31-32: migrate_exif.py 批量扫描
- [ ] Task #33-34: archiver.py 水印显示
- [ ] Week 1 验收：所有图片 EXIF 提取完成

### 9.3 Week 2 检查清单

- [ ] Task #35-36: text_analyzer.py 分词
- [ ] Task #37-38: 词云生成 + 字体配置
- [ ] Task #39-40: time_analyzer.py 趋势分析
- [ ] Task #41-42: 热力图 + 活跃度
- [ ] Task #43-44: 相机统计
- [ ] Week 2 验收：词云和热力图生成正常

### 9.4 Week 3 检查清单

- [ ] Task #45-46: visualizer.py 图表方法
- [ ] Task #47-48: 图表美化 + 高清输出
- [ ] Task #49-50: report_generator.py + 模板
- [ ] Task #51-52: 报告数据准备 + 图片嵌入
- [ ] Task #53-54: analysis_menu.py + 菜单集成
- [ ] Week 3 验收：HTML 报告完整美观

### 9.5 最终检查清单

- [ ] 所有单元测试通过（pytest）
- [ ] 代码覆盖率 > 80%
- [ ] 中文显示无乱码（多平台测试）
- [ ] HTML 报告美观（多浏览器测试）
- [ ] 性能达标（所有指标）
- [ ] 文档更新（README、FEATURES_DESIGN_OVERVIEW）
- [ ] GitHub 提交（标注"Mile3完成"）

---

## 10. 风险缓解措施

### 10.1 技术风险缓解

**风险 1：中文乱码**
- 缓解：提前配置字体，使用 `font_config.py` 自动检测
- 回退：使用英文标签，或提供手动配置选项

**风险 2：EXIF 数据缺失**
- 缓解：容错处理，字段可选
- 回退：部分字段显示"未知"

**风险 3：GPS 反查失败**
- 缓解：缓存结果，失败时显示坐标
- 回退：不显示地理位置，只显示坐标

**风险 4：依赖库冲突**
- 缓解：锁定版本，使用虚拟环境
- 回退：降级依赖版本

### 10.2 进度风险缓解

**风险 1：功能蔓延**
- 缓解：严格按 P0/P1/P2 优先级
- 回退：砍掉 P2 功能

**风险 2：测试不充分**
- 缓解：边开发边测试，预留测试时间
- 回退：减少功能范围

---

**文档结束**

**合并提示**: 将此文档与 `PHASE4_DETAILED_DESIGN.md` 合并，形成完整的 Phase 4 设计文档。

**下一步**: 等待用户确认后开始实施 Task #26。
