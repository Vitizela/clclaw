#!/bin/bash
# Phase 5 依赖安装脚本

echo "检测 Python 版本..."
python3 --version

echo ""
echo "安装 Phase 5 依赖..."
python3 -m pip install apscheduler==3.10.4 paho-mqtt==1.6.1

echo ""
echo "验证安装..."
python3 -c "import apscheduler; print('✅ apscheduler:', apscheduler.__version__)" || echo "❌ apscheduler 安装失败"
python3 -c "import paho.mqtt.client; print('✅ paho-mqtt 已安装')" || echo "❌ paho-mqtt 安装失败"

echo ""
echo "完成！现在可以使用定时任务功能了。"
