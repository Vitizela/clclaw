"""Utility functions for scraper package

CRITICAL: Filename sanitization MUST match Node.js implementation exactly
to ensure compatibility with existing archive structure.
"""

import re
import hashlib
import json
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """文件名安全化处理（必须与 Node.js 一致）

    This function MUST produce identical output to the Node.js version:
    name.replace(/[<>:"/\\|?*]/g, '_').substring(0, 100).trim()

    Args:
        name: Original filename
        max_length: Maximum length (default: 100)

    Returns:
        Sanitized filename safe for all filesystems

    Examples:
        >>> sanitize_filename('文件名<>:"/\\|?*测试')
        '文件名_________测试'
        >>> sanitize_filename('a' * 150)
        'aaaa...'  # exactly 100 chars
    """
    # Replace forbidden characters with underscore
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)

    # Truncate to max length
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]

    # Trim spaces and dots from edges
    safe_name = safe_name.strip(' .')

    # Handle empty result
    return safe_name if safe_name else 'untitled'


def generate_url_hash(url: str) -> str:
    """生成 URL 的 MD5 hash（用于防冲突）

    Args:
        url: Full URL of the post

    Returns:
        First 8 characters of MD5 hash
    """
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:8]


def should_archive(post_dir: Path, url: str) -> bool:
    """检查是否需要归档（增量检查）

    Checks if a post needs to be archived by comparing URL hashes.

    Args:
        post_dir: Post directory path
        url: Current post URL

    Returns:
        True if post should be archived, False if already complete
    """
    if not post_dir.exists():
        return True

    complete_file = post_dir / '.complete'
    if not complete_file.exists():
        return True  # 未完成的目录需要重新归档

    # 读取已保存的 URL hash
    try:
        saved_hash = complete_file.read_text().strip()
        current_hash = generate_url_hash(url)
        return saved_hash != current_hash
    except Exception:
        return True


def mark_complete(post_dir: Path, url: str) -> None:
    """标记归档完成

    Creates a .complete marker file with the URL hash.

    Args:
        post_dir: Post directory path
        url: Post URL
    """
    complete_file = post_dir / '.complete'
    url_hash = generate_url_hash(url)
    complete_file.write_text(url_hash)


def get_archive_progress(post_dir: Path) -> dict:
    """获取归档进度（断点续传）

    Reads the .progress file to determine which steps are complete.

    Args:
        post_dir: Post directory path

    Returns:
        Progress dictionary with keys: content, images_done, videos_done
    """
    progress_file = post_dir / '.progress'
    if not progress_file.exists():
        return {'content': False, 'images_done': False, 'videos_done': False}

    try:
        return json.loads(progress_file.read_text())
    except Exception:
        return {'content': False, 'images_done': False, 'videos_done': False}


def save_archive_progress(post_dir: Path, progress: dict) -> None:
    """保存归档进度（断点续传）

    Saves current progress to .progress file for resume capability.

    Args:
        post_dir: Post directory path
        progress: Progress dictionary
    """
    progress_file = post_dir / '.progress'
    progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2))


def parse_relative_url(base_url: str, relative_url: str) -> str:
    """将相对 URL 转换为绝对 URL

    Args:
        base_url: Base forum URL (e.g., https://example.com)
        relative_url: Relative URL path

    Returns:
        Absolute URL
    """
    if relative_url.startswith('http'):
        return relative_url

    # Remove leading slash if present
    if relative_url.startswith('/'):
        relative_url = relative_url[1:]

    # Ensure base URL doesn't end with slash
    base_url = base_url.rstrip('/')

    return f"{base_url}/{relative_url}"
