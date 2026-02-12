#!/usr/bin/env python3
"""自定义键绑定模块

提供统一的快捷键绑定，用于增强菜单交互体验。

支持的快捷键：
- q / Q: 返回上一级（用于选择菜单）
- Ctrl+B: 返回上一级（通用，适用于所有交互）
- ESC: 返回上一级（questionary 内置）
"""

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys


def create_menu_keybindings() -> KeyBindings:
    """创建菜单键绑定（适用于 select/checkbox 菜单）

    支持的快捷键：
    - ESC: 标准返回键（显式绑定）
    - q / Q: 快速返回（vim 风格）
    - Ctrl+B: 通用返回键

    注意：
    - ESC 被显式绑定以确保在所有终端环境中都能工作
    - 'q' 键会影响搜索功能（无法搜索包含 'q' 的选项）
    - 但在选择菜单中这个影响可以接受
    - 用户仍可通过"← 返回"选项或 Ctrl+B/ESC 返回

    Returns:
        KeyBindings: 键绑定对象
    """
    bindings = KeyBindings()

    @bindings.add(Keys.Escape)
    def _(event):
        """按 ESC 键返回（显式绑定）"""
        # 显式处理 ESC 键，确保在所有环境中都能工作
        event.app.exit(result=None)

    @bindings.add('q')
    @bindings.add('Q')
    def _(event):
        """按 q 或 Q 键返回"""
        # 退出当前交互，questionary.ask() 将返回 None
        event.app.exit(result=None)

    @bindings.add(Keys.ControlB)
    def _(event):
        """按 Ctrl+B 返回"""
        event.app.exit(result=None)

    return bindings


def create_input_keybindings() -> KeyBindings:
    """创建输入框键绑定（适用于 text/password 输入）

    支持的快捷键：
    - ESC: 标准取消键（显式绑定）
    - Ctrl+B: 取消输入并返回

    注意：
    - ESC 被显式绑定以确保在所有终端环境中都能工作
    - 不拦截 'q' 键，允许在输入框中正常输入 'q' 字符
    - 例如：输入 URL 时可能需要 'q' 字符（query 参数等）

    Returns:
        KeyBindings: 键绑定对象
    """
    bindings = KeyBindings()

    @bindings.add(Keys.Escape)
    def _(event):
        """按 ESC 键取消输入（显式绑定）"""
        # 显式处理 ESC 键，确保在所有环境中都能工作
        event.app.exit(result=None)

    @bindings.add(Keys.ControlB)
    def _(event):
        """按 Ctrl+B 取消输入"""
        event.app.exit(result=None)

    return bindings


# 创建全局实例（避免重复创建）
MENU_KEYBINDINGS = create_menu_keybindings()
INPUT_KEYBINDINGS = create_input_keybindings()
