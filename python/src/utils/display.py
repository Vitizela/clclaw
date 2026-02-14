"""界面显示工具

提供统一的界面显示功能
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Dict, Any


console = Console()


def format_archive_progress(author: Dict[str, Any]) -> str:
    """格式化归档进度显示

    Args:
        author: 作者数据字典，包含 total_posts 和 forum_total_posts

    Returns:
        格式化的进度字符串

    Examples:
        >>> format_archive_progress({'total_posts': 80, 'forum_total_posts': 120})
        '80/120 (67%)'

        >>> format_archive_progress({'total_posts': 80, 'forum_total_posts': None})
        '80'

        >>> format_archive_progress({'total_posts': 50, 'forum_total_posts': 50})
        '50/50 (100%) ✓'

        >>> format_archive_progress({'total_posts': 0, 'forum_total_posts': 120})
        '0/120 (0%)'
    """
    archived = author.get('total_posts', 0)
    forum_total = author.get('forum_total_posts')

    # 情况1: 没有论坛总数（旧数据或获取失败）
    if forum_total is None or forum_total == 0:
        return str(archived)

    # 情况2: 有论坛总数
    # 计算百分比（避免除以0）
    if forum_total > 0:
        percentage = int((archived / forum_total) * 100)
    else:
        percentage = 0

    # 情况3: 已完整归档（>=100%）
    if percentage >= 100:
        return f"{archived}/{forum_total} (100%) ✓"

    # 情况4: 部分归档
    return f"{archived}/{forum_total} ({percentage}%)"


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


def show_author_table(
    authors: List[Dict[str, Any]],
    show_last_update: bool = True,
    last_selected: List[str] = None
):
    """显示作者列表表格

    Args:
        authors: 作者列表
        show_last_update: 是否显示上次更新时间
        last_selected: 上次选择的作者名列表（用于显示 ✅/⬜ 标记）
    """
    table = Table(title=f"当前关注 {len(authors)} 位作者")

    # 如果提供了上次选择的数据，添加状态列
    if last_selected:
        table.add_column("状态", justify="center", width=4)

    table.add_column("序号", style="cyan", justify="right", width=4)
    table.add_column("作者名", style="green")

    if show_last_update:
        table.add_column("上次更新", style="yellow", width=16)

    table.add_column("关注日期", style="magenta", width=10)
    table.add_column("归档进度", justify="right", width=18)
    table.add_column("标签", style="dim")

    for i, author in enumerate(authors, 1):
        row_data = []

        # 添加状态标记（如果提供了 last_selected）
        if last_selected:
            if author['name'] in last_selected:
                row_data.append("[green]✅[/green]")
            else:
                row_data.append("[dim]⬜[/dim]")

        row_data.append(str(i))
        row_data.append(author['name'])

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
            format_archive_progress(author),
            ', '.join(author.get('tags', []))
        ])

        table.add_row(*row_data)

    console.print(table)
