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


def show_author_table(authors: List[Dict[str, Any]]):
    """显示作者列表表格"""
    table = Table(title=f"当前关注 {len(authors)} 位作者")
    table.add_column("序号", style="cyan", justify="right")
    table.add_column("作者名", style="green")
    table.add_column("关注日期", style="yellow")
    table.add_column("帖子数", justify="right")
    table.add_column("标签", style="magenta")

    for i, author in enumerate(authors, 1):
        table.add_row(
            str(i),
            author['name'],
            author.get('added_date', 'N/A'),
            str(author.get('total_posts', 0)),
            ', '.join(author.get('tags', []))
        )

    console.print(table)
