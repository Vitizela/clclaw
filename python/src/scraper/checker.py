"""帖子更新检测器

用于快速检测作者是否有新帖，无需下载内容。
使用PostTracker进行基于URL Hash的精确检测。
"""
import asyncio
from typing import List, Dict, Optional
from pathlib import Path

from ..data.post_tracker import PostTracker, generate_url_hash


class PostChecker:
    """帖子更新检测器（方案C：基于URL Hash）

    职责：
    1. 使用Playwright扫描论坛
    2. 收集作者的帖子URL
    3. 调用PostTracker检测新帖
    4. 支持批量并发检测
    """

    def __init__(self, config: dict, extractor=None):
        """初始化检测器

        Args:
            config: 配置字典
            extractor: PostExtractor实例（可选，用于复用）
        """
        self.config = config
        self.base_url = config.get('forum', {}).get('section_url', '')
        self.tracker = PostTracker()
        self.extractor = extractor
        self._owns_extractor = extractor is None

    async def start(self):
        """启动浏览器"""
        if self.extractor is None:
            from .extractor import PostExtractor

            project_root = Path(__file__).parent.parent.parent.parent
            log_dir = project_root / 'logs'
            log_dir.mkdir(exist_ok=True)

            self.extractor = PostExtractor(self.base_url, log_dir)
            await self.extractor.start()

    async def close(self):
        """关闭浏览器"""
        if self._owns_extractor and self.extractor:
            await self.extractor.close()

    async def check_new_posts(
        self,
        author_name: str,
        author_url: str,
        max_pages: Optional[int] = 3
    ) -> Dict:
        """检测单个作者的新帖子（方案C实现）

        Args:
            author_name: 作者名
            author_url: 作者URL（用于构造搜索URL）
            max_pages: 最多扫描的页数（None=全部，建议设置如3页）

        Returns:
            {
                'has_new': True/False,
                'new_count': 5,
                'new_urls': ['url1', 'url2', ...],
                'total_forum': 120,
                'total_archived': 80
            }
        """
        if not self.extractor:
            raise RuntimeError("检测器未启动，请先调用 start()")

        # 1. 获取已归档的hash集合（O(1)查找）
        archived_hashes = self.tracker.get_archived_hashes(author_name)

        # 2. 从论坛收集帖子URL（限制扫描深度）
        try:
            forum_urls = await self.extractor.collect_post_urls(
                author_url,
                max_pages=max_pages
            )
        except Exception as e:
            # 扫描失败，返回错误信息
            return {
                'has_new': False,
                'new_count': 0,
                'new_urls': [],
                'total_forum': 0,
                'total_archived': len(archived_hashes),
                'error': str(e)
            }

        # 3. 使用tracker检测新帖
        result = self.tracker.check_new_posts(author_name, forum_urls)

        return result

    async def batch_check_authors(
        self,
        authors: List[Dict],
        max_pages: int = 3,
        max_concurrent: int = 2
    ) -> Dict[str, Dict]:
        """批量检测多个作者（并发）

        Args:
            authors: 作者列表，每个作者是一个字典 {'name': '...', 'url': '...'}
            max_pages: 每个作者最多扫描页数（减少扫描时间）
            max_concurrent: 最大并发数（避免过载）

        Returns:
            {
                '作者名': {
                    'has_new': True,
                    'new_count': 5,
                    ...
                },
                ...
            }
        """
        results = {}
        semaphore = asyncio.Semaphore(max_concurrent)

        async def check_one(author):
            async with semaphore:
                try:
                    result = await self.check_new_posts(
                        author['name'],
                        author['url'],
                        max_pages=max_pages
                    )
                    return author['name'], result
                except Exception as e:
                    return author['name'], {
                        'has_new': False,
                        'new_count': 0,
                        'error': str(e)
                    }

        tasks = [check_one(author) for author in authors]
        results_list = await asyncio.gather(*tasks)

        return dict(results_list)

    async def check_new_posts_incremental(
        self,
        author_name: str,
        author_url: str,
        stop_on_old: int = 2
    ) -> Dict:
        """增量检测：遇到已归档帖子就提前停止（性能优化）

        Args:
            author_name: 作者名
            author_url: 作者URL
            stop_on_old: 连续遇到多少页旧帖就停止扫描

        Returns:
            检测结果字典（同check_new_posts）
        """
        if not self.extractor:
            raise RuntimeError("检测器未启动，请先调用 start()")

        archived_hashes = self.tracker.get_archived_hashes(author_name)
        all_forum_urls = []
        consecutive_old_pages = 0
        page = 1

        try:
            # 逐页扫描，遇到旧帖就停止
            while page <= 5:  # 最多5页
                page_urls = await self.extractor.collect_post_urls(
                    author_url,
                    max_pages=1  # 一页一页扫描
                )

                if not page_urls:
                    break

                # 检查本页是否有新帖
                page_has_new = False
                for url in page_urls:
                    hash_value = generate_url_hash(url)
                    if hash_value not in archived_hashes:
                        page_has_new = True
                    all_forum_urls.append(url)

                if not page_has_new:
                    consecutive_old_pages += 1
                    if consecutive_old_pages >= stop_on_old:
                        # 连续N页都是旧帖，停止扫描
                        break
                else:
                    consecutive_old_pages = 0

                page += 1

        except Exception as e:
            return {
                'has_new': False,
                'new_count': 0,
                'new_urls': [],
                'total_forum': len(all_forum_urls),
                'total_archived': len(archived_hashes),
                'error': str(e)
            }

        # 使用tracker检测新帖
        result = self.tracker.check_new_posts(author_name, all_forum_urls)
        return result
