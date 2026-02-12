"""主菜单系统"""
import asyncio
from datetime import datetime
import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Dict, Any

from ..config.manager import ConfigManager
from ..bridge.nodejs_bridge import NodeJSBridge
from ..utils.display import show_author_table, show_warning


class MainMenu:
    """主菜单系统"""

    custom_style = Style([
        ('qmark', 'fg:#673ab7 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#f44336 bold'),
        ('pointer', 'fg:#673ab7 bold'),
        ('highlighted', 'fg:#673ab7 bold'),
        ('selected', 'fg:#cc5454'),
    ])

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.console = Console()
        self.config_manager = ConfigManager()
        self.bridge = NodeJSBridge(config['legacy']['nodejs_path'])

    def run(self) -> None:
        """运行主菜单"""
        while True:
            self._show_status()
            choice = self._show_main_menu()

            if choice is None:  # 用户取消
                break

            if "关注新作者" in choice:
                self._follow_author()
            elif "查看关注列表" in choice:
                self._view_followed_authors()
            elif "立即更新" in choice:
                self._run_update()
            elif "取消关注" in choice:
                self._unfollow_author()
            elif "系统设置" in choice:
                self._show_settings()
            elif "查看统计" in choice:
                self._show_statistics()
            elif "数据分析" in choice:
                self._show_analysis()
            elif "退出" in choice:
                self.console.print("[yellow]再见！[/yellow]")
                break

    def _show_status(self) -> None:
        """显示系统状态"""
        self.console.clear()
        self.console.print(Panel(
            f"[cyan]关注作者:[/cyan] {len(self.config['followed_authors'])} 位\n"
            f"[cyan]论坛版块:[/cyan] {self.config['forum']['section_url']}\n"
            f"[cyan]归档路径:[/cyan] {self.config['storage']['archive_path']}",
            title="📊 论坛作者订阅归档系统",
            border_style="cyan"
        ))

    def _show_main_menu(self) -> str:
        """显示主菜单"""
        choices = [
            "🔍 关注新作者（通过帖子链接）",
            "📋 查看关注列表",
            "🔄 立即更新所有作者",
            "❌ 取消关注作者",
            "⚙️  系统设置",
            "📊 查看统计（Phase 3 后可用）",
            "📈 数据分析（Phase 4 后可用）",
            "🚪 退出"
        ]

        return questionary.select(
            "\n请选择操作：",
            choices=choices,
            style=self.custom_style
        ).ask()

    def _follow_author(self) -> None:
        """关注新作者"""
        self.console.print("\n[bold]🔍 关注新作者[/bold]\n")

        post_url = questionary.text(
            "请输入帖子 URL:",
            style=self.custom_style,
            validate=lambda x: len(x) > 0
        ).ask()

        if not post_url:
            return

        self.console.print(f"\n[cyan]正在调用 Node.js 脚本处理...[/cyan]\n")

        # 调用 Node.js 脚本
        stdout, stderr, returncode = self.bridge.follow_author(post_url)

        if returncode == 0:
            self.console.print(f"\n[green]✓ 操作完成[/green]")

            # 重要：同步配置（Node.js 修改了 config.json，需要同步到 config.yaml）
            self._sync_config_from_nodejs()

            # 重新加载配置
            self.config = self.config_manager.load()
        else:
            self.console.print(f"\n[red]✗ 操作失败[/red]")

        questionary.press_any_key_to_continue("按任意键继续...").ask()

    def _view_followed_authors(self) -> None:
        """查看关注列表"""
        self.console.print("\n[bold]📋 关注列表[/bold]\n")

        if not self.config['followed_authors']:
            show_warning("暂无关注的作者", "提示")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        # 显示作者表格
        show_author_table(self.config['followed_authors'])

        questionary.press_any_key_to_continue("\n按任意键返回...").ask()

    def _run_update(self) -> None:
        """立即更新所有作者"""
        self.console.print("\n[bold]🔄 立即更新[/bold]\n")

        if not self.config['followed_authors']:
            show_warning("暂无关注的作者，无需更新", "提示")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        confirm = questionary.confirm(
            f"确认为 {len(self.config['followed_authors'])} 位作者执行更新？",
            default=True,
            style=self.custom_style
        ).ask()

        if not confirm:
            return

        # 检查是否使用 Python 爬虫
        use_python = self.config.get('experimental', {}).get('use_python_scraper', False)

        if use_python:
            self.console.print(f"\n[cyan]🐍 使用 Python 爬虫更新...[/cyan]\n")
            try:
                # Run async Python scraper
                # Try to use existing event loop, or create new one
                try:
                    # Check if there's already a running event loop
                    asyncio.get_running_loop()
                    # If we get here, loop is running - use new_event_loop()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._run_python_scraper())
                    finally:
                        loop.close()
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run()
                    asyncio.run(self._run_python_scraper())
                return
            except Exception as e:
                self.console.print(f"\n[red]✗ Python 爬虫失败: {str(e)}[/red]")
                self.console.print(f"[yellow]⚠ 回退到 Node.js 爬虫...[/yellow]\n")
                # Fall through to Node.js scraper

        # 使用 Node.js 爬虫（默认或回退）
        self.console.print(f"\n[cyan]正在调用 Node.js 脚本更新...[/cyan]\n")

        # 调用 Node.js 脚本
        stdout, stderr, returncode = self.bridge.run_update()

        if returncode == 0:
            self.console.print(f"\n[green]✓ 更新完成[/green]")

            # 同步配置（以防 Node.js 脚本有变更）
            self._sync_config_from_nodejs()
        else:
            self.console.print(f"\n[red]✗ 更新失败[/red]")

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    async def _run_python_scraper(self) -> None:
        """运行 Python 爬虫更新（异步）"""
        from ..scraper.archiver import ForumArchiver

        archiver = ForumArchiver(self.config)

        # 准备需要更新的作者列表
        authors_to_update = self.config['followed_authors']

        for idx, author in enumerate(authors_to_update, 1):
            author_name = author['name']
            author_url = author.get('url')

            if not author_url:
                self.console.print(
                    f"[yellow]⚠ 跳过作者 {author_name}（无 URL）[/yellow]"
                )
                continue

            self.console.print(
                f"\n[bold cyan]({idx}/{len(authors_to_update)}) "
                f"更新作者: {author_name}[/bold cyan]"
            )

            try:
                # 🧪 测试模式：限制为 1 页（约 50 篇帖子）
                # 正式使用时改为 None（抓取全部）
                max_pages = 1  # None = 抓取全部，1 = 只测试 1 页
                result = await archiver.archive_author(author_name, author_url, max_pages)

                # 显示结果
                self.console.print(
                    f"  [green]✓ 完成:[/green] "
                    f"新增 {result['new']} 篇, "
                    f"跳过 {result['skipped']} 篇, "
                    f"失败 {result['failed']} 篇"
                )

                # 更新配置中的统计信息（可选）
                author['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                author['total_posts'] = author.get('total_posts', 0) + result['new']

            except Exception as e:
                self.console.print(
                    f"  [red]✗ 失败: {str(e)}[/red]"
                )

        # 保存更新后的配置
        self.config_manager.save(self.config)

        self.console.print(f"\n[green]✓ 所有作者更新完成[/green]")
        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _unfollow_author(self) -> None:
        """取消关注作者"""
        self.console.print("\n[bold]❌ 取消关注[/bold]\n")

        if not self.config['followed_authors']:
            show_warning("暂无关注的作者", "提示")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        # 选择作者
        author_choices = [a['name'] for a in self.config['followed_authors']]
        author_choices.append("← 返回")

        author_name = questionary.select(
            "选择要取消关注的作者：",
            choices=author_choices,
            style=self.custom_style
        ).ask()

        if author_name == "← 返回" or not author_name:
            return

        # 确认
        confirm = questionary.confirm(
            f"确认取消关注 {author_name}？（不会删除已归档的内容）",
            default=False,
            style=self.custom_style
        ).ask()

        if confirm:
            self.config_manager.remove_author(author_name)
            self.config = self.config_manager.load()

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _show_settings(self) -> None:
        """显示设置菜单"""
        while True:
            self.console.print("\n[bold]⚙️  系统设置[/bold]\n")

            setting_choices = [
                "修改论坛版块 URL",
                "修改归档路径",
                "下载选项设置",
                "查看完整配置",
                "← 返回"
            ]

            choice = questionary.select(
                "选择设置项：",
                choices=setting_choices,
                style=self.custom_style
            ).ask()

            if not choice or choice == "← 返回":
                break

            if "论坛版块" in choice:
                self._edit_forum_url()
            elif "归档路径" in choice:
                self._edit_archive_path()
            elif "下载选项" in choice:
                self._edit_download_options()
            elif "完整配置" in choice:
                self._view_full_config()

    def _edit_forum_url(self) -> None:
        """修改论坛 URL"""
        current = self.config['forum']['section_url']
        self.console.print(f"当前 URL: [cyan]{current}[/cyan]")

        new_url = questionary.text(
            "新 URL:",
            default=current,
            style=self.custom_style
        ).ask()

        if new_url and new_url != current:
            self.config['forum']['section_url'] = new_url
            self.config_manager.save(self.config)
            self.console.print("[green]✓ 已更新[/green]")

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _edit_archive_path(self) -> None:
        """修改归档路径"""
        current = self.config['storage']['archive_path']
        self.console.print(f"当前路径: [cyan]{current}[/cyan]")

        new_path = questionary.text(
            "新路径:",
            default=current,
            style=self.custom_style
        ).ask()

        if new_path and new_path != current:
            self.config['storage']['archive_path'] = new_path
            self.config_manager.save(self.config)
            self.console.print("[green]✓ 已更新[/green]")

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _edit_download_options(self) -> None:
        """修改下载选项"""
        download_images = questionary.confirm(
            "下载图片?",
            default=self.config['storage']['download']['images'],
            style=self.custom_style
        ).ask()

        download_videos = questionary.confirm(
            "下载视频?",
            default=self.config['storage']['download']['videos'],
            style=self.custom_style
        ).ask()

        self.config['storage']['download']['images'] = download_images
        self.config['storage']['download']['videos'] = download_videos
        self.config_manager.save(self.config)

        self.console.print("[green]✓ 已更新[/green]")
        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _view_full_config(self) -> None:
        """查看完整配置"""
        import yaml
        self.console.print("\n[bold]完整配置:[/bold]\n")
        self.console.print(yaml.dump(self.config, allow_unicode=True, sort_keys=False))
        questionary.press_any_key_to_continue("\n按任意键返回...").ask()

    def _show_statistics(self) -> None:
        """查看统计（Phase 3 后实现）"""
        show_warning("此功能将在 Phase 3 实现", "功能暂未实现")
        questionary.press_any_key_to_continue("\n按任意键返回...").ask()

    def _show_analysis(self) -> None:
        """数据分析（Phase 4 后实现）"""
        show_warning("此功能将在 Phase 4 实现", "功能暂未实现")
        questionary.press_any_key_to_continue("\n按任意键返回...").ask()

    def _sync_config_from_nodejs(self) -> None:
        """从 Node.js 的 config.json 同步配置到 config.yaml

        Phase 1 临时方案：Node.js 脚本修改 config.json，需要同步到 config.yaml
        Phase 2 后此方法将废弃
        """
        import json
        from pathlib import Path

        # 读取 Node.js 的 config.json
        json_path = Path(__file__).parent.parent.parent.parent.parent / "config.json"

        if not json_path.exists():
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                nodejs_config = json.load(f)

            # 同步关注列表
            if 'followedAuthors' in nodejs_config:
                # 获取当前 Python 配置
                current_config = self.config_manager.load()

                # 合并作者列表（保留已有的元数据）
                existing_authors = {a['name']: a for a in current_config['followed_authors']}

                for author_name in nodejs_config['followedAuthors']:
                    if author_name not in existing_authors:
                        # 新作者，添加完整信息
                        from datetime import datetime
                        existing_authors[author_name] = {
                            'name': author_name,
                            'added_date': datetime.now().strftime('%Y-%m-%d'),
                            'last_update': None,
                            'total_posts': 0,
                            'total_images': 0,
                            'total_videos': 0,
                            'tags': ['from_nodejs'],
                            'notes': '通过 Node.js 脚本添加'
                        }

                # 更新配置
                current_config['followed_authors'] = list(existing_authors.values())
                self.config_manager.save(current_config)

                self.console.print("[dim]✓ 配置已同步[/dim]")

        except Exception as e:
            self.console.print(f"[yellow]⚠ 配置同步失败: {e}[/yellow]")
