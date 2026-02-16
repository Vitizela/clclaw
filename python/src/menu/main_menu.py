"""主菜单系统"""
import asyncio
from datetime import datetime
import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Dict, Any, List
from pathlib import Path

from ..config.manager import ConfigManager
from ..bridge.nodejs_bridge import NodeJSBridge
from ..utils.display import show_author_table, show_warning
from ..utils.keybindings import select_with_keybindings, checkbox_with_keybindings, text_with_keybindings
from ..utils.logger import setup_logger
from ..utils.system_info_collector import SystemInfoCollector, StatusPanelData
from ..utils.status_panel_formatter import StatusPanelFormatter

# Phase 3: 数据库模块
from ..database import (
    get_default_connection,
    get_global_stats,
    get_author_ranking,
    get_author_detail_stats,
    import_all_data,
    check_all,
    generate_integrity_report
)

# Phase 4: 相机使用分析
from .camera_usage_menu import show_camera_usage_menu


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

        # 初始化日志记录器
        project_root = Path(__file__).parent.parent.parent.parent
        log_dir = project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        self.logger = setup_logger('menu', log_dir)

        # 新帖检测结果缓存
        self.new_posts_cache = {}

        # Phase 3: 初始化数据库连接
        self.db = None
        try:
            self.db = get_default_connection()
        except Exception as e:
            self.logger.error(f"数据库连接初始化失败: {e}")

        # Phase 5.5: 初始化系统信息收集器
        SystemInfoCollector.initialize()

    def run(self) -> None:
        """运行主菜单"""
        # Phase 3: 首次运行检测和数据库初始化
        self._check_first_run_and_import()

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
            elif "定时任务" in choice:
                self._show_scheduler()
            elif "退出" in choice:
                self.console.print("[yellow]再见！[/yellow]")
                break

    def _show_status(self) -> None:
        """显示系统状态（增强版）"""
        self.console.clear()

        # 收集信息
        program_info = SystemInfoCollector.get_program_info(scheduler=None)
        system_info = SystemInfoCollector.get_system_info()
        resource_info = SystemInfoCollector.get_resource_info(
            archive_path=self.config['storage']['archive_path']
        )

        # 构建状态数据
        panel_data = StatusPanelData(
            program_info=program_info,
            system_info=system_info,
            resource_info=resource_info,
            authors_count=len(self.config['followed_authors']),
            forum_url=self.config['forum']['section_url'],
            archive_path=self.config['storage']['archive_path']
        )

        # 格式化并显示
        panel = StatusPanelFormatter.format_panel(panel_data)
        self.console.print(panel)

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
            "⏰ 定时任务（Phase 5）",
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
        """立即更新作者（支持多选和页数设置）- 循环结构版本"""

        if not self.config['followed_authors']:
            show_warning("暂无关注的作者，无需更新", "提示")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        # ⭐ 关键：在循环外定义，保持状态
        selected_authors = None

        # ⭐ 主循环：允许用户在操作间自由切换
        while True:
            self.console.print("\n[bold]🔄 选择要更新的作者[/bold]\n")

            # 显示作者列表（带选择标记）
            self._show_author_list_with_selection(selected_authors)

            # 显示操作菜单
            action_choice = self._show_action_menu()

            if action_choice is None or action_choice == 'cancel':
                return  # 退出整个功能

            elif action_choice == 'refresh':
                # 刷新检测新帖
                asyncio.run(self._refresh_check_new_posts())
                continue  # ⭐ 返回循环开始，保留 selected_authors

            elif action_choice == 'update_new':
                # 只更新有新帖的作者
                self._update_authors_with_new_posts()
                return  # 完成后退出

            elif action_choice == 'all':
                # 更新所有作者
                selected_authors = self.config['followed_authors']
                self.console.print(
                    f"\n[green]✓ 将更新所有作者（{len(selected_authors)} 位）[/green]\n"
                )
                break  # ⭐ 退出循环，进入下载设置

            elif action_choice == 'select':
                # 处理作者选择流程
                result = self._handle_author_selection(selected_authors)

                if result['action'] == 'confirm':
                    selected_authors = result['authors']
                    break  # ⭐ 退出循环，进入下载设置

                elif result['action'] == 'back':
                    selected_authors = result['authors']
                    continue  # ⭐ 返回循环，保留选择

                elif result['action'] == 'reselect':
                    selected_authors = None  # 清除选择
                    continue  # ⭐ 返回循环

                elif result['action'] == 'cancel':
                    continue  # 返回操作菜单

        # ⭐ 退出循环后，继续下载限制设置并归档
        if selected_authors:
            self._configure_and_download(selected_authors)

    def _show_author_list_with_selection(self, selected_authors: list = None) -> None:
        """显示作者列表，标记当前选择

        Args:
            selected_authors: 当前选择的作者列表
        """
        self.console.print("[cyan]当前关注的作者:[/cyan]\n")

        # 确定要显示的选择标记
        if selected_authors:
            display_selected = [a['name'] for a in selected_authors]
            self.console.print(
                f"[green]✓ 当前已选择 {len(selected_authors)} 位作者[/green]\n"
            )
        else:
            last_saved = self.config.get('user_preferences', {}).get('last_selected_authors', [])
            display_selected = last_saved if last_saved else None

        # 显示表格
        show_author_table(
            self.config['followed_authors'],
            last_selected=display_selected,
            new_posts_marks=self.new_posts_cache if self.new_posts_cache else None
        )
        self.console.print()  # 空行

    def _show_action_menu(self) -> str:
        """显示操作菜单

        Returns:
            用户选择的操作
        """
        action_choices = [
            questionary.Choice("🔄 刷新检测新帖", value='refresh'),
            questionary.Choice("✅ 选择作者更新", value='select'),
        ]

        if self.new_posts_cache:
            action_choices.append(
                questionary.Choice("🆕 只更新有新帖的作者", value='update_new')
            )

        action_choices.extend([
            questionary.Choice("📥 更新全部作者", value='all'),
            questionary.Choice("← 返回主菜单", value='cancel'),
        ])

        return select_with_keybindings(
            "请选择操作：",
            choices=action_choices,
            style=self.custom_style,
            default='select'
        )

    def _handle_author_selection(self, current_selection: list = None) -> dict:
        """处理作者选择流程

        Args:
            current_selection: 当前已选择的作者

        Returns:
            {
                'action': 'confirm' | 'back' | 'reselect' | 'cancel',
                'authors': [...] | None
            }
        """
        # 智能选择：检查是否有上次的选择
        remember_enabled = self.config.get('user_preferences', {}).get('remember_selection', True)
        last_selected = self.config.get('user_preferences', {}).get('last_selected_authors', [])

        selected_authors = None

        # 如果有上次选择且启用了记忆，提供快速选择
        if last_selected and remember_enabled and current_selection is None:
            current_author_names = {a['name'] for a in self.config['followed_authors']}
            valid_last_selected = [name for name in last_selected if name in current_author_names]

            if valid_last_selected:
                self.console.print(
                    f"[dim]上次选择了 {len(valid_last_selected)} 位作者: "
                    f"{', '.join(valid_last_selected[:3])}"
                    f"{'...' if len(valid_last_selected) > 3 else ''}[/dim]\n"
                )

                quick_choice = select_with_keybindings(
                    "选择方式:",
                    choices=[
                        questionary.Choice(f"⚡ 使用上次的选择（{len(valid_last_selected)} 位作者）", value='last'),
                        questionary.Choice("🔄 重新选择作者", value='reselect'),
                        questionary.Choice("← 返回", value='cancel'),
                    ],
                    style=self.custom_style,
                    default='last'
                )

                if quick_choice is None or quick_choice == 'cancel':
                    return {'action': 'cancel', 'authors': None}

                if quick_choice == 'last':
                    selected_authors = [
                        a for a in self.config['followed_authors']
                        if a['name'] in valid_last_selected
                    ]
                    self.console.print(
                        f"\n[green]✓ 已加载上次的选择（{len(selected_authors)} 位作者）[/green]\n"
                    )

        # 如果还没有选择，进入多选界面
        if selected_authors is None:
            author_choices = []
            for author in self.config['followed_authors']:
                label = f"{author['name']}"
                total_posts = author.get('total_posts', 0)
                if total_posts > 0:
                    label += f" ({total_posts} 篇)"

                # 默认选择：如果有当前选择，使用当前；否则使用上次；否则全选
                if current_selection:
                    checked = author['name'] in [a['name'] for a in current_selection]
                elif last_selected:
                    checked = author['name'] in last_selected
                else:
                    checked = True

                author_choices.append(
                    questionary.Choice(title=label, value=author, checked=checked)
                )

            selected_authors = checkbox_with_keybindings(
                "请选择要更新的作者（Space 勾选，Enter 确认）:",
                choices=author_choices,
                style=self.custom_style,
                validate=lambda x: len(x) > 0 or "至少选择一位作者"
            )

            if not selected_authors:
                return {'action': 'cancel', 'authors': None}

            self.console.print(f"\n[green]✓ 已选择 {len(selected_authors)} 位作者:[/green]\n")

            # 显示选中作者的汇总表格
            self._show_selection_summary(selected_authors)
            self.console.print()

        # 确认选择
        confirm_choice = select_with_keybindings(
            "确认更新这些作者吗？",
            choices=[
                questionary.Choice("✅ 确认并继续", value='confirm'),
                questionary.Choice("🔄 重新选择作者", value='reselect'),
                questionary.Choice("← 返回上一步", value='back'),  # ⭐ 改名
            ],
            style=self.custom_style,
            default='confirm'
        )

        if confirm_choice is None or confirm_choice == 'cancel':
            return {'action': 'cancel', 'authors': None}

        if confirm_choice == 'confirm':
            return {'action': 'confirm', 'authors': selected_authors}

        if confirm_choice == 'back':
            return {'action': 'back', 'authors': selected_authors}  # ⭐ 保存选择

        if confirm_choice == 'reselect':
            return {'action': 'reselect', 'authors': None}  # 清除选择

    def _configure_and_download(self, selected_authors: list) -> None:
        """配置下载限制并开始归档

        Args:
            selected_authors: 要更新的作者列表
        """
        # 设置下载限制
        download_mode = select_with_keybindings(
            "选择下载限制方式:",
            choices=[
                questionary.Choice("📄 按页数限制（快速，推荐测试）", value='pages'),
                questionary.Choice("📊 按帖子数量限制（精确控制）", value='posts'),
                questionary.Choice("📚 下载全部内容", value='all'),
                questionary.Choice("← 返回", value='cancel'),
            ],
            style=self.custom_style,
            default='pages'
        )

        if download_mode is None or download_mode == 'cancel':
            return

        max_pages = None
        max_posts = None

        # 按页数限制
        if download_mode == 'pages':
            page_options = select_with_keybindings(
                "选择下载页数:",
                choices=[
                    questionary.Choice("📄 仅第 1 页（约 50 篇，推荐测试）", value=1),
                    questionary.Choice("📄 前 3 页（约 150 篇）", value=3),
                    questionary.Choice("📄 前 5 页（约 250 篇）", value=5),
                    questionary.Choice("📄 前 10 页（约 500 篇）", value=10),
                    questionary.Choice("⚙️  自定义页数", value='custom'),
                    questionary.Choice("← 返回", value='cancel'),
                ],
                style=self.custom_style,
                default=1
            )

            if page_options is None or page_options == 'cancel':
                return

            if page_options == 'custom':
                self.console.print("[dim]提示: ESC=返回[/dim]")
                custom_pages = text_with_keybindings(
                    "请输入页数（正整数）:",
                    validate=lambda x: x is None or (x.isdigit() and int(x) > 0) or "请输入正整数",
                    style=self.custom_style
                )
                if custom_pages is None:
                    return
                max_pages = int(custom_pages)
            else:
                max_pages = page_options

        # 按帖子数量限制
        elif download_mode == 'posts':
            post_options = select_with_keybindings(
                "选择下载帖子数量:",
                choices=[
                    questionary.Choice("📝 前 50 篇（推荐测试）", value=50),
                    questionary.Choice("📝 前 100 篇", value=100),
                    questionary.Choice("📝 前 200 篇", value=200),
                    questionary.Choice("📝 前 500 篇", value=500),
                    questionary.Choice("⚙️  自定义数量", value='custom'),
                    questionary.Choice("← 返回", value='cancel'),
                ],
                style=self.custom_style,
                default=50
            )

            if post_options is None or post_options == 'cancel':
                return

            if post_options == 'custom':
                self.console.print("[dim]提示: ESC=返回[/dim]")
                custom_posts = text_with_keybindings(
                    "请输入帖子数量（正整数）:",
                    validate=lambda x: x is None or (x.isdigit() and int(x) > 0) or "请输入正整数",
                    style=self.custom_style
                )
                if custom_posts is None:
                    return
                max_posts = int(custom_posts)
            else:
                max_posts = post_options

        # 全部内容
        elif download_mode == 'all':
            max_pages = None
            max_posts = None

        # 显示确认信息
        if max_pages:
            limit_desc = f"前 {max_pages} 页"
        elif max_posts:
            limit_desc = f"前 {max_posts} 篇帖子"
        else:
            limit_desc = "全部内容"

        self.console.print(
            f"\n[cyan]将为 {len(selected_authors)} 位作者下载 {limit_desc}[/cyan]\n"
        )

        # 检查是否使用 Python 爬虫
        use_python = self.config.get('experimental', {}).get('use_python_scraper', False)

        if use_python:
            self.console.print(f"[cyan]🐍 使用 Python 爬虫更新...[/cyan]\n")
            try:
                # Run async Python scraper
                asyncio.run(self._run_python_scraper(selected_authors, max_pages, max_posts))

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

            # 清空新帖缓存（已更新，缓存过时）
            self.new_posts_cache.clear()
        else:
            self.console.print(f"\n[red]✗ 更新失败[/red]")

        questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    async def _run_python_scraper(
        self,
        selected_authors: list = None,
        max_pages: int = None,
        max_posts: int = None
    ) -> None:
        """运行 Python 爬虫更新（异步）

        Args:
            selected_authors: 选中的作者列表（None 表示全部）
            max_pages: 每个作者下载的最大页数（None 表示全部）
            max_posts: 每个作者下载的最大帖子数（None 表示全部）
        """
        from ..scraper.archiver import ForumArchiver

        archiver = ForumArchiver(self.config)

        # 使用选中的作者，如果未提供则使用全部
        authors_to_update = selected_authors or self.config['followed_authors']

        # 如果 max_pages 和 max_posts 都未提供，使用默认值（测试模式）
        if max_pages is None and max_posts is None:
            max_pages = 1  # 默认测试模式
            self.console.print(
                "[yellow]提示: 未指定下载限制，默认只下载第 1 页（测试模式）[/yellow]\n"
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

            # 显示下载范围信息
            if max_posts:
                limit_info = f"前 {max_posts} 篇帖子"
            elif max_pages:
                limit_info = f"前 {max_pages} 页"
            else:
                limit_info = "全部内容"
            self.console.print(f"[dim]  下载范围: {limit_info}[/dim]")

            try:
                # 使用传入的参数
                result = await archiver.archive_author(author_name, author_url, max_pages, max_posts)

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

                # 新增：更新论坛总数（如果归档流程中获取到了）
                if result.get('forum_total'):
                    # 使用最大值：论坛主题帖只增不减，保留历史最大值
                    old_total = author.get('forum_total_posts', 0)
                    new_total = result['forum_total']
                    author['forum_total_posts'] = max(old_total, new_total)
                    author['forum_stats_updated'] = datetime.now().strftime('%Y-%m-%d')

                    # 记录日志
                    if new_total > old_total:
                        self.logger.info(f"论坛总数更新: {old_total} -> {new_total}")
                    elif new_total < old_total:
                        self.logger.info(f"论坛总数保持: {old_total} (本次扫描: {new_total}, 使用历史最大值)")
                    else:
                        self.logger.info(f"论坛总数不变: {old_total}")

            except Exception as e:
                self.console.print(
                    f"  [red]✗ 失败: {str(e)}[/red]"
                )

        # 保存更新后的配置
        self.config_manager.save(self.config)

        # 清空新帖缓存（因为已经更新，缓存已过时）
        self.new_posts_cache.clear()

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

    def _check_first_run_and_import(self) -> None:
        """检查首次运行并导入历史数据（Phase 3）"""
        if self.db is None:
            return

        try:
            # 检查数据库是否已初始化
            if not self.db.is_initialized():
                self.db.initialize_database()
                self.logger.info("数据库初始化完成")

            # 检查是否有数据（判断是否首次运行）
            stats = get_global_stats(self.db)
            if stats['total_posts'] == 0 and len(self.config['followed_authors']) > 0:
                # 有关注的作者但数据库为空，提示导入
                self._prompt_import_historical_data()

        except Exception as e:
            self.logger.error(f"首次运行检测失败: {e}")

    def _prompt_import_historical_data(self) -> None:
        """提示导入历史归档数据"""
        self.console.print("\n[bold yellow]📊 检测到首次使用统计功能[/bold yellow]\n")
        self.console.print("系统发现您已有归档数据，需要导入到数据库以启用统计功能。\n")

        # 估算数据量
        author_count = len(self.config['followed_authors'])
        self.console.print(f"[cyan]关注作者数:[/cyan] {author_count} 位")
        self.console.print(f"[cyan]预计时间:[/cyan] ~15 秒\n")

        # 询问是否立即导入
        choices = ["立即导入", "稍后导入"]
        choice = select_with_keybindings(
            "是否立即导入历史数据？",
            choices=choices,
            style=self.custom_style
        )

        if choice and "立即导入" in choice:
            self._import_historical_data()
        else:
            self.console.print("[yellow]已跳过导入。您可以稍后在统计菜单中手动导入。[/yellow]")
            questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _import_historical_data(self) -> None:
        """导入历史归档数据"""
        self.console.print("\n[bold]正在导入历史数据...[/bold]\n")

        try:
            archive_path = self.config['storage']['archive_path']

            # 调用导入函数
            result = import_all_data(
                archive_path=archive_path,
                config=self.config,
                db=self.db,
                force_rebuild=False,
                show_progress=True
            )

            # 显示结果
            self.console.print(f"\n[green]✓ 导入完成！[/green]\n")
            self.console.print(f"  - 作者数: {result['authors_added']}")
            self.console.print(f"  - 帖子数: {result['posts_added']}")
            self.console.print(f"  - 媒体数: {result['media_added']}")
            self.console.print(f"  - 用时: {result['duration_seconds']:.2f} 秒")

            if result.get('errors'):
                self.console.print(f"\n[yellow]⚠ 遇到 {len(result['errors'])} 个错误（已跳过）[/yellow]")

            questionary.press_any_key_to_continue("\n按任意键继续...").ask()

        except Exception as e:
            self.console.print(f"\n[red]✗ 导入失败: {e}[/red]")
            self.logger.error(f"历史数据导入失败: {e}")
            questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _show_statistics(self) -> None:
        """查看统计（Phase 3）"""
        if self.db is None or not self.db.is_initialized():
            show_warning("数据库未初始化", "统计功能不可用")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        while True:
            # 获取全局统计
            try:
                stats = get_global_stats(self.db)
            except Exception as e:
                self.console.print(f"[red]获取统计失败: {e}[/red]")
                questionary.press_any_key_to_continue("\n按任意键返回...").ask()
                return

            # 显示统计信息
            self.console.clear()
            self.console.print(Panel(
                f"[cyan]总关注作者:[/cyan] {stats['total_authors']} 位\n"
                f"[cyan]总归档帖子:[/cyan] {stats['total_posts']} 篇\n"
                f"[cyan]总下载图片:[/cyan] {stats['total_images']} 张\n"
                f"[cyan]总下载视频:[/cyan] {stats['total_videos']} 个\n"
                f"[cyan]占用空间:[/cyan] {stats['total_size_gb']:.2f} GB\n"
                f"[cyan]最后更新:[/cyan] {stats.get('latest_update', 'N/A')}",
                title="📊 全局统计",
                border_style="cyan"
            ))

            # 显示作者排行榜
            try:
                ranking = get_author_ranking(order_by='posts', limit=10, db=self.db)

                if ranking:
                    self.console.print("\n[bold]📈 作者排行榜（按帖子数）[/bold]\n")

                    table = Table(show_header=True, header_style="bold cyan")
                    table.add_column("排名", style="dim", width=6)
                    table.add_column("作者", style="cyan")
                    table.add_column("帖子", justify="right")
                    table.add_column("图片", justify="right")
                    table.add_column("视频", justify="right")

                    for author in ranking[:10]:
                        table.add_row(
                            f"#{author['rank']}",
                            author['name'],
                            str(author['post_count']),
                            str(author['image_count']),
                            str(author['video_count'])
                        )

                    self.console.print(table)

            except Exception as e:
                self.console.print(f"[yellow]获取排行榜失败: {e}[/yellow]")

            # 统计菜单
            choices = [
                "📋 查看作者详细统计",
                "📷 相机使用分析",
                "🔄 重新导入数据",
                "🔍 数据完整性检查",
                "⬅️  返回主菜单"
            ]

            choice = select_with_keybindings(
                "\n请选择操作：",
                choices=choices,
                style=self.custom_style
            )

            if choice is None or "返回主菜单" in choice:
                break
            elif "查看作者详细统计" in choice:
                self._show_author_detail_stats()
            elif "相机使用分析" in choice:
                self._show_camera_usage_analysis()
            elif "重新导入数据" in choice:
                self._reimport_data()
            elif "数据完整性检查" in choice:
                self._check_data_integrity()

    def _show_author_detail_stats(self) -> None:
        """查看作者详细统计"""
        if not self.config['followed_authors']:
            show_warning("没有关注的作者", "请先关注作者")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        # 选择作者
        author_names = [a['name'] for a in self.config['followed_authors']]
        author_names.append("⬅️ 返回")

        choice = select_with_keybindings(
            "选择要查看的作者：",
            choices=author_names,
            style=self.custom_style
        )

        if choice is None or "返回" in choice:
            return

        # 获取详细统计
        try:
            detail = get_author_detail_stats(choice, db=self.db)

            if detail is None:
                self.console.print(f"[yellow]未找到作者 {choice} 的数据[/yellow]")
                questionary.press_any_key_to_continue("\n按任意键返回...").ask()
                return

            # 显示详细信息
            self.console.clear()
            self.console.print(f"\n[bold cyan]作者: {detail['basic_info']['name']}[/bold cyan]\n")

            # 基本信息
            self.console.print("[bold]📌 基本信息[/bold]")
            self.console.print(f"  关注日期: {detail['basic_info']['added_date']}")
            self.console.print(f"  最后更新: {detail['basic_info'].get('last_update', 'N/A')}")
            if detail['basic_info'].get('url'):
                self.console.print(f"  作者 URL: {detail['basic_info']['url']}")

            # 归档统计
            self.console.print("\n[bold]📊 归档统计[/bold]")
            archive_stats = detail['archive_stats']
            self.console.print(f"  总帖子数: {archive_stats['total_posts']} 篇")
            self.console.print(f"  总图片数: {archive_stats['total_images']} 张")
            self.console.print(f"  总视频数: {archive_stats['total_videos']} 个")
            self.console.print(f"  总大小: {archive_stats['total_size_mb']:.2f} MB")
            self.console.print(f"  平均图片/帖: {archive_stats['avg_images_per_post']:.1f}")
            self.console.print(f"  平均视频/帖: {archive_stats['avg_videos_per_post']:.1f}")

            if archive_stats.get('forum_total_posts', 0) > 0:
                progress = archive_stats.get('archive_progress', 0)
                self.console.print(f"  归档进度: {progress:.1f}% ({archive_stats['total_posts']}/{archive_stats['forum_total_posts']})")

            # 时间统计
            self.console.print("\n[bold]📅 时间跨度[/bold]")
            time_stats = detail['time_stats']
            if time_stats.get('first_post_date'):
                self.console.print(f"  最早帖子: {time_stats['first_post_date']}")
            if time_stats.get('latest_post_date'):
                self.console.print(f"  最新帖子: {time_stats['latest_post_date']}")
            if time_stats.get('active_days'):
                self.console.print(f"  活跃天数: {time_stats['active_days']} 天")

            questionary.press_any_key_to_continue("\n按任意键返回...").ask()

        except Exception as e:
            self.console.print(f"[red]获取详细统计失败: {e}[/red]")
            self.logger.error(f"获取作者详细统计失败: {e}")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()

    def _show_camera_usage_analysis(self) -> None:
        """显示相机使用分析菜单（Phase 4 Week 3）"""
        try:
            show_camera_usage_menu()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]已取消操作[/yellow]")
        except Exception as e:
            self.console.print(f"[red]相机使用分析失败: {e}[/red]")
            self.logger.error(f"相机使用分析失败: {e}")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()

    def _reimport_data(self) -> None:
        """重新导入数据"""
        self.console.print("\n[yellow]⚠ 这将清空数据库并重新导入所有数据[/yellow]\n")

        choices = ["确认重新导入", "取消"]
        choice = select_with_keybindings(
            "确定要继续吗？",
            choices=choices,
            style=self.custom_style
        )

        if choice and "确认" in choice:
            try:
                archive_path = self.config['storage']['archive_path']

                result = import_all_data(
                    archive_path=archive_path,
                    config=self.config,
                    db=self.db,
                    force_rebuild=True,  # 强制重建
                    show_progress=True
                )

                self.console.print(f"\n[green]✓ 重新导入完成！[/green]")
                self.console.print(f"  - 作者数: {result['authors_added']}")
                self.console.print(f"  - 帖子数: {result['posts_added']}")
                self.console.print(f"  - 用时: {result['duration_seconds']:.2f} 秒")

                questionary.press_any_key_to_continue("\n按任意键继续...").ask()

            except Exception as e:
                self.console.print(f"\n[red]✗ 重新导入失败: {e}[/red]")
                self.logger.error(f"重新导入数据失败: {e}")
                questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _check_data_integrity(self) -> None:
        """检查数据完整性"""
        self.console.print("\n[bold]🔍 正在检查数据完整性...[/bold]\n")

        try:
            archive_path = self.config['storage']['archive_path']

            # 执行检查
            result = check_all(archive_path, db=self.db, fix=False)

            # 显示结果
            self.console.print(f"\n[bold]检查结果[/bold]")
            self.console.print(f"  检查项目: {result['total_checked']}")
            self.console.print(f"  发现问题: {len(result['issues'])}")

            if result['issues']:
                # 按严重性分类
                high = [i for i in result['issues'] if i.get('severity') == 'high']
                medium = [i for i in result['issues'] if i.get('severity') == 'medium']
                low = [i for i in result['issues'] if i.get('severity') == 'low']

                if high:
                    self.console.print(f"\n[red]高严重性: {len(high)} 项[/red]")
                if medium:
                    self.console.print(f"[yellow]中严重性: {len(medium)} 项[/yellow]")
                if low:
                    self.console.print(f"[dim]低严重性: {len(low)} 项[/dim]")

                # 询问是否自动修复
                self.console.print("\n")
                choices = ["自动修复", "生成详细报告", "返回"]
                choice = select_with_keybindings(
                    "请选择操作：",
                    choices=choices,
                    style=self.custom_style
                )

                if choice and "自动修复" in choice:
                    self.console.print("\n[yellow]正在修复...[/yellow]")
                    fix_result = check_all(archive_path, db=self.db, fix=True)
                    self.console.print(f"\n[green]✓ 修复完成: {fix_result.get('fixed', 0)} 项[/green]")

                elif choice and "生成详细报告" in choice:
                    report_file = Path(archive_path).parent / "integrity_report.txt"
                    generate_integrity_report(archive_path, str(report_file), db=self.db)
                    self.console.print(f"\n[green]✓ 报告已保存: {report_file}[/green]")

            else:
                self.console.print("\n[green]✓ 未发现问题，数据完整性良好！[/green]")

            questionary.press_any_key_to_continue("\n按任意键返回...").ask()

        except Exception as e:
            self.console.print(f"\n[red]✗ 完整性检查失败: {e}[/red]")
            self.logger.error(f"数据完整性检查失败: {e}")
            questionary.press_any_key_to_continue("\n按任意键继续...").ask()

    def _show_analysis(self) -> None:
        """数据分析（Phase 4）"""
        from ..menu.analysis_menu import show_analysis_menu
        show_analysis_menu()

    def _show_scheduler(self) -> None:
        """定时任务管理（Phase 5）"""
        from ..menu.scheduler_menu import SchedulerMenu
        try:
            scheduler_menu = SchedulerMenu(self.config)
            scheduler_menu.show()
        except Exception as e:
            self.console.print(f"[red]启动定时任务菜单失败: {e}[/red]")
            self.logger.error(f"启动定时任务菜单失败: {e}")
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

    def _show_selection_summary(self, selected_authors: list) -> None:
        """显示选中作者的汇总表格（带标记）

        Args:
            selected_authors: 用户选择的作者列表
        """
        from rich.table import Table

        table = Table(show_header=True, header_style="bold cyan", border_style="dim")
        table.add_column("状态", justify="center", width=6)
        table.add_column("作者名", style="cyan")
        table.add_column("帖子数", justify="right")
        table.add_column("最后更新", style="dim")

        selected_names = {author['name'] for author in selected_authors}

        for author in self.config['followed_authors']:
            if author['name'] in selected_names:
                status = "[green]✅[/green]"
                name_style = "[bold cyan]"
            else:
                status = "[dim]⬜[/dim]"
                name_style = "[dim]"

            name = f"{name_style}{author['name']}[/]"
            total_posts = author.get('total_posts', 0)
            last_update = author.get('last_update', '从未')

            table.add_row(
                status,
                name,
                str(total_posts) if total_posts > 0 else "-",
                last_update if last_update else "-"
            )

        self.console.print(table)

    async def _refresh_check_new_posts(self) -> None:
        """刷新检测所有作者的新帖（方案C实现）"""
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from ..scraper.checker import PostChecker

        authors = self.config['followed_authors']

        if not authors:
            self.console.print("\n[yellow]⚠️  暂无关注的作者[/yellow]\n")
            return

        self.console.print("\n[yellow]🔍 正在检测新帖（精确模式）...[/yellow]\n")

        # 创建检测器
        checker = PostChecker(self.config)

        try:
            await checker.start()

            # 显示进度
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task(
                    f"扫描中... (0/{len(authors)})",
                    total=len(authors)
                )

                # 批量检测（限制扫描深度：前3页）
                results = await checker.batch_check_authors(
                    authors,
                    max_pages=3,      # 只扫描前3页（提高速度）
                    max_concurrent=2  # 并发2个作者
                )

                progress.update(task, completed=len(authors))

            # 更新缓存
            self.new_posts_cache = {
                name: {
                    'has_new': result.get('has_new', False),
                    'new_count': result.get('new_count', 0)
                }
                for name, result in results.items()
            }

            # 【新增】同步更新 forum_total_posts（用于显示归档进度）
            updated_count = 0
            for author in self.config['followed_authors']:
                author_name = author['name']
                if author_name in results:
                    result = results[author_name]

                    # 更新论坛总数
                    if result.get('total_forum'):
                        old_total = author.get('forum_total_posts', 0)
                        new_total = result['total_forum']
                        # 使用最大值：论坛主题帖只增不减
                        author['forum_total_posts'] = max(old_total, new_total)
                        author['forum_stats_updated'] = datetime.now().strftime('%Y-%m-%d')

                        # 日志记录
                        if new_total > old_total:
                            self.logger.info(f"{author_name}: 论坛总数更新 {old_total} -> {new_total}")
                            updated_count += 1
                        elif new_total < old_total:
                            self.logger.info(f"{author_name}: 论坛总数保持 {old_total} (本次: {new_total})")
                        else:
                            self.logger.info(f"{author_name}: 论坛总数不变: {old_total}")

            # 保存配置
            if updated_count > 0:
                self.config_manager.save(self.config)
                self.console.print(f"[dim]✓ 已更新 {updated_count} 位作者的论坛总数[/dim]\n")

            # 统计结果
            new_count = sum(1 for r in results.values() if r.get('has_new', False))
            total_new_posts = sum(r.get('new_count', 0) for r in results.values())

            self.console.print(
                f"\n[green]✓ 检测完成！[/green] "
                f"发现 {new_count}/{len(authors)} 位作者有新帖，"
                f"共约 {total_new_posts} 篇新帖\n"
            )

        except Exception as e:
            self.console.print(f"\n[red]✗ 检测失败: {str(e)}[/red]\n")
            self.logger.error(f"刷新检测新帖失败: {str(e)}")

        finally:
            await checker.close()

    def _update_authors_with_new_posts(self) -> None:
        """只更新有新帖的作者"""
        if not self.new_posts_cache:
            self.console.print("\n[yellow]⚠️  请先刷新检测新帖[/yellow]\n")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        # 筛选有新帖的作者
        authors_with_new = [
            author for author in self.config['followed_authors']
            if self.new_posts_cache.get(author['name'], {}).get('has_new', False)
        ]

        if not authors_with_new:
            self.console.print("\n[green]✓ 所有作者都是最新的，无需更新[/green]\n")
            questionary.press_any_key_to_continue("\n按任意键返回...").ask()
            return

        self.console.print(f"\n[cyan]发现 {len(authors_with_new)} 位作者有新帖：[/cyan]\n")
        for author in authors_with_new:
            new_count = self.new_posts_cache.get(author['name'], {}).get('new_count', 0)
            self.console.print(f"  🆕 {author['name']} ({new_count} 篇新帖)")

        self.console.print()

        # 确认是否更新
        confirm = select_with_keybindings(
            "确认更新这些作者吗？",
            choices=[
                questionary.Choice("✅ 确认并更新", value='confirm'),
                questionary.Choice("← 返回", value='cancel'),
            ],
            style=self.custom_style,
            default='confirm'
        )

        if confirm is None or confirm == 'cancel':
            return

        # 调用更新流程（复用现有逻辑）
        asyncio.run(self._run_python_scraper(authors_with_new))

        # 保存选择偏好
        self._save_author_selection(authors_with_new)

        # 清空新帖缓存（已更新，缓存过时）
        self.new_posts_cache.clear()
        self.console.print("[dim]✓ 已清空新帖缓存[/dim]")

        questionary.press_any_key_to_continue("\n按任意键返回...").ask()
