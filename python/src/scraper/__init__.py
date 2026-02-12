"""Scraper package for Phase 2 - Python爬虫核心

This package provides Python-native web scraping functionality to replace
the Node.js bridge, using Playwright for browser automation.

Modules:
    utils: Filename sanitization, URL hashing, archive utilities
    extractor: Post list and detail extraction
    downloader: Concurrent media downloading with retry
    archiver: Main orchestration layer
"""

__all__ = ['utils', 'extractor', 'downloader', 'archiver']
__version__ = '1.0.0-phase2'
