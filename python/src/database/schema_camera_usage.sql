-- ==================== 相机使用分析视图 ====================
-- 创建日期: 2026-02-16
-- 作者: Claude Sonnet 4.5
-- 用途: 支持相机使用分析功能（Phase 4 Week 3）
-- 依赖: schema_v2.sql（EXIF 字段必须已存在）

-- ==================== 视图 1: 相机与作者关联 ====================
-- 用途: 查询相机被哪些作者使用，或作者使用了哪些相机

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

    -- EXIF 参数统计
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

-- 查询示例:
-- 查询 vivo X Fold3 Pro 被哪些作者使用:
--   SELECT * FROM v_camera_author_usage
--   WHERE make = 'vivo' AND model = 'X Fold3 Pro';
--
-- 查询某作者使用的所有相机:
--   SELECT * FROM v_camera_author_usage
--   WHERE author_name = '同花顺心'
--   ORDER BY photo_count DESC;

-- ==================== 视图 2: 相机使用时间线 ====================
-- 用途: 查询相机在不同日期的使用情况

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

-- 查询示例:
-- 查询 vivo X Fold3 Pro 的使用时间线:
--   SELECT date, photo_count, post_count, authors
--   FROM v_camera_daily_usage
--   WHERE make = 'vivo' AND model = 'X Fold3 Pro'
--   ORDER BY date DESC;
--
-- 查询 2024 年 12 月所有相机使用情况:
--   SELECT camera_full, SUM(photo_count) as total_photos
--   FROM v_camera_daily_usage
--   WHERE year = 2024 AND month = 12
--   GROUP BY camera_full
--   ORDER BY total_photos DESC;

-- ==================== 视图 3: 作者相机使用汇总 ====================
-- 用途: 查询作者使用的相机统计（相机数量、列表、最常用）

CREATE VIEW IF NOT EXISTS v_author_camera_summary AS
SELECT
    -- 作者信息
    a.id as author_id,
    a.name as author_name,

    -- 相机统计
    COUNT(DISTINCT m.exif_make || '-' || m.exif_model) as camera_count,
    GROUP_CONCAT(DISTINCT m.exif_make || ' ' || m.exif_model) as camera_list,

    -- 最常用相机（子查询）
    (
        SELECT m2.exif_make || ' ' || m2.exif_model
        FROM media m2
        JOIN posts p2 ON m2.post_id = p2.id
        WHERE p2.author_id = a.id
          AND m2.type = 'image'
          AND m2.exif_make IS NOT NULL
          AND m2.exif_model IS NOT NULL
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
  AND m.exif_model IS NOT NULL
GROUP BY a.id
ORDER BY total_photos DESC;

-- 查询示例:
-- 查询所有作者的相机使用汇总:
--   SELECT * FROM v_author_camera_summary;
--
-- 查询某作者的相机统计:
--   SELECT * FROM v_author_camera_summary
--   WHERE author_name = '同花顺心';

-- ==================== 视图完成 ====================
-- 使用方法:
--   sqlite3 python/data/forum_data.db < python/src/database/schema_camera_usage.sql
--
-- 验证方法:
--   sqlite3 python/data/forum_data.db "SELECT * FROM v_camera_author_usage LIMIT 5;"
--   sqlite3 python/data/forum_data.db "SELECT * FROM v_camera_daily_usage LIMIT 5;"
--   sqlite3 python/data/forum_data.db "SELECT * FROM v_author_camera_summary LIMIT 5;"
