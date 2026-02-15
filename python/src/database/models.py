"""
数据模型模块

提供轻量级的 ORM 接口，封装数据库 CRUD 操作。
包含三个核心模型：Author（作者）、Post（帖子）、Media（媒体）
"""

import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from .connection import DatabaseConnection


# =============================================================================
# 辅助函数
# =============================================================================

def _dict_from_row(row) -> dict:
    """将 sqlite3.Row 对象转换为字典"""
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def _parse_json_field(value: Optional[str]) -> Optional[List[str]]:
    """解析 JSON 字段（如 tags）"""
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


def _serialize_json_field(value: Optional[List[str]]) -> Optional[str]:
    """序列化 JSON 字段"""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


# =============================================================================
# Author 模型
# =============================================================================

@dataclass
class Author:
    """
    作者模型

    属性:
        id: 作者 ID（主键）
        name: 作者名
        added_date: 关注日期
        last_update: 最后更新时间
        url: 作者 URL
        total_posts: 已归档帖子数
        forum_total_posts: 论坛总帖子数
        total_images: 总图片数
        total_videos: 总视频数
        total_size_bytes: 总占用空间
        tags: 标签列表
        notes: 备注
        created_at: 记录创建时间
        updated_at: 记录更新时间
    """

    id: Optional[int] = None
    name: str = ""
    added_date: str = ""
    last_update: Optional[str] = None
    url: Optional[str] = None
    total_posts: int = 0
    forum_total_posts: int = 0
    total_images: int = 0
    total_videos: int = 0
    total_size_bytes: int = 0
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # 数据库连接（类级别共享）
    _db: Optional[DatabaseConnection] = field(default=None, init=False, repr=False)

    @classmethod
    def _get_db(cls) -> DatabaseConnection:
        """获取数据库连接"""
        if cls._db is None:
            from .connection import get_default_connection
            cls._db = get_default_connection()
        return cls._db

    @classmethod
    def from_row(cls, row) -> 'Author':
        """从数据库行创建 Author 对象"""
        if row is None:
            return None

        return cls(
            id=row['id'],
            name=row['name'],
            added_date=row['added_date'],
            last_update=row['last_update'],
            url=row['url'],
            total_posts=row['total_posts'],
            forum_total_posts=row['forum_total_posts'],
            total_images=row['total_images'],
            total_videos=row['total_videos'],
            total_size_bytes=row['total_size_bytes'],
            tags=_parse_json_field(row['tags']),
            notes=row['notes'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    @classmethod
    def get_by_id(cls, author_id: int) -> Optional['Author']:
        """根据 ID 获取作者"""
        db = cls._get_db()
        conn = db.get_connection()

        cursor = conn.execute(
            "SELECT * FROM authors WHERE id = ?",
            (author_id,)
        )
        row = cursor.fetchone()
        return cls.from_row(row)

    @classmethod
    def get_by_name(cls, name: str) -> Optional['Author']:
        """根据名称获取作者"""
        db = cls._get_db()
        conn = db.get_connection()

        cursor = conn.execute(
            "SELECT * FROM authors WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return cls.from_row(row)

    @classmethod
    def get_all(cls) -> List['Author']:
        """获取所有作者"""
        db = cls._get_db()
        conn = db.get_connection()

        cursor = conn.execute("SELECT * FROM authors ORDER BY name")
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def create(
        cls,
        name: str,
        added_date: str,
        url: Optional[str] = None,
        forum_total_posts: int = 0,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> 'Author':
        """
        创建新作者

        Args:
            name: 作者名
            added_date: 关注日期（YYYY-MM-DD）
            url: 作者 URL
            forum_total_posts: 论坛总帖子数
            tags: 标签列表
            notes: 备注

        Returns:
            Author 对象
        """
        db = cls._get_db()
        conn = db.get_connection()

        cursor = conn.execute(
            """
            INSERT INTO authors (
                name, added_date, url, forum_total_posts, tags, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                added_date,
                url,
                forum_total_posts,
                _serialize_json_field(tags),
                notes
            )
        )
        conn.commit()

        # 返回新创建的作者对象
        return cls.get_by_id(cursor.lastrowid)

    def update(self, **kwargs):
        """
        更新作者信息

        Args:
            **kwargs: 要更新的字段（name, url, forum_total_posts, tags, notes等）
        """
        if self.id is None:
            raise ValueError("无法更新未保存的作者")

        db = self._get_db()
        conn = db.get_connection()

        # 构建更新语句
        update_fields = []
        values = []

        for field, value in kwargs.items():
            if field == 'tags':
                value = _serialize_json_field(value)
            update_fields.append(f"{field} = ?")
            values.append(value)

        if not update_fields:
            return

        # 添加 updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(self.id)

        sql = f"UPDATE authors SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(sql, values)
        conn.commit()

        # 重新加载对象
        updated = self.get_by_id(self.id)
        if updated:
            self.__dict__.update(updated.__dict__)

    def delete(self):
        """删除作者（级联删除相关帖子和媒体）"""
        if self.id is None:
            raise ValueError("无法删除未保存的作者")

        db = self._get_db()
        conn = db.get_connection()

        conn.execute("DELETE FROM authors WHERE id = ?", (self.id,))
        conn.commit()

        self.id = None

    def get_posts(self) -> List['Post']:
        """获取该作者的所有帖子"""
        if self.id is None:
            return []
        return Post.get_by_author(self.id)

    def get_stats(self) -> dict:
        """
        获取作者统计信息

        Returns:
            包含统计信息的字典
        """
        if self.id is None:
            return {}

        db = self._get_db()
        conn = db.get_connection()

        # 使用视图查询
        cursor = conn.execute(
            "SELECT * FROM v_author_stats WHERE id = ?",
            (self.id,)
        )
        row = cursor.fetchone()

        if row is None:
            return {}

        return _dict_from_row(row)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'added_date': self.added_date,
            'last_update': self.last_update,
            'url': self.url,
            'total_posts': self.total_posts,
            'forum_total_posts': self.forum_total_posts,
            'total_images': self.total_images,
            'total_videos': self.total_videos,
            'total_size_bytes': self.total_size_bytes,
            'tags': self.tags,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


# =============================================================================
# Post 模型
# =============================================================================

@dataclass
class Post:
    """
    帖子模型

    属性:
        id: 帖子 ID（主键）
        author_id: 作者 ID（外键）
        url: 帖子 URL
        url_hash: URL hash
        title: 帖子标题
        publish_date: 发布日期
        publish_year: 发布年份
        publish_month: 发布月份
        publish_hour: 发布小时
        publish_weekday: 星期几
        content_length: 内容长度
        word_count: 字数统计
        image_count: 图片数量
        video_count: 视频数量
        file_path: 归档目录路径
        archived_date: 归档日期
        file_size_bytes: 文件大小
        is_complete: 是否完整归档
        created_at: 记录创建时间
        updated_at: 记录更新时间
    """

    id: Optional[int] = None
    author_id: int = 0
    url: str = ""
    url_hash: str = ""
    title: str = ""
    publish_date: Optional[str] = None
    publish_year: Optional[int] = None
    publish_month: Optional[int] = None
    publish_hour: Optional[int] = None
    publish_weekday: Optional[int] = None
    content_length: int = 0
    word_count: int = 0
    image_count: int = 0
    video_count: int = 0
    file_path: str = ""
    archived_date: str = ""
    file_size_bytes: int = 0
    is_complete: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    _db: Optional[DatabaseConnection] = field(default=None, init=False, repr=False)

    @classmethod
    def _get_db(cls) -> DatabaseConnection:
        """获取数据库连接"""
        if cls._db is None:
            from .connection import get_default_connection
            cls._db = get_default_connection()
        return cls._db

    @classmethod
    def from_row(cls, row) -> 'Post':
        """从数据库行创建 Post 对象"""
        if row is None:
            return None

        return cls(
            id=row['id'],
            author_id=row['author_id'],
            url=row['url'],
            url_hash=row['url_hash'],
            title=row['title'],
            publish_date=row['publish_date'],
            publish_year=row['publish_year'],
            publish_month=row['publish_month'],
            publish_hour=row['publish_hour'],
            publish_weekday=row['publish_weekday'],
            content_length=row['content_length'],
            word_count=row['word_count'],
            image_count=row['image_count'],
            video_count=row['video_count'],
            file_path=row['file_path'],
            archived_date=row['archived_date'],
            file_size_bytes=row['file_size_bytes'],
            is_complete=bool(row['is_complete']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    @classmethod
    def get_by_id(cls, post_id: int) -> Optional['Post']:
        """根据 ID 获取帖子"""
        db = cls._get_db()
        conn = db.get_connection()

        cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        return cls.from_row(row)

    @classmethod
    def get_by_url(cls, url: str) -> Optional['Post']:
        """根据 URL 获取帖子"""
        db = cls._get_db()
        conn = db.get_connection()

        cursor = conn.execute("SELECT * FROM posts WHERE url = ?", (url,))
        row = cursor.fetchone()
        return cls.from_row(row)

    @classmethod
    def get_by_author(cls, author_id: int, limit: Optional[int] = None) -> List['Post']:
        """
        获取指定作者的所有帖子

        Args:
            author_id: 作者 ID
            limit: 限制返回数量

        Returns:
            Post 对象列表
        """
        db = cls._get_db()
        conn = db.get_connection()

        sql = "SELECT * FROM posts WHERE author_id = ? ORDER BY publish_date DESC"
        params = [author_id]

        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        cursor = conn.execute(sql, params)
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def create(
        cls,
        author_id: int,
        url: str,
        url_hash: str,
        title: str,
        file_path: str,
        archived_date: str,
        publish_date: Optional[str] = None,
        image_count: int = 0,
        video_count: int = 0,
        content_length: int = 0,
        word_count: int = 0,
        file_size_bytes: int = 0,
        is_complete: bool = True
    ) -> 'Post':
        """
        创建新帖子

        Args:
            author_id: 作者 ID
            url: 帖子 URL
            url_hash: URL hash
            title: 帖子标题
            file_path: 归档目录路径
            archived_date: 归档日期
            publish_date: 发布日期
            image_count: 图片数量
            video_count: 视频数量
            content_length: 内容长度
            word_count: 字数统计
            file_size_bytes: 文件大小
            is_complete: 是否完整归档

        Returns:
            Post 对象
        """
        db = cls._get_db()
        conn = db.get_connection()

        # 从 publish_date 提取冗余字段
        publish_year = None
        publish_month = None
        publish_hour = None
        publish_weekday = None

        if publish_date:
            try:
                dt = datetime.strptime(publish_date, "%Y-%m-%d %H:%M:%S")
                publish_year = dt.year
                publish_month = dt.month
                publish_hour = dt.hour
                publish_weekday = dt.weekday()
            except ValueError:
                pass

        cursor = conn.execute(
            """
            INSERT INTO posts (
                author_id, url, url_hash, title, publish_date,
                publish_year, publish_month, publish_hour, publish_weekday,
                content_length, word_count, image_count, video_count,
                file_path, archived_date, file_size_bytes, is_complete
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                author_id, url, url_hash, title, publish_date,
                publish_year, publish_month, publish_hour, publish_weekday,
                content_length, word_count, image_count, video_count,
                file_path, archived_date, file_size_bytes, is_complete
            )
        )
        conn.commit()

        return cls.get_by_id(cursor.lastrowid)

    @staticmethod
    def exists(url: str) -> bool:
        """检查帖子是否已存在"""
        post = Post.get_by_url(url)
        return post is not None

    def update(self, **kwargs):
        """更新帖子信息"""
        if self.id is None:
            raise ValueError("无法更新未保存的帖子")

        db = self._get_db()
        conn = db.get_connection()

        # 构建更新语句
        update_fields = []
        values = []

        for field, value in kwargs.items():
            update_fields.append(f"{field} = ?")
            values.append(value)

        if not update_fields:
            return

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(self.id)

        sql = f"UPDATE posts SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(sql, values)
        conn.commit()

        # 重新加载对象
        updated = self.get_by_id(self.id)
        if updated:
            self.__dict__.update(updated.__dict__)

    def delete(self):
        """删除帖子（级联删除相关媒体）"""
        if self.id is None:
            raise ValueError("无法删除未保存的帖子")

        db = self._get_db()
        conn = db.get_connection()

        conn.execute("DELETE FROM posts WHERE id = ?", (self.id,))
        conn.commit()

        self.id = None

    def get_media(self) -> List['Media']:
        """获取该帖子的所有媒体"""
        if self.id is None:
            return []
        return Media.get_by_post(self.id)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'author_id': self.author_id,
            'url': self.url,
            'url_hash': self.url_hash,
            'title': self.title,
            'publish_date': self.publish_date,
            'publish_year': self.publish_year,
            'publish_month': self.publish_month,
            'publish_hour': self.publish_hour,
            'publish_weekday': self.publish_weekday,
            'content_length': self.content_length,
            'word_count': self.word_count,
            'image_count': self.image_count,
            'video_count': self.video_count,
            'file_path': self.file_path,
            'archived_date': self.archived_date,
            'file_size_bytes': self.file_size_bytes,
            'is_complete': self.is_complete,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


# =============================================================================
# Media 模型
# =============================================================================

@dataclass
class Media:
    """
    媒体模型

    属性:
        id: 媒体 ID（主键）
        post_id: 帖子 ID（外键）
        type: 类型（'image' 或 'video'）
        url: 原始 URL
        file_name: 文件名
        file_path: 文件相对路径
        file_size_bytes: 文件大小
        width: 图片宽度
        height: 图片高度
        duration: 视频时长
        is_downloaded: 是否已下载
        download_date: 下载日期
        created_at: 记录创建时间
    """

    id: Optional[int] = None
    post_id: int = 0
    type: str = ""
    url: str = ""
    file_name: str = ""
    file_path: str = ""
    file_size_bytes: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    is_downloaded: bool = True
    download_date: Optional[str] = None
    created_at: Optional[str] = None

    # EXIF 元数据字段（Phase 4）
    exif_make: Optional[str] = None
    exif_model: Optional[str] = None
    exif_datetime: Optional[str] = None
    exif_iso: Optional[int] = None
    exif_aperture: Optional[float] = None
    exif_shutter_speed: Optional[str] = None
    exif_focal_length: Optional[float] = None
    exif_gps_lat: Optional[float] = None
    exif_gps_lng: Optional[float] = None
    exif_location: Optional[str] = None

    _db: Optional[DatabaseConnection] = field(default=None, init=False, repr=False)

    @classmethod
    def _get_db(cls) -> DatabaseConnection:
        """获取数据库连接"""
        if cls._db is None:
            from .connection import get_default_connection
            cls._db = get_default_connection()
        return cls._db

    @classmethod
    def from_row(cls, row) -> 'Media':
        """从数据库行创建 Media 对象"""
        if row is None:
            return None

        # EXIF 字段（使用 try-except 处理可能不存在的列）
        def safe_get(key):
            try:
                return row[key]
            except (KeyError, IndexError):
                return None

        return cls(
            id=row['id'],
            post_id=row['post_id'],
            type=row['type'],
            url=row['url'],
            file_name=row['file_name'],
            file_path=row['file_path'],
            file_size_bytes=row['file_size_bytes'],
            width=row['width'],
            height=row['height'],
            duration=row['duration'],
            is_downloaded=bool(row['is_downloaded']),
            download_date=row['download_date'],
            created_at=row['created_at'],
            # EXIF 字段
            exif_make=safe_get('exif_make'),
            exif_model=safe_get('exif_model'),
            exif_datetime=safe_get('exif_datetime'),
            exif_iso=safe_get('exif_iso'),
            exif_aperture=safe_get('exif_aperture'),
            exif_shutter_speed=safe_get('exif_shutter_speed'),
            exif_focal_length=safe_get('exif_focal_length'),
            exif_gps_lat=safe_get('exif_gps_lat'),
            exif_gps_lng=safe_get('exif_gps_lng'),
            exif_location=safe_get('exif_location')
        )

    @classmethod
    def get_by_id(cls, media_id: int) -> Optional['Media']:
        """根据 ID 获取媒体"""
        db = cls._get_db()
        conn = db.get_connection()

        cursor = conn.execute("SELECT * FROM media WHERE id = ?", (media_id,))
        row = cursor.fetchone()
        return cls.from_row(row)

    @classmethod
    def get_by_post(cls, post_id: int, media_type: Optional[str] = None) -> List['Media']:
        """
        获取指定帖子的所有媒体

        Args:
            post_id: 帖子 ID
            media_type: 媒体类型过滤（'image' 或 'video'）

        Returns:
            Media 对象列表
        """
        db = cls._get_db()
        conn = db.get_connection()

        if media_type:
            cursor = conn.execute(
                "SELECT * FROM media WHERE post_id = ? AND type = ? ORDER BY file_name",
                (post_id, media_type)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM media WHERE post_id = ? ORDER BY file_name",
                (post_id,)
            )

        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def create(
        cls,
        post_id: int,
        type: str,
        url: str,
        file_name: str,
        file_path: str,
        file_size_bytes: int = 0,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[int] = None,
        is_downloaded: bool = True,
        download_date: Optional[str] = None
    ) -> 'Media':
        """
        创建新媒体记录

        Args:
            post_id: 帖子 ID
            type: 类型（'image' 或 'video'）
            url: 原始 URL
            file_name: 文件名
            file_path: 文件相对路径
            file_size_bytes: 文件大小
            width: 图片宽度
            height: 图片高度
            duration: 视频时长
            is_downloaded: 是否已下载
            download_date: 下载日期

        Returns:
            Media 对象
        """
        db = cls._get_db()
        conn = db.get_connection()

        cursor = conn.execute(
            """
            INSERT INTO media (
                post_id, type, url, file_name, file_path, file_size_bytes,
                width, height, duration, is_downloaded, download_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post_id, type, url, file_name, file_path, file_size_bytes,
                width, height, duration, is_downloaded, download_date
            )
        )
        conn.commit()

        return cls.get_by_id(cursor.lastrowid)

    def update(self, **kwargs):
        """更新媒体信息"""
        if self.id is None:
            raise ValueError("无法更新未保存的媒体")

        db = self._get_db()
        conn = db.get_connection()

        update_fields = []
        values = []

        for field, value in kwargs.items():
            update_fields.append(f"{field} = ?")
            values.append(value)

        if not update_fields:
            return

        values.append(self.id)
        sql = f"UPDATE media SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(sql, values)
        conn.commit()

        # 重新加载对象
        updated = self.get_by_id(self.id)
        if updated:
            self.__dict__.update(updated.__dict__)

    def delete(self):
        """删除媒体记录"""
        if self.id is None:
            raise ValueError("无法删除未保存的媒体")

        db = self._get_db()
        conn = db.get_connection()

        conn.execute("DELETE FROM media WHERE id = ?", (self.id,))
        conn.commit()

        self.id = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'type': self.type,
            'url': self.url,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size_bytes': self.file_size_bytes,
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'is_downloaded': self.is_downloaded,
            'download_date': self.download_date,
            'created_at': self.created_at
        }
