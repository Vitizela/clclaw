#!/usr/bin/env python3
"""
Phase 2 依赖检查脚本

检查所有 Phase 2 需要的依赖是否正确安装
"""
import sys
import subprocess
from pathlib import Path


def check_python_dependencies():
    """检查 Python 包依赖"""
    print("=" * 50)
    print("检查 Python 依赖...")
    print("=" * 50)

    # Phase 1 依赖
    phase1_deps = {
        'PyYAML': 'import yaml',
        'questionary': 'import questionary',
        'rich': 'from rich.console import Console',
        'click': 'import click',
        'python-dateutil': 'from dateutil import parser',
    }

    # Phase 2 新增依赖
    phase2_deps = {
        'playwright': 'from playwright.async_api import async_playwright',
        'aiohttp': 'import aiohttp',
        'beautifulsoup4': 'from bs4 import BeautifulSoup',
        'tqdm': 'from tqdm import tqdm',
        'requests': 'import requests',
    }

    all_deps = {**phase1_deps, **phase2_deps}
    failed = []

    for name, import_cmd in all_deps.items():
        try:
            exec(import_cmd)
            marker = '✓' if name in phase2_deps else '○'
            phase = 'Phase 2' if name in phase2_deps else 'Phase 1'
            print(f"{marker} {name:<20} ({phase})")
        except ImportError:
            print(f"✗ {name:<20} - 未安装")
            failed.append(name)

    return failed


def check_playwright_browsers():
    """检查 Playwright 浏览器是否已安装"""
    print("\n" + "=" * 50)
    print("检查 Playwright 浏览器...")
    print("=" * 50)

    try:
        # 运行 playwright install --dry-run
        result = subprocess.run(
            ['playwright', 'install', '--dry-run', 'chromium'],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout.lower() + result.stderr.lower()

        # 检查输出中是否包含 "already installed" 或类似信息
        if 'already installed' in output or 'up to date' in output:
            print("✓ Chromium 浏览器已安装")
            return True
        else:
            print("✗ Chromium 浏览器未安装")
            print("  运行: playwright install chromium")
            return False

    except FileNotFoundError:
        print("✗ playwright 命令未找到")
        print("  请确保已安装 playwright: pip install playwright")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  检查超时，请手动验证")
        return False
    except Exception as e:
        print(f"✗ 检查失败: {str(e)}")
        return False


def check_optional_tools():
    """检查可选工具"""
    print("\n" + "=" * 50)
    print("检查可选工具...")
    print("=" * 50)

    tools = {
        'git': ['git', '--version'],
        'node': ['node', '--version'],
    }

    for name, cmd in tools.items():
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"○ {name:<10} - {version}")
            else:
                print(f"✗ {name:<10} - 未安装")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(f"✗ {name:<10} - 未安装")


def main():
    """主函数"""
    print("\nPhase 2 依赖检查")
    print("=" * 50)
    print(f"Python 版本: {sys.version.split()[0]}")
    print(f"工作目录: {Path.cwd()}")
    print("")

    # 检查 Python 依赖
    failed_deps = check_python_dependencies()

    # 检查 Playwright 浏览器
    browser_ok = check_playwright_browsers()

    # 检查可选工具
    check_optional_tools()

    # 总结
    print("\n" + "=" * 50)
    print("检查结果总结")
    print("=" * 50)

    if failed_deps:
        print(f"✗ 缺少 {len(failed_deps)} 个 Python 包:")
        for dep in failed_deps:
            print(f"  - {dep}")
        print("\n安装命令:")
        print("  pip install -r requirements.txt")
        return False

    if not browser_ok:
        print("✗ Playwright 浏览器未就绪")
        print("\n安装命令:")
        print("  playwright install chromium")
        return False

    print("✅ 所有依赖已就绪")
    print("\n下一步:")
    print("  - 查看 Phase 2 实施指南: MIGRATION_GUIDE.md")
    print("  - 查看 Phase 2 测试指南: PHASE2_TESTING.md")
    print("  - 查看 Playwright API 映射: PHASE2_API_MAPPING.md")
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
