"""统一日志系统

Provides consistent logging across all scraper modules with:
- File rotation (10MB max, 5 backups)
- Console and file output
- Configurable log levels
"""

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str,
    log_dir: Path,
    level: str = 'INFO',
    console: bool = True
) -> logging.Logger:
    """创建统一的日志记录器

    Args:
        name: Logger name (will be used as filename: {name}.log)
        log_dir: Directory for log files
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Whether to also output to console

    Returns:
        Configured logger instance

    Example:
        >>> log_dir = Path('./logs')
        >>> logger = setup_logger('scraper', log_dir)
        >>> logger.info('Starting scrape...')
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)

    # 文件 handler - 带日志轮转
    log_file = log_dir / f'{name}.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 控制台 handler - 简化格式
    if console:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取已存在的 logger

    Args:
        name: Logger name

    Returns:
        Existing logger instance
    """
    return logging.getLogger(name)
