#!/bin/bash
# Week 1 功能快速验证脚本

cd ~/gemini-work/gemini-t66y/python

echo "========================================="
echo "Week 1 功能验证"
echo "========================================="
echo ""

echo "1️⃣  检查数据库结构..."
sqlite3 data/forum_data.db "PRAGMA table_info(media);" | grep exif | wc -l | xargs echo "   EXIF 字段数:"
sqlite3 data/forum_data.db ".indexes media" | grep exif | wc -l | xargs echo "   EXIF 索引数:"

echo ""
echo "2️⃣  检查视图..."
sqlite3 data/forum_data.db ".tables" | grep -E "v_camera|v_location|v_exif" | wc -l | xargs echo "   统计视图数:"

echo ""
echo "3️⃣  检查 EXIF 数据..."
python3 << 'PYTHON'
from src.database.connection import get_default_connection
db = get_default_connection()
conn = db.get_connection()

cursor = conn.execute("SELECT * FROM v_exif_completeness")
row = cursor.fetchone()

print(f"   总图片数: {row['total_images']}")
print(f"   有相机信息: {row['has_make']} ({row['make_pct']}%)")
print(f"   有 GPS: {row['has_gps']} ({row['gps_pct']}%)")
PYTHON

echo ""
echo "4️⃣  检查模板..."
grep -q "exif-watermark" src/templates/post.html && echo "   ✅ 模板已更新" || echo "   ❌ 模板未更新"

echo ""
echo "5️⃣  检查集成..."
grep -q "_get_exif_data_for_post" src/scraper/archiver.py && echo "   ✅ archiver 已集成" || echo "   ❌ archiver 未集成"

echo ""
echo "========================================="
echo "验证完成！"
echo ""
echo "💡 提示："
echo "   - 如果 EXIF 数据为 0，运行: python3 -m src.database.migrate_exif --limit 100 --no-gps"
echo "   - 详细验证步骤见: WEEK1_VERIFICATION_GUIDE.md"
echo "========================================="
