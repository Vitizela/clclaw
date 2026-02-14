"""配置管理器

职责:
1. 加载和保存 YAML 配置
2. 从旧 config.json 自动迁移
3. 配置验证和默认值合并
"""
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ConfigManager:
    """配置文件管理器"""

    DEFAULT_CONFIG = {
        'version': '2.0',
        'forum': {
            'section_url': '',
            'timeout': 60,
            'max_retries': 3
        },
        'followed_authors': [],
        'storage': {
            'archive_path': './论坛存档',
            'analysis_path': './分析报告',
            'database_path': './python/data/forum_data.db',
            'download': {
                'images': True,
                'videos': True,
                'max_file_size_mb': 100
            },
            'organization': {
                'structure': 'author/year/month/title',
                'filename_max_length': 100
            }
        },
        'analysis': {
            'enabled': False
        },
        'schedule': {
            'enabled': False,
            'frequency': 'daily',
            'time': '03:00'
        },
        'logging': {
            'level': 'INFO',
            'file': './logs/scraper.log',
            'max_size_mb': 50,
            'backup_count': 5
        },
        'advanced': {
            'parallel_downloads': 5,
            'browser_headless': True,
            'proxy': None
        },
        'experimental': {
            'use_python_scraper': False,
            'enable_database': False
        },
        'legacy': {
            'keep_nodejs_scripts': True,
            'nodejs_path': '../'
        }
    }

    def __init__(self, config_path: str = "config.yaml"):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径（相对于 python/ 目录）
        """
        # 配置文件路径（python/config.yaml）
        self.config_path = Path(__file__).parent.parent.parent / config_path

        # 旧配置文件路径（项目根目录/config.json）
        self.legacy_json_path = self.config_path.parent.parent / "config.json"

    def config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.config_path.exists()

    def load(self) -> Dict[str, Any]:
        """加载配置

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        if not self.config_exists():
            # 尝试从 JSON 迁移
            if self.legacy_json_path.exists():
                print("📦 检测到旧配置文件 config.json")
                return self._migrate_from_json()
            else:
                raise FileNotFoundError(
                    f"配置文件不存在: {self.config_path}\n"
                    "请运行配置向导或手动创建配置文件"
                )

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 合并默认配置（处理新增字段）
        config = self._merge_with_defaults(config)

        return config

    def save(self, config: Dict[str, Any]) -> None:
        """保存配置

        Args:
            config: 配置字典
        """
        # 更新时间戳
        config['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                indent=2
            )

    def add_author(self, author_name: str, tags: Optional[list] = None,
                   forum_total_posts: Optional[int] = None) -> None:
        """添加关注作者

        Args:
            author_name: 作者名
            tags: 可选标签
            forum_total_posts: 论坛总帖子数（可选）
        """
        config = self.load()

        # 检查是否已存在
        for author in config['followed_authors']:
            if author['name'] == author_name:
                print(f"作者 {author_name} 已在关注列表中")
                return

        # 添加新作者
        config['followed_authors'].append({
            'name': author_name,
            'added_date': datetime.now().strftime('%Y-%m-%d'),
            'last_update': None,
            'total_posts': 0,
            'total_images': 0,
            'total_videos': 0,
            'forum_total_posts': forum_total_posts,  # 新增：论坛总帖子数
            'forum_stats_updated': datetime.now().strftime('%Y-%m-%d') if forum_total_posts else None,  # 新增：论坛数据更新时间
            'tags': tags or [],
            'notes': ''
        })

        self.save(config)
        print(f"✓ 已添加作者: {author_name}")

    def remove_author(self, author_name: str) -> bool:
        """移除关注作者

        Args:
            author_name: 作者名

        Returns:
            是否成功移除
        """
        config = self.load()

        original_length = len(config['followed_authors'])
        config['followed_authors'] = [
            a for a in config['followed_authors']
            if a['name'] != author_name
        ]

        if len(config['followed_authors']) < original_length:
            self.save(config)
            print(f"✓ 已移除作者: {author_name}")
            return True
        else:
            print(f"作者 {author_name} 不在关注列表中")
            return False

    def _migrate_from_json(self) -> Dict[str, Any]:
        """从旧 config.json 迁移

        Returns:
            新配置字典
        """
        print("🔄 正在从 config.json 迁移配置...")

        with open(self.legacy_json_path, 'r', encoding='utf-8') as f:
            old_config = json.load(f)

        # 转换为新格式
        new_config = self.DEFAULT_CONFIG.copy()
        new_config.update({
            'migrated_from_json': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'forum': {
                'section_url': old_config.get('forumSectionUrl', ''),
                'timeout': 60,
                'max_retries': 3
            },
            'followed_authors': [
                {
                    'name': author,
                    'added_date': datetime.now().strftime('%Y-%m-%d'),
                    'last_update': None,
                    'total_posts': 0,
                    'total_images': 0,
                    'total_videos': 0,
                    'tags': ['migrated'],
                    'notes': '从 config.json 迁移'
                }
                for author in old_config.get('followedAuthors', [])
            ]
        })

        # 保存新配置
        self.save(new_config)
        print(f"✓ 配置已成功迁移至: {self.config_path}")
        print(f"  - 论坛 URL: {new_config['forum']['section_url']}")
        print(f"  - 关注作者: {len(new_config['followed_authors'])} 位")

        return new_config

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置（处理新增字段）

        Args:
            config: 用户配置

        Returns:
            合并后的配置
        """
        def deep_merge(default: dict, custom: dict) -> dict:
            """递归合并字典"""
            result = default.copy()
            for key, value in custom.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(self.DEFAULT_CONFIG, config)
