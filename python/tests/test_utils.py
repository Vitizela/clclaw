"""Unit tests for scraper.utils module

CRITICAL: filename sanitization tests ensure compatibility with Node.js
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from src.scraper.utils import (
    sanitize_filename,
    generate_url_hash,
    should_archive,
    mark_complete,
    get_archive_progress,
    save_archive_progress,
    parse_relative_url
)


class TestSanitizeFilename:
    """Test filename sanitization (P0 - must match Node.js exactly)"""

    def test_special_characters_replacement(self):
        """测试特殊字符替换"""
        # All forbidden characters should be replaced with underscore
        result = sanitize_filename('文件名<>:"/\\|?*测试')
        assert result == '文件名_________测试'

    def test_length_truncation(self):
        """测试长度截断"""
        long_name = 'a' * 150
        result = sanitize_filename(long_name)
        assert len(result) == 100
        assert result == 'a' * 100

    def test_trim_spaces_and_dots(self):
        """测试空格和点号处理"""
        assert sanitize_filename('  test.  ') == 'test'
        assert sanitize_filename('...test...') == 'test'
        # Note: internal spaces/dots are preserved, only edges are trimmed
        assert sanitize_filename(' . test . ') == 'test'

    def test_empty_string(self):
        """测试空字符串"""
        assert sanitize_filename('') == 'untitled'
        assert sanitize_filename('   ') == 'untitled'
        assert sanitize_filename('...') == 'untitled'

    def test_custom_max_length(self):
        """测试自定义最大长度"""
        result = sanitize_filename('a' * 150, max_length=50)
        assert len(result) == 50

    def test_unicode_preservation(self):
        """测试 Unicode 字符保留"""
        result = sanitize_filename('中文标题测试123')
        assert result == '中文标题测试123'

    def test_mixed_content(self):
        """测试混合内容"""
        result = sanitize_filename('Post: "Hello World" <2026>')
        assert result == 'Post_ _Hello World_ _2026_'


class TestUrlHashing:
    """Test URL hashing functionality"""

    def test_generate_url_hash(self):
        """测试 URL hash 生成"""
        url = "https://example.com/post/123"
        hash1 = generate_url_hash(url)

        # Should be 8 characters
        assert len(hash1) == 8

        # Should be deterministic
        hash2 = generate_url_hash(url)
        assert hash1 == hash2

        # Different URLs should produce different hashes
        different_url = "https://example.com/post/456"
        hash3 = generate_url_hash(different_url)
        assert hash1 != hash3


class TestArchiveTracking:
    """Test archive completion tracking"""

    def setup_method(self):
        """创建临时目录用于测试"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理临时目录"""
        shutil.rmtree(self.temp_dir)

    def test_should_archive_new_directory(self):
        """测试新目录需要归档"""
        post_dir = self.temp_dir / "new_post"
        assert should_archive(post_dir, "https://example.com/post/1")

    def test_should_archive_incomplete_directory(self):
        """测试未完成的目录需要归档"""
        post_dir = self.temp_dir / "incomplete_post"
        post_dir.mkdir()

        # Directory exists but no .complete file
        assert should_archive(post_dir, "https://example.com/post/1")

    def test_should_not_archive_completed_same_url(self):
        """测试已完成的相同 URL 不需要归档"""
        post_dir = self.temp_dir / "completed_post"
        post_dir.mkdir()

        url = "https://example.com/post/1"
        mark_complete(post_dir, url)

        assert not should_archive(post_dir, url)

    def test_should_archive_completed_different_url(self):
        """测试已完成但 URL 不同需要归档"""
        post_dir = self.temp_dir / "completed_post"
        post_dir.mkdir()

        url1 = "https://example.com/post/1"
        url2 = "https://example.com/post/2"

        mark_complete(post_dir, url1)

        assert should_archive(post_dir, url2)

    def test_mark_complete(self):
        """测试标记完成"""
        post_dir = self.temp_dir / "test_post"
        post_dir.mkdir()

        url = "https://example.com/post/123"
        mark_complete(post_dir, url)

        complete_file = post_dir / '.complete'
        assert complete_file.exists()

        saved_hash = complete_file.read_text().strip()
        expected_hash = generate_url_hash(url)
        assert saved_hash == expected_hash


class TestProgressTracking:
    """Test progress tracking for resume capability"""

    def setup_method(self):
        """创建临时目录用于测试"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.post_dir = self.temp_dir / "test_post"
        self.post_dir.mkdir()

    def teardown_method(self):
        """清理临时目录"""
        shutil.rmtree(self.temp_dir)

    def test_get_progress_no_file(self):
        """测试无进度文件时的默认状态"""
        progress = get_archive_progress(self.post_dir)
        assert progress == {
            'content': False,
            'images_done': False,
            'videos_done': False
        }

    def test_save_and_get_progress(self):
        """测试保存和读取进度"""
        initial_progress = {
            'content': True,
            'images_done': True,
            'videos_done': False
        }

        save_archive_progress(self.post_dir, initial_progress)
        loaded_progress = get_archive_progress(self.post_dir)

        assert loaded_progress == initial_progress

    def test_progress_file_corruption_handling(self):
        """测试损坏的进度文件处理"""
        progress_file = self.post_dir / '.progress'
        progress_file.write_text("invalid json {{{")

        progress = get_archive_progress(self.post_dir)
        assert progress == {
            'content': False,
            'images_done': False,
            'videos_done': False
        }


class TestUrlParsing:
    """Test URL parsing utilities"""

    def test_parse_relative_url_with_leading_slash(self):
        """测试带前导斜杠的相对 URL"""
        base = "https://example.com"
        relative = "/post/123"
        result = parse_relative_url(base, relative)
        assert result == "https://example.com/post/123"

    def test_parse_relative_url_without_leading_slash(self):
        """测试不带前导斜杠的相对 URL"""
        base = "https://example.com"
        relative = "post/123"
        result = parse_relative_url(base, relative)
        assert result == "https://example.com/post/123"

    def test_parse_absolute_url(self):
        """测试绝对 URL 直接返回"""
        base = "https://example.com"
        absolute = "https://other.com/post/123"
        result = parse_relative_url(base, absolute)
        assert result == absolute

    def test_base_url_with_trailing_slash(self):
        """测试 base URL 带尾部斜杠"""
        base = "https://example.com/"
        relative = "/post/123"
        result = parse_relative_url(base, relative)
        assert result == "https://example.com/post/123"
