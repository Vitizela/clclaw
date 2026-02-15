#!/usr/bin/env python3
"""
EXIF 提取结果查看脚本（Python 版本）
无需 sqlite3 命令行工具
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'python'))

from src.database.connection import get_default_connection
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def main():
    console.print(Panel.fit(
        "[bold cyan]EXIF 提取结果查看[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    try:
        db = get_default_connection()
        conn = db.get_connection()

        # 1. 统计概览
        console.print("[bold]📊 统计概览：[/bold]")
        cursor = conn.execute("SELECT * FROM v_exif_completeness")
        row = cursor.fetchone()

        stats_table = Table(show_header=True)
        stats_table.add_column("项目", style="cyan")
        stats_table.add_column("数值", justify="right", style="green")

        stats_table.add_row("总图片数", f"{row['total_images']:,}")
        stats_table.add_row("有相机信息", f"{row['has_make']} ({row['make_pct']}%)")
        stats_table.add_row("有拍摄时间", f"{row['has_datetime']} ({row.get('datetime_pct', 0)}%)")
        stats_table.add_row("有 ISO", f"{row['has_iso']}")
        stats_table.add_row("有 GPS", f"{row['has_gps']} ({row['gps_pct']}%)")
        stats_table.add_row("有地理位置", f"{row['has_location']}")

        console.print(stats_table)
        console.print()

        # 2. 相机使用排行
        console.print("[bold]📷 相机使用排行（Top 5）：[/bold]")
        cursor = conn.execute("""
            SELECT * FROM v_camera_stats LIMIT 5
        """)
        cameras = cursor.fetchall()

        if cameras:
            camera_table = Table(show_header=True)
            camera_table.add_column("相机", style="cyan")
            camera_table.add_column("照片数", justify="right")
            camera_table.add_column("帖子数", justify="right")
            camera_table.add_column("平均ISO", justify="right")
            camera_table.add_column("平均光圈", justify="right")
            camera_table.add_column("平均焦距", justify="right")

            for cam in cameras:
                camera_name = f"{cam['make']} {cam['model']}"
                camera_table.add_row(
                    camera_name,
                    str(cam['photo_count']),
                    str(cam['post_count']),
                    str(int(cam['avg_iso'])) if cam['avg_iso'] else 'N/A',
                    f"f/{cam['avg_aperture']}" if cam['avg_aperture'] else 'N/A',
                    f"{int(cam['avg_focal_length'])}mm" if cam['avg_focal_length'] else 'N/A'
                )

            console.print(camera_table)
        else:
            console.print("   [yellow]暂无相机数据[/yellow]")
        console.print()

        # 3. 拍摄地点排行（如果有）
        if row['has_location'] > 0:
            console.print("[bold]📍 拍摄地点排行（Top 5）：[/bold]")
            cursor = conn.execute("""
                SELECT * FROM v_location_stats LIMIT 5
            """)
            locations = cursor.fetchall()

            if locations:
                location_table = Table(show_header=True)
                location_table.add_column("地点", style="cyan")
                location_table.add_column("照片数", justify="right")
                location_table.add_column("帖子数", justify="right")

                for loc in locations:
                    location_table.add_row(
                        loc['location'],
                        str(loc['photo_count']),
                        str(loc['post_count'])
                    )

                console.print(location_table)
            console.print()

        # 4. 有 EXIF 的图片示例
        console.print("[bold]🖼️  有 EXIF 的图片示例（前 10 张）：[/bold]")
        cursor = conn.execute("""
            SELECT
                file_name,
                exif_make,
                exif_model,
                exif_aperture,
                exif_shutter_speed,
                exif_iso,
                exif_focal_length,
                exif_datetime,
                exif_location
            FROM media
            WHERE type = 'image'
              AND exif_make IS NOT NULL
            LIMIT 10
        """)
        images = cursor.fetchall()

        if images:
            img_table = Table(show_header=True)
            img_table.add_column("文件名", style="cyan", max_width=25)
            img_table.add_column("相机", max_width=20)
            img_table.add_column("参数", max_width=30)
            img_table.add_column("时间", max_width=20)
            img_table.add_column("地点", max_width=15)

            for img in images:
                camera = f"{img['exif_make']} {img['exif_model']}" if img['exif_make'] and img['exif_model'] else 'N/A'

                params_parts = []
                if img['exif_aperture']:
                    params_parts.append(f"f/{img['exif_aperture']}")
                if img['exif_shutter_speed']:
                    params_parts.append(f"{img['exif_shutter_speed']}s")
                if img['exif_iso']:
                    params_parts.append(f"ISO{img['exif_iso']}")
                if img['exif_focal_length']:
                    params_parts.append(f"{int(img['exif_focal_length'])}mm")
                params = " · ".join(params_parts) if params_parts else 'N/A'

                datetime = img['exif_datetime'][:19] if img['exif_datetime'] else 'N/A'
                location = img['exif_location'][:15] if img['exif_location'] else 'N/A'

                img_table.add_row(
                    img['file_name'][:25],
                    camera[:20],
                    params[:30],
                    datetime,
                    location
                )

            console.print(img_table)
        else:
            console.print("   [yellow]暂无包含 EXIF 的图片[/yellow]")
            console.print()
            console.print("   [dim]💡 提示：运行以下命令提取 EXIF：[/dim]")
            console.print("   [dim]   cd python && python3 -m src.database.migrate_exif --limit 100 --no-gps[/dim]")
        console.print()

        # 5. 总结
        console.print("─" * 60)
        if row['has_make'] > 0:
            console.print(f"[green]✅ 已提取 {row['has_make']} 张图片的 EXIF 数据！[/green]")
            if row['has_gps'] > 0:
                console.print(f"[green]✅ 其中 {row['has_gps']} 张包含 GPS 信息[/green]")
        else:
            console.print("[yellow]⚠️  尚未提取 EXIF 数据[/yellow]")
            console.print()
            console.print("[dim]💡 运行以下命令开始提取：[/dim]")
            console.print("[dim]   cd python && python3 -m src.database.migrate_exif --limit 50 --no-gps[/dim]")

    except Exception as e:
        console.print(f"[red]❌ 错误: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
