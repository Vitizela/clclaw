"""Integration tests for Phase 2 scraper components

These tests verify that all components work together correctly.
"""

import pytest
from pathlib import Path
from src.scraper.archiver import ForumArchiver


class TestScraperIntegration:
    """Test scraper component integration"""

    def test_archiver_initialization(self):
        """测试归档器初始化"""
        config = {
            'forum': {
                'section_url': 'https://t66y.com/thread0806.php?fid=7',
                'timeout': 60,
                'max_retries': 3
            },
            'storage': {
                'archive_path': './test_archive',
                'download': {
                    'images': True,
                    'videos': True
                },
                'organization': {
                    'filename_max_length': 100
                }
            },
            'advanced': {
                'max_concurrent': 5,
                'download_retry': 3,
                'download_timeout': 30,
                'rate_limit_delay': 0.5
            }
        }

        archiver = ForumArchiver(config)

        assert archiver.base_url == 'https://t66y.com'
        assert archiver.archive_dir == Path('./test_archive')
        assert archiver.download_images is True
        assert archiver.download_videos is True
        assert archiver.rate_limit_delay == 0.5

    def test_post_directory_calculation(self):
        """测试帖子目录路径计算"""
        config = {
            'forum': {
                'section_url': 'https://t66y.com/thread0806.php?fid=7'
            },
            'storage': {
                'archive_path': './test_archive',
                'download': {
                    'images': True,
                    'videos': True
                },
                'organization': {
                    'filename_max_length': 100
                }
            },
            'advanced': {
                'max_concurrent': 5,
                'download_retry': 3,
                'download_timeout': 30,
                'rate_limit_delay': 0.5
            }
        }

        archiver = ForumArchiver(config)

        post_data = {
            'title': '测试帖子<标题>',
            'time': '2026-02-11 10:30:00',
            'author': '测试作者',
            'url': 'https://example.com/post/123'
        }

        post_dir = archiver._get_post_directory('测试作者', post_data)

        # Should sanitize title and organize by year/month
        expected = Path('./test_archive/测试作者/2026/02/测试帖子_标题_')
        assert post_dir == expected


class TestConfigCompatibility:
    """Test config compatibility"""

    def test_config_structure(self):
        """测试配置结构兼容性"""
        from src.config.manager import ConfigManager

        manager = ConfigManager()
        config = manager.load()

        # 验证 Phase 2 所需的配置项
        assert 'experimental' in config
        assert 'use_python_scraper' in config['experimental']
        assert 'advanced' in config
        assert 'max_concurrent' in config['advanced']
        assert 'download_retry' in config['advanced']
        assert 'download_timeout' in config['advanced']
        assert 'rate_limit_delay' in config['advanced']
