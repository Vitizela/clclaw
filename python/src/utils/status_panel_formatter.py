#!/usr/bin/env python3
"""
状态面板格式化器
功能：将系统信息格式化为 Rich Panel 显示
"""

from rich.panel import Panel
from rich.text import Text
from .system_info_collector import StatusPanelData


class StatusPanelFormatter:
    """状态面板格式化器"""

    @staticmethod
    def format_panel(data: StatusPanelData) -> Panel:
        """
        格式化状态面板

        Args:
            data: StatusPanelData 对象

        Returns:
            Panel: Rich Panel 对象
        """
        # 构建面板内容
        lines = []

        # 第一行：关注作者 + 归档路径
        line1 = (
            f"关注作者: {data.authors_count} 位  │  "
            f"归档路径: {data.archive_path}"
        )
        lines.append(line1)

        # 第二行：论坛版块 URL
        line2 = f"论坛版块: {data.forum_url}"
        lines.append(line2)

        # 第三行：动态信息（运行时长、启动时间、调度器、内存）
        start_time_str = data.program_info.start_time.strftime("%m-%d %H:%M")

        # 调度器状态显示
        if data.program_info.active_tasks > 0:
            scheduler_display = f"{data.program_info.scheduler_status} {data.program_info.active_tasks}任务"
        else:
            scheduler_display = data.program_info.scheduler_status

        line3_parts = [
            f"⏱️ 运行: {data.program_info.uptime_str}",
            f"🕐 启动: {start_time_str}",
            f"⚙️ 调度器: {scheduler_display}",
            f"💾 内存: {data.resource_info.memory_percent}%"
        ]

        line3 = "  │  ".join(line3_parts)
        lines.append(line3)

        # 第四行：静态系统信息（OS + Python + IP）
        line4_parts = [
            f"💻 {data.system_info.os_display}",
            f"🐍 Python {data.system_info.python_version}",
            f"📡 {data.system_info.ip_address}"
        ]

        line4 = "  │  ".join(line4_parts)
        lines.append(line4)

        # 合并所有行
        content = "\n".join(lines)

        # 创建 Panel
        panel = Panel(
            content,
            title="📊 论坛作者订阅归档系统",
            border_style="blue",
            expand=False
        )

        return panel

    @staticmethod
    def format_compact(data: StatusPanelData) -> str:
        """
        格式化为紧凑文本（用于日志）

        Args:
            data: StatusPanelData 对象

        Returns:
            str: 紧凑格式的文本
        """
        return (
            f"[运行: {data.program_info.uptime_str}] "
            f"[调度器: {data.program_info.scheduler_status}] "
            f"[内存: {data.resource_info.memory_percent}%] "
            f"[作者: {data.authors_count}] "
            f"[系统: {data.system_info.os_display}]"
        )
