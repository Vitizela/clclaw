#!/usr/bin/env python3
"""诊断导入问题"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("Python 环境诊断")
print("=" * 60)

# 1. Python 版本和路径
print(f"\nPython 版本: {sys.version}")
print(f"Python 可执行文件: {sys.executable}")

# 2. sys.path
print("\nsys.path:")
for i, path in enumerate(sys.path):
    print(f"  {i}. {path}")

# 3. 测试导入 apscheduler
print("\n" + "=" * 60)
print("测试导入 apscheduler")
print("=" * 60)

try:
    import apscheduler
    print(f"✅ apscheduler 导入成功")
    print(f"   版本: {apscheduler.__version__}")
    print(f"   路径: {apscheduler.__file__}")
except ImportError as e:
    print(f"❌ apscheduler 导入失败: {e}")
    print("\n解决方案:")
    print(f"  {sys.executable} -m pip install apscheduler==3.10.4")

# 4. 测试导入 paho-mqtt
print("\n" + "=" * 60)
print("测试导入 paho-mqtt")
print("=" * 60)

try:
    import paho.mqtt.client as mqtt
    print(f"✅ paho-mqtt 导入成功")
    print(f"   版本: {mqtt.__version__ if hasattr(mqtt, '__version__') else '未知'}")
except ImportError as e:
    print(f"❌ paho-mqtt 导入失败: {e}")
    print("\n解决方案:")
    print(f"  {sys.executable} -m pip install paho-mqtt==1.6.1")

# 5. 模拟 main.py 的导入
print("\n" + "=" * 60)
print("模拟 main.py 的导入过程")
print("=" * 60)

# 添加 src 到路径（模拟 main.py 的行为）
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print(f"\n添加到 sys.path: {Path(__file__).parent / 'src'}")

# 尝试导入 scheduler_menu
try:
    print("\n尝试导入: from menu.scheduler_menu import SchedulerMenu")
    from menu.scheduler_menu import SchedulerMenu
    print("✅ SchedulerMenu 导入成功")

    # 尝试创建实例
    print("\n尝试创建 SchedulerMenu 实例...")
    from config.manager import ConfigManager
    config_manager = ConfigManager()
    config = config_manager.load()

    menu = SchedulerMenu(config)
    print("✅ SchedulerMenu 实例创建成功")
    print(f"   调度器: {menu.scheduler}")
    print(f"   归档器: {menu.archiver}")

except Exception as e:
    print(f"❌ 导入/创建失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
