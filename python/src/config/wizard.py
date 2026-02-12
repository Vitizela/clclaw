"""配置向导

引导用户完成首次配置
"""
import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from .manager import ConfigManager


class ConfigWizard:
    """配置向导 - 引导用户完成首次配置"""

    custom_style = Style([
        ('qmark', 'fg:#673ab7 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#f44336 bold'),
        ('pointer', 'fg:#673ab7 bold'),
        ('highlighted', 'fg:#673ab7 bold'),
        ('selected', 'fg:#cc5454'),
        ('separator', 'fg:#cc5454'),
        ('instruction', ''),
        ('text', ''),
    ])

    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager()

    def run(self) -> None:
        """运行配置向导"""
        self.console.print(Panel(
            "[bold cyan]欢迎使用论坛作者订阅归档系统[/bold cyan]\n\n"
            "首次运行检测到，启动配置向导...\n"
            "请按照提示完成配置。",
            title="🎉 欢迎",
            border_style="cyan"
        ))

        config = {}

        # 1. 基本设置
        self.console.print("\n[bold]📝 步骤 1/4: 基本设置[/bold]")
        config['forum'] = self._configure_forum()

        # 2. 存储设置
        self.console.print("\n[bold]📁 步骤 2/4: 存储设置[/bold]")
        config['storage'] = self._configure_storage()

        # 3. 分析设置
        self.console.print("\n[bold]📊 步骤 3/4: 数据分析设置[/bold]")
        config['analysis'] = self._configure_analysis()

        # 4. 定时任务
        self.console.print("\n[bold]⏰ 步骤 4/4: 定时任务[/bold]")
        config['schedule'] = self._configure_schedule()

        # 合并默认配置
        full_config = self.config_manager.DEFAULT_CONFIG.copy()
        full_config.update(config)

        # 保存配置
        self.config_manager.save(full_config)

        self.console.print(Panel(
            f"[green]✓ 配置完成！[/green]\n\n"
            f"配置文件已保存至: [cyan]{self.config_manager.config_path}[/cyan]\n\n"
            f"您现在可以开始使用系统了！",
            title="✅ 完成",
            border_style="green"
        ))

    def _configure_forum(self) -> dict:
        """配置论坛设置"""
        forum_url = questionary.text(
            "论坛版块 URL:",
            default="https://t66y.com/thread0806.php?fid=7",
            style=self.custom_style
        ).ask()

        timeout = questionary.text(
            "页面加载超时（秒）:",
            default="60",
            style=self.custom_style,
            validate=lambda x: x.isdigit() and int(x) > 0
        ).ask()

        return {
            'section_url': forum_url,
            'timeout': int(timeout),
            'max_retries': 3
        }

    def _configure_storage(self) -> dict:
        """配置存储设置"""
        archive_path = questionary.text(
            "归档存储路径:",
            default="./论坛存档",
            style=self.custom_style
        ).ask()

        download_images = questionary.confirm(
            "是否下载图片?",
            default=True,
            style=self.custom_style
        ).ask()

        download_videos = questionary.confirm(
            "是否下载视频?",
            default=True,
            style=self.custom_style
        ).ask()

        return {
            'archive_path': archive_path,
            'analysis_path': './分析报告',
            'database_path': './python/data/forum_data.db',
            'download': {
                'images': download_images,
                'videos': download_videos,
                'max_file_size_mb': 100
            },
            'organization': {
                'structure': 'author/year/month/title',
                'filename_max_length': 100
            }
        }

    def _configure_analysis(self) -> dict:
        """配置分析设置"""
        enable_analysis = questionary.confirm(
            "启用数据分析功能?（Phase 4 后可用）",
            default=False,
            style=self.custom_style
        ).ask()

        return {
            'enabled': enable_analysis
        }

    def _configure_schedule(self) -> dict:
        """配置定时任务"""
        enable_schedule = questionary.confirm(
            "是否配置定时更新?",
            default=False,
            style=self.custom_style
        ).ask()

        if not enable_schedule:
            return {
                'enabled': False,
                'frequency': 'daily',
                'time': '03:00'
            }

        frequency = questionary.select(
            "更新频率:",
            choices=[
                '每6小时',
                '每12小时',
                '每天凌晨3点（推荐）',
                '自定义'
            ],
            style=self.custom_style
        ).ask()

        freq_map = {
            '每6小时': ('6hours', None),
            '每12小时': ('12hours', None),
            '每天凌晨3点（推荐）': ('daily', '03:00'),
            '自定义': ('custom', None)
        }

        freq_value, time_value = freq_map[frequency]

        if freq_value == 'custom':
            time_value = questionary.text(
                "更新时间（24小时格式，如 14:30）:",
                default="03:00",
                style=self.custom_style
            ).ask()

        return {
            'enabled': True,
            'frequency': freq_value,
            'time': time_value or '03:00',
            'cron_expression': self._generate_cron(freq_value, time_value)
        }

    @staticmethod
    def _generate_cron(frequency: str, time: str) -> str:
        """生成 cron 表达式"""
        if frequency == 'daily':
            hour, minute = time.split(':')
            return f"{minute} {hour} * * *"
        elif frequency == '6hours':
            return "0 */6 * * *"
        elif frequency == '12hours':
            return "0 */12 * * *"
        else:
            hour, minute = time.split(':')
            return f"{minute} {hour} * * *"
