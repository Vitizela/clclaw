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
        self.geolocator = None  # 延迟初始化

        # GPS 反查缓存（避免重复查询）
        self._location_cache: Dict[Tuple[float, float], str] = {}

    def _init_geolocator(self):
        """延迟初始化 geopy"""
        if self.geolocator is None:
            try:
                from geopy.geocoders import Nominatim
                self.geolocator = Nominatim(
                    user_agent="t66y-forum-archiver/1.0",
                    timeout=10
                )
            except ImportError:
                logger.warning("geopy 未安装，GPS 反查功能不可用")
                self.geolocator = False

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
                'datetime': self._get_exif_tag(exif_data, 'DateTimeOriginal') or self._get_exif_tag(exif_data, 'DateTime'),
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
                # 处理字节类型（转为字符串）
                if isinstance(value, bytes):
                    try:
                        return value.decode('utf-8', errors='ignore').strip()
                    except:
                        return None
                return value
        return None

    def _parse_aperture(self, exif_data) -> Optional[float]:
        """
        解析光圈值

        EXIF FNumber 格式：(280, 100) 表示 f/2.8
        """
        f_number = self._get_exif_tag(exif_data, 'FNumber')
        if f_number and isinstance(f_number, tuple) and len(f_number) == 2:
            try:
                return round(f_number[0] / f_number[1], 1)
            except:
                pass
        return None

    def _parse_shutter_speed(self, exif_data) -> Optional[str]:
        """
        解析快门速度

        EXIF ExposureTime 格式：(1, 1000) 表示 1/1000s
        """
        exposure_time = self._get_exif_tag(exif_data, 'ExposureTime')
        if exposure_time and isinstance(exposure_time, tuple) and len(exposure_time) == 2:
            try:
                numerator, denominator = exposure_time
                if numerator == 1:
                    return f"1/{denominator}"
                else:
                    return f"{numerator}/{denominator}"
            except:
                pass
        return None

    def _parse_focal_length(self, exif_data) -> Optional[float]:
        """
        解析焦距

        EXIF FocalLength 格式：(500, 10) 表示 50.0mm
        """
        focal_length = self._get_exif_tag(exif_data, 'FocalLength')
        if focal_length and isinstance(focal_length, tuple) and len(focal_length) == 2:
            try:
                return round(focal_length[0] / focal_length[1], 1)
            except:
                pass
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
        self._init_geolocator()

        if self.geolocator is False:
            return None

        # 检查缓存
        cache_key = (round(latitude, 4), round(longitude, 4))
        if cache_key in self._location_cache:
            return self._location_cache[cache_key]

        try:
            from geopy.exc import GeocoderTimedOut, GeocoderServiceError

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
            SELECT * FROM v_camera_stats
            LIMIT 10
        """)

        return [dict(row) for row in cursor.fetchall()]

    def batch_extract_exif(
        self,
        media_records: List[Dict],
        show_progress: bool = True
    ) -> Dict[str, int]:
        """
        批量提取 EXIF 数据

        Args:
            media_records: Media 记录列表
                [{'id': 1, 'file_path': '/path/to/img.jpg'}, ...]
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
        total = len(media_records)
        success = 0
        failed = 0
        has_gps = 0

        if show_progress:
            from rich.progress import Progress

            with Progress() as progress:
                task = progress.add_task(
                    "[cyan]提取 EXIF 数据...",
                    total=total
                )

                for record in media_records:
                    result = self._process_single_media(record)
                    if result:
                        success += 1
                        if result.get('gps_lat'):
                            has_gps += 1
                    else:
                        failed += 1
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
                    self._update_media_exif(record['id'], exif_data)

                return exif_data

        except Exception as e:
            logger.error(f"处理失败: {record.get('file_path', 'unknown')}, 错误: {e}")

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
            sql = f"UPDATE media SET {', '.join(fields)} WHERE id = ?"
            conn.execute(sql, values)
            conn.commit()
