"""
数据库连接管理模块

提供单例模式的数据库连接管理，负责：
- 创建和管理 SQLite 数据库连接
- 初始化数据库结构（执行 schema.sql）
- 配置 SQLite 优化参数
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional


class DatabaseConnection:
    """
    数据库连接管理类（单例模式）

    使用示例:
        db = DatabaseConnection.get_instance()
        db.initialize_database()
        conn = db.get_connection()
    """

    _instance: Optional['DatabaseConnection'] = None
    _connection: Optional[sqlite3.Connection] = None
    _db_path: Optional[str] = None

    def __new__(cls, db_path: Optional[str] = None):
        """
        单例模式：确保全局只有一个实例

        Args:
            db_path: 数据库文件路径（首次调用时必须提供）
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库连接管理器

        Args:
            db_path: 数据库文件路径
        """
        # 如果已经初始化过，且没有提供新路径，则跳过
        if self._db_path is not None and db_path is None:
            return

        # 如果提供了新路径，更新路径
        if db_path is not None:
            self._db_path = db_path

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> 'DatabaseConnection':
        """
        获取单例实例

        Args:
            db_path: 数据库文件路径（首次调用时必须提供）

        Returns:
            DatabaseConnection 实例
        """
        if cls._instance is None:
            if db_path is None:
                raise ValueError("首次调用必须提供 db_path 参数")
            cls._instance = cls(db_path)
        elif db_path is not None and db_path != cls._db_path:
            # 如果提供了不同的路径，关闭旧连接并更新路径
            cls._instance.close()
            cls._instance._db_path = db_path
            cls._instance._connection = None
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接（懒加载）

        Returns:
            sqlite3.Connection 对象
        """
        if self._connection is None:
            if self._db_path is None:
                raise ValueError("数据库路径未设置")

            # 确保数据库目录存在
            db_dir = os.path.dirname(self._db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            # 创建连接
            self._connection = sqlite3.connect(self._db_path)

            # 配置连接
            self._configure_connection()

        return self._connection

    def _configure_connection(self):
        """
        配置数据库连接参数

        配置项：
        - Row factory: 使查询结果可以通过列名访问
        - Foreign keys: 启用外键约束
        - WAL mode: 写入优化（已在 schema.sql 中配置）
        """
        if self._connection is None:
            return

        # 设置 row_factory，使查询结果可以通过列名访问
        self._connection.row_factory = sqlite3.Row

        # 启用外键约束
        self._connection.execute("PRAGMA foreign_keys = ON")

    def initialize_database(self) -> bool:
        """
        初始化数据库结构

        执行 schema.sql 文件，创建表、索引、视图、触发器

        Returns:
            bool: 初始化是否成功
        """
        try:
            conn = self.get_connection()

            # 获取 schema.sql 文件路径
            current_dir = Path(__file__).parent
            schema_file = current_dir / 'schema.sql'

            if not schema_file.exists():
                raise FileNotFoundError(f"Schema 文件不存在: {schema_file}")

            # 读取并执行 schema.sql
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            conn.executescript(schema_sql)
            conn.commit()

            return True

        except Exception as e:
            print(f"数据库初始化失败: {e}")
            return False

    def is_initialized(self) -> bool:
        """
        检查数据库是否已初始化

        通过检查核心表是否存在来判断

        Returns:
            bool: 数据库是否已初始化
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='authors'"
            )
            result = cursor.fetchone()
            return result is not None
        except Exception:
            return False

    def close(self):
        """
        关闭数据库连接
        """
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception as e:
                print(f"关闭数据库连接失败: {e}")
            finally:
                self._connection = None

    def get_db_path(self) -> Optional[str]:
        """
        获取当前数据库文件路径

        Returns:
            str: 数据库文件路径
        """
        return self._db_path

    def get_db_info(self) -> dict:
        """
        获取数据库基本信息

        Returns:
            dict: 包含数据库信息的字典
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute("PRAGMA database_list")
            db_info = cursor.fetchone()

            # 获取表数量
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            )
            table_count = cursor.fetchone()[0]

            # 获取索引数量
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
            )
            index_count = cursor.fetchone()[0]

            # 获取视图数量
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='view'"
            )
            view_count = cursor.fetchone()[0]

            # 获取触发器数量
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'"
            )
            trigger_count = cursor.fetchone()[0]

            # 获取数据库文件大小
            db_size = 0
            if self._db_path and os.path.exists(self._db_path):
                db_size = os.path.getsize(self._db_path)

            return {
                'path': self._db_path,
                'initialized': self.is_initialized(),
                'table_count': table_count,
                'index_count': index_count,
                'view_count': view_count,
                'trigger_count': trigger_count,
                'file_size_bytes': db_size,
                'file_size_mb': round(db_size / (1024 * 1024), 2)
            }
        except Exception as e:
            return {
                'path': self._db_path,
                'error': str(e)
            }

    def __del__(self):
        """
        析构函数：确保连接被关闭
        """
        self.close()

    def __repr__(self):
        """
        返回对象的字符串表示
        """
        status = "connected" if self._connection else "not connected"
        return f"<DatabaseConnection(path={self._db_path}, status={status})>"


# 便捷函数：获取默认数据库连接
def get_default_connection() -> DatabaseConnection:
    """
    获取默认数据库连接

    使用项目默认的数据库路径: python/data/forum_data.db

    Returns:
        DatabaseConnection 实例
    """
    # 获取项目根目录
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    default_db_path = project_root / 'data' / 'forum_data.db'

    return DatabaseConnection.get_instance(str(default_db_path))
