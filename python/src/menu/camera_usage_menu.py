#!/usr/bin/env python3
"""
相机使用分析菜单模块
用于分析相机型号与作者、时间的关系
"""

import sys
from pathlib import Path
from typing import Optional

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from database.connection import get_default_connection
from database.query import (
    get_camera_usage_by_authors,
    get_camera_usage_timeline,
    get_author_camera_usage
)

console = Console()


def show_camera_usage_menu() -> None:
    """显示相机使用分析主菜单"""
    while True:
        console.print()
        console.print(Panel.fit(
            "[bold cyan]相机使用分析[/bold cyan]\n"
            "分析相机型号与作者、时间的关系",
            border_style="cyan"
        ))

        console.print("\n[bold]请选择操作：[/bold]")
        console.print("  [cyan]1.[/cyan] 查询相机与作者关联")
        console.print("  [cyan]2.[/cyan] 查询相机使用时间线")
        console.print("  [cyan]3.[/cyan] 查询作者相机统计")
        console.print("  [cyan]0.[/cyan] 返回上级菜单")

        choice = Prompt.ask(
            "\n[bold yellow]请输入选项[/bold yellow]",
            choices=["0", "1", "2", "3"],
            default="0"
        )

        if choice == "0":
            break
        elif choice == "1":
            _show_camera_author_usage()
        elif choice == "2":
            _show_camera_timeline()
        elif choice == "3":
            _show_author_camera_stats()


def _show_camera_author_usage() -> None:
    """显示相机与作者关联查询"""
    console.print("\n[bold cyan]═══ 相机与作者关联查询 ═══[/bold cyan]\n")

    # 询问过滤条件
    console.print("[dim]支持按相机制造商、型号、作者名过滤（留空则查询全部）[/dim]")
    camera_make = Prompt.ask("相机制造商 (如 Apple, vivo)", default="")
    camera_model = Prompt.ask("相机型号 (如 iPhone 13 Pro)", default="")
    author_name = Prompt.ask("作者名 (如 同花顺心)", default="")
    limit = Prompt.ask("显示数量", default="50")

    # 构建过滤参数
    kwargs = {"limit": int(limit)}
    if camera_make:
        kwargs["camera_make"] = camera_make
    if camera_model:
        kwargs["camera_model"] = camera_model
    if author_name:
        kwargs["author_name"] = author_name

    # 查询数据
    try:
        db = get_default_connection()
        results = get_camera_usage_by_authors(**kwargs, db=db)

        if not results:
            console.print("\n[yellow]未找到匹配的数据[/yellow]")
            return

        # 显示结果表格
        table = Table(
            title=f"相机与作者关联查询结果（共 {len(results)} 条）",
            show_header=True,
            header_style="bold magenta",
            border_style="blue"
        )

        table.add_column("相机型号", style="cyan", no_wrap=True)
        table.add_column("作者", style="green")
        table.add_column("照片数", justify="right", style="yellow")
        table.add_column("帖子数", justify="right", style="yellow")
        table.add_column("首次使用", style="dim")
        table.add_column("最近使用", style="dim")
        table.add_column("平均ISO", justify="right", style="magenta")
        table.add_column("平均光圈", justify="right", style="magenta")
        table.add_column("平均焦距", justify="right", style="magenta")

        for row in results:
            table.add_row(
                row['camera_full'],
                row['author_name'],
                str(row['photo_count']),
                str(row['post_count']),
                row['first_use_date'][:10] if row['first_use_date'] else '-',
                row['last_use_date'][:10] if row['last_use_date'] else '-',
                str(int(row['avg_iso'])) if row['avg_iso'] else '-',
                f"f/{row['avg_aperture']}" if row['avg_aperture'] else '-',
                f"{int(row['avg_focal_length'])}mm" if row['avg_focal_length'] else '-'
            )

        console.print()
        console.print(table)

    except Exception as e:
        console.print(f"\n[red]查询失败: {e}[/red]")


def _show_camera_timeline() -> None:
    """显示相机使用时间线查询"""
    console.print("\n[bold cyan]═══ 相机使用时间线查询 ═══[/bold cyan]\n")

    # 必填：相机信息
    camera_make = Prompt.ask("相机制造商 (必填，如 Apple, vivo)")
    camera_model = Prompt.ask("相机型号 (必填，如 iPhone 13 Pro)")

    if not camera_make or not camera_model:
        console.print("[yellow]相机制造商和型号为必填项[/yellow]")
        return

    # 可选：时间过滤
    console.print("\n[dim]可按年份、月份过滤（留空则查询全部）[/dim]")
    year_input = Prompt.ask("年份 (如 2024)", default="")
    month_input = Prompt.ask("月份 (如 12)", default="")
    author_name = Prompt.ask("作者名 (可选)", default="")

    # 构建过滤参数
    kwargs = {
        "camera_make": camera_make,
        "camera_model": camera_model
    }
    if year_input:
        kwargs["year"] = int(year_input)
    if month_input:
        kwargs["month"] = int(month_input)
    if author_name:
        kwargs["author_name"] = author_name

    # 查询数据
    try:
        db = get_default_connection()
        results = get_camera_usage_timeline(**kwargs, db=db)

        if not results:
            console.print("\n[yellow]未找到匹配的数据[/yellow]")
            return

        # 显示结果表格
        table = Table(
            title=f"{camera_make} {camera_model} 使用时间线（共 {len(results)} 条）",
            show_header=True,
            header_style="bold magenta",
            border_style="blue"
        )

        table.add_column("日期", style="cyan", no_wrap=True)
        table.add_column("年份", justify="right", style="dim")
        table.add_column("月份", justify="right", style="dim")
        table.add_column("照片数", justify="right", style="yellow")
        table.add_column("帖子数", justify="right", style="yellow")
        table.add_column("作者", style="green")

        for row in results:
            table.add_row(
                row['date'],
                str(row['year']),
                str(row['month']),
                str(row['photo_count']),
                str(row['post_count']),
                row['authors'] or '-'
            )

        console.print()
        console.print(table)

        # 显示汇总统计
        total_photos = sum(r['photo_count'] for r in results)
        total_posts = sum(r['post_count'] for r in results)
        date_range = f"{results[-1]['date']} 至 {results[0]['date']}" if len(results) > 1 else results[0]['date']

        console.print(f"\n[bold]汇总统计：[/bold]")
        console.print(f"  时间范围: {date_range}")
        console.print(f"  总照片数: [yellow]{total_photos}[/yellow] 张")
        console.print(f"  总帖子数: [yellow]{total_posts}[/yellow] 篇")

    except Exception as e:
        console.print(f"\n[red]查询失败: {e}[/red]")


def _show_author_camera_stats() -> None:
    """显示作者相机统计查询"""
    console.print("\n[bold cyan]═══ 作者相机统计查询 ═══[/bold cyan]\n")

    # 输入作者名
    author_name = Prompt.ask("作者名 (必填，如 同花顺心)")

    if not author_name:
        console.print("[yellow]作者名为必填项[/yellow]")
        return

    # 查询数据
    try:
        db = get_default_connection()
        result = get_author_camera_usage(author_name, db=db)

        if result['total_cameras'] == 0:
            console.print(f"\n[yellow]作者 '{author_name}' 没有相机使用数据[/yellow]")
            return

        # 显示作者基本统计
        console.print(f"\n[bold]作者：[/bold][cyan]{result['author_name']}[/cyan]")
        console.print(f"[bold]使用相机数量：[/bold][yellow]{result['total_cameras']}[/yellow] 款")
        console.print(f"[bold]总照片数：[/bold][yellow]{result['total_photos']}[/yellow] 张")

        # 显示相机使用详情表格
        if result['cameras']:
            table = Table(
                title="相机使用详情",
                show_header=True,
                header_style="bold magenta",
                border_style="blue"
            )

            table.add_column("排名", justify="right", style="dim")
            table.add_column("相机型号", style="cyan", no_wrap=True)
            table.add_column("照片数", justify="right", style="yellow")
            table.add_column("占比", justify="right", style="green")
            table.add_column("帖子数", justify="right", style="yellow")
            table.add_column("首次使用", style="dim")
            table.add_column("最近使用", style="dim")

            for idx, camera in enumerate(result['cameras'], 1):
                # 高亮最常用相机
                rank_style = "bold red" if idx == 1 else "dim"

                table.add_row(
                    str(idx),
                    camera['camera_full'],
                    str(camera['photo_count']),
                    f"{camera['usage_percent']:.1f}%",
                    str(camera['post_count']),
                    camera['first_use'] if camera['first_use'] else '-',
                    camera['last_use'] if camera['last_use'] else '-',
                    style=rank_style if idx == 1 else None
                )

            console.print()
            console.print(table)

            # 显示使用习惯分析
            console.print("\n[bold]使用习惯分析：[/bold]")
            top_camera = result['cameras'][0]
            console.print(f"  最常用相机: [cyan]{top_camera['camera_full']}[/cyan] "
                         f"([yellow]{top_camera['usage_percent']:.1f}%[/yellow])")

            if result['total_cameras'] >= 3:
                console.print(f"  相机多样性: [green]高[/green] (使用了 {result['total_cameras']} 款相机)")
            elif result['total_cameras'] == 2:
                console.print(f"  相机多样性: [yellow]中等[/yellow] (使用了 2 款相机)")
            else:
                console.print(f"  相机多样性: [dim]低[/dim] (仅使用 1 款相机)")

    except Exception as e:
        console.print(f"\n[red]查询失败: {e}[/red]")


def main():
    """主函数（用于独立测试）"""
    try:
        show_camera_usage_menu()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]已取消操作[/yellow]")
    except Exception as e:
        console.print(f"\n[red]发生错误: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
