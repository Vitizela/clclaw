#!/usr/bin/env python3
"""
论坛作者订阅归档系统 - 主入口

支持菜单模式和命令行模式

使用方法:
    python main.py           # 菜单模式（推荐）
    python main.py <command> # 命令行模式（Phase 5）
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config.manager import ConfigManager
from src.config.wizard import ConfigWizard
from src.menu.main_menu import MainMenu
from src.cli.commands import CLI


def main():
    """主入口"""
    try:
        # 检查配置文件
        config_manager = ConfigManager()

        if not config_manager.config_exists():
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("  检测到首次运行，启动配置向导...")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print()
            wizard = ConfigWizard()
            wizard.run()
            print()
            print("配置完成！即将进入主菜单...")
            input("按 Enter 继续...")

        # 加载配置
        config = config_manager.load()

        # 判断模式
        if len(sys.argv) > 1:
            # 命令行模式
            cli = CLI(config)
            cli.run()
        else:
            # 菜单模式
            menu = MainMenu(config)
            menu.run()

    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
