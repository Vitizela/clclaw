-- =============================================================================
-- T66Y 论坛归档系统 - 数据库结构定义
-- =============================================================================
-- 版本: v1.0
-- 创建日期: 2026-02-14
-- 说明: 定义 SQLite 数据库的完整结构，包括表、索引、视图、触发器
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SQLite 配置优化
-- -----------------------------------------------------------------------------

-- 启用 WAL 模式（写入优化，支持并发读写）
PRAGMA journal_mode = WAL;

-- 平衡安全性和性能
PRAGMA synchronous = NORMAL;

-- 增大缓存（约 40MB）
PRAGMA cache_size = 10000;

-- 临时表存储在内存
PRAGMA temp_store = MEMORY;

-- 启用外键约束
PRAGMA foreign_keys = ON;

-- =============================================================================
-- 表定义
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 表 1: authors - 作者表
-- -----------------------------------------------------------------------------
-- 用途: 存储关注的作者基本信息和统计数据
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS authors (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 基本信息
    name TEXT UNIQUE NOT NULL,                   -- 作者名（唯一）
    added_date TEXT NOT NULL,                    -- 关注日期（YYYY-MM-DD）
    last_update TEXT,                            -- 最后更新时间（YYYY-MM-DD HH:MM:SS）
    url TEXT,                                    -- 作者 URL

    -- 统计信息（冗余字段，由触发器自动维护）
    total_posts INTEGER DEFAULT 0,               -- 已归档帖子数
    forum_total_posts INTEGER DEFAULT 0,         -- 论坛总帖子数
    total_images INTEGER DEFAULT 0,              -- 总图片数
    total_videos INTEGER DEFAULT 0,              -- 总视频数
    total_size_bytes INTEGER DEFAULT 0,          -- 总占用空间（字节）

    -- 扩展信息
    tags TEXT,                                   -- 标签（JSON 数组字符串）
    notes TEXT,                                  -- 备注

    -- 元数据
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,   -- 记录创建时间
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP    -- 记录更新时间
);

-- 索引：加速按作者名查询
CREATE UNIQUE INDEX IF NOT EXISTS idx_authors_name ON authors(name);

-- -----------------------------------------------------------------------------
-- 表 2: posts - 帖子表
-- -----------------------------------------------------------------------------
-- 用途: 存储每篇帖子的元数据
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS posts (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 关联关系
    author_id INTEGER NOT NULL,                  -- 作者 ID（外键）

    -- 帖子标识
    url TEXT UNIQUE NOT NULL,                    -- 帖子 URL（唯一标识）
    url_hash TEXT NOT NULL,                      -- URL 的 MD5 hash（8 位）
    title TEXT NOT NULL,                         -- 帖子标题

    -- 发布时间（含冗余字段，加速查询）
    publish_date TEXT,                           -- 发布日期（YYYY-MM-DD HH:MM:SS）
    publish_year INTEGER,                        -- 发布年份（冗余）
    publish_month INTEGER,                       -- 发布月份（1-12，冗余）
    publish_hour INTEGER,                        -- 发布小时（0-23，冗余）
    publish_weekday INTEGER,                     -- 星期几（0=周一，冗余）

    -- 内容统计
    content_length INTEGER DEFAULT 0,            -- 内容长度（字符数）
    word_count INTEGER DEFAULT 0,                -- 字数统计（分词后）
    image_count INTEGER DEFAULT 0,               -- 图片数量
    video_count INTEGER DEFAULT 0,               -- 视频数量

    -- 文件系统信息
    file_path TEXT NOT NULL,                     -- 归档目录路径（相对路径）
    archived_date TEXT NOT NULL,                 -- 归档日期
    file_size_bytes INTEGER DEFAULT 0,           -- 目录占用空间（字节）

    -- 状态标记
    is_complete BOOLEAN DEFAULT 1,               -- 是否完整归档

    -- 元数据
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,   -- 记录创建时间
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,   -- 记录更新时间

    -- 外键约束
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
);

-- 索引：关键查询索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_url ON posts(url);
CREATE INDEX IF NOT EXISTS idx_posts_url_hash ON posts(url_hash);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id);

-- 索引：时间查询索引
CREATE INDEX IF NOT EXISTS idx_posts_publish_date ON posts(publish_date);
CREATE INDEX IF NOT EXISTS idx_posts_year_month ON posts(publish_year, publish_month);

-- 索引：统计查询索引
CREATE INDEX IF NOT EXISTS idx_posts_author_date ON posts(author_id, publish_date);

-- -----------------------------------------------------------------------------
-- 表 3: media - 媒体文件表
-- -----------------------------------------------------------------------------
-- 用途: 存储图片和视频的详细信息
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS media (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 关联关系
    post_id INTEGER NOT NULL,                    -- 帖子 ID（外键）

    -- 媒体信息
    type TEXT NOT NULL,                          -- 类型：'image' 或 'video'
    url TEXT NOT NULL,                           -- 原始 URL
    file_name TEXT NOT NULL,                     -- 文件名（如 img_1.jpg）
    file_path TEXT NOT NULL,                     -- 文件相对路径
    file_size_bytes INTEGER DEFAULT 0,           -- 文件大小（字节）

    -- 媒体属性（为 Phase 4 可视化预留）
    width INTEGER,                               -- 图片宽度（可选）
    height INTEGER,                              -- 图片高度（可选）
    duration INTEGER,                            -- 视频时长（秒，可选）

    -- 下载状态
    is_downloaded BOOLEAN DEFAULT 1,             -- 是否已下载
    download_date TEXT,                          -- 下载日期

    -- 元数据
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,   -- 记录创建时间

    -- 外键约束
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- 索引：加速按帖子查询媒体
CREATE INDEX IF NOT EXISTS idx_media_post ON media(post_id);
CREATE INDEX IF NOT EXISTS idx_media_type ON media(type);
CREATE INDEX IF NOT EXISTS idx_media_post_type ON media(post_id, type);

-- -----------------------------------------------------------------------------
-- 表 4: sync_history - 同步历史表（可选）
-- -----------------------------------------------------------------------------
-- 用途: 记录数据库同步操作历史，便于调试和监控
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sync_history (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 同步信息
    sync_type TEXT NOT NULL,                     -- 类型：'import', 'archive', 'check'
    author_name TEXT,                            -- 相关作者

    -- 统计信息
    posts_added INTEGER DEFAULT 0,               -- 新增帖子数
    posts_updated INTEGER DEFAULT 0,             -- 更新帖子数
    errors INTEGER DEFAULT 0,                    -- 错误数

    -- 性能信息
    duration_seconds REAL,                       -- 耗时（秒）

    -- 状态信息
    status TEXT NOT NULL,                        -- 状态：'success', 'failed', 'partial'
    error_message TEXT,                          -- 错误信息

    -- 元数据
    created_at TEXT DEFAULT CURRENT_TIMESTAMP    -- 同步时间
);

-- 索引：加速按类型和日期查询同步历史
CREATE INDEX IF NOT EXISTS idx_sync_history_type ON sync_history(sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_history_date ON sync_history(created_at);

-- =============================================================================
-- 视图定义
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 视图 1: v_author_stats - 作者统计视图
-- -----------------------------------------------------------------------------
-- 用途: 快速查询每个作者的完整统计信息
-- -----------------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS v_author_stats AS
SELECT
    a.id,
    a.name,
    a.added_date,
    a.last_update,
    a.url,
    a.tags,

    -- 统计信息（从冗余字段读取，性能更好）
    a.total_posts as post_count,
    a.total_images as image_count,
    a.total_videos as video_count,
    a.total_size_bytes,
    a.forum_total_posts,

    -- 时间跨度
    MIN(p.publish_date) as first_post_date,
    MAX(p.publish_date) as latest_post_date,

    -- 平均值
    CASE WHEN a.total_posts > 0
         THEN CAST(a.total_images AS REAL) / a.total_posts
         ELSE 0
    END as avg_images_per_post,

    CASE WHEN a.total_posts > 0
         THEN CAST(a.total_videos AS REAL) / a.total_posts
         ELSE 0
    END as avg_videos_per_post,

    CASE WHEN a.total_posts > 0
         THEN CAST(a.total_size_bytes AS REAL) / a.total_posts
         ELSE 0
    END as avg_size_per_post

FROM authors a
LEFT JOIN posts p ON a.id = p.author_id
GROUP BY a.id;

-- -----------------------------------------------------------------------------
-- 视图 2: v_monthly_stats - 月度统计视图
-- -----------------------------------------------------------------------------
-- 用途: 为 Phase 4 趋势分析预留
-- -----------------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS v_monthly_stats AS
SELECT
    a.name as author_name,
    p.publish_year,
    p.publish_month,
    COUNT(*) as post_count,
    SUM(p.image_count) as image_count,
    SUM(p.video_count) as video_count,
    SUM(p.file_size_bytes) as total_size_bytes
FROM posts p
JOIN authors a ON p.author_id = a.id
WHERE p.publish_year IS NOT NULL AND p.publish_month IS NOT NULL
GROUP BY a.name, p.publish_year, p.publish_month
ORDER BY p.publish_year DESC, p.publish_month DESC;

-- =============================================================================
-- 触发器定义
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 触发器 1: 插入帖子时自动更新作者统计
-- -----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_posts_insert_update_author
AFTER INSERT ON posts
FOR EACH ROW
BEGIN
    UPDATE authors SET
        total_posts = (
            SELECT COUNT(*)
            FROM posts
            WHERE author_id = NEW.author_id
        ),
        total_images = (
            SELECT COALESCE(SUM(image_count), 0)
            FROM posts
            WHERE author_id = NEW.author_id
        ),
        total_videos = (
            SELECT COALESCE(SUM(video_count), 0)
            FROM posts
            WHERE author_id = NEW.author_id
        ),
        total_size_bytes = (
            SELECT COALESCE(SUM(file_size_bytes), 0)
            FROM posts
            WHERE author_id = NEW.author_id
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.author_id;
END;

-- -----------------------------------------------------------------------------
-- 触发器 2: 更新帖子时自动更新作者统计
-- -----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_posts_update_update_author
AFTER UPDATE ON posts
FOR EACH ROW
BEGIN
    UPDATE authors SET
        total_posts = (
            SELECT COUNT(*)
            FROM posts
            WHERE author_id = NEW.author_id
        ),
        total_images = (
            SELECT COALESCE(SUM(image_count), 0)
            FROM posts
            WHERE author_id = NEW.author_id
        ),
        total_videos = (
            SELECT COALESCE(SUM(video_count), 0)
            FROM posts
            WHERE author_id = NEW.author_id
        ),
        total_size_bytes = (
            SELECT COALESCE(SUM(file_size_bytes), 0)
            FROM posts
            WHERE author_id = NEW.author_id
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.author_id;
END;

-- -----------------------------------------------------------------------------
-- 触发器 3: 删除帖子时自动更新作者统计
-- -----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_posts_delete_update_author
AFTER DELETE ON posts
FOR EACH ROW
BEGIN
    UPDATE authors SET
        total_posts = (
            SELECT COUNT(*)
            FROM posts
            WHERE author_id = OLD.author_id
        ),
        total_images = (
            SELECT COALESCE(SUM(image_count), 0)
            FROM posts
            WHERE author_id = OLD.author_id
        ),
        total_videos = (
            SELECT COALESCE(SUM(video_count), 0)
            FROM posts
            WHERE author_id = OLD.author_id
        ),
        total_size_bytes = (
            SELECT COALESCE(SUM(file_size_bytes), 0)
            FROM posts
            WHERE author_id = OLD.author_id
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.author_id;
END;

-- =============================================================================
-- 初始化完成
-- =============================================================================

-- 验证表结构
-- SELECT name FROM sqlite_master WHERE type='table';
-- SELECT name FROM sqlite_master WHERE type='index';
-- SELECT name FROM sqlite_master WHERE type='view';
-- SELECT name FROM sqlite_master WHERE type='trigger';
