"""
数据完整性检查模块

负责检查数据库与文件系统的一致性，检测并修复数据错误。

功能:
- check_all(): 执行全面的数据一致性检查
- fix_statistics(): 修复统计字段
- check_orphaned_records(): 检测孤立记录
"""

from pathlib import Path
from typing import Dict, List, Optional
from .connection import DatabaseConnection
from .models import Author, Post, Media


def _get_db() -> DatabaseConnection:
    """获取数据库连接"""
    from .connection import get_default_connection
    return get_default_connection()


# =============================================================================
# 核心检查函数
# =============================================================================

def check_all(
    archive_path: str,
    db: Optional[DatabaseConnection] = None,
    fix: bool = False
) -> Dict:
    """
    执行全面的数据一致性检查

    检查项:
    1. 数据库中的帖子在文件系统中是否存在
    2. 文件系统中的帖子在数据库中是否存在
    3. 统计字段是否准确
    4. 外键关系是否完整

    Args:
        archive_path: 归档目录路径
        db: 数据库连接（可选）
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
    if db is None:
        db = _get_db()

    if not db.is_initialized():
        return {
            'total_checked': 0,
            'issues': [],
            'error': '数据库未初始化'
        }

    # 设置模型使用的数据库
    Author._db = db
    Post._db = db
    Media._db = db

    result = {
        'total_checked': 0,
        'issues': [],
        'fixed': 0
    }

    archive_dir = Path(archive_path)

    print("开始数据完整性检查...")

    # 检查 1: 数据库中的帖子文件是否存在
    print("\n[1/4] 检查数据库记录对应的文件...")
    all_posts = Post.get_all() if hasattr(Post, 'get_all') else []

    for post in all_posts:
        result['total_checked'] += 1

        # 检查文件路径
        post_path = Path(post.file_path)
        if not post_path.exists():
            result['issues'].append({
                'type': 'missing_file',
                'post_id': post.id,
                'url': post.url,
                'file_path': post.file_path,
                'severity': 'high'
            })

            if fix:
                # 删除数据库记录
                post.delete()
                result['fixed'] += 1

    # 检查 2: 文件系统中的帖子是否在数据库中
    print("[2/4] 检查文件系统中的帖子...")

    if archive_dir.exists():
        for author_dir in archive_dir.iterdir():
            if not author_dir.is_dir():
                continue

            author_name = author_dir.name

            # 检查作者是否在数据库中
            author = Author.get_by_name(author_name)
            if author is None:
                result['issues'].append({
                    'type': 'author_missing_in_db',
                    'author_name': author_name,
                    'severity': 'medium'
                })
                continue

            # 遍历帖子
            for year_dir in author_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir():
                        continue
                    for post_dir in month_dir.iterdir():
                        if not post_dir.is_dir():
                            continue

                        # 检查帖子是否在数据库中
                        post_url = f"file://{post_dir}"
                        if not Post.exists(post_url):
                            result['issues'].append({
                                'type': 'post_missing_in_db',
                                'path': str(post_dir),
                                'author_name': author_name,
                                'severity': 'medium'
                            })

                            if fix:
                                # 可以选择导入这个帖子
                                # 这里暂不实现自动导入，因为需要完整的元数据提取
                                pass

    # 检查 3: 统计字段是否准确
    print("[3/4] 检查统计字段...")

    all_authors = Author.get_all()
    conn = db.get_connection()

    for author in all_authors:
        # 从数据库重新计算统计
        cursor = conn.execute("""
            SELECT
                COUNT(*) as post_count,
                SUM(image_count) as image_count,
                SUM(video_count) as video_count,
                SUM(file_size_bytes) as total_size
            FROM posts
            WHERE author_id = ?
        """, (author.id,))

        row = cursor.fetchone()
        actual_posts = row[0] or 0
        actual_images = row[1] or 0
        actual_videos = row[2] or 0
        actual_size = row[3] or 0

        # 检查是否一致
        if author.total_posts != actual_posts:
            result['issues'].append({
                'type': 'stat_mismatch',
                'author': author.name,
                'field': 'total_posts',
                'expected': actual_posts,
                'actual': author.total_posts,
                'severity': 'low'
            })

        if author.total_images != actual_images:
            result['issues'].append({
                'type': 'stat_mismatch',
                'author': author.name,
                'field': 'total_images',
                'expected': actual_images,
                'actual': author.total_images,
                'severity': 'low'
            })

        if author.total_videos != actual_videos:
            result['issues'].append({
                'type': 'stat_mismatch',
                'author': author.name,
                'field': 'total_videos',
                'expected': actual_videos,
                'actual': author.total_videos,
                'severity': 'low'
            })

        if author.total_size_bytes != actual_size:
            result['issues'].append({
                'type': 'stat_mismatch',
                'author': author.name,
                'field': 'total_size_bytes',
                'expected': actual_size,
                'actual': author.total_size_bytes,
                'severity': 'low'
            })

    if fix and any(issue['type'] == 'stat_mismatch' for issue in result['issues']):
        # 修复统计字段
        fixed_count = fix_statistics(db)
        result['fixed'] += fixed_count

    # 检查 4: 孤立记录
    print("[4/4] 检查孤立记录...")

    orphaned = check_orphaned_records(db)

    for orphaned_post in orphaned.get('orphaned_posts', []):
        result['issues'].append({
            'type': 'orphaned_post',
            'post_id': orphaned_post['id'],
            'title': orphaned_post['title'],
            'severity': 'high'
        })

        if fix:
            # 删除孤立的帖子
            post = Post.get_by_id(orphaned_post['id'])
            if post:
                post.delete()
                result['fixed'] += 1

    for orphaned_media in orphaned.get('orphaned_media', []):
        result['issues'].append({
            'type': 'orphaned_media',
            'media_id': orphaned_media['id'],
            'file_name': orphaned_media['file_name'],
            'severity': 'high'
        })

        if fix:
            # 删除孤立的媒体
            media = Media.get_by_id(orphaned_media['id'])
            if media:
                media.delete()
                result['fixed'] += 1

    print("\n检查完成!")
    return result


def fix_statistics(db: Optional[DatabaseConnection] = None) -> int:
    """
    重新计算并更新所有作者的统计字段

    Args:
        db: 数据库连接（可选）

    Returns:
        int: 修复的作者数量
    """
    if db is None:
        db = _get_db()

    if not db.is_initialized():
        return 0

    # 设置模型使用的数据库
    Author._db = db

    conn = db.get_connection()
    fixed_count = 0

    try:
        # 获取所有作者
        all_authors = Author.get_all()

        for author in all_authors:
            # 重新计算统计
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as post_count,
                    COALESCE(SUM(image_count), 0) as image_count,
                    COALESCE(SUM(video_count), 0) as video_count,
                    COALESCE(SUM(file_size_bytes), 0) as total_size
                FROM posts
                WHERE author_id = ?
            """, (author.id,))

            row = cursor.fetchone()

            # 更新作者统计
            conn.execute("""
                UPDATE authors SET
                    total_posts = ?,
                    total_images = ?,
                    total_videos = ?,
                    total_size_bytes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (row[0], row[1], row[2], row[3], author.id))

            fixed_count += 1

        conn.commit()
        print(f"✓ 修复了 {fixed_count} 个作者的统计字段")

    except Exception as e:
        print(f"修复统计字段失败: {e}")
        conn.rollback()

    return fixed_count


def check_orphaned_records(db: Optional[DatabaseConnection] = None) -> Dict:
    """
    检测孤立的数据库记录

    孤立记录:
    - 帖子表中 author_id 指向不存在的作者
    - 媒体表中 post_id 指向不存在的帖子

    Args:
        db: 数据库连接（可选）

    Returns:
        {
            'orphaned_posts': [
                {'id': 123, 'title': '...', 'author_id': 5},
                ...
            ],
            'orphaned_media': [
                {'id': 456, 'file_name': '...', 'post_id': 10},
                ...
            ]
        }
    """
    if db is None:
        db = _get_db()

    if not db.is_initialized():
        return {
            'orphaned_posts': [],
            'orphaned_media': []
        }

    conn = db.get_connection()
    result = {
        'orphaned_posts': [],
        'orphaned_media': []
    }

    try:
        # 查找孤立的帖子
        cursor = conn.execute("""
            SELECT id, title, author_id
            FROM posts
            WHERE author_id NOT IN (SELECT id FROM authors)
        """)

        for row in cursor.fetchall():
            result['orphaned_posts'].append({
                'id': row[0],
                'title': row[1],
                'author_id': row[2]
            })

        # 查找孤立的媒体
        cursor = conn.execute("""
            SELECT id, file_name, post_id
            FROM media
            WHERE post_id NOT IN (SELECT id FROM posts)
        """)

        for row in cursor.fetchall():
            result['orphaned_media'].append({
                'id': row[0],
                'file_name': row[1],
                'post_id': row[2]
            })

    except Exception as e:
        print(f"检测孤立记录失败: {e}")

    return result


# =============================================================================
# 其他检查函数
# =============================================================================

def check_media_files_exist(db: Optional[DatabaseConnection] = None) -> Dict:
    """
    检查媒体表中记录的文件是否实际存在

    Args:
        db: 数据库连接（可选）

    Returns:
        {
            'total_checked': 1000,
            'missing_files': [
                {'id': 123, 'file_path': '...', 'type': 'image'},
                ...
            ]
        }
    """
    if db is None:
        db = _get_db()

    if not db.is_initialized():
        return {
            'total_checked': 0,
            'missing_files': []
        }

    Media._db = db
    conn = db.get_connection()

    result = {
        'total_checked': 0,
        'missing_files': []
    }

    try:
        cursor = conn.execute("SELECT id, file_path, type FROM media")

        for row in cursor.fetchall():
            result['total_checked'] += 1

            media_id = row[0]
            file_path = row[1]
            media_type = row[2]

            if not Path(file_path).exists():
                result['missing_files'].append({
                    'id': media_id,
                    'file_path': file_path,
                    'type': media_type
                })

    except Exception as e:
        print(f"检查媒体文件失败: {e}")

    return result


def verify_database_structure(db: Optional[DatabaseConnection] = None) -> Dict:
    """
    验证数据库结构是否完整

    检查所有必需的表、索引、视图、触发器是否存在

    Args:
        db: 数据库连接（可选）

    Returns:
        {
            'tables': ['authors', 'posts', 'media', 'sync_history'],
            'indexes': [...],
            'views': ['v_author_stats', 'v_monthly_stats'],
            'triggers': [...],
            'missing': [],
            'is_valid': True
        }
    """
    if db is None:
        db = _get_db()

    conn = db.get_connection()

    result = {
        'tables': [],
        'indexes': [],
        'views': [],
        'triggers': [],
        'missing': [],
        'is_valid': False
    }

    try:
        # 查询表
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        result['tables'] = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']

        # 查询索引
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
        result['indexes'] = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]

        # 查询视图
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
        result['views'] = [row[0] for row in cursor.fetchall()]

        # 查询触发器
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name")
        result['triggers'] = [row[0] for row in cursor.fetchall()]

        # 检查必需的表
        required_tables = ['authors', 'posts', 'media', 'sync_history']
        for table in required_tables:
            if table not in result['tables']:
                result['missing'].append(f'table:{table}')

        # 检查必需的视图
        required_views = ['v_author_stats', 'v_monthly_stats']
        for view in required_views:
            if view not in result['views']:
                result['missing'].append(f'view:{view}')

        # 判断是否有效
        result['is_valid'] = len(result['missing']) == 0

    except Exception as e:
        print(f"验证数据库结构失败: {e}")

    return result


def generate_integrity_report(
    archive_path: str,
    output_file: Optional[str] = None,
    db: Optional[DatabaseConnection] = None
) -> str:
    """
    生成数据完整性检查报告

    Args:
        archive_path: 归档目录路径
        output_file: 输出文件路径（可选，默认打印到控制台）
        db: 数据库连接（可选）

    Returns:
        str: 报告内容
    """
    check_result = check_all(archive_path, db, fix=False)

    report = []
    report.append("=" * 60)
    report.append("数据完整性检查报告")
    report.append("=" * 60)
    report.append(f"总检查项: {check_result['total_checked']}")
    report.append(f"发现问题: {len(check_result['issues'])}")
    report.append("")

    if check_result['issues']:
        # 按严重性分类
        high_severity = [i for i in check_result['issues'] if i.get('severity') == 'high']
        medium_severity = [i for i in check_result['issues'] if i.get('severity') == 'medium']
        low_severity = [i for i in check_result['issues'] if i.get('severity') == 'low']

        if high_severity:
            report.append(f"高严重性问题: {len(high_severity)}")
            for issue in high_severity[:10]:  # 只显示前 10 个
                report.append(f"  - {issue['type']}: {issue}")

        if medium_severity:
            report.append(f"\n中严重性问题: {len(medium_severity)}")
            for issue in medium_severity[:10]:
                report.append(f"  - {issue['type']}: {issue}")

        if low_severity:
            report.append(f"\n低严重性问题: {len(low_severity)}")
            for issue in low_severity[:10]:
                report.append(f"  - {issue['type']}: {issue}")

    else:
        report.append("✓ 未发现问题，数据完整性良好!")

    report.append("")
    report.append("=" * 60)

    report_text = "\n".join(report)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"报告已保存到: {output_file}")
    else:
        print(report_text)

    return report_text
