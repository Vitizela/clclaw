"""主菜单系统"""
import asyncio
from datetime import datetime
import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Dict, Any, List

from ..config.manager import ConfigManager
from ..bridge.nodejs_bridge import NodeJSBridge
from ..utils.display import show_author_table, show_warning
from ..utils.keybindings import select_with_keybindings, checkbox_with_keybindings, text_with_keybindings


class MainMenu:
    """主菜单系统"""

    custom_style = Style([
        ('qmark', 'fg:#FFD700 bold'),       # 明亮金黄色
        ('question', 'bold'),
        ('answer', 'fg:#4CAF50 bold'),      # 绿色（更清晰）
        ('pointer', 'fg:#FFD700 bold'),     # 明亮金黄色
        ('highlighted', 'fg:#FFD700 bold'), # 明亮金黄色（高亮）
        ('selected', 'fg:#FFA500'),         # 橙黄色（已选项）
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
        self.console.print("[dim]提示: ESC=退出, ↑↓=导航, Enter=确认[/dim]\n")

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

        return select_with_keybindings(
            "\n请选择操作：",
            choices=choices,
            style=self.custom_style
        )

    def _follow_author(self) -> None:
        """关注新作者"""
        self.console.print("\n[bold]🔍 关注新作者[/bold]\n")
        self.console.print("[dim]提示: ESC 返回, 留空也可返回[/dim]\n")

        post_url = text_with_keybindings(
            "请输入帖子 URL (留空返回):",
            style=self.custom_style,
            validate=lambda x: True  # 允许空输入以返回
        )

        if not post_url or not post_url.strip():
            self.console.print("[yellow]已取消操作[/yellow]")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        self.console.print(f"\n[cyan]正在调用 Node.js 脚本处理...[/cyan]\n")

        # 调用 Node.js 脚本（只添加到关注列表，不立即归档）
        stdout, stderr, returncode = self.bridge.follow_author(post_url, no_archive=True)

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
        """立即更新作者（支持多选和页数设置）"""
        self.console.print("\n[bold]🔄 选择要更新的作者[/bold]\n")

        if not self.config['followed_authors']:
            show_warning("暂无关注的作者，无需更新", "提示")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        # Phase 2-B 需求 1: 显示作者列表
        self.console.print("[cyan]当前关注的作者:[/cyan]\n")
        show_author_table(self.config['followed_authors'])
        self.console.print()  # 空行

        # 智能选择：检查是否有上次的选择
        last_selected = self.config.get('user_preferences', {}).get('last_selected_authors', [])
        remember_enabled = self.config.get('user_preferences', {}).get('remember_selection', True)

        selected_authors = None

        # 如果有上次的选择且启用了记忆功能，提供快速选择
        if last_selected and remember_enabled:
            # 验证上次选择的作者是否仍在关注列表中
            current_author_names = {a['name'] for a in self.config['followed_authors']}
            valid_last_selected = [name for name in last_selected if name in current_author_names]

            if valid_last_selected:
                self.console.print(f"[dim]上次选择了 {len(valid_last_selected)} 位作者: {', '.join(valid_last_selected[:3])}{'...' if len(valid_last_selected) > 3 else ''}[/dim]\n")

                quick_choice = select_with_keybindings(
                    "选择方式:",
                    choices=[
                        questionary.Choice(f"⚡ 使用上次的选择（{len(valid_last_selected)} 位作者）", value='last'),
                        questionary.Choice("🔄 重新选择作者", value='reselect'),
                        questionary.Choice("📚 更新所有作者", value='all'),
                        questionary.Choice("← 返回", value='cancel'),
                    ],
                    style=self.custom_style,
                    default='last'
                )

                if quick_choice is None or quick_choice == 'cancel':  # 用户取消或选择返回
                    return

                if quick_choice == 'last':
                    # 使用上次的选择
                    selected_authors = [a for a in self.config['followed_authors'] if a['name'] in valid_last_selected]
                    self.console.print(f"\n[green]✓ 已加载上次的选择（{len(selected_authors)} 位作者）[/green]\n")
                elif quick_choice == 'all':
                    # 选择所有作者
                    selected_authors = self.config['followed_authors']
                    self.console.print(f"\n[green]✓ 将更新所有作者（{len(selected_authors)} 位）[/green]\n")
                # 如果选择 'reselect'，继续下面的多选界面

        # 如果还没有选择作者（首次使用或选择重新选择），进入多选界面
        if selected_authors is None:
            # Phase 2-B 需求 2: 多选作者界面
            author_choices = []
            for author in self.config['followed_authors']:
                # 显示格式: "作者名 (帖子数 篇)"
                label = f"{author['name']}"
                total_posts = author.get('total_posts', 0)
                if total_posts > 0:
                    label += f" ({total_posts} 篇)"

                # 如果有上次选择，使用上次的选择作为默认；否则全选
                if last_selected:
                    checked = author['name'] in last_selected
                else:
                    checked = True

                author_choices.append(
                    questionary.Choice(
                        title=label,
                        value=author,  # 保存完整的 author 对象
                        checked=checked
                    )
                )

            selected_authors = checkbox_with_keybindings(
                "请选择要更新的作者（Space 勾选，Enter 确认，ESC 返回）:",
                choices=author_choices,
                style=self.custom_style,
                validate=lambda x: x is None or len(x) > 0 or "至少选择一位作者"  # 允许 ESC 返回 None
            )

            if not selected_authors:
                return

            self.console.print(f"\n[green]已选择 {len(selected_authors)} 位作者[/green]\n")

        # Phase 2-B 需求 3: 设置下载页数
        page_options = select_with_keybindings(
            "选择下载页数:",
            choices=[
                questionary.Choice("📄 仅第 1 页（约 50 篇，推荐测试）", value=1),
                questionary.Choice("📄 前 3 页（约 150 篇）", value=3),
                questionary.Choice("📄 前 5 页（约 250 篇）", value=5),
                questionary.Choice("📄 前 10 页（约 500 篇）", value=10),
                questionary.Choice("📚 全部页面（可能很多）", value=None),
                questionary.Choice("⚙️  自定义页数", value='custom'),
                questionary.Choice("← 返回", value='cancel'),
            ],
            style=self.custom_style,
            default=1  # 使用 value 而不是 title
        )

        if page_options is None or page_options == 'cancel':  # 用户取消或选择返回
            return

        # 处理自定义页数
        max_pages = page_options
        if page_options == 'custom':
            self.console.print("[dim]提示: 留空=全部页面, ESC=返回[/dim]")
            custom_pages = text_with_keybindings(
                "请输入页数（留空=全部）:",
                validate=lambda x: x is None or x == '' or (x.isdigit() and int(x) > 0) or "请输入正整数或留空",  # 允许 ESC 返回 None
                style=self.custom_style
            )

            if custom_pages is None:  # 用户按 ESC 取消
                return
            elif custom_pages == '':
                max_pages = None
            else:
                max_pages = int(custom_pages)

        # 显示确认信息
        page_desc = f"前 {max_pages} 页" if max_pages else "全部页面"
        self.console.print(
            f"\n[cyan]将为 {len(selected_authors)} 位作者更新 {page_desc}[/cyan]\n"
        )

        # 检查是否使用 Python 爬虫
        use_python = self.config.get('experimental', {}).get('use_python_scraper', False)

        if use_python:
            self.console.print(f"[cyan]🐍 使用 Python 爬虫更新...[/cyan]\n")
            try:
                # Run async Python scraper
                asyncio.run(self._run_python_scraper(selected_authors, max_pages))

                # 保存本次选择的作者（用于下次快速选择）
                self._save_author_selection(selected_authors)

                # 更新完成后等待用户确认
                questionary.press_any_key_to_continue("\n按任意键继续...").ask()
                return
            except Exception as e:
                self.console.print(f"\n[red]✗ Python 爬虫失败: {str(e)}[/red]")
                self.console.print(f"[yellow]⚠ 回退到 Node.js 爬虫...[/yellow]\n")
                # Fall through to Node.js scraper

        # 使用 Node.js 爬虫（默认或回退）
        self.console.print(
            f"[yellow]⚠ Node.js 爬虫不支持选择性更新和页数设置[/yellow]\n"
            f"[yellow]  将更新所有作者的全部内容[/yellow]\n"
        )
        self.console.print(f"[cyan]正在调用 Node.js 脚本更新...[/cyan]\n")

        # 调用 Node.js 脚本
        stdout, stderr, returncode = self.bridge.run_update()

        if returncode == 0:
            self.console.print(f"\n[green]✓ 更新完成[/green]")

            # 同步配置（以防 Node.js 脚本有变更）
            self._sync_config_from_nodejs()

            # 保存选择（Node.js 更新所有作者，所以保存所有）
            self._save_author_selection(self.config['followed_authors'])
        else:
            self.console.print(f"\n[red]✗ 更新失败[/red]")

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    async def _run_python_scraper(
        self,
        selected_authors: list = None,
        max_pages: int = None
    ) -> None:
        """运行 Python 爬虫更新（异步）

        Args:
            selected_authors: 选中的作者列表（None 表示全部）
            max_pages: 每个作者下载的最大页数（None 表示全部）
        """
        from ..scraper.archiver import ForumArchiver

        archiver = ForumArchiver(self.config)

        # 使用选中的作者，如果未提供则使用全部
        authors_to_update = selected_authors or self.config['followed_authors']

        # 如果 max_pages 未提供，使用默认值（测试模式）
        if max_pages is None:
            max_pages = 1  # 默认测试模式
            self.console.print(
                "[yellow]提示: 未指定页数，默认只下载第 1 页（测试模式）[/yellow]\n"
            )

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

            # 显示页数信息
            page_info = f"前 {max_pages} 页" if max_pages else "全部页面"
            self.console.print(f"[dim]  下载范围: {page_info}[/dim]")

            try:
                # 使用传入的 max_pages 参数
                result = await archiver.archive_author(author_name, author_url, max_pages)

                # 显示结果
                self.console.print(
                    f"  [green]✓ 完成:[/green] "
                    f"新增 {result['new']} 篇, "
                    f"跳过 {result['skipped']} 篇, "
                    f"失败 {result['failed']} 篇"
                )

                # 更新配置中的统计信息
                author['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                author['total_posts'] = author.get('total_posts', 0) + result['new']

            except Exception as e:
                self.console.print(
                    f"  [red]✗ 失败: {str(e)}[/red]"
                )

        # 保存更新后的配置
        self.config_manager.save(self.config)

        self.console.print(f"\n[green]✓ 所有作者更新完成[/green]")

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

        author_name = select_with_keybindings(
            "选择要取消关注的作者：",
            choices=author_choices,
            style=self.custom_style
        )

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

            choice = select_with_keybindings(
                "选择设置项：",
                choices=setting_choices,
                style=self.custom_style
            )

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
        self.console.print("[dim]提示: ESC 取消修改[/dim]\n")

        new_url = text_with_keybindings(
            "新 URL:",
            default=current,
            style=self.custom_style
        )

        if new_url is None:  # 用户按 ESC 取消
            self.console.print("[yellow]已取消修改[/yellow]")
        elif new_url and new_url != current:
            self.config['forum']['section_url'] = new_url
            self.config_manager.save(self.config)
            self.console.print("[green]✓ 已更新[/green]")
        else:
            self.console.print("[dim]未修改[/dim]")

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _edit_archive_path(self) -> None:
        """修改归档路径"""
        current = self.config['storage']['archive_path']
        self.console.print(f"当前路径: [cyan]{current}[/cyan]")
        self.console.print("[dim]提示: ESC 取消修改[/dim]\n")

        new_path = text_with_keybindings(
            "新路径:",
            default=current,
            style=self.custom_style
        )

        if new_path is None:  # 用户按 ESC 取消
            self.console.print("[yellow]已取消修改[/yellow]")
        elif new_path and new_path != current:
            self.config['storage']['archive_path'] = new_path
            self.config_manager.save(self.config)
            self.console.print("[green]✓ 已更新[/green]")
        else:
            self.console.print("[dim]未修改[/dim]")

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
        # __file__ 是 .../python/src/menu/main_menu.py
        # .parent.parent.parent.parent 到达项目根目录
        json_path = Path(__file__).parent.parent.parent.parent / "config.json"

        if not json_path.exists():
            self.console.print(f"[yellow]⚠ config.json 不存在: {json_path}[/yellow]")
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
                            'url': f"https://t66y.com/@{author_name}",  # 添加 URL
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

    def _save_author_selection(self, selected_authors: list) -> None:
        """保存用户选择的作者列表（用于下次快速选择）

        Args:
            selected_authors: 用户选择的作者列表（author对象列表）
        """
        try:
            # 提取作者名列表
            author_names = [author['name'] for author in selected_authors]

            # 更新配置
            if 'user_preferences' not in self.config:
                self.config['user_preferences'] = {}

            self.config['user_preferences']['last_selected_authors'] = author_names
            self.config['user_preferences']['remember_selection'] = True

            # 保存配置
            self.config_manager.save(self.config)

            self.console.print(f"[dim]✓ 已保存选择偏好（{len(author_names)} 位作者）[/dim]")
        except Exception as e:
            # 保存失败不影响主流程，只记录警告
            self.console.print(f"[dim yellow]⚠ 保存选择失败: {e}[/dim yellow]")
