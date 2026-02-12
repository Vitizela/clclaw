"""Node.js 脚本桥接器（Phase 2 前的临时方案）

此模块将在 Phase 2 完成后删除
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class NodeJSBridge:
    """桥接器：调用现有 Node.js 脚本

    Phase 1 临时使用，Phase 2 完成后删除
    """

    def __init__(self, nodejs_dir: str = "../"):
        """初始化桥接器

        Args:
            nodejs_dir: Node.js 脚本目录（相对于 python/ 目录）
        """
        # 计算 Node.js 目录的绝对路径
        # __file__ 是 .../python/src/bridge/nodejs_bridge.py
        # .parent.parent.parent 到达 python/ 目录
        # 然后加上 nodejs_dir (默认 "../") 到达项目根目录
        self.nodejs_dir = (Path(__file__).parent.parent.parent / nodejs_dir).resolve()

        if not self.nodejs_dir.exists():
            raise FileNotFoundError(
                f"Node.js 目录不存在: {self.nodejs_dir}\n"
                f"请确保 Node.js 脚本在正确位置"
            )

        print(f"[桥接] Node.js 目录: {self.nodejs_dir}")

    def follow_author(self, post_url: str) -> Tuple[str, str, int]:
        """调用 follow_author.js

        Args:
            post_url: 帖子 URL

        Returns:
            (stdout, stderr, returncode)
        """
        return self._run_script("follow_author.js", [post_url])

    def archive_posts(self, authors: List[str]) -> Tuple[str, str, int]:
        """调用 archive_posts.js

        Args:
            authors: 作者名列表

        Returns:
            (stdout, stderr, returncode)
        """
        # 为每个作者名加引号（防止空格问题）
        quoted_authors = [f'"{author}"' for author in authors]
        return self._run_script("archive_posts.js", quoted_authors)

    def run_update(self) -> Tuple[str, str, int]:
        """调用 run_scheduled_update.js

        Returns:
            (stdout, stderr, returncode)
        """
        return self._run_script("run_scheduled_update.js", [])

    def discover_authors(self, forum_url: str) -> Tuple[str, str, int]:
        """调用 discover_authors_v2.js

        Args:
            forum_url: 论坛版块 URL

        Returns:
            (stdout, stderr, returncode)
        """
        return self._run_script("discover_authors_v2.js", [forum_url])

    def _run_script(self, script_name: str, args: List[str]) -> Tuple[str, str, int]:
        """执行 Node.js 脚本

        Args:
            script_name: 脚本文件名
            args: 命令行参数

        Returns:
            (stdout, stderr, returncode)
        """
        script_path = self.nodejs_dir / script_name

        if not script_path.exists():
            raise FileNotFoundError(f"脚本不存在: {script_path}")

        # 构建命令
        cmd = ["node", str(script_path)] + args

        print(f"[桥接] 执行: {' '.join(cmd)}")

        # 执行命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=str(self.nodejs_dir)  # 设置工作目录
        )

        # 实时显示输出
        stdout_lines = []
        stderr_lines = []

        # 读取 stdout
        if process.stdout:
            for line in process.stdout:
                print(line, end='')
                stdout_lines.append(line)

        # 读取 stderr
        if process.stderr:
            for line in process.stderr:
                print(line, end='', file=sys.stderr)
                stderr_lines.append(line)

        # 等待完成
        returncode = process.wait()

        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)

        if returncode != 0:
            print(f"[桥接] 脚本执行失败，返回码: {returncode}")
        else:
            print(f"[桥接] 脚本执行成功")

        return stdout, stderr, returncode
