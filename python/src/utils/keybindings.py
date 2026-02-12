#!/usr/bin/env python3
"""自定义键绑定模块

提供统一的快捷键绑定，用于增强菜单交互体验。

支持的快捷键：
- q / Q: 返回上一级（用于选择菜单）
- Ctrl+B: 返回上一级（通用，适用于所有交互）
- ESC: 返回上一级（questionary 内置）
"""

from typing import List, Any, Optional
import questionary
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys


def create_custom_keybindings(include_q: bool = True) -> KeyBindings:
    """创建自定义键绑定

    Args:
        include_q: 是否包含 'q' 键绑定（选择菜单为 True，输入框为 False）

    Returns:
        KeyBindings: 键绑定对象
    """
    bindings = KeyBindings()

    @bindings.add(Keys.Escape)
    def _(event):
        """按 ESC 键返回"""
        event.app.exit(result=None)

    @bindings.add(Keys.ControlB)
    def _(event):
        """按 Ctrl+B 返回"""
        event.app.exit(result=None)

    if include_q:
        @bindings.add('q')
        @bindings.add('Q')
        def _(event):
            """按 q 或 Q 键返回"""
            event.app.exit(result=None)

    return bindings


def select_with_keybindings(message: str, choices: List[Any], **kwargs) -> Any:
    """带自定义键绑定的 select 菜单

    支持 ESC、q、Ctrl+B 返回
    """
    # 获取或创建 key_bindings
    custom_kb = create_custom_keybindings(include_q=True)

    # 如果 kwargs 中已有 key_bindings，需要合并
    if 'key_bindings' in kwargs:
        # 移除以避免冲突
        kwargs.pop('key_bindings')

    # 使用 kb 参数而不是 key_bindings（questionary 的正确参数名）
    try:
        return questionary.select(
            message,
            choices=choices,
            kb=custom_kb,  # 尝试使用 kb 参数
            **kwargs
        ).ask()
    except TypeError:
        # 如果 kb 也不支持，尝试不带键绑定
        # 但手动捕获 EOFError
        try:
            return questionary.select(
                message,
                choices=choices,
                **kwargs
            ).unsafe_ask()
        except (EOFError, KeyboardInterrupt):
            return None


def checkbox_with_keybindings(message: str, choices: List[Any], **kwargs) -> Any:
    """带自定义键绑定的 checkbox 菜单

    支持 ESC、q、Ctrl+B 返回
    """
    custom_kb = create_custom_keybindings(include_q=True)

    if 'key_bindings' in kwargs:
        kwargs.pop('key_bindings')

    try:
        return questionary.checkbox(
            message,
            choices=choices,
            kb=custom_kb,
            **kwargs
        ).ask()
    except TypeError:
        try:
            return questionary.checkbox(
                message,
                choices=choices,
                **kwargs
            ).unsafe_ask()
        except (EOFError, KeyboardInterrupt):
            return None


def text_with_keybindings(message: str, **kwargs) -> Any:
    """带自定义键绑定的 text 输入框

    支持 ESC、Ctrl+B 返回（不包含 q，允许正常输入）
    """
    custom_kb = create_custom_keybindings(include_q=False)

    if 'key_bindings' in kwargs:
        kwargs.pop('key_bindings')

    try:
        return questionary.text(
            message,
            kb=custom_kb,
            **kwargs
        ).ask()
    except TypeError:
        try:
            return questionary.text(
                message,
                **kwargs
            ).unsafe_ask()
        except (EOFError, KeyboardInterrupt):
            return None


# 为了向后兼容，保留这些常量（但不再使用）
MENU_KEYBINDINGS = create_custom_keybindings(include_q=True)
INPUT_KEYBINDINGS = create_custom_keybindings(include_q=False)
