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
import sys

from jinja2 import Environment, FileSystemLoader

from .extractor import PostExtractor
from .downloader import MediaDownloader
from .utils import (
    sanitize_filename,
    should_archive,
    mark_complete,
    get_archive_progress,
    save_archive_progress
)
from ..utils.logger import setup_logger

# Add parent to path for templates import
sys.path.insert(0, str(Path(__file__).parent.parent))
from templates.filters import clean_html_content, format_file_size


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
        self.extractor = PostExtractor(self.base_url, log_dir, config)
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

        # Initialize Jinja2 template engine
        template_dir = Path(__file__).parent.parent / 'templates'
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Register custom filters
        self.jinja_env.filters['clean'] = clean_html_content
        self.jinja_env.filters['size'] = format_file_size

        self.logger.info("模板引擎已初始化")

    async def archive_author(
        self,
        author_name: str,
        author_url: str,
        max_pages: Optional[int] = None,
        max_posts: Optional[int] = None
    ) -> Dict:
        """归档作者的所有帖子

        Args:
            author_name: Author name
            author_url: Author's post list URL
            max_pages: Maximum pages to scrape (None = all)
            max_posts: Maximum posts to archive (None = all)

        Returns:
            Statistics dict with keys: total, new, skipped, failed
        """
        self.logger.info(f"=" * 60)
        self.logger.info(f"开始归档作者: {author_name}")
        self.logger.info(f"作者 URL: {author_url}")
        if max_posts:
            self.logger.info(f"限制: 最多 {max_posts} 篇帖子")
        elif max_pages:
            self.logger.info(f"限制: 最多 {max_pages} 页")
        self.logger.info(f"=" * 60)

        try:
            # 启动浏览器
            await self.extractor.start()

            # 阶段一：收集所有帖子 URL（带作者过滤）
            self.logger.info("【阶段 1】收集帖子 URL...")
            post_urls = await self.extractor.collect_post_urls(
                author_url,
                max_pages,
                max_posts,
                author_name=author_name
            )

            # 🧪 测试模式：限制帖子数量（取消注释下面这行）
            # post_urls = post_urls[:3]  # 只处理前 3 篇帖子

            total_posts = len(post_urls)

            # 论坛总数 = 实际收集到的主题帖数量
            # 说明：只统计作者作为楼主的原创主题帖，不包含回复别人的帖子
            forum_total = total_posts
            self.logger.info(
                f"作者 {author_name} 的主题帖总数: {forum_total} "
                f"(只统计楼主原创帖，不含回复)"
            )

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

                    # 验证作者名是否匹配（忽略大小写和空格）
                    actual_author = post_data['author'].strip()
                    expected_author = author_name.strip()
                    if actual_author.lower() != expected_author.lower():
                        self.logger.warning(
                            f"⚠ 作者不匹配，跳过: {post_data['title']} "
                            f"(实际作者: {actual_author}, 期望: {expected_author})"
                        )
                        skipped_posts += 1
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
                'failed': failed_posts,
                'forum_total': forum_total  # 新增：返回论坛总数
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

            # Step 1: 下载图片（如果启用且未完成）
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

            # Step 2: 下载视频（如果启用且未完成）
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

            # Step 3: 生成 content.html（使用新模板）
            # 注意：在媒体下载完成后生成，这样可以正确列出本地文件
            if not progress.get('content', False):
                self.logger.info("  → 生成 content.html...")
                self._save_content_html(post_data, post_dir)

                progress['content'] = True
                save_archive_progress(post_dir, progress)

            # 所有步骤完成，标记完成并删除进度文件
            mark_complete(post_dir, post_data['url'])

            progress_file = post_dir / '.progress'
            if progress_file.exists():
                progress_file.unlink()

            return True

        except Exception as e:
            self.logger.error(f"归档帖子失败: {str(e)}", exc_info=True)
            return False

    def _prepare_media_list(self, media_urls: List[str], media_type: str, post_dir: Path) -> List[Dict]:
        """准备媒体文件列表（用于模板）

        Args:
            media_urls: 原始 URL 列表
            media_type: 'image' 或 'video'
            post_dir: 帖子目录

        Returns:
            [{'filename': 'img_1.jpg', 'url': '...', 'size': '1.2 MB'}, ...]
        """
        media_list = []

        # 确定子目录和文件前缀
        if media_type == 'image':
            subdir = post_dir / 'photo'
            prefix = 'img_'
            extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        else:  # video
            subdir = post_dir / 'video'
            prefix = 'video_'
            extensions = ['.mp4', '.avi', '.mkv', '.webm', '.mov']

        if not subdir.exists():
            return []

        # 遍历原始 URL，匹配本地文件
        for idx, url in enumerate(media_urls, 1):
            # 尝试找到对应的本地文件
            filename = None
            file_size = None

            # 方法1：按索引匹配（img_1.jpg, img_2.jpg...）
            for ext in extensions:
                candidate = subdir / f"{prefix}{idx}{ext}"
                if candidate.exists():
                    filename = f"{prefix}{idx}{ext}"
                    file_size = candidate.stat().st_size
                    break

            # 如果找不到，使用占位
            if not filename:
                filename = f"{prefix}{idx}.unknown"

            media_list.append({
                'filename': filename,
                'url': url,
                'size': format_file_size(file_size) if file_size else None
            })

        return media_list

    def _save_content_html(self, post_data: Dict, post_dir: Path):
        """使用模板生成并保存 content.html

        Args:
            post_data: 帖子数据（包含 title, author, time, content, images, videos, url）
            post_dir: 帖子目录
        """
        try:
            # 准备模板数据
            template_data = {
                'title': post_data.get('title', '无标题'),
                'author': post_data.get('author', '未知作者'),
                'publish_time': post_data.get('time', 'N/A'),
                'archive_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'url': post_data.get('url', ''),
                'content': clean_html_content(post_data.get('content', '')),
                'content_length': len(post_data.get('content', '')),
                'images': self._prepare_media_list(
                    post_data.get('images', []),
                    'image',
                    post_dir
                ),
                'videos': self._prepare_media_list(
                    post_data.get('videos', []),
                    'video',
                    post_dir
                )
            }

            # 加载模板
            template = self.jinja_env.get_template('post.html')

            # 渲染 HTML
            html = template.render(**template_data)

            # 保存文件
            content_file = post_dir / 'content.html'
            content_file.write_text(html, encoding='utf-8')

            self.logger.info(f"  ✓ 已生成 content.html")

        except Exception as e:
            self.logger.error(f"生成 content.html 失败: {str(e)}", exc_info=True)
            raise

    def _get_post_directory(self, author_name: str, post_data: Dict) -> Path:
        """计算帖子目录路径

        Args:
            author_name: Author name
            post_data: Post data dictionary

        Returns:
            Post directory path following structure: author/year/month/YYYY-MM-DD_title
        """
        # 解析发布时间
        pub_time = self._parse_time(post_data['time'])

        year = str(pub_time.year)
        month = f"{pub_time.month:02d}"

        # 格式化日期：YYYY-MM-DD
        date_prefix = pub_time.strftime('%Y-%m-%d')

        # 安全化标题
        max_length = self.config.get('storage', {}).get('organization', {}).get(
            'filename_max_length', 100
        )

        # 计算标题最大长度：总长度 - 日期长度 - 下划线
        # 格式：YYYY-MM-DD_标题
        # 日期：10字符，下划线：1字符
        title_max_length = max_length - 11  # 100 - 11 = 89
        safe_title = sanitize_filename(post_data['title'], max_length=title_max_length)

        # 构建带日期的目录名
        dir_name = f"{date_prefix}_{safe_title}"

        # 构建完整路径
        post_dir = self.archive_dir / author_name / year / month / dir_name

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
