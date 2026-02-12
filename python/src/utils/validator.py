"""输入验证工具

提供各种输入验证功能
"""
import re
from typing import Optional


def validate_url(url: str) -> bool:
    """验证 URL 格式

    Args:
        url: URL 字符串

    Returns:
        是否有效
    """
    if not url:
        return False

    # 简单的 URL 验证
    pattern = r'^https?://.+'
    return bool(re.match(pattern, url))


def validate_positive_int(value: str) -> bool:
    """验证正整数

    Args:
        value: 值字符串

    Returns:
        是否为正整数
    """
    try:
        return int(value) > 0
    except ValueError:
        return False


def validate_time_format(time_str: str) -> bool:
    """验证时间格式 HH:MM

    Args:
        time_str: 时间字符串

    Returns:
        是否为有效时间格式
    """
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))


def validate_non_empty(value: str) -> bool:
    """验证非空

    Args:
        value: 值字符串

    Returns:
        是否非空
    """
    return bool(value and value.strip())
