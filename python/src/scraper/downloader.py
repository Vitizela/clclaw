"""Media downloader with concurrent download, retry, and resume support

Features:
- Concurrent downloads with semaphore control
- Automatic retry on failure
- Resume capability (HTTP Range requests)
- Progress bar with tqdm
- File completion markers
"""

import asyncio
import aiohttp
from pathlib import Path
from typing import List, Optional
from tqdm.asyncio import tqdm
import os

from utils.logger import setup_logger


class MediaDownloader:
    """媒体资源下载器（支持并发、重试和断点续传）"""

    def __init__(
        self,
        max_concurrent: int,
        retry_count: int,
        timeout: int,
        log_dir: Path
    ):
        """Initialize downloader

        Args:
            max_concurrent: Maximum number of concurrent downloads
            retry_count: Number of retry attempts on failure
            timeout: Request timeout in seconds
            log_dir: Directory for log files
        """
        self.max_concurrent = max_concurrent
        self.retry_count = retry_count
        self.timeout = timeout
        self.logger = setup_logger('downloader', log_dir)
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def download_files(
        self,
        urls: List[str],
        output_dir: Path,
        prefix: str = ''
    ) -> List[bool]:
        """批量下载文件

        Args:
            urls: List of URLs to download
            output_dir: Output directory
            prefix: Filename prefix (e.g., 'img_', 'video_')

        Returns:
            List of success/failure booleans
        """
        if not urls:
            return []

        output_dir.mkdir(parents=True, exist_ok=True)

        tasks = []
        for idx, url in enumerate(urls, 1):
            # Extract file extension from URL
            ext = self._get_extension(url)
            filename = f"{prefix}{idx}{ext}"
            output_path = output_dir / filename
            tasks.append(self._download_single(url, output_path))

        # 使用 tqdm 显示进度
        self.logger.info(f"开始下载 {len(urls)} 个文件到 {output_dir}")

        results = []
        with tqdm(
            total=len(tasks),
            desc=f"下载{prefix.rstrip('_')}",
            unit="file"
        ) as pbar:
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                pbar.update(1)

        success_count = sum(1 for r in results if r)
        self.logger.info(
            f"下载完成: {success_count}/{len(urls)} 成功, "
            f"{len(urls) - success_count} 失败"
        )
        return results

    async def _download_single(self, url: str, output_path: Path) -> bool:
        """下载单个文件（带重试和断点续传）

        Args:
            url: File URL
            output_path: Output file path

        Returns:
            True if successful, False otherwise
        """
        async with self.semaphore:
            # 检查文件是否已完整下载
            if self._is_download_complete(output_path):
                self.logger.debug(f"文件已存在，跳过: {output_path.name}")
                return True

            # 获取已下载的大小（断点续传）
            downloaded_size = 0
            temp_path = output_path.with_suffix(output_path.suffix + '.downloading')

            if temp_path.exists():
                downloaded_size = temp_path.stat().st_size
                self.logger.info(
                    f"继续下载 {output_path.name}，已下载 {downloaded_size} 字节"
                )

            for attempt in range(self.retry_count):
                try:
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        # 设置 Range 头实现断点续传
                        headers = {}
                        if downloaded_size > 0:
                            headers['Range'] = f'bytes={downloaded_size}-'

                        async with session.get(url, headers=headers) as response:
                            # 206 表示部分内容（断点续传），200 表示完整下载
                            if response.status in (200, 206):
                                # 206 表示服务器支持断点续传，追加写入
                                mode = 'ab' if response.status == 206 else 'wb'

                                with open(temp_path, mode) as f:
                                    async for chunk in response.content.iter_chunked(8192):
                                        f.write(chunk)

                                # 下载完成，重命名临时文件
                                temp_path.rename(output_path)

                                # 创建完成标记
                                self._mark_download_complete(output_path)

                                self.logger.debug(f"下载成功: {output_path.name}")
                                return True

                            elif response.status == 416:
                                # 416 Range Not Satisfiable - 文件可能已经完整
                                if temp_path.exists():
                                    temp_path.rename(output_path)
                                    self._mark_download_complete(output_path)
                                    self.logger.debug(
                                        f"下载完成（Range 416）: {output_path.name}"
                                    )
                                    return True
                                else:
                                    self.logger.warning(
                                        f"下载失败 {url}: HTTP 416 (无临时文件)"
                                    )
                                    return False

                            else:
                                self.logger.warning(
                                    f"下载失败 {url}: HTTP {response.status}"
                                )

                except asyncio.TimeoutError:
                    if attempt < self.retry_count - 1:
                        self.logger.warning(
                            f"下载超时，重试 {attempt+1}/{self.retry_count}: {url}"
                        )
                        # 更新已下载大小
                        if temp_path.exists():
                            downloaded_size = temp_path.stat().st_size
                        await asyncio.sleep(1 * (attempt + 1))  # 指数退避
                    else:
                        self.logger.error(f"下载超时（已达最大重试次数）: {url}")

                except Exception as e:
                    if attempt < self.retry_count - 1:
                        self.logger.warning(
                            f"下载失败，重试 {attempt+1}/{self.retry_count}: {url} - {str(e)}"
                        )
                        # 更新已下载大小
                        if temp_path.exists():
                            downloaded_size = temp_path.stat().st_size
                        await asyncio.sleep(1 * (attempt + 1))
                    else:
                        self.logger.error(f"下载失败（已达最大重试次数）: {url} - {str(e)}")

            return False

    def _is_download_complete(self, file_path: Path) -> bool:
        """检查文件是否已完整下载

        Args:
            file_path: File path to check

        Returns:
            True if file exists and has completion marker
        """
        if not file_path.exists():
            return False

        # 检查完成标记文件
        marker_file = file_path.with_suffix(file_path.suffix + '.done')
        return marker_file.exists()

    def _mark_download_complete(self, file_path: Path) -> None:
        """标记文件下载完成

        Args:
            file_path: Downloaded file path
        """
        marker_file = file_path.with_suffix(file_path.suffix + '.done')
        marker_file.touch()

    def _get_extension(self, url: str) -> str:
        """从 URL 中提取文件扩展名

        Args:
            url: File URL

        Returns:
            File extension (e.g., '.jpg', '.mp4')
        """
        # Remove query parameters
        url_path = url.split('?')[0]

        # Extract extension
        ext = Path(url_path).suffix

        # Default extensions if not found
        if not ext:
            if any(x in url.lower() for x in ['jpg', 'jpeg', 'png', 'gif', 'webp']):
                ext = '.jpg'
            elif any(x in url.lower() for x in ['mp4', 'webm', 'mov', 'avi']):
                ext = '.mp4'
            else:
                ext = '.bin'

        return ext
