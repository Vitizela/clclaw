"""
EXIF 数据批量迁移工具

功能：
1. 扫描所有已归档图片
2. 批量提取 EXIF 数据
3. 更新数据库 media 表
4. 显示进度和统计

使用方法：
    python -m src.database.migrate_exif

选项：
    --dry-run: 预览模式，不实际写入数据库
    --limit N: 只处理前 N 张图片（用于测试）
    --no-gps: 跳过 GPS 反查（加快速度）
    --force: 强制重新提取已有 EXIF 数据的图片

作者: Claude Sonnet 4.5
日期: 2026-02-14
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import time

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import get_default_connection
from src.database.models import Media
from src.analysis import ExifAnalyzer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.panel import Panel


console = Console()


class ExifMigrator:
    """EXIF 数据批量迁移器"""

    def __init__(
        self,
        dry_run: bool = False,
        skip_gps: bool = False,
        force: bool = False
    ):
        """
        初始化迁移器

        Args:
            dry_run: 预览模式，不写入数据库
            skip_gps: 跳过 GPS 反查
            force: 强制重新提取
        """
        self.dry_run = dry_run
        self.skip_gps = skip_gps
        self.force = force

        self.db = get_default_connection()
        self.exif_analyzer = ExifAnalyzer(self.db)

        # 统计数据
        self.stats = {
            'total': 0,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'has_exif': 0,
            'has_gps': 0,
            'has_location': 0,
            'already_done': 0,
        }

    def get_images_to_process(self, limit: Optional[int] = None) -> List[Dict]:
        """
        获取需要处理的图片列表

        Args:
            limit: 限制数量（用于测试）

        Returns:
            list: Media 记录列表
        """
        conn = self.db.get_connection()

        # 查询条件
        if self.force:
            # 强制模式：处理所有图片
            sql = "SELECT id, file_path, file_name, post_id FROM media WHERE type = 'image' ORDER BY id ASC"
        else:
            # 正常模式：只处理未提取 EXIF 的图片
            sql = "SELECT id, file_path, file_name, post_id FROM media WHERE type = 'image' AND exif_make IS NULL ORDER BY id ASC"

        if limit:
            sql += f" LIMIT {limit}"

        cursor = conn.execute(sql)
        rows = cursor.fetchall()

        return [
            {
                'id': row['id'],
                'file_path': row['file_path'],
                'file_name': row['file_name'],
                'post_id': row['post_id'],
            }
            for row in rows
        ]

    def process_single_image(self, image: Dict) -> bool:
        """
        处理单张图片

        Args:
            image: Media 记录字典

        Returns:
            bool: 是否成功
        """
        file_path = Path(image['file_path'])

        # 处理 .done 标记文件（数据库中可能存储了标记文件路径）
        if file_path.suffix == '.done':
            file_path = file_path.with_suffix('')  # 移除 .done 后缀

        # 检查文件是否存在
        if not file_path.exists():
            # 尝试添加 .done 后缀（可能数据库路径没有 .done）
            done_file = Path(image['file_path'] + '.done')
            if done_file.exists():
                # 使用原始路径（不带 .done）
                file_path = Path(image['file_path'])
            else:
                console.print(f"[yellow]文件不存在: {file_path.name}[/yellow]")
                self.stats['failed'] += 1
                return False

        try:
            # 提取 EXIF
            exif_data = self.exif_analyzer.extract_exif(str(file_path))

            if not exif_data:
                self.stats['skipped'] += 1
                return False

            self.stats['has_exif'] += 1

            # GPS 反查（如果启用）
            if not self.skip_gps and 'gps_lat' in exif_data and 'gps_lng' in exif_data:
                self.stats['has_gps'] += 1

                location = self.exif_analyzer.reverse_geocode(
                    exif_data['gps_lat'],
                    exif_data['gps_lng']
                )

                if location:
                    exif_data['location'] = location
                    self.stats['has_location'] += 1

            # 更新数据库（如果不是预览模式）
            if not self.dry_run:
                self._update_media_exif(image['id'], exif_data)

            self.stats['success'] += 1
            return True

        except Exception as e:
            console.print(f"[red]处理失败: {file_path.name} - {e}[/red]")
            self.stats['failed'] += 1
            return False

    def _update_media_exif(self, media_id: int, exif_data: Dict):
        """更新 Media 表的 EXIF 字段"""
        Media._db = self.db
        media = Media.get_by_id(media_id)

        if media:
            media.update(
                exif_make=exif_data.get('make'),
                exif_model=exif_data.get('model'),
                exif_datetime=exif_data.get('datetime'),
                exif_iso=exif_data.get('iso'),
                exif_aperture=exif_data.get('aperture'),
                exif_shutter_speed=exif_data.get('shutter_speed'),
                exif_focal_length=exif_data.get('focal_length'),
                exif_gps_lat=exif_data.get('gps_lat'),
                exif_gps_lng=exif_data.get('gps_lng'),
                exif_location=exif_data.get('location')
            )

    def run(self, limit: Optional[int] = None):
        """
        运行批量迁移

        Args:
            limit: 限制处理数量（用于测试）
        """
        # 显示配置
        config_table = Table(show_header=False, box=None)
        config_table.add_row("模式", "预览模式 (不写入数据库)" if self.dry_run else "正常模式")
        config_table.add_row("GPS 反查", "跳过" if self.skip_gps else "启用")
        config_table.add_row("强制模式", "是" if self.force else "否")
        if limit:
            config_table.add_row("限制数量", str(limit))

        console.print(Panel(config_table, title="🔧 配置信息", border_style="cyan"))

        # 获取待处理图片
        console.print("\n[cyan]正在扫描数据库...[/cyan]")
        images = self.get_images_to_process(limit)

        if not images:
            console.print("[green]✅ 没有需要处理的图片！[/green]")
            return

        self.stats['total'] = len(images)

        console.print(f"[cyan]找到 {len(images)} 张图片待处理[/cyan]\n")

        # 批量处理
        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]提取 EXIF 数据...",
                total=len(images)
            )

            for image in images:
                self.process_single_image(image)
                self.stats['processed'] += 1
                progress.update(task, advance=1)

        elapsed_time = time.time() - start_time

        # 显示统计结果
        self._show_statistics(elapsed_time)

    def _show_statistics(self, elapsed_time: float):
        """显示统计结果"""
        # 统计表格
        stats_table = Table(title="📊 处理统计", show_header=True)
        stats_table.add_column("项目", style="cyan")
        stats_table.add_column("数量", justify="right", style="green")
        stats_table.add_column("占比", justify="right", style="yellow")

        total = self.stats['total']
        if total == 0:
            return

        def calc_pct(count):
            return f"{count / total * 100:.1f}%"

        stats_table.add_row("总计", str(total), "100.0%")
        stats_table.add_row("已处理", str(self.stats['processed']), calc_pct(self.stats['processed']))
        stats_table.add_row("成功", str(self.stats['success']), calc_pct(self.stats['success']))
        stats_table.add_row("失败", str(self.stats['failed']), calc_pct(self.stats['failed']))
        stats_table.add_row("跳过（无EXIF）", str(self.stats['skipped']), calc_pct(self.stats['skipped']))
        stats_table.add_row("", "", "")
        stats_table.add_row("有 EXIF 数据", str(self.stats['has_exif']), calc_pct(self.stats['has_exif']))
        stats_table.add_row("有 GPS 坐标", str(self.stats['has_gps']), calc_pct(self.stats['has_gps']))

        if not self.skip_gps:
            stats_table.add_row("有地理位置", str(self.stats['has_location']), calc_pct(self.stats['has_location']))

        console.print("\n")
        console.print(stats_table)

        # 性能信息
        speed = self.stats['processed'] / elapsed_time if elapsed_time > 0 else 0

        perf_table = Table(show_header=False, box=None)
        perf_table.add_row("总耗时", f"{elapsed_time:.2f} 秒")
        perf_table.add_row("处理速度", f"{speed:.1f} 张/秒")

        console.print(Panel(perf_table, title="⚡ 性能信息", border_style="magenta"))

        # 完成提示
        if self.dry_run:
            console.print("\n[yellow]⚠️  预览模式：未实际写入数据库[/yellow]")
        else:
            console.print(f"\n[green]✅ 迁移完成！{self.stats['success']}/{total} 张图片成功提取 EXIF[/green]")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="EXIF 数据批量迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.database.migrate_exif                    # 正常运行
  python -m src.database.migrate_exif --dry-run          # 预览模式
  python -m src.database.migrate_exif --limit 100        # 只处理 100 张图片
  python -m src.database.migrate_exif --no-gps           # 跳过 GPS 反查（更快）
  python -m src.database.migrate_exif --force            # 强制重新提取所有图片
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际写入数据库'
    )

    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='只处理前 N 张图片（用于测试）'
    )

    parser.add_argument(
        '--no-gps',
        action='store_true',
        help='跳过 GPS 反查（加快速度）'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新提取已有 EXIF 数据的图片'
    )

    args = parser.parse_args()

    # 显示标题
    console.print(Panel.fit(
        "[bold cyan]EXIF 数据批量迁移工具[/bold cyan]\n"
        "[dim]Phase 4: 图片元数据分析[/dim]",
        border_style="cyan"
    ))

    try:
        migrator = ExifMigrator(
            dry_run=args.dry_run,
            skip_gps=args.no_gps,
            force=args.force
        )

        migrator.run(limit=args.limit)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  用户中断[/yellow]")
        sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]❌ 错误: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
