"""Forum archiver - orchestrates extraction and downloading

Two-phase archive process:
1. Collect all post URLs from author pages
2. For each post: extract details, download media, save content

Features:
- Incremental archiving (skip completed posts)
- Resume capability (post-level and file-level)
- Progress tracking with .progress and .complete markers
- Rate limiting to avoid anti-scraping measures
"""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import re

from .extractor import PostExtractor
from .downloader import MediaDownloader
from .utils import (
    sanitize_filename,
    should_archive,
    mark_complete,
    get_archive_progress,
    save_archive_progress
)
from utils.logger import setup_logger


class ForumArchiver:
    """论坛归档器（协调 Extractor + Downloader）"""

    def __init__(self, config: dict):
        """Initialize archiver

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config

        # Extract forum URL (base URL)
        section_url = config['forum']['section_url']
        # Parse base URL from section URL (e.g., https://t66y.com/...)
        match = re.match(r'(https?://[^/]+)', section_url)
        self.base_url = match.group(1) if match else section_url

        self.archive_dir = Path(config['storage']['archive_path'])

        # Setup logging
        project_root = Path(__file__).parent.parent.parent.parent
        log_dir = project_root / 'logs'
        log_dir.mkdir(exist_ok=True)

        self.logger = setup_logger('archiver', log_dir)

        # Initialize sub-components
        self.extractor = PostExtractor(self.base_url, log_dir)
        self.downloader = MediaDownloader(
            max_concurrent=config.get('advanced', {}).get('max_concurrent', 5),
            retry_count=config.get('advanced', {}).get('download_retry', 3),
            timeout=config.get('advanced', {}).get('download_timeout', 30),
            log_dir=log_dir
        )

        # Rate limiting delay
        self.rate_limit_delay = config.get('advanced', {}).get('rate_limit_delay', 0.5)

        # Download settings
        self.download_images = config.get('storage', {}).get('download', {}).get('images', True)
        self.download_videos = config.get('storage', {}).get('download', {}).get('videos', True)

    async def archive_author(
        self,
        author_name: str,
        author_url: str,
        max_pages: Optional[int] = None
    ) -> Dict:
        """归档作者的所有帖子

        Args:
            author_name: Author name
            author_url: Author's post list URL
            max_pages: Maximum pages to scrape (None = all)

        Returns:
            Statistics dict with keys: total, new, skipped, failed
        """
        self.logger.info(f"=" * 60)
        self.logger.info(f"开始归档作者: {author_name}")
        self.logger.info(f"作者 URL: {author_url}")
        self.logger.info(f"=" * 60)

        try:
            # 启动浏览器
            await self.extractor.start()

            # 阶段一：收集所有帖子 URL
            self.logger.info("【阶段 1】收集帖子 URL...")
            post_urls = await self.extractor.collect_post_urls(author_url, max_pages)
            total_posts = len(post_urls)

            if total_posts == 0:
                self.logger.warning(f"未找到任何帖子")
                return {
                    'total': 0,
                    'new': 0,
                    'skipped': 0,
                    'failed': 0
                }

            # 阶段二：逐个处理帖子
            self.logger.info(f"【阶段 2】处理 {total_posts} 篇帖子...")
            new_posts = 0
            skipped_posts = 0
            failed_posts = 0

            for idx, post_url in enumerate(post_urls, 1):
                self.logger.info(f"\n--- 帖子 {idx}/{total_posts} ---")

                try:
                    # 提取帖子详情
                    post_data = await self.extractor.extract_post_details(post_url)

                    if not post_data:
                        self.logger.error(f"提取失败，跳过帖子: {post_url}")
                        failed_posts += 1
                        continue

                    # 计算目录路径
                    post_dir = self._get_post_directory(author_name, post_data)

                    # 增量检查
                    if not should_archive(post_dir, post_url):
                        self.logger.info(f"✓ 跳过已归档: {post_data['title']}")
                        skipped_posts += 1
                        continue

                    # 归档帖子
                    success = await self._archive_post(post_dir, post_data)

                    if success:
                        new_posts += 1
                        self.logger.info(f"✓ 归档成功: {post_data['title']}")
                    else:
                        failed_posts += 1
                        self.logger.error(f"✗ 归档失败: {post_data['title']}")

                    # 防反爬延迟
                    if idx < total_posts:
                        await asyncio.sleep(self.rate_limit_delay)

                except Exception as e:
                    self.logger.error(f"处理帖子失败: {str(e)}")
                    failed_posts += 1
                    continue

            # 汇总统计
            self.logger.info(f"\n" + "=" * 60)
            self.logger.info(f"归档完成: {author_name}")
            self.logger.info(f"  总计: {total_posts} 篇")
            self.logger.info(f"  新增: {new_posts} 篇")
            self.logger.info(f"  跳过: {skipped_posts} 篇")
            self.logger.info(f"  失败: {failed_posts} 篇")
            self.logger.info(f"=" * 60)

            return {
                'total': total_posts,
                'new': new_posts,
                'skipped': skipped_posts,
                'failed': failed_posts
            }

        except Exception as e:
            self.logger.error(f"归档失败: {str(e)}", exc_info=True)
            raise

        finally:
            await self.extractor.close()

    async def _archive_post(self, post_dir: Path, post_data: Dict) -> bool:
        """归档单个帖子（带断点续传）

        Args:
            post_dir: Post directory path
            post_data: Post data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # 创建目录
            post_dir.mkdir(parents=True, exist_ok=True)

            # 获取归档进度（断点续传）
            progress = get_archive_progress(post_dir)

            # Step 1: 保存正文（如果未完成）
            if not progress.get('content', False):
                self.logger.info("  → 保存正文...")
                content_file = post_dir / 'content.html'

                # Save metadata + content
                metadata = f"""<!-- 帖子元数据
标题: {post_data['title']}
作者: {post_data['author']}
时间: {post_data['time']}
URL: {post_data['url']}
-->

"""
                full_content = metadata + post_data['content']
                content_file.write_text(full_content, encoding='utf-8')

                progress['content'] = True
                save_archive_progress(post_dir, progress)
                self.logger.info("  ✓ 正文已保存")

            # Step 2: 下载图片（如果启用且未完成）
            if (self.download_images and
                post_data['images'] and
                not progress.get('images_done', False)):

                self.logger.info(f"  → 下载图片 ({len(post_data['images'])} 张)...")
                photo_dir = post_dir / 'photo'
                results = await self.downloader.download_files(
                    post_data['images'],
                    photo_dir,
                    prefix='img_'
                )

                progress['images_done'] = True
                save_archive_progress(post_dir, progress)

                success_count = sum(1 for r in results if r)
                self.logger.info(
                    f"  ✓ 图片下载完成: {success_count}/{len(post_data['images'])}"
                )

            # Step 3: 下载视频（如果启用且未完成）
            if (self.download_videos and
                post_data['videos'] and
                not progress.get('videos_done', False)):

                self.logger.info(f"  → 下载视频 ({len(post_data['videos'])} 个)...")
                video_dir = post_dir / 'video'
                results = await self.downloader.download_files(
                    post_data['videos'],
                    video_dir,
                    prefix='video_'
                )

                progress['videos_done'] = True
                save_archive_progress(post_dir, progress)

                success_count = sum(1 for r in results if r)
                self.logger.info(
                    f"  ✓ 视频下载完成: {success_count}/{len(post_data['videos'])}"
                )

            # 所有步骤完成，标记完成并删除进度文件
            mark_complete(post_dir, post_data['url'])

            progress_file = post_dir / '.progress'
            if progress_file.exists():
                progress_file.unlink()

            return True

        except Exception as e:
            self.logger.error(f"归档帖子失败: {str(e)}", exc_info=True)
            return False

    def _get_post_directory(self, author_name: str, post_data: Dict) -> Path:
        """计算帖子目录路径

        Args:
            author_name: Author name
            post_data: Post data dictionary

        Returns:
            Post directory path following structure: author/year/month/title
        """
        # 解析发布时间
        pub_time = self._parse_time(post_data['time'])

        year = str(pub_time.year)
        month = f"{pub_time.month:02d}"

        # 安全化标题
        max_length = self.config.get('storage', {}).get('organization', {}).get(
            'filename_max_length', 100
        )
        safe_title = sanitize_filename(post_data['title'], max_length=max_length)

        # 构建路径
        post_dir = self.archive_dir / author_name / year / month / safe_title

        return post_dir

    def _parse_time(self, time_text: str) -> datetime:
        """解析时间字符串

        Args:
            time_text: Time string from post

        Returns:
            Datetime object
        """
        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d %H:%M',
            '%Y/%m/%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(time_text.strip(), fmt)
            except ValueError:
                continue

        # If parsing fails, use current time
        self.logger.warning(f"无法解析时间: {time_text}, 使用当前时间")
        return datetime.now()
