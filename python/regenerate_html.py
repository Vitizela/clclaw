#!/usr/bin/env python3
"""
重新生成帖子的 content.html（带 EXIF 水印）

用于已归档的帖子，在提取 EXIF 后重新生成 HTML
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import get_default_connection
from src.database.models import Post, Media
from src.scraper.archiver import ForumArchiver
from rich.console import Console
from rich.panel import Panel
import yaml

console = Console()


def regenerate_post_html(post_url: str):
    """重新生成指定帖子的 HTML"""

    console.print(Panel.fit(
        "[bold cyan]重新生成 HTML（带 EXIF 水印）[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    try:
        # 初始化数据库
        db = get_default_connection()
        if not db.is_initialized():
            console.print("[red]❌ 数据库未初始化[/red]")
            return False

        Post._db = db
        Media._db = db

        # 查找帖子
        console.print(f"🔍 查找帖子: {post_url}")
        post = Post.get_by_url(post_url)

        if not post:
            console.print(f"[red]❌ 未找到帖子: {post_url}[/red]")
            return False

        console.print(f"[green]✅ 找到帖子: {post.title}[/green]")
        console.print(f"   路径: {post.file_path}")
        console.print()

        # 获取帖子目录
        post_dir = Path(post.file_path)
        if not post_dir.exists():
            console.print(f"[red]❌ 帖子目录不存在: {post_dir}[/red]")
            return False

        # 获取图片和视频
        images = Media.get_by_post(post.id, media_type='image')
        videos = Media.get_by_post(post.id, media_type='video')

        console.print(f"📊 媒体文件:")
        console.print(f"   图片: {len(images)} 张")
        console.print(f"   视频: {len(videos)} 个")

        # 统计有 EXIF 的图片
        exif_count = sum(1 for img in images if img.exif_make)
        if exif_count > 0:
            console.print(f"   [green]EXIF: {exif_count} 张[/green]")
        else:
            console.print(f"   [yellow]⚠️  无 EXIF 数据（水印将不显示）[/yellow]")
        console.print()

        # 准备数据
        console.print("📝 准备数据...")

        # 读取 content.txt（如果存在）
        content = ""
        content_txt = post_dir / 'content.txt'
        if content_txt.exists():
            content = content_txt.read_text(encoding='utf-8')

        # 构建 post_data
        post_data = {
            'title': post.title,
            'author': post.author_id,  # 需要转换为作者名
            'time': post.publish_date or 'N/A',
            'url': post.url,
            'content': content,
            'images': [],
            'videos': []
        }

        # 准备图片列表（使用相对路径）
        for img in images:
            file_path = Path(img.file_path)
            if file_path.name.endswith('.done'):
                file_path = file_path.with_suffix('')

            relative_path = file_path.relative_to(post_dir)
            post_data['images'].append(str(relative_path))

        # 准备视频列表
        for vid in videos:
            file_path = Path(vid.file_path)
            if file_path.name.endswith('.done'):
                file_path = file_path.with_suffix('')

            relative_path = file_path.relative_to(post_dir)
            post_data['videos'].append(str(relative_path))

        # 获取作者名
        from src.database.models import Author
        Author._db = db
        author = Author.get_by_id(post.author_id)
        if author:
            post_data['author'] = author.name

        # 初始化 archiver
        console.print("🔄 生成 HTML...")

        # 读取配置
        config_file = Path(__file__).parent / 'config.yaml'
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        archiver = ForumArchiver(config)

        # 备份旧 HTML
        old_html = post_dir / 'content.html'
        if old_html.exists():
            backup = post_dir / f'content.html.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            old_html.rename(backup)
            console.print(f"   备份旧文件: {backup.name}")

        # 生成新 HTML
        archiver._save_content_html(post_data, post_dir)

        console.print()
        console.print("[green]✅ HTML 重新生成完成！[/green]")
        console.print()
        console.print(f"📂 文件路径:")
        console.print(f"   {post_dir / 'content.html'}")
        console.print()

        if exif_count > 0:
            console.print("[green]🎨 现在打开 HTML 可以看到 EXIF 水印了！[/green]")
            console.print()
            console.print(f"   firefox \"{post_dir / 'content.html'}\"")
        else:
            console.print("[yellow]⚠️  该帖子图片无 EXIF 数据，水印不会显示[/yellow]")

        return True

    except Exception as e:
        console.print(f"[red]❌ 错误: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="重新生成帖子的 HTML（带 EXIF 水印）"
    )
    parser.add_argument(
        'post_url',
        nargs='?',
        help='帖子 URL（可选，不提供则自动查找有 EXIF 的帖子）'
    )

    args = parser.parse_args()

    if args.post_url:
        # 重新生成指定帖子
        regenerate_post_html(args.post_url)
    else:
        # 自动查找并重新生成有 EXIF 的帖子
        console.print("[cyan]🔍 自动查找有 EXIF 数据的帖子...[/cyan]\n")

        db = get_default_connection()
        conn = db.get_connection()

        cursor = conn.execute("""
            SELECT DISTINCT p.url, p.title
            FROM posts p
            JOIN media m ON p.id = m.post_id
            WHERE m.type = 'image'
              AND m.exif_make IS NOT NULL
            ORDER BY p.archived_date DESC
            LIMIT 5
        """)

        posts = cursor.fetchall()

        if not posts:
            console.print("[yellow]❌ 未找到包含 EXIF 的帖子[/yellow]")
            return

        console.print(f"[green]✅ 找到 {len(posts)} 个帖子[/green]\n")

        for i, post in enumerate(posts, 1):
            console.print(f"{i}. {post['title'][:60]}...")
            regenerate_post_html(post['url'])
            console.print("─" * 60)
            console.print()


if __name__ == '__main__':
    main()
