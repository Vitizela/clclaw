"""
数据迁移工具

负责从文件系统扫描历史归档数据并导入到数据库。

主要功能:
- extract_post_metadata(): 从帖子目录提取元数据
- import_all_data(): 全量导入所有历史数据
- import_author_data(): 导入单个作者的数据
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # 简单的进度条替代
    class tqdm:
        def __init__(self, iterable=None, total=None, desc=None, **kwargs):
            self.iterable = iterable
            self.total = total
            self.desc = desc
            self.n = 0

        def __iter__(self):
            for item in self.iterable:
                yield item
                self.n += 1

        def update(self, n=1):
            self.n += n

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

from .connection import DatabaseConnection
from .models import Author, Post, Media


# =============================================================================
# 辅助函数
# =============================================================================

def _get_directory_size(path: Path) -> int:
    """
    递归计算目录大小

    Args:
        path: 目录路径

    Returns:
        总大小（字节）
    """
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


def _calculate_url_hash(url: str) -> str:
    """
    计算 URL 的 hash（与 archived_posts.json 保持一致）

    Args:
        url: 帖子 URL

    Returns:
        8 位 MD5 hash
    """
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:8]


def _parse_html_metadata(html_path: Path) -> Dict:
    """
    从 content.html 解析元数据

    Args:
        html_path: content.html 文件路径

    Returns:
        包含元数据的字典
    """
    metadata = {
        'title': None,
        'publish_date': None,
        'content_length': 0,
        'word_count': 0
    }

    try:
        if not html_path.exists():
            return metadata

        # 读取 HTML 内容
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

        metadata['content_length'] = len(html_content)

        # 简单的字数统计（去除 HTML 标签后）
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text).strip()
        metadata['word_count'] = len(text)

        # 尝试从 HTML 中提取标题
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()

        # 尝试从 HTML 中提取发布时间
        # 常见格式: <span class="date">2026-02-10 15:30:00</span>
        # 或: <meta name="publish_date" content="2026-02-10 15:30:00">
        date_patterns = [
            r'<span[^>]*class=["\']date["\'][^>]*>(.*?)</span>',
            r'<meta[^>]*name=["\']publish_date["\'][^>]*content=["\']([^"\']+)["\']',
            r'<time[^>]*datetime=["\']([^"\']+)["\']',
            r'发布时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
        ]

        for pattern in date_patterns:
            date_match = re.search(pattern, html_content, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1).strip()
                # 尝试解析日期
                try:
                    # 支持多种日期格式
                    for fmt in [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d %H:%M",
                        "%Y/%m/%d %H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S"
                    ]:
                        try:
                            dt = datetime.strptime(date_str, fmt)
                            metadata['publish_date'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass

                if metadata['publish_date']:
                    break

    except Exception as e:
        print(f"解析 HTML 元数据失败 ({html_path}): {e}")

    return metadata


def _scan_media_files(post_dir: Path) -> Tuple[List[str], List[str]]:
    """
    扫描帖子目录中的图片和视频文件

    Args:
        post_dir: 帖子目录路径

    Returns:
        (图片文件列表, 视频文件列表)
    """
    images = []
    videos = []

    # 扫描 photo 目录
    photo_dir = post_dir / 'photo'
    if photo_dir.exists() and photo_dir.is_dir():
        for img_file in photo_dir.iterdir():
            if img_file.is_file():
                images.append(str(img_file.relative_to(post_dir)))

    # 扫描 video 目录
    video_dir = post_dir / 'video'
    if video_dir.exists() and video_dir.is_dir():
        for vid_file in video_dir.iterdir():
            if vid_file.is_file():
                videos.append(str(vid_file.relative_to(post_dir)))

    return sorted(images), sorted(videos)


# =============================================================================
# 核心函数
# =============================================================================

def extract_post_metadata(post_dir: Path, author_name: str = None) -> Optional[Dict]:
    """
    从帖子目录提取元数据

    目录结构:
        论坛存档/作者名/YYYY/MM/帖子标题/
            ├── content.html
            ├── photo/
            │   ├── img_1.jpg
            │   └── img_2.jpg
            └── video/
                └── video_1.mp4

    Args:
        post_dir: 帖子目录路径
        author_name: 作者名（如果从路径无法提取，可手动指定）

    Returns:
        包含元数据的字典，失败返回 None
    """
    try:
        if not post_dir.exists() or not post_dir.is_dir():
            return None

        # 从路径提取信息
        # 路径格式: 论坛存档/作者名/YYYY/MM/帖子标题/
        parts = post_dir.parts

        # 提取作者名（倒数第 4 层）
        if author_name is None and len(parts) >= 4:
            author_name = parts[-4]

        # 提取年份和月份
        year = None
        month = None
        if len(parts) >= 3:
            try:
                year = int(parts[-3])
                month = int(parts[-2])
            except ValueError:
                pass

        # 提取标题（目录名）
        title = post_dir.name

        # 解析 HTML 元数据
        html_path = post_dir / 'content.html'
        html_metadata = _parse_html_metadata(html_path)

        # 使用 HTML 中的标题（如果有）
        if html_metadata['title']:
            title = html_metadata['title']

        # 扫描媒体文件
        images, videos = _scan_media_files(post_dir)

        # 计算目录大小
        file_size_bytes = _get_directory_size(post_dir)

        # 获取归档日期（使用目录的修改时间）
        archived_date = datetime.fromtimestamp(
            post_dir.stat().st_mtime
        ).strftime("%Y-%m-%d")

        # 发布日期（优先使用 HTML 中的，否则使用目录修改时间）
        publish_date = html_metadata['publish_date']
        if not publish_date and year and month:
            # 使用目录的修改时间作为替代
            mod_time = datetime.fromtimestamp(post_dir.stat().st_mtime)
            publish_date = mod_time.strftime("%Y-%m-%d %H:%M:%S")

        # 构建元数据字典
        metadata = {
            'author_name': author_name,
            'title': title,
            'publish_date': publish_date,
            'publish_year': year,
            'publish_month': month,
            'content_length': html_metadata['content_length'],
            'word_count': html_metadata['word_count'],
            'image_count': len(images),
            'video_count': len(videos),
            'images': images,
            'videos': videos,
            'file_size_bytes': file_size_bytes,
            'archived_date': archived_date,
            'file_path': str(post_dir),
            'has_content': html_path.exists()
        }

        return metadata

    except Exception as e:
        print(f"提取元数据失败 ({post_dir}): {e}")
        return None


def import_author_data(
    author_name: str,
    archive_path: str,
    config: Dict,
    db: DatabaseConnection,
    show_progress: bool = True
) -> Dict:
    """
    导入单个作者的数据

    Args:
        author_name: 作者名
        archive_path: 归档目录路径
        config: 配置字典
        db: 数据库连接
        show_progress: 是否显示进度条

    Returns:
        导入结果统计
    """
    result = {
        'author_name': author_name,
        'posts_added': 0,
        'posts_skipped': 0,
        'media_added': 0,
        'errors': []
    }

    try:
        # 设置模型使用的数据库
        Author._db = db
        Post._db = db
        Media._db = db

        # 获取或创建作者
        author = Author.get_by_name(author_name)

        if author is None:
            # 从 config 中查找作者信息
            author_config = next(
                (a for a in config.get('followed_authors', []) if a['name'] == author_name),
                None
            )

            if author_config:
                author = Author.create(
                    name=author_name,
                    added_date=author_config.get('added_date', datetime.now().strftime("%Y-%m-%d")),
                    url=author_config.get('url'),
                    forum_total_posts=author_config.get('forum_total_posts', 0),
                    tags=author_config.get('tags'),
                    notes=author_config.get('notes')
                )
            else:
                author = Author.create(
                    name=author_name,
                    added_date=datetime.now().strftime("%Y-%m-%d")
                )

        # 扫描作者目录
        author_dir = Path(archive_path) / author_name
        if not author_dir.exists():
            return result

        # 收集所有帖子目录
        post_dirs = []
        for year_dir in author_dir.iterdir():
            if not year_dir.is_dir():
                continue
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                for post_dir in month_dir.iterdir():
                    if post_dir.is_dir():
                        post_dirs.append(post_dir)

        # 导入每篇帖子
        iterator = tqdm(post_dirs, desc=f"导入 {author_name}", disable=not show_progress)

        for post_dir in iterator:
            try:
                # 提取元数据
                metadata = extract_post_metadata(post_dir, author_name)
                if metadata is None:
                    result['errors'].append(f"无法提取元数据: {post_dir}")
                    continue

                # 生成伪 URL（因为我们可能没有原始 URL）
                # 使用文件路径作为唯一标识
                post_url = f"file://{metadata['file_path']}"
                url_hash = _calculate_url_hash(post_url)

                # 检查是否已存在
                if Post.exists(post_url):
                    result['posts_skipped'] += 1
                    continue

                # 创建帖子
                post = Post.create(
                    author_id=author.id,
                    url=post_url,
                    url_hash=url_hash,
                    title=metadata['title'],
                    file_path=metadata['file_path'],
                    archived_date=metadata['archived_date'],
                    publish_date=metadata['publish_date'],
                    image_count=metadata['image_count'],
                    video_count=metadata['video_count'],
                    content_length=metadata['content_length'],
                    word_count=metadata['word_count'],
                    file_size_bytes=metadata['file_size_bytes'],
                    is_complete=metadata['has_content']
                )

                result['posts_added'] += 1

                # 导入媒体文件
                for img_path in metadata['images']:
                    img_full_path = post_dir / img_path
                    img_size = img_full_path.stat().st_size if img_full_path.exists() else 0

                    Media.create(
                        post_id=post.id,
                        type='image',
                        url=f"file://{img_full_path}",
                        file_name=img_full_path.name,
                        file_path=str(img_full_path),
                        file_size_bytes=img_size,
                        download_date=metadata['archived_date']
                    )
                    result['media_added'] += 1

                for vid_path in metadata['videos']:
                    vid_full_path = post_dir / vid_path
                    vid_size = vid_full_path.stat().st_size if vid_full_path.exists() else 0

                    Media.create(
                        post_id=post.id,
                        type='video',
                        url=f"file://{vid_full_path}",
                        file_name=vid_full_path.name,
                        file_path=str(vid_full_path),
                        file_size_bytes=vid_size,
                        download_date=metadata['archived_date']
                    )
                    result['media_added'] += 1

            except Exception as e:
                error_msg = f"导入帖子失败 ({post_dir}): {e}"
                result['errors'].append(error_msg)
                print(error_msg)

    except Exception as e:
        error_msg = f"导入作者数据失败 ({author_name}): {e}"
        result['errors'].append(error_msg)
        print(error_msg)

    return result


def import_all_data(
    archive_path: str,
    config: Dict,
    db: Optional[DatabaseConnection] = None,
    force_rebuild: bool = False,
    show_progress: bool = True
) -> Dict:
    """
    导入所有历史数据

    Args:
        archive_path: 归档目录路径
        config: 配置字典（python/config.yaml 的内容）
        db: 数据库连接（可选，默认使用默认连接）
        force_rebuild: 是否强制重建（清空数据库重新导入）
        show_progress: 是否显示进度条

    Returns:
        导入结果统计
    """
    start_time = time.time()

    # 获取数据库连接
    if db is None:
        from .connection import get_default_connection
        db = get_default_connection()

    # 初始化数据库
    if not db.is_initialized():
        db.initialize_database()

    # 设置模型使用的数据库
    Author._db = db
    Post._db = db
    Media._db = db

    conn = db.get_connection()

    # 强制重建：清空数据库
    if force_rebuild:
        print("清空数据库...")
        conn.execute("DELETE FROM media")
        conn.execute("DELETE FROM posts")
        conn.execute("DELETE FROM authors")
        conn.execute("DELETE FROM sync_history")
        conn.commit()

    # 收集结果
    total_result = {
        'authors_added': 0,
        'posts_added': 0,
        'posts_skipped': 0,
        'media_added': 0,
        'errors': [],
        'duration_seconds': 0
    }

    # 获取所有作者
    archive_dir = Path(archive_path)
    if not archive_dir.exists():
        print(f"归档目录不存在: {archive_path}")
        return total_result

    # 扫描所有作者目录
    author_dirs = [d for d in archive_dir.iterdir() if d.is_dir()]

    if show_progress:
        print(f"\n开始导入历史数据...")
        print(f"归档路径: {archive_path}")
        print(f"作者数量: {len(author_dirs)}")
        print(f"{'=' * 60}\n")

    # 导入每个作者
    for author_dir in author_dirs:
        author_name = author_dir.name

        print(f"\n正在导入作者: {author_name}")

        result = import_author_data(
            author_name=author_name,
            archive_path=archive_path,
            config=config,
            db=db,
            show_progress=show_progress
        )

        total_result['authors_added'] += 1
        total_result['posts_added'] += result['posts_added']
        total_result['posts_skipped'] += result['posts_skipped']
        total_result['media_added'] += result['media_added']
        total_result['errors'].extend(result['errors'])

        print(f"  ✓ 新增帖子: {result['posts_added']}, 跳过: {result['posts_skipped']}, 媒体: {result['media_added']}")

    # 记录同步历史
    duration = time.time() - start_time
    total_result['duration_seconds'] = round(duration, 2)

    conn.execute(
        """
        INSERT INTO sync_history (
            sync_type, posts_added, errors, duration_seconds, status
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            'import',
            total_result['posts_added'],
            len(total_result['errors']),
            duration,
            'success' if len(total_result['errors']) == 0 else 'partial'
        )
    )
    conn.commit()

    # 打印总结
    if show_progress:
        print(f"\n{'=' * 60}")
        print(f"✓ 导入完成!")
        print(f"  - 作者数: {total_result['authors_added']}")
        print(f"  - 帖子数: {total_result['posts_added']} (跳过: {total_result['posts_skipped']})")
        print(f"  - 媒体数: {total_result['media_added']}")
        print(f"  - 用时: {duration:.2f} 秒")
        if total_result['errors']:
            print(f"  - 错误数: {len(total_result['errors'])}")

    return total_result
