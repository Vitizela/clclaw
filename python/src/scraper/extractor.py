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

    def __init__(self, base_url: str, log_dir: Path):
        """Initialize extractor

        Args:
            base_url: Forum base URL (e.g., https://example.com)
            log_dir: Directory for log files
        """
        self.base_url = base_url.rstrip('/')
        self.logger = setup_logger('extractor', log_dir)
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

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
        max_pages: Optional[int] = None
    ) -> List[str]:
        """收集作者的所有帖子 URL（两阶段的第一阶段）

        Args:
            author_url: Author's post list URL
            max_pages: Maximum number of pages to scrape (None = all)

        Returns:
            List of post URLs
        """
        self.logger.info(f"开始收集帖子列表: {author_url}")
        post_urls = []
        page_num = 1

        while True:
            if max_pages and page_num > max_pages:
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
                await self.page.goto(current_url, wait_until='networkidle', timeout=30000)

                # 提取帖子 URL（注意：使用 Python API - query_selector_all）
                # Selector: 匹配所有包含 htm_data 的帖子链接
                links = await self.page.query_selector_all('table a[href*="htm_data"]')

                if not links:
                    self.logger.info(f"第 {page_num} 页无更多帖子")
                    break

                # 获取所有 href 属性
                page_post_urls = []
                for link in links:
                    href = await link.get_attribute('href')
                    if href:
                        # Convert to absolute URL
                        full_url = parse_relative_url(self.base_url, href)
                        page_post_urls.append(full_url)

                post_urls.extend(page_post_urls)
                self.logger.info(f"第 {page_num} 页: 找到 {len(page_post_urls)} 篇帖子")

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
            await self.page.goto(post_url, wait_until='networkidle', timeout=30000)

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
                '.tr1.do_not_catch .f10',
                '.postinfo',
                '.authorinfo em'
            ]
            for selector in selectors:
                time_elem = await self.page.query_selector(selector)
                if time_elem:
                    time_text = await time_elem.inner_text()
                    # Clean up time text
                    time_text = re.sub(r'发表于[:：\s]*', '', time_text)
                    return time_text.strip()

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

            # Try video elements
            video_elems = await self.page.query_selector_all('video source')
            for video in video_elems:
                src = await video.get_attribute('src')
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
