#!/usr/bin/env python3
"""
分析菜单 - 数据分析功能交互界面

功能:
- 生成作者分析报告
- 生成全局分析报告
- 查看已生成的图表
- 返回主菜单

作者: Claude Sonnet 4.5
日期: 2026-02-15
"""

import logging
import questionary
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..database.connection import get_default_connection
from ..database.models import Author
from ..analysis.report_generator import ReportGenerator

logger = logging.getLogger(__name__)
console = Console()


class AnalysisMenu:
    """分析菜单类"""

    def __init__(self, db_connection=None):
        """
        初始化分析菜单

        Args:
            db_connection: 数据库连接（可选）
        """
        if db_connection is None:
            db_connection = get_default_connection()

        self.db_connection = db_connection
        self.report_generator = ReportGenerator(db_connection=db_connection)

        # 设置数据库
        Author._db = self.db_connection

    def show(self):
        """显示分析菜单"""
        while True:
            console.clear()
            console.print(Panel.fit(
                "[bold cyan]📊 数据分析[/bold cyan]",
                border_style="cyan"
            ))
            console.print()

            choice = questionary.select(
                "请选择操作:",
                choices=[
                    "📝 生成作者分析报告",
                    "🌍 生成全局分析报告",
                    "📁 查看已生成的报告",
                    "🔙 返回主菜单"
                ],
                style=questionary.Style([
                    ('selected', 'fg:cyan bold'),
                    ('pointer', 'fg:cyan bold'),
                ])
            ).ask()

            if choice is None or choice == "🔙 返回主菜单":
                break
            elif choice == "📝 生成作者分析报告":
                self._generate_author_report()
            elif choice == "🌍 生成全局分析报告":
                self._generate_global_report()
            elif choice == "📁 查看已生成的报告":
                self._view_reports()

    def _generate_author_report(self):
        """生成作者分析报告"""
        console.print("\n[cyan]生成作者分析报告[/cyan]")
        console.print()

        # 获取所有作者
        authors = Author.get_all()
        if not authors:
            console.print("[yellow]⚠️  数据库中没有作者数据[/yellow]")
            input("\n按回车键继续...")
            return

        # 选择作者
        author_choices = [f"{author.name} ({author.total_posts} 篇)" for author in authors]
        author_choices.append("🔙 返回")

        selected = questionary.select(
            "选择作者:",
            choices=author_choices,
            style=questionary.Style([
                ('selected', 'fg:cyan bold'),
                ('pointer', 'fg:cyan bold'),
            ])
        ).ask()

        if selected is None or selected == "🔙 返回":
            return

        # 提取作者名
        author_name = selected.split(" (")[0]

        # 生成报告
        console.print(f"\n[cyan]正在生成报告: {author_name}[/cyan]")
        console.print()

        with console.status("[bold cyan]生成中..."):
            output_path = self.report_generator.generate_author_report(author_name)

        if output_path:
            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            console.print(f"\n[green]✅ 报告生成成功！[/green]")
            console.print(f"\n文件路径: [cyan]{output_path}[/cyan]")
            console.print(f"文件大小: [cyan]{file_size:.2f} MB[/cyan]")
            console.print(f"\n💡 使用浏览器打开该文件即可查看报告")

            # 询问是否打开
            if questionary.confirm("是否立即打开报告？", default=False).ask():
                self._open_file(output_path)
        else:
            console.print("\n[red]❌ 报告生成失败[/red]")

        input("\n按回车键继续...")

    def _generate_global_report(self):
        """生成全局分析报告"""
        console.print("\n[cyan]生成全局分析报告[/cyan]")
        console.print()

        # 确认生成
        if not questionary.confirm(
            "生成全局报告可能需要较长时间，是否继续？",
            default=True
        ).ask():
            return

        # 生成报告
        console.print(f"\n[cyan]正在生成全局报告...[/cyan]")
        console.print()

        with console.status("[bold cyan]生成中..."):
            output_path = self.report_generator.generate_global_report()

        if output_path:
            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            console.print(f"\n[green]✅ 报告生成成功！[/green]")
            console.print(f"\n文件路径: [cyan]{output_path}[/cyan]")
            console.print(f"文件大小: [cyan]{file_size:.2f} MB[/cyan]")
            console.print(f"\n💡 使用浏览器打开该文件即可查看报告")

            # 询问是否打开
            if questionary.confirm("是否立即打开报告？", default=False).ask():
                self._open_file(output_path)
        else:
            console.print("\n[red]❌ 报告生成失败[/red]")

        input("\n按回车键继续...")

    def _view_reports(self):
        """查看已生成的报告"""
        console.print("\n[cyan]已生成的报告[/cyan]")
        console.print()

        # 获取报告目录
        reports_dir = Path(__file__).parent.parent.parent / 'data' / 'reports'
        if not reports_dir.exists():
            console.print("[yellow]⚠️  还没有生成任何报告[/yellow]")
            input("\n按回车键继续...")
            return

        # 获取所有 HTML 文件
        reports = sorted(reports_dir.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True)

        if not reports:
            console.print("[yellow]⚠️  还没有生成任何报告[/yellow]")
            input("\n按回车键继续...")
            return

        # 创建表格
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("序号", style="dim", width=6)
        table.add_column("文件名", style="cyan")
        table.add_column("大小", justify="right")
        table.add_column("修改时间")

        for i, report in enumerate(reports, 1):
            file_size = report.stat().st_size / (1024 * 1024)
            mtime = report.stat().st_mtime
            mtime_str = Path(report).stat().st_mtime
            import datetime
            mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

            table.add_row(
                str(i),
                report.name,
                f"{file_size:.2f} MB",
                mtime_str
            )

        console.print(table)
        console.print()

        # 选择操作
        choice = questionary.select(
            "请选择操作:",
            choices=[
                "📂 打开报告",
                "🗑️  删除报告",
                "🔙 返回"
            ],
            style=questionary.Style([
                ('selected', 'fg:cyan bold'),
                ('pointer', 'fg:cyan bold'),
            ])
        ).ask()

        if choice == "📂 打开报告":
            report_num = questionary.text(
                "输入序号:",
                validate=lambda x: x.isdigit() and 1 <= int(x) <= len(reports)
            ).ask()

            if report_num:
                report_path = reports[int(report_num) - 1]
                self._open_file(str(report_path))

        elif choice == "🗑️  删除报告":
            report_num = questionary.text(
                "输入序号:",
                validate=lambda x: x.isdigit() and 1 <= int(x) <= len(reports)
            ).ask()

            if report_num:
                report_path = reports[int(report_num) - 1]
                if questionary.confirm(f"确定删除 {report_path.name}？", default=False).ask():
                    report_path.unlink()
                    console.print(f"\n[green]✅ 已删除: {report_path.name}[/green]")
                    input("\n按回车键继续...")

    def _open_file(self, file_path: str):
        """
        打开文件（跨平台）

        Args:
            file_path: 文件路径
        """
        import platform
        import subprocess

        try:
            system = platform.system()
            if system == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            elif system == 'Linux':
                subprocess.run(['xdg-open', file_path])
            elif system == 'Windows':
                subprocess.run(['start', file_path], shell=True)
            else:
                console.print(f"[yellow]⚠️  无法自动打开文件，请手动打开: {file_path}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️  打开失败: {e}[/yellow]")
            console.print(f"[yellow]请手动打开: {file_path}[/yellow]")


def show_analysis_menu():
    """显示分析菜单（独立函数）"""
    menu = AnalysisMenu()
    menu.show()


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO)
    show_analysis_menu()
