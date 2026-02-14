"""帖子追踪器：管理已归档帖子的URL hash

职责：
1. 记录已归档帖子的URL hash
2. 检测新帖子（未归档的URL）
3. 数据持久化到JSON文件
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Optional
from datetime import datetime


def generate_url_hash(url: str) -> str:
    """生成URL的短hash值

    使用MD5算法生成8位hex字符串，用于URL去重和快速查找。

    Args:
        url: 帖子URL

    Returns:
        8位hex字符串（32位整数）

    Example:
        >>> generate_url_hash("https://t66y.com/htm_data/2602/7/7139669.html")
        'a3f5b2c1'

    Note:
        8位hex = 32位 = 4,294,967,296 种可能
        对于单个作者几百篇帖子，冲突概率极低（约1/42亿）
    """
    hash_obj = hashlib.md5(url.encode('utf-8'))
    return hash_obj.hexdigest()[:8]


class PostTracker:
    """帖子URL追踪器

    管理已归档帖子的URL hash，用于检测新帖和防止重复归档。

    数据格式：
        {
            "作者名": {
                "hashes": ["hash1", "hash2", ...],
                "last_check": "2026-02-13 18:30:00",
                "total_count": 80
            }
        }

    存储位置：
        python/data/archived_posts.json
    """

    def __init__(self, data_file: Optional[Path] = None):
        """初始化追踪器

        Args:
            data_file: 数据文件路径，默认为 python/data/archived_posts.json
        """
        if data_file is None:
            # 默认路径：python/data/archived_posts.json
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / 'data'
            data_dir.mkdir(exist_ok=True)
            data_file = data_dir / 'archived_posts.json'

        self.data_file = data_file
        self.data = self._load()

    def _load(self) -> Dict:
        """从文件加载数据

        Returns:
            数据字典，如果文件不存在则返回空字典
        """
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告：无法加载数据文件 {self.data_file}: {e}")
                return {}
        else:
            return {}

    def _save(self):
        """保存数据到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"错误：无法保存数据文件 {self.data_file}: {e}")

    def get_archived_hashes(self, author_name: str) -> Set[str]:
        """获取作者的已归档hash集合

        使用set提高查找速度（O(1)时间复杂度）

        Args:
            author_name: 作者名

        Returns:
            Set of hash strings
        """
        if author_name not in self.data:
            return set()
        return set(self.data[author_name].get('hashes', []))

    def add_archived_post(self, author_name: str, url: str):
        """记录单个已归档的帖子

        Args:
            author_name: 作者名
            url: 帖子URL
        """
        hash_value = generate_url_hash(url)

        if author_name not in self.data:
            self.data[author_name] = {
                'hashes': [],
                'last_check': None,
                'total_count': 0
            }

        # 避免重复
        if hash_value not in self.data[author_name]['hashes']:
            self.data[author_name]['hashes'].append(hash_value)
            self.data[author_name]['total_count'] = len(self.data[author_name]['hashes'])

        self._save()

    def add_archived_posts_batch(self, author_name: str, urls: List[str]):
        """批量记录已归档的帖子（性能优化）

        Args:
            author_name: 作者名
            urls: 帖子URL列表
        """
        if author_name not in self.data:
            self.data[author_name] = {
                'hashes': [],
                'last_check': None,
                'total_count': 0
            }

        existing_hashes = set(self.data[author_name]['hashes'])
        new_hashes = []

        for url in urls:
            hash_value = generate_url_hash(url)
            if hash_value not in existing_hashes:
                new_hashes.append(hash_value)
                existing_hashes.add(hash_value)

        self.data[author_name]['hashes'].extend(new_hashes)
        self.data[author_name]['total_count'] = len(self.data[author_name]['hashes'])

        self._save()

    def check_new_posts(self, author_name: str, forum_urls: List[str]) -> Dict:
        """检测新帖子

        对比论坛上的URL列表与已归档的hash，找出新帖。

        Args:
            author_name: 作者名
            forum_urls: 从论坛获取的所有帖子URL列表

        Returns:
            {
                'has_new': True/False,
                'new_count': 5,
                'new_urls': ['url1', 'url2', ...],
                'total_forum': 120,
                'total_archived': 80
            }
        """
        archived_hashes = self.get_archived_hashes(author_name)

        new_urls = []
        for url in forum_urls:
            hash_value = generate_url_hash(url)
            if hash_value not in archived_hashes:
                new_urls.append(url)

        # 更新最后检查时间
        if author_name in self.data:
            self.data[author_name]['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save()

        return {
            'has_new': len(new_urls) > 0,
            'new_count': len(new_urls),
            'new_urls': new_urls,
            'total_forum': len(forum_urls),
            'total_archived': len(archived_hashes)
        }

    def cleanup_old_hashes(self, author_name: str, keep_count: int = 500):
        """清理旧的hash，只保留最近N个（可选维护）

        Args:
            author_name: 作者名
            keep_count: 保留的hash数量
        """
        if author_name in self.data:
            hashes = self.data[author_name]['hashes']
            if len(hashes) > keep_count:
                # 保留最后N个（假设是最新的）
                self.data[author_name]['hashes'] = hashes[-keep_count:]
                self.data[author_name]['total_count'] = keep_count
                self._save()

    def get_stats(self, author_name: str) -> Dict:
        """获取统计信息

        Args:
            author_name: 作者名

        Returns:
            {
                'total_archived': 80,
                'last_check': '2026-02-13 18:30:00'
            }
        """
        if author_name not in self.data:
            return {'total_archived': 0, 'last_check': None}

        return {
            'total_archived': self.data[author_name].get('total_count', 0),
            'last_check': self.data[author_name].get('last_check')
        }
