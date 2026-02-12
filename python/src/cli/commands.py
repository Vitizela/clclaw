"""命令行接口（Phase 5 完善）

Phase 1: 简化版，仅提示用户使用菜单模式
Phase 5: 完整实现所有 CLI 命令
"""
import sys


class CLI:
    """命令行接口"""

    def __init__(self, config):
        self.config = config

    def run(self):
        """运行 CLI"""
        # Phase 1: 简单提示
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  命令行模式将在 Phase 5 完善")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        print("当前请使用菜单模式：")
        print("  python main.py")
        print()
        print("可用的简单命令（Phase 1）：")
        print("  python main.py           # 菜单模式")
        print()
        print("计划的命令（Phase 5）：")
        print("  python main.py follow <URL>")
        print("  python main.py update")
        print("  python main.py list")
        print("  python main.py stats")
        print("  python main.py analyze wordcloud")
        print()
