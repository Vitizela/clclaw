#!/bin/bash

# 清理测试帖子

echo "🗑️  清理旧归档目录..."
rm -rf "/home/ben/Download/t66y/特兰克斯斯/2026/02/2026-02-15_30岁新人，首次发帖，分享两张老婆的骚臀"
echo "✓ 已删除目录"

echo ""
echo "🗄️  清理数据库记录..."
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, 'python')

from src.database.connection import get_default_connection

db = get_default_connection()
conn = db.get_connection()

# 删除这个帖子的记录
conn.execute('DELETE FROM posts WHERE url = ?', ('https://t66y.com/htm_data/2601/7/7115026.html',))
conn.commit()

print('✓ 已清理数据库旧记录')
"

echo ""
echo "✅ 清理完成！现在可以重新归档了："
echo "   python3 python/main.py"
