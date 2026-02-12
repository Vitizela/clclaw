"""界面显示工具

提供统一的界面显示功能
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Dict, Any


console = Console()


def show_info(message: str, title: str = "信息"):
    """显示信息面板"""
    console.print(Panel(message, title=f"ℹ️  {title}", border_style="blue"))


def show_success(message: str, title: str = "成功"):
    """显示成功面板"""
    console.print(Panel(f"[green]{message}[/green]", title=f"✅ {title}", border_style="green"))


def show_error(message: str, title: str = "错误"):
    """显示错误面板"""
    console.print(Panel(f"[red]{message}[/red]", title=f"❌ {title}", border_style="red"))


def show_warning(message: str, title: str = "警告"):
    """显示警告面板"""
    console.print(Panel(f"[yellow]{message}[/yellow]", title=f"⚠️  {title}", border_style="yellow"))


def show_author_table(authors: List[Dict[str, Any]], show_last_update: bool = True):
    """显示作者列表表格

    Args:
        authors: 作者列表
        show_last_update: 是否显示上次更新时间
    """
    table = Table(title=f"当前关注 {len(authors)} 位作者")
    table.add_column("序号", style="cyan", justify="right", width=4)
    table.add_column("作者名", style="green")

    if show_last_update:
        table.add_column("上次更新", style="yellow", width=16)

    table.add_column("关注日期", style="magenta", width=10)
    table.add_column("帖子数", justify="right", width=6)
    table.add_column("标签", style="dim")

    for i, author in enumerate(authors, 1):
        row_data = [
            str(i),
            author['name'],
        ]

        if show_last_update:
            last_update = author.get('last_update', 'N/A')
            # 格式化时间：2026-02-11 22:28:01 -> 02-11 22:28
            if last_update and last_update != 'N/A':
                try:
                    last_update = last_update[5:16]
                except:
                    pass
            row_data.append(last_update)

        row_data.extend([
            author.get('added_date', 'N/A'),
            str(author.get('total_posts', 0)),
            ', '.join(author.get('tags', []))
        ])

        table.add_row(*row_data)

    console.print(table)
