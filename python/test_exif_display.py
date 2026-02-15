#!/usr/bin/env python3
"""
快速测试 EXIF 静态显示功能

自动找到有 EXIF 数据的帖子，重新生成 HTML，并打开浏览器查看
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import get_default_connection
from src.database.models import Post, Media
from regenerate_html import regenerate_post_html
from rich.console import Console
from rich.panel import Panel
import subprocess

console = Console()


def main():
    console.print(Panel.fit(
        "[bold cyan]EXIF 静态显示测试[/bold cyan]\n"
        "[dim]自动找到有 EXIF 的帖子并重新生成 HTML[/dim]",
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

        # 查找有 EXIF 的帖子
        console.print("🔍 查找包含 EXIF 数据的帖子...\n")

        conn = db.get_connection()
        cursor = conn.execute("""
            SELECT DISTINCT p.url, p.title, p.file_path, COUNT(*) as exif_count
            FROM posts p
            JOIN media m ON p.id = m.post_id
            WHERE m.type = 'image'
              AND m.exif_make IS NOT NULL
            GROUP BY p.id
            ORDER BY p.archived_date DESC
            LIMIT 1
        """)

        post_row = cursor.fetchone()

        if not post_row:
            console.print("[yellow]❌ 未找到包含 EXIF 的帖子[/yellow]")
            console.print()
            console.print("提示：请先归档一个帖子，或运行以下命令提取 EXIF：")
            console.print("  python3 -m src.database.migrate_exif --limit 100")
            return False

        post_url = post_row['url']
        post_title = post_row['title']
        post_path = post_row['file_path']
        exif_count = post_row['exif_count']

        console.print(f"[green]✅ 找到帖子[/green]")
        console.print(f"   标题: {post_title[:50]}...")
        console.print(f"   EXIF: {exif_count} 张图片")
        console.print()

        # 重新生成 HTML
        console.print("🔄 重新生成 HTML（使用新模板 v2.7）...\n")

        success = regenerate_post_html(post_url)

        if not success:
            return False

        # 打开浏览器
        html_path = Path(post_path) / 'content.html'

        if html_path.exists():
            console.print()
            console.print("[bold green]🎉 测试准备完成！[/bold green]")
            console.print()
            console.print("📖 现在用浏览器打开 HTML 查看 EXIF 静态显示：")
            console.print(f"   [cyan]{html_path}[/cyan]")
            console.print()
            console.print("✨ 期望效果：")
            console.print("   • 图片下方显示灰色背景的 EXIF 信息")
            console.print("   • 包含相机型号、参数、拍摄时间、位置（如有）")
            console.print("   • 在下载按钮上方，始终可见，无需悬停")
            console.print()

            # 尝试自动打开浏览器
            try:
                console.print("🌐 尝试自动打开浏览器...")
                subprocess.run(['xdg-open', str(html_path)], check=False)
                console.print("[green]✅ 浏览器已打开[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  无法自动打开浏览器: {e}[/yellow]")
                console.print()
                console.print("请手动运行：")
                console.print(f'  firefox "{html_path}"')

            return True
        else:
            console.print(f"[red]❌ HTML 文件不存在: {html_path}[/red]")
            return False

    except Exception as e:
        console.print(f"[red]❌ 错误: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    main()
