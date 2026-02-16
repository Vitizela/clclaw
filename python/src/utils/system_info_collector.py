#!/usr/bin/env python3
"""
系统信息收集器
功能：收集程序运行信息、系统信息和资源使用情况
"""

import platform
import socket
import sys
import psutil
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class ProgramInfo:
    """程序运行信息"""
    start_time: datetime
    uptime_seconds: int
    uptime_str: str
    scheduler_status: str
    active_tasks: int


@dataclass
class SystemInfo:
    """系统信息（静态）"""
    os_name: str
    os_version: str
    os_display: str
    python_version: str
    hostname: str
    ip_address: str


@dataclass
class ResourceInfo:
    """资源使用情况（动态）"""
    memory_percent: int
    disk_percent: Optional[int]


@dataclass
class StatusPanelData:
    """状态面板完整数据"""
    program_info: ProgramInfo
    system_info: SystemInfo
    resource_info: ResourceInfo
    # 业务信息
    authors_count: int
    forum_url: str
    archive_path: str


class SystemInfoCollector:
    """系统信息收集器"""

    # 程序启动时间（类变量，全局唯一）
    _start_time: Optional[datetime] = None

    # 系统信息缓存（静态信息只获取一次）
    _system_info_cache: Optional[SystemInfo] = None

    @classmethod
    def initialize(cls):
        """初始化收集器，记录程序启动时间"""
        if cls._start_time is None:
            cls._start_time = datetime.now()

    @classmethod
    def get_program_info(cls, scheduler=None) -> ProgramInfo:
        """
        获取程序运行信息

        Args:
            scheduler: 可选的调度器实例（TaskScheduler）

        Returns:
            ProgramInfo: 程序信息对象
        """
        # 确保已初始化
        if cls._start_time is None:
            cls.initialize()

        # 计算运行时长
        now = datetime.now()
        uptime_seconds = int((now - cls._start_time).total_seconds())
        uptime_str = cls._format_uptime(uptime_seconds)

        # 获取调度器状态
        scheduler_status = "🔴 未启用"
        active_tasks = 0

        if scheduler:
            try:
                scheduler_status = "🟢 运行中" if scheduler.is_running() else "🔴 已停止"
                if scheduler.is_running():
                    active_tasks = len(scheduler.get_all_tasks())
            except Exception:
                scheduler_status = "🔴 未知"

        return ProgramInfo(
            start_time=cls._start_time,
            uptime_seconds=uptime_seconds,
            uptime_str=uptime_str,
            scheduler_status=scheduler_status,
            active_tasks=active_tasks
        )

    @classmethod
    def get_system_info(cls) -> SystemInfo:
        """
        获取系统信息（使用缓存）

        Returns:
            SystemInfo: 系统信息对象
        """
        if cls._system_info_cache is not None:
            return cls._system_info_cache

        # 获取操作系统信息
        os_name = platform.system()
        os_version = ""
        os_display = ""

        try:
            if os_name == "Linux":
                import distro
                os_display = f"{distro.name()} {distro.version()}"
            elif os_name == "Darwin":
                mac_version = platform.mac_ver()[0]
                os_display = f"macOS {mac_version}"
            elif os_name == "Windows":
                win_version = platform.win32_ver()[0]
                os_display = f"Windows {win_version}"
            else:
                os_display = f"{os_name} {platform.release()}"
        except Exception:
            os_display = f"{os_name} {platform.release()}"

        # 获取 Python 版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # 获取主机名
        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = "未知"

        # 获取 IP 地址（优先局域网地址）
        ip_address = cls._get_local_ip()

        cls._system_info_cache = SystemInfo(
            os_name=os_name,
            os_version=os_version,
            os_display=os_display,
            python_version=python_version,
            hostname=hostname,
            ip_address=ip_address
        )

        return cls._system_info_cache

    @classmethod
    def get_resource_info(cls, archive_path: Optional[str] = None) -> ResourceInfo:
        """
        获取资源使用情况

        Args:
            archive_path: 归档路径（用于磁盘使用率检测）

        Returns:
            ResourceInfo: 资源信息对象
        """
        # 获取内存使用率
        try:
            memory = psutil.virtual_memory()
            memory_percent = int(memory.percent)
        except Exception:
            memory_percent = 0

        # 获取磁盘使用率（可选）
        disk_percent = None
        if archive_path:
            try:
                disk = psutil.disk_usage(archive_path)
                disk_percent = int(disk.percent)
            except Exception:
                pass

        return ResourceInfo(
            memory_percent=memory_percent,
            disk_percent=disk_percent
        )

    @staticmethod
    def _format_uptime(seconds: int) -> str:
        """
        格式化运行时长

        Args:
            seconds: 运行秒数

        Returns:
            str: 格式化字符串（例如：2h 15m）
        """
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"

    @staticmethod
    def _get_local_ip() -> str:
        """
        获取本机 IP 地址（优先局域网地址）

        Returns:
            str: IP 地址字符串
        """
        try:
            # 创建 UDP socket（不会实际发送数据）
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接到外部地址（Google DNS）
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "未知"

    @classmethod
    def reset(cls):
        """重置收集器状态（用于测试）"""
        cls._start_time = None
        cls._system_info_cache = None
