#!/bin/bash

# 验证 EXIF 数据是否正确提取和显示

echo "🔍 检查数据库中的 EXIF 数据..."
echo ""

python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, 'python')

from src.database.connection import get_default_connection
from src.database.models import Post, Media

db = get_default_connection()
Post._db = db
Media._db = db

post = Post.get_by_url('https://t66y.com/htm_data/2601/7/7115026.html')
if post:
    print(f'✓ 帖子已入库: {post.title}')
    print(f'  ID: {post.id}')
    print(f'  归档时间: {post.archived_date}')
    print()

    images = Media.get_by_post(post.id, media_type='image')
    print(f'✓ 图片记录: {len(images)} 张')
    print()

    if len(images) == 0:
        print('❌ 图片记录为 0，数据库同步失败！')
        exit(1)

    exif_count = 0
    for i, img in enumerate(images, 1):
        print(f'  [{i}] {Path(img.file_path).name}')

        if img.exif_make or img.exif_model:
            exif_count += 1
            print(f'      📷 {img.exif_make or \"\"} {img.exif_model or \"\"}')
            if img.exif_datetime:
                print(f'      🕐 {img.exif_datetime}')
            if img.exif_aperture or img.exif_iso:
                aperture = f'f/{img.exif_aperture}' if img.exif_aperture else ''
                iso = f'ISO{img.exif_iso}' if img.exif_iso else ''
                print(f'      ⚙️  {aperture} {iso}'.strip())
        else:
            print(f'      ❌ 无 EXIF 数据')
        print()

    if exif_count > 0:
        print(f'✅ 成功提取 {exif_count}/{len(images)} 张图片的 EXIF 数据')
        print()
        print('📂 现在打开 HTML 查看显示效果：')
        print(f'   firefox \"{post.file_path}/content.html\"')
        print()
        print('或运行：')
        print('   python3 python/test_exif_display.py')
    else:
        print('⚠️  所有图片均无 EXIF 数据')
else:
    print('❌ 帖子未找到，请先重新归档')
    exit(1)
"
