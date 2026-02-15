#!/bin/bash
# 查看 EXIF 提取结果

cd ~/gemini-work/gemini-t66y/python/data

echo "========================================="
echo "EXIF 提取结果查看"
echo "========================================="
echo ""

echo "📊 统计概览："
sqlite3 forum_data.db << 'SQL'
.mode column
.headers on
SELECT * FROM v_exif_completeness;
SQL

echo ""
echo "📷 相机使用排行（Top 5）："
sqlite3 forum_data.db << 'SQL'
.mode column
.headers on
SELECT
    make || ' ' || model as camera,
    photo_count,
    post_count,
    avg_iso,
    avg_aperture,
    avg_focal_length
FROM v_camera_stats
LIMIT 5;
SQL

echo ""
echo "🖼️  有 EXIF 的图片示例："
sqlite3 forum_data.db << 'SQL'
.mode column
.headers on
SELECT
    substr(file_name, 1, 20) as file,
    exif_make as brand,
    exif_model as model,
    'f/' || exif_aperture as aperture,
    'ISO' || exif_iso as iso,
    substr(exif_datetime, 1, 10) as date
FROM media
WHERE type = 'image'
  AND exif_make IS NOT NULL
LIMIT 10;
SQL

echo ""
echo "========================================="
