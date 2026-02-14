"""Post extractor using Playwright

Two-phase extraction:
1. Collect all post URLs from author pages (with pagination)
2. Extract detailed content from each post

CRITICAL: Uses Python Playwright API (snake_case), not Node.js API!
"""

import asyncio
import re
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, Playwright
from bs4 import BeautifulSoup

from ..utils.logger import setup_logger
from .utils import parse_relative_url


class PostExtractor:
    """帖子提取器（使用 Python Playwright API）"""

    def __init__(self, base_url: str, log_dir: Path, config: dict = None):
        """Initialize extractor

        Args:
            base_url: Forum base URL (e.g., https://example.com)
            log_dir: Directory for log files
            config: Configuration dictionary (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.logger = setup_logger('extractor', log_dir)
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # 从配置读取超时和等待策略
        self.config = config or {}
        self.page_timeout = self.config.get('advanced', {}).get('page_load_timeout', 60) * 1000  # 转为毫秒
        self.wait_until = self.config.get('advanced', {}).get('wait_until', 'domcontentloaded')

        self.logger.info(f"页面超时: {self.page_timeout}ms, 等待策略: {self.wait_until}")

    async def start(self):
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
            self.logger.info("浏览器启动成功")
        except Exception as e:
            self.logger.error(f"浏览器启动失败: {str(e)}")
            raise

    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("浏览器已关闭")
        except Exception as e:
            self.logger.error(f"浏览器关闭失败: {str(e)}")

    async def collect_post_urls(
        self,
        author_url: str,
        max_pages: Optional[int] = None,
        max_posts: Optional[int] = None,
        author_name: Optional[str] = None
    ) -> List[str]:
        """收集作者的所有帖子 URL（两阶段的第一阶段）

        Args:
            author_url: Author's post list URL
            max_pages: Maximum number of pages to scrape (None = all)
            max_posts: Maximum number of posts to collect (None = all, takes priority over max_pages)
            author_name: Expected author name for filtering (optional)

        Returns:
            List of post URLs
        """
        self.logger.info(f"开始收集帖子列表: {author_url}")

        # 显示限制信息
        if max_posts:
            self.logger.info(f"限制: 最多收集 {max_posts} 篇帖子")
        elif max_pages:
            self.logger.info(f"限制: 最多收集 {max_pages} 页")

        post_urls = []
        page_num = 1

        # 检测 URL 类型：@作者名 页面不需要作者过滤
        is_author_homepage = '/@' in author_url
        if is_author_homepage:
            self.logger.info("检测到作者主页格式，跳过作者过滤")

        while True:
            # 检查帖子数限制（优先）
            if max_posts and len(post_urls) >= max_posts:
                self.logger.info(f"已达到帖子数限制: {len(post_urls)} 篇")
                break

            # 检查页数限制
            if max_pages and page_num > max_pages:
                self.logger.info(f"已达到页数限制: {page_num-1} 页")
                break

            # 构造分页 URL
            if page_num > 1:
                # Assume pagination format: &page=N
                separator = '&' if '?' in author_url else '?'
                current_url = f"{author_url}{separator}page={page_num}"
            else:
                current_url = author_url

            try:
                self.logger.info(f"正在抓取第 {page_num} 页...")
                await self.page.goto(current_url, wait_until=self.wait_until, timeout=self.page_timeout)

                # 找所有包含帖子链接的行
                all_rows = await self.page.query_selector_all('table tbody tr')

                page_post_urls = []
                filtered_count = 0

                for row in all_rows:
                    # 检查这行是否包含帖子链接
                    link = await row.query_selector('a[href*="htm_data"]')
                    if not link:
                        continue

                    # 如果指定了作者名且不是作者主页，检查作者列（TD3）
                    if author_name and not is_author_homepage:
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 3:
                            # TD3 包含作者信息（格式：作者名 时间）
                            author_cell = cells[2]
                            author_text = await author_cell.inner_text()
                            # 提取作者名（空格前的部分）
                            row_author = author_text.split()[0] if author_text else ''

                            # 检查作者名是否匹配
                            if row_author.lower().strip() != author_name.lower().strip():
                                filtered_count += 1
                                continue

                    # 获取帖子 URL
                    href = await link.get_attribute('href')
                    if href:
                        full_url = parse_relative_url(self.base_url, href)
                        page_post_urls.append(full_url)

                        # 如果有帖子数限制，检查是否已达到
                        if max_posts and (len(post_urls) + len(page_post_urls)) >= max_posts:
                            break  # 达到限制，停止添加

                if filtered_count > 0:
                    self.logger.info(f"  过滤掉 {filtered_count} 个其他作者的帖子")

                if not page_post_urls:
                    self.logger.info(f"第 {page_num} 页无更多匹配的帖子")
                    break

                # 添加本页的帖子URL（可能需要截断以满足max_posts限制）
                if max_posts:
                    remaining = max_posts - len(post_urls)
                    page_post_urls = page_post_urls[:remaining]

                post_urls.extend(page_post_urls)
                self.logger.info(
                    f"第 {page_num} 页: 收集 {len(page_post_urls)} 篇帖子 "
                    f"（累计 {len(post_urls)} 篇）"
                )

                # 如果已达到帖子数限制，退出
                if max_posts and len(post_urls) >= max_posts:
                    break

                # 检查是否已达到页数限制
                if max_pages and page_num >= max_pages:
                    self.logger.info(f"已达到页数限制 ({max_pages} 页)，停止收集")
                    break

                page_num += 1

                # 检查是否有下一页
                next_page = await self.page.query_selector('.pages .next')
                if not next_page:
                    self.logger.info("没有下一页，收集完成")
                    break

                # 防反爬延迟
                await asyncio.sleep(0.5)

            except Exception as e:
                self.logger.error(f"第 {page_num} 页提取失败: {str(e)}")
                break

        self.logger.info(f"收集完成，共 {len(post_urls)} 篇帖子")
        return post_urls

    async def extract_post_details(self, post_url: str) -> Optional[Dict]:
        """提取单个帖子的详细信息（两阶段的第二阶段）

        Args:
            post_url: Full URL of the post

        Returns:
            Dictionary with keys: url, title, author, time, content, images, videos
            Returns None if extraction fails
        """
        self.logger.info(f"提取帖子详情: {post_url}")

        try:
            await self.page.goto(post_url, wait_until=self.wait_until, timeout=self.page_timeout)

            # 提取标题（选择器: h4.f16 或 h1）
            title = await self._extract_title()

            # 提取作者（选择器: .tr1.do_not_catch b 或 .authicon a）
            author = await self._extract_author()

            # 提取发布时间（选择器: .tr1.do_not_catch .f10）
            time_text = await self._extract_time()

            # 提取正文内容（选择器: .tpc_content 或 .t_msgfont）
            content = await self._extract_content()

            # 提取图片 URL
            images = await self._extract_images()

            # 提取视频 URL
            videos = await self._extract_videos()

            post_data = {
                'url': post_url,
                'title': title,
                'author': author,
                'time': time_text,
                'content': content,
                'images': images,
                'videos': videos
            }

            self.logger.info(
                f"提取成功: {title} | "
                f"{len(images)} 图片 | "
                f"{len(videos)} 视频"
            )

            return post_data

        except Exception as e:
            self.logger.error(f"提取失败 {post_url}: {str(e)}")
            return None

    async def _extract_title(self) -> str:
        """提取标题"""
        try:
            # Try multiple selectors
            selectors = ['h4.f16', 'h1', '.postbox h1', 'h2.ts']
            for selector in selectors:
                title_elem = await self.page.query_selector(selector)
                if title_elem:
                    title = await title_elem.inner_text()
                    return title.strip()

            self.logger.warning("未找到标题")
            return '无标题'
        except Exception as e:
            self.logger.error(f"标题提取失败: {str(e)}")
            return '无标题'

    async def _extract_author(self) -> str:
        """提取作者"""
        try:
            # Try multiple selectors
            selectors = [
                '.tr1.do_not_catch b',
                '.authicon a',
                '.postinfo a.author'
            ]
            for selector in selectors:
                author_elem = await self.page.query_selector(selector)
                if author_elem:
                    author = await author_elem.inner_text()
                    return author.strip()

            self.logger.warning("未找到作者")
            return '未知作者'
        except Exception as e:
            self.logger.error(f"作者提取失败: {str(e)}")
            return '未知作者'

    async def _extract_time(self) -> str:
        """提取发布时间"""
        try:
            # Try multiple selectors
            selectors = [
                '.tipad',                      # 最常见的位置
                '.tr1.do_not_catch .f10',
                '.postinfo',
                '.authorinfo em'
            ]
            for selector in selectors:
                time_elem = await self.page.query_selector(selector)
                if time_elem:
                    time_text = await time_elem.inner_text()

                    # 提取 "Posted: YYYY-MM-DD HH:MM" 格式
                    posted_match = re.search(r'Posted:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', time_text)
                    if posted_match:
                        return posted_match.group(1)

                    # 清理其他格式的时间文本
                    time_text = re.sub(r'发表于[:：\s]*', '', time_text)
                    time_text = time_text.strip()

                    # 如果包含时间格式，返回
                    if re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', time_text):
                        return time_text

            self.logger.warning("未找到发布时间")
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            self.logger.error(f"时间提取失败: {str(e)}")
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    async def _extract_content(self) -> str:
        """提取正文内容（HTML 格式）"""
        try:
            # Try multiple selectors
            selectors = [
                '.tpc_content',
                '.t_msgfont',
                '.postbody .message',
                '.postmessage'
            ]
            for selector in selectors:
                content_elem = await self.page.query_selector(selector)
                if content_elem:
                    content = await content_elem.inner_html()
                    return content

            self.logger.warning("未找到正文内容")
            return ''
        except Exception as e:
            self.logger.error(f"内容提取失败: {str(e)}")
            return ''

    async def _extract_images(self) -> List[str]:
        """提取图片 URL"""
        try:
            # Try multiple selectors for images
            selectors = [
                '.tpc_content img',
                '.t_msgfont img',
                '.postbody img',
                '.message img'
            ]

            images = []
            for selector in selectors:
                img_elems = await self.page.query_selector_all(selector)
                if img_elems:
                    for img in img_elems:
                        # Try multiple attributes
                        src = (
                            await img.get_attribute('data-original') or
                            await img.get_attribute('file') or
                            await img.get_attribute('src')
                        )
                        if src and src not in images:
                            # Convert to absolute URL
                            abs_url = parse_relative_url(self.base_url, src)
                            images.append(abs_url)
                    break

            return images
        except Exception as e:
            self.logger.error(f"图片提取失败: {str(e)}")
            return []

    async def _extract_videos(self) -> List[str]:
        """提取视频 URL"""
        try:
            videos = []

            # Try video elements with src attribute (most common)
            video_elems = await self.page.query_selector_all('video[src]')
            for video in video_elems:
                src = await video.get_attribute('src')
                if src and src not in videos:
                    abs_url = parse_relative_url(self.base_url, src)
                    videos.append(abs_url)

            # Try video elements with source children
            source_elems = await self.page.query_selector_all('video source')
            for source in source_elems:
                src = await source.get_attribute('src')
                if src and src not in videos:
                    abs_url = parse_relative_url(self.base_url, src)
                    videos.append(abs_url)

            # Try embed/iframe for video platforms
            iframe_elems = await self.page.query_selector_all('iframe')
            for iframe in iframe_elems:
                src = await iframe.get_attribute('src')
                if src and ('video' in src.lower() or 'player' in src.lower()):
                    if src not in videos:
                        videos.append(src)

            return videos
        except Exception as e:
            self.logger.error(f"视频提取失败: {str(e)}")
            return []

