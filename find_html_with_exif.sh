#!/bin/bash
# 查找包含 EXIF 数据的 HTML 页面

cd ~/gemini-work/gemini-t66y/python

echo "========================================="
echo "查找有 EXIF 数据的帖子"
echo "========================================="
echo ""

echo "🔍 正在查询数据库..."

python3 << 'PYTHON'
from src.database.connection import get_default_connection
from pathlib import Path

db = get_default_connection()
conn = db.get_connection()

# 查找有 EXIF 数据的帖子
cursor = conn.execute("""
    SELECT DISTINCT
        p.file_path,
        p.title,
        COUNT(m.id) as image_count,
        SUM(CASE WHEN m.exif_make IS NOT NULL THEN 1 ELSE 0 END) as exif_count
    FROM posts p
    JOIN media m ON p.id = m.post_id
    WHERE m.type = 'image'
    GROUP BY p.id
    HAVING exif_count > 0
    ORDER BY exif_count DESC
    LIMIT 5
""")

posts = cursor.fetchall()

if not posts:
    print("❌ 暂无包含 EXIF 数据的帖子")
    print("")
    print("💡 提示：")
    print("   1. 先运行: python3 -m src.database.migrate_exif --limit 100 --no-gps")
    print("   2. 或归档一个新帖子测试自动提取功能")
else:
    print(f"✅ 找到 {len(posts)} 个包含 EXIF 数据的帖子：")
    print("")

    for i, post in enumerate(posts, 1):
        file_path = Path(post['file_path'])
        html_path = file_path / 'content.html'

        print(f"{i}. {post['title'][:50]}...")
        print(f"   路径: {html_path}")
        print(f"   图片: {post['image_count']} 张 | EXIF: {post['exif_count']} 张")
        print("")

    # 打开第一个
    if posts:
        first_html = Path(posts[0]['file_path']) / 'content.html'
        print("========================================")
        print(f"")
        print(f"💡 打开第一个帖子查看水印效果：")
        print(f"")
        print(f"   firefox \"{first_html}\"")
        print(f"")
        print(f"   # 或用 w3m 终端查看：")
        print(f"   w3m \"{first_html}\"")
        print("")
PYTHON

echo "========================================="
