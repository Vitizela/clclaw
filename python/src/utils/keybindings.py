#!/usr/bin/env python3
"""questionary 包装器，确保 ESC 键正常工作

questionary 2.0.1 的 .ask() 方法可能不正确处理 ESC（EOFError），
这个模块提供包装函数，使用 .unsafe_ask() 并手动捕获 EOFError。
"""

from typing import List, Any, Optional
import questionary


def select_with_keybindings(message: str, choices: List[Any], **kwargs) -> Optional[Any]:
    """select 菜单包装器，确保 ESC 返回 None

    使用 unsafe_ask() 并捕获 EOFError，确保 ESC 键能正常返回 None。
    """
    try:
        return questionary.select(
            message,
            choices=choices,
            **kwargs
        ).unsafe_ask()
    except (EOFError, KeyboardInterrupt):
        # ESC 触发 EOFError，Ctrl+C 触发 KeyboardInterrupt
        return None


def checkbox_with_keybindings(message: str, choices: List[Any], **kwargs) -> Optional[Any]:
    """checkbox 菜单包装器，确保 ESC 返回 None

    使用 unsafe_ask() 并捕获 EOFError，确保 ESC 键能正常返回 None。
    """
    try:
        return questionary.checkbox(
            message,
            choices=choices,
            **kwargs
        ).unsafe_ask()
    except (EOFError, KeyboardInterrupt):
        return None


def text_with_keybindings(message: str, **kwargs) -> Optional[str]:
    """text 输入框包装器，确保 ESC 返回 None

    使用 unsafe_ask() 并捕获 EOFError，确保 ESC 键能正常返回 None。
    """
    try:
        return questionary.text(
            message,
            **kwargs
        ).unsafe_ask()
    except (EOFError, KeyboardInterrupt):
        return None
