"""
数据库模块

Phase 3: 数据库 + 基础统计

模块结构:
- connection.py: 数据库连接管理
- models.py: 数据模型（Author, Post, Media）
- migrate.py: 历史数据导入工具
- query.py: 查询辅助函数
- sync.py: 数据同步工具
- integrity.py: 数据完整性检查
"""

# 核心模块
from .connection import DatabaseConnection, get_default_connection
from .models import Author, Post, Media

# 迁移工具
from .migrate import (
    extract_post_metadata,
    import_all_data,
    import_author_data
)

# 查询工具
from .query import (
    get_global_stats,
    get_author_ranking,
    get_monthly_stats,
    get_hourly_distribution,
    get_weekday_distribution,
    get_author_detail_stats,
    search_posts
)

# 同步工具
from .sync import (
    sync_archived_post,
    sync_delete_author,
    sync_config_to_db,
    sync_all_from_filesystem,
    sync_author_from_filesystem,
    is_database_enabled,
    enable_database
)

# 完整性检查
from .integrity import (
    check_all,
    fix_statistics,
    check_orphaned_records,
    check_media_files_exist,
    verify_database_structure,
    generate_integrity_report
)

__all__ = [
    # 核心
    'DatabaseConnection',
    'get_default_connection',
    'Author',
    'Post',
    'Media',

    # 迁移
    'extract_post_metadata',
    'import_all_data',
    'import_author_data',

    # 查询
    'get_global_stats',
    'get_author_ranking',
    'get_monthly_stats',
    'get_hourly_distribution',
    'get_weekday_distribution',
    'get_author_detail_stats',
    'search_posts',

    # 同步
    'sync_archived_post',
    'sync_delete_author',
    'sync_config_to_db',
    'sync_all_from_filesystem',
    'sync_author_from_filesystem',
    'is_database_enabled',
    'enable_database',

    # 完整性
    'check_all',
    'fix_statistics',
    'check_orphaned_records',
    'check_media_files_exist',
    'verify_database_structure',
    'generate_integrity_report',
]

__version__ = '1.0.0'