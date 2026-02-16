"""
查询辅助函数模块

提供高级查询功能，用于统计、聚合、排行等操作。
为菜单系统提供数据接口。
"""

from typing import Dict, List, Optional
from .connection import DatabaseConnection
from .models import Author, Post, Media


def _get_db() -> DatabaseConnection:
    """获取数据库连接"""
    from .connection import get_default_connection
    return get_default_connection()


# =============================================================================
# 全局统计
# =============================================================================

def get_global_stats(db: Optional[DatabaseConnection] = None) -> dict:
    """
    获取全局统计信息

    Returns:
        {
            'total_authors': 7,
            'total_posts': 245,
            'total_images': 1245,
            'total_videos': 67,
            'total_size_bytes': 2466988032,
            'total_size_mb': 2352.5,
            'total_size_gb': 2.3,
            'latest_update': '2026-02-13 16:30:00',
            'earliest_post': '2025-01-15 10:30:00',
            'avg_posts_per_author': 35.0,
            'avg_images_per_post': 5.1,
            'avg_videos_per_post': 0.3
        }
    """
    if db is None:
        db = _get_db()
    conn = db.get_connection()

    try:
        # 基础统计
        cursor = conn.execute("""
            SELECT
                COUNT(DISTINCT id) as total_authors
            FROM authors
        """)
        row = cursor.fetchone()
        total_authors = row[0] if row else 0

        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_posts,
                SUM(image_count) as total_images,
                SUM(video_count) as total_videos,
                SUM(file_size_bytes) as total_size_bytes,
                MAX(archived_date) as latest_update,
                MIN(publish_date) as earliest_post
            FROM posts
        """)
        row = cursor.fetchone()

        total_posts = row[0] if row and row[0] else 0
        total_images = row[1] if row and row[1] else 0
        total_videos = row[2] if row and row[2] else 0
        total_size_bytes = row[3] if row and row[3] else 0
        latest_update = row[4] if row and row[4] else None
        earliest_post = row[5] if row and row[5] else None

        # 计算平均值
        avg_posts_per_author = total_posts / total_authors if total_authors > 0 else 0
        avg_images_per_post = total_images / total_posts if total_posts > 0 else 0
        avg_videos_per_post = total_videos / total_posts if total_posts > 0 else 0

        return {
            'total_authors': total_authors,
            'total_posts': total_posts,
            'total_images': total_images,
            'total_videos': total_videos,
            'total_size_bytes': total_size_bytes,
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
            'total_size_gb': round(total_size_bytes / (1024 * 1024 * 1024), 2),
            'latest_update': latest_update,
            'earliest_post': earliest_post,
            'avg_posts_per_author': round(avg_posts_per_author, 1),
            'avg_images_per_post': round(avg_images_per_post, 1),
            'avg_videos_per_post': round(avg_videos_per_post, 1)
        }

    except Exception as e:
        print(f"获取全局统计失败: {e}")
        return {
            'total_authors': 0,
            'total_posts': 0,
            'total_images': 0,
            'total_videos': 0,
            'total_size_bytes': 0,
            'total_size_mb': 0,
            'total_size_gb': 0,
            'latest_update': None,
            'earliest_post': None,
            'avg_posts_per_author': 0,
            'avg_images_per_post': 0,
            'avg_videos_per_post': 0
        }


# =============================================================================
# 作者排行榜
# =============================================================================

def get_author_ranking(
    order_by: str = 'posts',
    limit: int = 10,
    offset: int = 0,
    db: Optional['DatabaseConnection'] = None
) -> List[dict]:
    """
    获取作者排行榜

    Args:
        order_by: 排序字段 ('posts', 'images', 'videos', 'size')
        limit: 返回数量
        offset: 偏移量（用于分页）

    Returns:
        [
            {
                'rank': 1,
                'name': '独醉笑清风',
                'post_count': 80,
                'image_count': 245,
                'video_count': 8,
                'total_size_mb': 856.3,
                'avg_images_per_post': 3.1,
                'avg_videos_per_post': 0.1,
                'first_post_date': '2025-01-15',
                'latest_post_date': '2026-02-10'
            },
            ...
        ]
    """
    if db is None:
        db = _get_db()
    conn = db.get_connection()

    # 映射排序字段
    order_by_map = {
        'posts': 'post_count',
        'images': 'image_count',
        'videos': 'video_count',
        'size': 'total_size_bytes'
    }

    order_field = order_by_map.get(order_by, 'post_count')

    try:
        cursor = conn.execute(f"""
            SELECT
                name,
                post_count,
                image_count,
                video_count,
                total_size_bytes,
                avg_images_per_post,
                avg_videos_per_post,
                first_post_date,
                latest_post_date,
                forum_total_posts
            FROM v_author_stats
            ORDER BY {order_field} DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        ranking = []
        for rank, row in enumerate(cursor.fetchall(), start=offset + 1):
            ranking.append({
                'rank': rank,
                'name': row[0],
                'post_count': row[1] or 0,
                'image_count': row[2] or 0,
                'video_count': row[3] or 0,
                'total_size_bytes': row[4] or 0,
                'total_size_mb': round((row[4] or 0) / (1024 * 1024), 2),
                'avg_images_per_post': round(row[5] or 0, 1),
                'avg_videos_per_post': round(row[6] or 0, 1),
                'first_post_date': row[7],
                'latest_post_date': row[8],
                'forum_total_posts': row[9] or 0
            })

        return ranking

    except Exception as e:
        print(f"获取作者排行榜失败: {e}")
        return []


# =============================================================================
# 月度统计
# =============================================================================

def get_monthly_stats(
    author_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
    db: Optional['DatabaseConnection'] = None
) -> List[dict]:
    """
    获取月度发帖统计

    Args:
        author_name: 作者名（可选，不指定则统计所有作者）
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
        limit: 限制返回数量

    Returns:
        [
            {
                'author_name': '独醉笑清风',  # 如果指定作者则全部相同
                'year': 2026,
                'month': 2,
                'post_count': 15,
                'image_count': 45,
                'video_count': 3,
                'total_size_mb': 125.5
            },
            ...
        ]
    """
    if db is None:
        db = _get_db()
    conn = db.get_connection()

    try:
        # 构建查询条件
        conditions = []
        params = []

        if author_name:
            conditions.append("author_name = ?")
            params.append(author_name)

        if start_date:
            conditions.append("(publish_year || '-' || printf('%02d', publish_month) || '-01') >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("(publish_year || '-' || printf('%02d', publish_month) || '-01') <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"""
            SELECT
                author_name,
                publish_year,
                publish_month,
                post_count,
                image_count,
                video_count,
                total_size_bytes
            FROM v_monthly_stats
            WHERE {where_clause}
            ORDER BY publish_year DESC, publish_month DESC
        """

        if limit:
            sql += f" LIMIT {limit}"

        cursor = conn.execute(sql, params)

        results = []
        for row in cursor.fetchall():
            results.append({
                'author_name': row[0],
                'year': row[1],
                'month': row[2],
                'post_count': row[3] or 0,
                'image_count': row[4] or 0,
                'video_count': row[5] or 0,
                'total_size_bytes': row[6] or 0,
                'total_size_mb': round((row[6] or 0) / (1024 * 1024), 2)
            })

        return results

    except Exception as e:
        print(f"获取月度统计失败: {e}")
        return []


# =============================================================================
# 时间分布统计
# =============================================================================

def get_hourly_distribution(author_name: Optional[str] = None, db: Optional['DatabaseConnection'] = None) -> dict:
    """
    获取发帖的小时分布（为 Phase 4 热力图准备）

    Args:
        author_name: 作者名（可选，不指定则统计所有作者）

    Returns:
        {
            0: 2,   # 凌晨 0 点发了 2 篇
            1: 0,
            2: 1,
            ...
            23: 5
        }
    """
    if db is None:
        db = _get_db()
    conn = db.get_connection()

    try:
        # 初始化 24 小时的分布（全部为 0）
        distribution = {hour: 0 for hour in range(24)}

        # 构建查询
        if author_name:
            cursor = conn.execute("""
                SELECT publish_hour, COUNT(*) as count
                FROM posts
                WHERE publish_hour IS NOT NULL
                  AND author_id = (SELECT id FROM authors WHERE name = ?)
                GROUP BY publish_hour
            """, (author_name,))
        else:
            cursor = conn.execute("""
                SELECT publish_hour, COUNT(*) as count
                FROM posts
                WHERE publish_hour IS NOT NULL
                GROUP BY publish_hour
            """)

        # 填充实际数据
        for row in cursor.fetchall():
            hour = row[0]
            count = row[1]
            if 0 <= hour <= 23:
                distribution[hour] = count

        return distribution

    except Exception as e:
        print(f"获取时间分布失败: {e}")
        return {hour: 0 for hour in range(24)}


def get_weekday_distribution(author_name: Optional[str] = None, db: Optional['DatabaseConnection'] = None) -> dict:
    """
    获取发帖的星期分布

    Args:
        author_name: 作者名（可选）

    Returns:
        {
            0: 15,  # 周一
            1: 20,  # 周二
            ...
            6: 10   # 周日
        }
    """
    if db is None:
        db = _get_db()
    conn = db.get_connection()

    try:
        distribution = {day: 0 for day in range(7)}

        if author_name:
            cursor = conn.execute("""
                SELECT publish_weekday, COUNT(*) as count
                FROM posts
                WHERE publish_weekday IS NOT NULL
                  AND author_id = (SELECT id FROM authors WHERE name = ?)
                GROUP BY publish_weekday
            """, (author_name,))
        else:
            cursor = conn.execute("""
                SELECT publish_weekday, COUNT(*) as count
                FROM posts
                WHERE publish_weekday IS NOT NULL
                GROUP BY publish_weekday
            """)

        for row in cursor.fetchall():
            weekday = row[0]
            count = row[1]
            if 0 <= weekday <= 6:
                distribution[weekday] = count

        return distribution

    except Exception as e:
        print(f"获取星期分布失败: {e}")
        return {day: 0 for day in range(7)}


# =============================================================================
# 作者详细统计
# =============================================================================

def get_author_detail_stats(author_name: str, db: Optional['DatabaseConnection'] = None) -> Optional[dict]:
    """
    获取作者的详细统计信息

    Args:
        author_name: 作者名

    Returns:
        {
            'basic_info': {...},      # 基本信息
            'archive_stats': {...},   # 归档统计
            'time_stats': {...},      # 时间统计
            'content_stats': {...}    # 内容统计
        }
    """
    if db is None:
        db = _get_db()
    conn = db.get_connection()

    # 设置模型使用的数据库
    Author._db = db

    try:
        # 获取作者
        author = Author.get_by_name(author_name)
        if author is None:
            return None

        # 基本信息
        basic_info = {
            'name': author.name,
            'added_date': author.added_date,
            'last_update': author.last_update,
            'url': author.url,
            'tags': author.tags,
            'notes': author.notes
        }

        # 归档统计
        stats = author.get_stats()
        archive_stats = {
            'total_posts': stats.get('post_count', 0),
            'total_images': stats.get('image_count', 0),
            'total_videos': stats.get('video_count', 0),
            'total_size_bytes': stats.get('total_size_bytes', 0),
            'total_size_mb': round((stats.get('total_size_bytes', 0)) / (1024 * 1024), 2),
            'forum_total_posts': author.forum_total_posts,
            'archive_progress': round(
                (stats.get('post_count', 0) / author.forum_total_posts * 100)
                if author.forum_total_posts > 0 else 0,
                1
            ),
            'avg_images_per_post': round(stats.get('avg_images_per_post', 0), 1),
            'avg_videos_per_post': round(stats.get('avg_videos_per_post', 0), 1),
            'avg_size_per_post_mb': round(stats.get('avg_size_per_post', 0) / (1024 * 1024), 2)
        }

        # 时间统计
        time_stats = {
            'first_post_date': stats.get('first_post_date'),
            'latest_post_date': stats.get('latest_post_date'),
            'active_days': None,
            'hourly_distribution': get_hourly_distribution(author_name, db),
            'weekday_distribution': get_weekday_distribution(author_name, db)
        }

        # 计算活跃天数
        if time_stats['first_post_date'] and time_stats['latest_post_date']:
            from datetime import datetime
            try:
                first = datetime.strptime(time_stats['first_post_date'], "%Y-%m-%d %H:%M:%S")
                latest = datetime.strptime(time_stats['latest_post_date'], "%Y-%m-%d %H:%M:%S")
                time_stats['active_days'] = (latest - first).days + 1
            except ValueError:
                pass

        # 内容统计
        cursor = conn.execute("""
            SELECT
                AVG(content_length) as avg_content_length,
                AVG(word_count) as avg_word_count,
                MAX(image_count) as max_images,
                MAX(video_count) as max_videos
            FROM posts
            WHERE author_id = ?
        """, (author.id,))

        row = cursor.fetchone()
        content_stats = {
            'avg_content_length': round(row[0] or 0, 0),
            'avg_word_count': round(row[1] or 0, 0),
            'max_images_per_post': row[2] or 0,
            'max_videos_per_post': row[3] or 0
        }

        return {
            'basic_info': basic_info,
            'archive_stats': archive_stats,
            'time_stats': time_stats,
            'content_stats': content_stats
        }

    except Exception as e:
        print(f"获取作者详细统计失败: {e}")
        return None


# =============================================================================
# 搜索功能
# =============================================================================

def search_posts(
    keyword: Optional[str] = None,
    author_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    has_images: Optional[bool] = None,
    has_videos: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Optional['DatabaseConnection'] = None
) -> List[dict]:
    """
    搜索帖子

    Args:
        keyword: 关键词（在标题中搜索）
        author_name: 作者名
        start_date: 开始日期
        end_date: 结束日期
        has_images: 是否有图片
        has_videos: 是否有视频
        limit: 限制返回数量
        offset: 偏移量

    Returns:
        帖子列表
    """
    if db is None:
        db = _get_db()
    conn = db.get_connection()

    try:
        conditions = []
        params = []

        if keyword:
            conditions.append("posts.title LIKE ?")
            params.append(f"%{keyword}%")

        if author_name:
            conditions.append("authors.name = ?")
            params.append(author_name)

        if start_date:
            conditions.append("posts.publish_date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("posts.publish_date <= ?")
            params.append(end_date)

        if has_images is not None:
            if has_images:
                conditions.append("posts.image_count > 0")
            else:
                conditions.append("posts.image_count = 0")

        if has_videos is not None:
            if has_videos:
                conditions.append("posts.video_count > 0")
            else:
                conditions.append("posts.video_count = 0")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"""
            SELECT
                posts.id,
                posts.title,
                authors.name as author_name,
                posts.publish_date,
                posts.image_count,
                posts.video_count,
                posts.file_path
            FROM posts
            JOIN authors ON posts.author_id = authors.id
            WHERE {where_clause}
            ORDER BY posts.publish_date DESC
            LIMIT ? OFFSET ?
        """

        params.extend([limit, offset])
        cursor = conn.execute(sql, params)

        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'author_name': row[2],
                'publish_date': row[3],
                'image_count': row[4],
                'video_count': row[5],
                'file_path': row[6]
            })

        return results

    except Exception as e:
        print(f"搜索帖子失败: {e}")
        return []


def get_camera_ranking(
    limit: int = 10,
    db: Optional['DatabaseConnection'] = None
) -> List[dict]:
    """
    查询相机使用排行（基于 v_camera_stats 视图）

    Args:
        limit: 返回前 N 个相机（默认 10）
        db: 数据库连接（可选）

    Returns:
        相机排行列表 [{'make': '...', 'model': '...', 'photo_count': N}, ...]
    """
    if db is None:
        db = _get_db()
    conn = db.get_connection()

    try:
        cursor = conn.execute("""
            SELECT make, model, photo_count
            FROM v_camera_stats
            ORDER BY photo_count DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        print(f"查询相机排行失败: {e}")
        return []


# =============================================================================
# 相机使用分析（Phase 4 Week 3）
# =============================================================================

def get_camera_usage_by_authors(
    camera_make: Optional[str] = None,
    camera_model: Optional[str] = None,
    author_name: Optional[str] = None,
    limit: int = 50,
    db: Optional['DatabaseConnection'] = None
) -> List[dict]:
    """
    查询相机被哪些作者使用

    Args:
        camera_make: 相机制造商（如 'vivo'），None 表示全部
        camera_model: 相机型号（如 'X Fold3 Pro'），None 表示全部
        author_name: 作者名称（用于反向查询），None 表示全部
        limit: 返回结果数量限制（默认 50）
        db: 数据库连接（可选）

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
                'avg_iso': 400.0,
                'avg_aperture': 2.2,
                'avg_focal_length': 50.0
            },
            ...
        ]
    """
    if db is None:
        db = _get_db()
    conn = db.get_connection()

    try:
        # 构建动态 WHERE 条件
        conditions = []
        params = []

        if camera_make:
            conditions.append("make = ?")
            params.append(camera_make)

        if camera_model:
            conditions.append("model = ?")
            params.append(camera_model)

        if author_name:
            conditions.append("author_name = ?")
            params.append(author_name)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 执行查询
        cursor = conn.execute(f"""
            SELECT
                camera_full,
                make,
                model,
                author_name,
                photo_count,
                post_count,
                first_use_date,
                last_use_date,
                avg_iso,
                avg_aperture,
                avg_focal_length
            FROM v_camera_author_usage
            WHERE {where_clause}
            ORDER BY camera_full, photo_count DESC
            LIMIT ?
        """, params + [limit])

        return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        print(f"查询相机作者使用失败: {e}")
        return []


def get_camera_usage_timeline(
    camera_make: str,
    camera_model: str,
    author_name: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Optional['DatabaseConnection'] = None
) -> List[dict]:
    """
    查询相机使用的时间线（按日期聚合）

    Args:
        camera_make: 相机制造商（必填）
        camera_model: 相机型号（必填）
        author_name: 作者名称（可选，用于过滤）
        year: 年份过滤（可选）
        month: 月份过滤（可选，1-12）
        db: 数据库连接（可选）

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

    try:
        # 构建动态 WHERE 条件
        conditions = ["make = ?", "model = ?"]
        params = [camera_make, camera_model]

        if author_name:
            conditions.append("authors LIKE ?")
            params.append(f"%{author_name}%")

        if year:
            conditions.append("year = ?")
            params.append(year)

        if month:
            conditions.append("month = ?")
            params.append(month)

        where_clause = " AND ".join(conditions)

        # 执行查询
        cursor = conn.execute(f"""
            SELECT
                date,
                year,
                month,
                photo_count,
                post_count,
                authors
            FROM v_camera_daily_usage
            WHERE {where_clause}
            ORDER BY date DESC
        """, params)

        return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        print(f"查询相机使用时间线失败: {e}")
        return []


def get_author_camera_usage(
    author_name: str,
    db: Optional['DatabaseConnection'] = None
) -> dict:
    """
    查询作者使用的所有相机型号

    Args:
        author_name: 作者名称
        db: 数据库连接（可选）

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

    try:
        # 查询作者的所有相机使用情况
        cursor = conn.execute("""
            SELECT
                camera_full,
                make,
                model,
                photo_count,
                post_count,
                first_use_date,
                last_use_date
            FROM v_camera_author_usage
            WHERE author_name = ?
            ORDER BY photo_count DESC
        """, (author_name,))

        cameras = []
        total_photos = 0

        for row in cursor.fetchall():
            row_dict = dict(row)
            cameras.append({
                'camera_full': row_dict['camera_full'],
                'make': row_dict['make'],
                'model': row_dict['model'],
                'photo_count': row_dict['photo_count'],
                'post_count': row_dict['post_count'],
                'first_use': row_dict['first_use_date'][:10] if row_dict['first_use_date'] else None,
                'last_use': row_dict['last_use_date'][:10] if row_dict['last_use_date'] else None
            })
            total_photos += row_dict['photo_count']

        # 计算使用百分比
        for camera in cameras:
            camera['usage_percent'] = round(
                camera['photo_count'] / total_photos * 100, 1
            ) if total_photos > 0 else 0.0

        return {
            'author_name': author_name,
            'total_cameras': len(cameras),
            'total_photos': total_photos,
            'cameras': cameras
        }

    except Exception as e:
        print(f"查询作者相机使用失败: {e}")
        return {
            'author_name': author_name,
            'total_cameras': 0,
            'total_photos': 0,
            'cameras': []
        }
