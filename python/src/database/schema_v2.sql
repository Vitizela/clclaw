-- Phase 4: 数据库 Schema 扩展
-- 扩展 media 表，添加 EXIF 元数据字段
-- 创建日期: 2026-02-14
-- 作者: Claude Sonnet 4.5

-- ==================== 检查是否已扩展 ====================
-- 如果已经扩展过，跳过执行
-- SELECT COUNT(*) FROM pragma_table_info('media') WHERE name = 'exif_make';

-- ==================== 扩展 media 表 ====================
-- 注意：EXIF 字段已在数据库中存在，跳过 ALTER TABLE
-- 如果字段不存在，需要手动执行以下语句：
--
-- ALTER TABLE media ADD COLUMN exif_make TEXT;
-- ALTER TABLE media ADD COLUMN exif_model TEXT;
-- ALTER TABLE media ADD COLUMN exif_datetime TEXT;
-- ALTER TABLE media ADD COLUMN exif_iso INTEGER;
-- ALTER TABLE media ADD COLUMN exif_aperture REAL;
-- ALTER TABLE media ADD COLUMN exif_shutter_speed TEXT;
-- ALTER TABLE media ADD COLUMN exif_focal_length REAL;
-- ALTER TABLE media ADD COLUMN exif_gps_lat REAL;
-- ALTER TABLE media ADD COLUMN exif_gps_lng REAL;
-- ALTER TABLE media ADD COLUMN exif_location TEXT;

-- ==================== 创建索引 ====================
-- 优化查询性能

-- 相机信息索引
CREATE INDEX IF NOT EXISTS idx_media_exif_make ON media(exif_make);
CREATE INDEX IF NOT EXISTS idx_media_exif_model ON media(exif_model);

-- 拍摄时间索引
CREATE INDEX IF NOT EXISTS idx_media_exif_datetime ON media(exif_datetime);

-- GPS 位置索引（复合索引）
CREATE INDEX IF NOT EXISTS idx_media_gps ON media(exif_gps_lat, exif_gps_lng);

-- 图片类型 + 相机型号（复合索引，用于相机统计）
-- 注意：字段名是 type 而不是 media_type
CREATE INDEX IF NOT EXISTS idx_media_type_camera ON media(type, exif_make, exif_model);

-- ==================== 创建视图 ====================

-- 视图 1: 相机使用统计
CREATE VIEW IF NOT EXISTS v_camera_stats AS
SELECT
    exif_make as make,
    exif_model as model,
    COUNT(*) as photo_count,
    COUNT(DISTINCT post_id) as post_count,
    MIN(exif_datetime) as first_use,
    MAX(exif_datetime) as last_use,
    ROUND(AVG(exif_iso), 0) as avg_iso,
    ROUND(AVG(exif_aperture), 1) as avg_aperture,
    ROUND(AVG(exif_focal_length), 0) as avg_focal_length
FROM media
WHERE type = 'image'
  AND exif_make IS NOT NULL
  AND exif_model IS NOT NULL
GROUP BY exif_make, exif_model
ORDER BY photo_count DESC;

-- 视图 2: 拍摄地点统计
CREATE VIEW IF NOT EXISTS v_location_stats AS
SELECT
    exif_location as location,
    COUNT(*) as photo_count,
    COUNT(DISTINCT post_id) as post_count,
    ROUND(AVG(exif_gps_lat), 4) as avg_lat,
    ROUND(AVG(exif_gps_lng), 4) as avg_lng,
    MIN(exif_datetime) as first_visit,
    MAX(exif_datetime) as last_visit
FROM media
WHERE type = 'image'
  AND exif_location IS NOT NULL
GROUP BY exif_location
ORDER BY photo_count DESC;

-- 视图 3: EXIF 数据完整性检查
CREATE VIEW IF NOT EXISTS v_exif_completeness AS
SELECT
    COUNT(*) as total_images,
    SUM(CASE WHEN exif_make IS NOT NULL THEN 1 ELSE 0 END) as has_make,
    SUM(CASE WHEN exif_model IS NOT NULL THEN 1 ELSE 0 END) as has_model,
    SUM(CASE WHEN exif_datetime IS NOT NULL THEN 1 ELSE 0 END) as has_datetime,
    SUM(CASE WHEN exif_iso IS NOT NULL THEN 1 ELSE 0 END) as has_iso,
    SUM(CASE WHEN exif_gps_lat IS NOT NULL AND exif_gps_lng IS NOT NULL THEN 1 ELSE 0 END) as has_gps,
    SUM(CASE WHEN exif_location IS NOT NULL THEN 1 ELSE 0 END) as has_location,
    ROUND(CAST(SUM(CASE WHEN exif_make IS NOT NULL THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100, 1) as make_pct,
    ROUND(CAST(SUM(CASE WHEN exif_gps_lat IS NOT NULL THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100, 1) as gps_pct
FROM media
WHERE type = 'image';

-- ==================== 完成 ====================
-- Schema 扩展完成
--
-- 使用方法:
--   sqlite3 python/data/forum_data.db < python/src/database/schema_v2.sql
--
-- 验证方法:
--   sqlite3 python/data/forum_data.db "PRAGMA table_info(media);"
--   sqlite3 python/data/forum_data.db "SELECT * FROM v_exif_completeness;"
