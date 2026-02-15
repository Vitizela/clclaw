"""
数据同步工具模块

负责在归档、删除、配置变更等操作时同步更新数据库。

集成点:
- archiver.py: 归档完成后调用 sync_archived_post()
- main_menu.py: 取消关注作者后调用 sync_delete_author()
- config_manager.py: 配置变更后调用 sync_config_to_db()
"""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import hashlib
import logging

from .connection import DatabaseConnection
from .models import Author, Post, Media

# 延迟导入 ExifAnalyzer（避免循环依赖）
_exif_analyzer = None

def _get_exif_analyzer():
    """获取 EXIF 分析器实例（单例模式）"""
    global _exif_analyzer
    if _exif_analyzer is None:
        try:
            from ..analysis import ExifAnalyzer
            _exif_analyzer = ExifAnalyzer()
        except ImportError:
            logging.warning("ExifAnalyzer 不可用，EXIF 提取功能将被禁用")
            _exif_analyzer = False
    return _exif_analyzer if _exif_analyzer is not False else None


def _get_db() -> DatabaseConnection:
    """获取数据库连接"""
    from .connection import get_default_connection
    return get_default_connection()


def _calculate_url_hash(url: str) -> str:
    """计算 URL 的 hash"""
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:8]


def _get_directory_size(path: Path) -> int:
    """递归计算目录大小"""
    total_size = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                try:
                    total_size += entry.stat().st_size
                except (OSError, PermissionError):
                    pass
    except Exception:
        pass
    return total_size


# =============================================================================
# 核心同步函数
# =============================================================================

def sync_archived_post(
    author_name: str,
    post_url: str,
    post_dir: Path,
    metadata: Dict,
    db: Optional[DatabaseConnection] = None
) -> bool:
    """
    归档完成后调用，将帖子信息写入数据库

    Args:
        author_name: 作者名
        post_url: 帖子 URL
        post_dir: 帖子目录路径
        metadata: 帖子元数据（由 archiver 提供）
            {
                'title': '帖子标题',
                'publish_date': '2026-02-10 15:30:00',
                'image_count': 5,
                'video_count': 2,
                'images': ['photo/img_1.jpg', ...],
                'videos': ['video/video_1.mp4', ...],
                'content_length': 1000,
                'word_count': 500,
                'file_size_bytes': 5000000
            }
        db: 数据库连接（可选）

    Returns:
        bool: 同步是否成功
    """
    try:
        # 获取数据库连接
        if db is None:
            db = _get_db()

        # 检查数据库是否已初始化
        if not db.is_initialized():
            db.initialize_database()

        # 设置模型使用的数据库
        Author._db = db
        Post._db = db
        Media._db = db

        # 获取或创建作者
        author = Author.get_by_name(author_name)
        if author is None:
            # 作者不存在，创建新作者
            author = Author.create(
                name=author_name,
                added_date=datetime.now().strftime("%Y-%m-%d"),
                url=f"https://t66y.com/@{author_name}"
            )

        # 准备归档日期（Media 创建时需要）
        archived_date = datetime.now().strftime("%Y-%m-%d")

        # 检查帖子是否已存在
        if Post.exists(post_url):
            # 帖子已存在，更新元数据
            post = Post.get_by_url(post_url)
            post.update(
                title=metadata.get('title', post.title),
                image_count=metadata.get('image_count', post.image_count),
                video_count=metadata.get('video_count', post.video_count),
                content_length=metadata.get('content_length', post.content_length),
                word_count=metadata.get('word_count', post.word_count),
                file_size_bytes=metadata.get('file_size_bytes', post.file_size_bytes),
                is_complete=True
            )
            # 注意：不要直接返回，继续执行 Media 同步
        else:
            # 创建新帖子
            url_hash = _calculate_url_hash(post_url)

            post = Post.create(
                author_id=author.id,
                url=post_url,
                url_hash=url_hash,
                title=metadata.get('title', '未知标题'),
                file_path=str(post_dir),
                archived_date=archived_date,
                publish_date=metadata.get('publish_date'),
                image_count=metadata.get('image_count', 0),
                video_count=metadata.get('video_count', 0),
                content_length=metadata.get('content_length', 0),
                word_count=metadata.get('word_count', 0),
                file_size_bytes=metadata.get('file_size_bytes', 0),
                is_complete=True
            )

        # 同步媒体文件
        exif_analyzer = _get_exif_analyzer()

        for img_path in metadata.get('images', []):
            img_full_path = post_dir / img_path
            img_size = img_full_path.stat().st_size if img_full_path.exists() else 0

            # 提取 EXIF 数据
            exif_data = {}
            if exif_analyzer and img_full_path.exists():
                try:
                    exif_data = exif_analyzer.extract_exif(str(img_full_path))

                    # 如果有 GPS 信息，尝试反查地理位置
                    if 'gps_lat' in exif_data and 'gps_lng' in exif_data:
                        location = exif_analyzer.reverse_geocode(
                            exif_data['gps_lat'],
                            exif_data['gps_lng']
                        )
                        if location:
                            exif_data['location'] = location
                except Exception as e:
                    logging.debug(f"提取 EXIF 失败: {img_full_path.name} - {e}")

            Media.create(
                post_id=post.id,
                type='image',
                url=metadata.get('image_urls', {}).get(img_path, f"file://{img_full_path}"),
                file_name=img_full_path.name,
                file_path=str(img_full_path),
                file_size_bytes=img_size,
                download_date=archived_date,
                # EXIF 数据
                exif_make=exif_data.get('make'),
                exif_model=exif_data.get('model'),
                exif_datetime=exif_data.get('datetime'),
                exif_iso=exif_data.get('iso'),
                exif_aperture=exif_data.get('aperture'),
                exif_shutter_speed=exif_data.get('shutter_speed'),
                exif_focal_length=exif_data.get('focal_length'),
                exif_gps_lat=exif_data.get('gps_lat'),
                exif_gps_lng=exif_data.get('gps_lng'),
                exif_location=exif_data.get('location')
            )

        for vid_path in metadata.get('videos', []):
            vid_full_path = post_dir / vid_path
            vid_size = vid_full_path.stat().st_size if vid_full_path.exists() else 0

            Media.create(
                post_id=post.id,
                type='video',
                url=metadata.get('video_urls', {}).get(vid_path, f"file://{vid_full_path}"),
                file_name=vid_full_path.name,
                file_path=str(vid_full_path),
                file_size_bytes=vid_size,
                download_date=archived_date
            )

        # 记录同步历史
        conn = db.get_connection()
        conn.execute(
            """
            INSERT INTO sync_history (
                sync_type, author_name, posts_added, status
            ) VALUES (?, ?, ?, ?)
            """,
            ('archive', author_name, 1, 'success')
        )
        conn.commit()

        return True

    except Exception as e:
        print(f"同步归档帖子失败: {e}")

        # 记录失败历史
        try:
            if db:
                conn = db.get_connection()
                conn.execute(
                    """
                    INSERT INTO sync_history (
                        sync_type, author_name, errors, status, error_message
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    ('archive', author_name, 1, 'failed', str(e))
                )
                conn.commit()
        except:
            pass

        return False


def sync_delete_author(
    author_name: str,
    db: Optional[DatabaseConnection] = None
) -> bool:
    """
    取消关注作者时调用，删除数据库中的记录

    注意：不删除文件系统中的归档数据

    Args:
        author_name: 作者名
        db: 数据库连接（可选）

    Returns:
        bool: 同步是否成功
    """
    try:
        # 获取数据库连接
        if db is None:
            db = _get_db()

        if not db.is_initialized():
            return False

        # 设置模型使用的数据库
        Author._db = db

        # 获取作者
        author = Author.get_by_name(author_name)
        if author is None:
            return True  # 作者不存在，视为成功

        # 删除作者（级联删除帖子和媒体）
        author.delete()

        # 记录同步历史
        conn = db.get_connection()
        conn.execute(
            """
            INSERT INTO sync_history (
                sync_type, author_name, status
            ) VALUES (?, ?, ?)
            """,
            ('delete_author', author_name, 'success')
        )
        conn.commit()

        return True

    except Exception as e:
        print(f"同步删除作者失败: {e}")
        return False


def sync_config_to_db(
    config: Dict,
    db: Optional[DatabaseConnection] = None
) -> bool:
    """
    配置文件变更后同步到数据库

    同步内容:
    - 作者 tags 变更
    - 作者 notes 变更
    - 作者 URL 变更
    - 作者 forum_total_posts 变更

    Args:
        config: 配置字典（python/config.yaml 的内容）
        db: 数据库连接（可选）

    Returns:
        bool: 同步是否成功
    """
    try:
        # 获取数据库连接
        if db is None:
            db = _get_db()

        if not db.is_initialized():
            return False

        # 设置模型使用的数据库
        Author._db = db

        # 遍历配置中的所有作者
        for author_config in config.get('followed_authors', []):
            author_name = author_config['name']

            # 获取数据库中的作者
            author = Author.get_by_name(author_name)

            if author is None:
                # 数据库中没有，创建新作者
                Author.create(
                    name=author_name,
                    added_date=author_config.get('added_date', datetime.now().strftime("%Y-%m-%d")),
                    url=author_config.get('url'),
                    forum_total_posts=author_config.get('forum_total_posts', 0),
                    tags=author_config.get('tags'),
                    notes=author_config.get('notes')
                )
            else:
                # 更新作者信息
                update_fields = {}

                # URL
                if author_config.get('url') and author_config['url'] != author.url:
                    update_fields['url'] = author_config['url']

                # forum_total_posts (只增不减)
                new_forum_total = author_config.get('forum_total_posts', 0)
                if new_forum_total > author.forum_total_posts:
                    update_fields['forum_total_posts'] = new_forum_total

                # tags
                new_tags = author_config.get('tags')
                if new_tags != author.tags:
                    update_fields['tags'] = new_tags

                # notes
                new_notes = author_config.get('notes')
                if new_notes != author.notes:
                    update_fields['notes'] = new_notes

                # 执行更新
                if update_fields:
                    author.update(**update_fields)

        return True

    except Exception as e:
        print(f"同步配置到数据库失败: {e}")
        return False


# =============================================================================
# 批量同步
# =============================================================================

def sync_all_from_filesystem(
    archive_path: str,
    config: Dict,
    db: Optional[DatabaseConnection] = None
) -> Dict:
    """
    从文件系统全量同步到数据库

    这是 migrate.import_all_data() 的包装，用于统一接口

    Args:
        archive_path: 归档目录路径
        config: 配置字典
        db: 数据库连接（可选）

    Returns:
        同步结果统计
    """
    from .migrate import import_all_data

    if db is None:
        db = _get_db()

    return import_all_data(
        archive_path=archive_path,
        config=config,
        db=db,
        force_rebuild=False,
        show_progress=True
    )


def sync_author_from_filesystem(
    author_name: str,
    archive_path: str,
    config: Dict,
    db: Optional[DatabaseConnection] = None
) -> Dict:
    """
    从文件系统同步单个作者的数据

    Args:
        author_name: 作者名
        archive_path: 归档目录路径
        config: 配置字典
        db: 数据库连接（可选）

    Returns:
        同步结果统计
    """
    from .migrate import import_author_data

    if db is None:
        db = _get_db()

    return import_author_data(
        author_name=author_name,
        archive_path=archive_path,
        config=config,
        db=db,
        show_progress=True
    )


# =============================================================================
# 工具函数
# =============================================================================

def is_database_enabled() -> bool:
    """
    检查数据库功能是否启用

    Returns:
        bool: 数据库是否启用
    """
    try:
        db = _get_db()
        return db.is_initialized()
    except:
        return False


def enable_database() -> bool:
    """
    启用数据库功能

    Returns:
        bool: 启用是否成功
    """
    try:
        db = _get_db()
        return db.initialize_database()
    except Exception as e:
        print(f"启用数据库失败: {e}")
        return False
