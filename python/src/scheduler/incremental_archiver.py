# python/src/scheduler/incremental_archiver.py

from typing import Dict, Optional
from datetime import datetime
import asyncio


class IncrementalArchiver:
    """
    增量归档器

    职责：
    - 检测作者的新帖
    - 只归档未归档的帖子
    - 返回归档结果统计

    工作流程：
    1. 调用 PostChecker 检测新帖
    2. 调用 ForumArchiver 归档新帖
    3. 返回统计结果
    """

    def __init__(self, config: dict):
        """
        初始化增量归档器

        Args:
            config: 配置字典
        """
        self.config = config

        # 延迟导入以避免循环依赖
        from database.connection import get_default_connection
        self.db = get_default_connection()

    async def archive_author_incremental(
        self,
        author_name: str,
        max_pages: Optional[int] = None
    ) -> Dict:
        """
        增量归档单个作者

        Args:
            author_name: 作者名称
            max_pages: 最大扫描页数（None = 全部）

        Returns:
            归档结果字典:
            {
                'author_name': str,
                'new_posts': int,           # 新增归档数
                'skipped_posts': int,       # 跳过数（已存在）
                'failed_posts': int,        # 失败数
                'total_archived': int,      # 总归档数（归档前）
                'total_forum': int,         # 论坛总数
                'start_time': str,
                'end_time': str,
                'duration': float,
                'status': 'completed' | 'failed',
                'error': str (可选)
            }
        """
        start_time = datetime.now()
        result = {
            'author_name': author_name,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'new_posts': 0,
            'skipped_posts': 0,
            'failed_posts': 0,
            'total_archived': 0,
            'total_forum': 0,
            'status': 'failed'
        }

        try:
            # 延迟导入
            from database.models import Author
            from scraper.checker import PostChecker
            from scraper.archiver import ForumArchiver

            # 1. 获取作者信息
            author = Author.get_by_name(author_name, db=self.db)
            if not author:
                raise ValueError(f"作者不存在: {author_name}")

            author_url = author.url
            result['total_archived'] = author.total_posts

            # 2. 检测新帖
            checker = PostChecker(self.config)
            await checker.start()

            try:
                check_result = await checker.check_new_posts(
                    author_name=author_name,
                    author_url=author_url,
                    max_pages=max_pages
                )
            finally:
                await checker.close()

            # 提取检测结果
            new_urls = check_result.get('new_urls', [])
            result['skipped_posts'] = check_result.get('existing_count', 0)
            result['total_forum'] = check_result.get('total_forum', 0)

            # 检查是否有错误
            if 'error' in check_result:
                result['error'] = f"检测失败: {check_result['error']}"
                result['status'] = 'failed'
                return result

            # 如果没有新帖，直接返回成功
            if len(new_urls) == 0:
                result['status'] = 'completed'
                result['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                result['duration'] = (datetime.now() - start_time).total_seconds()
                return result

            # 3. 归档新帖
            archiver = ForumArchiver(self.config)
            archive_result = await archiver.archive_author(
                author_name=author_name,
                author_url=author_url,
                target_urls=new_urls  # ← 只归档新帖
            )

            # 提取归档结果
            result['new_posts'] = archive_result.get('new', 0)
            result['failed_posts'] = archive_result.get('failed', 0)
            result['status'] = 'completed'

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)

        finally:
            end_time = datetime.now()
            result['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
            result['duration'] = (end_time - start_time).total_seconds()

        return result

    async def archive_authors_batch(
        self,
        author_names: list,
        max_pages: Optional[int] = None
    ) -> list:
        """
        批量增量归档

        Args:
            author_names: 作者列表
            max_pages: 最大扫描页数

        Returns:
            归档结果列表
        """
        results = []
        for author_name in author_names:
            result = await self.archive_author_incremental(
                author_name=author_name,
                max_pages=max_pages
            )
            results.append(result)

        return results
