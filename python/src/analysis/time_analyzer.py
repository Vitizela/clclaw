#!/usr/bin/env python3
"""
时间分析器 - 发帖时间趋势与活跃度分析

功能:
- 月度发帖趋势图
- 时间热力图（weekday x hour）
- 活跃度模式分析
- 相机使用排行图

设计模式: 遵循 ExifAnalyzer 模式（可选 db_connection）
"""

import logging
from typing import Optional, Dict, List
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

# 设置中文字体（matplotlib）
# 检测并配置中文字体
_chinese_font_path = None
try:
    from ..utils.font_config import FontConfig
    _chinese_font_path = FontConfig.get_chinese_font()
    if _chinese_font_path:
        import matplotlib.font_manager as fm
        # 先尝试安装 wqy-zenhei 字体（如果可用）
        wqy_font = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
        from pathlib import Path
        if Path(wqy_font).exists():
            _chinese_font_path = wqy_font

        # 添加字体到 matplotlib
        fm.fontManager.addfont(_chinese_font_path)
        font_prop = fm.FontProperties(fname=_chinese_font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
except Exception as e:
    logger.warning(f"中文字体配置失败: {e}")
    pass  # 使用默认字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号


class TimeAnalyzer:
    """时间分析器 - 发帖时间趋势与活跃度分析"""

    def __init__(self, db_connection=None):
        """
        初始化时间分析器

        Args:
            db_connection: 可选的数据库连接（遵循 ExifAnalyzer 模式）
        """
        self.db_connection = db_connection

    def get_monthly_trend(self, author_name: Optional[str] = None) -> pd.DataFrame:
        """
        获取月度发帖趋势数据

        Args:
            author_name: 作者名（None=全局统计）

        Returns:
            DataFrame with columns: year_month, post_count
        """
        if not self.db_connection:
            logger.error("数据库连接未提供")
            return pd.DataFrame()

        try:
            from ..database.query import get_monthly_stats

            stats = get_monthly_stats(author_name=author_name, db=self.db_connection)

            if not stats:
                logger.warning("无月度统计数据")
                return pd.DataFrame()

            # 转换为 DataFrame
            df = pd.DataFrame(stats)

            # 生成 year_month 列（YYYY-MM 格式）
            df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)

            return df[['year_month', 'post_count']]

        except Exception as e:
            logger.error(f"获取月度趋势数据失败: {e}")
            return pd.DataFrame()

    def plot_monthly_trend(
        self,
        author_name: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        绘制月度发帖趋势图（折线图）

        Args:
            author_name: 作者名（None=全局统计）
            output_path: 输出路径（默认 data/analysis/monthly_trend_{作者名}.png）

        Returns:
            输出文件路径，失败返回 None
        """
        try:
            # 获取数据
            df = self.get_monthly_trend(author_name)

            if df.empty:
                logger.warning("无数据，无法绘制月度趋势图")
                return None

            # 创建图表
            fig, ax = plt.subplots(figsize=(12, 6))

            # 绘制折线图
            ax.plot(df['year_month'], df['post_count'], marker='o', linewidth=2, markersize=6)

            # 设置标题和标签
            title = f"月度发帖趋势" + (f" - {author_name}" if author_name else " (全局)")
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel('月份', fontsize=12)
            ax.set_ylabel('帖子数', fontsize=12)

            # 网格
            ax.grid(True, alpha=0.3, linestyle='--')

            # X 轴标签旋转
            plt.xticks(rotation=45, ha='right')

            # 紧凑布局
            plt.tight_layout()

            # 保存图片
            if output_path is None:
                output_dir = Path(__file__).parent.parent.parent / 'data' / 'analysis'
                suffix = f"_{author_name}" if author_name else "_global"
                output_path = str(output_dir / f"monthly_trend{suffix}.png")

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"月度趋势图生成成功: {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"月度趋势图生成失败: {e}")
            return None

    def plot_time_heatmap(
        self,
        author_name: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        绘制时间热力图（weekday x hour）

        Args:
            author_name: 作者名（None=全局统计）
            output_path: 输出路径（默认 data/analysis/time_heatmap_{作者名}.png）

        Returns:
            输出文件路径，失败返回 None
        """
        if not self.db_connection:
            logger.error("数据库连接未提供")
            return None

        try:
            # 查询数据
            conn = self.db_connection.get_connection()

            if author_name:
                query = """
                    SELECT publish_weekday, publish_hour, COUNT(*) as count
                    FROM posts
                    JOIN authors ON posts.author_id = authors.id
                    WHERE authors.name = ? AND publish_hour IS NOT NULL
                    GROUP BY publish_weekday, publish_hour
                """
                cursor = conn.execute(query, (author_name,))
            else:
                query = """
                    SELECT publish_weekday, publish_hour, COUNT(*) as count
                    FROM posts
                    WHERE publish_hour IS NOT NULL
                    GROUP BY publish_weekday, publish_hour
                """
                cursor = conn.execute(query)

            rows = cursor.fetchall()

            if not rows:
                logger.warning("无时间数据，无法绘制热力图")
                return None

            # 构建 7x24 矩阵
            heatmap_data = np.zeros((7, 24))

            for row in rows:
                weekday = row['publish_weekday']
                hour = row['publish_hour']
                count = row['count']
                heatmap_data[weekday][hour] = count

            # 创建 DataFrame（用于 seaborn）
            df = pd.DataFrame(
                heatmap_data,
                index=['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
                columns=[f"{h:02d}" for h in range(24)]
            )

            # 创建图表
            fig, ax = plt.subplots(figsize=(14, 6))

            # 绘制热力图
            sns.heatmap(
                df,
                annot=False,
                fmt='g',
                cmap='YlOrRd',
                cbar_kws={'label': '帖子数'},
                linewidths=0.5,
                ax=ax
            )

            # 设置标题
            title = f"发帖时间热力图" + (f" - {author_name}" if author_name else " (全局)")
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel('小时', fontsize=12)
            ax.set_ylabel('星期', fontsize=12)

            # 紧凑布局
            plt.tight_layout()

            # 保存图片
            if output_path is None:
                output_dir = Path(__file__).parent.parent.parent / 'data' / 'analysis'
                suffix = f"_{author_name}" if author_name else "_global"
                output_path = str(output_dir / f"time_heatmap{suffix}.png")

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"时间热力图生成成功: {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"时间热力图生成失败: {e}")
            return None

    def analyze_active_patterns(
        self,
        author_name: Optional[str] = None
    ) -> Dict:
        """
        分析活跃度模式

        Args:
            author_name: 作者名（None=全局统计）

        Returns:
            活跃度指标字典:
            - most_active_hour: 最活跃小时 (0-23)
            - most_active_weekday: 最活跃星期 (0=周一, 6=周日)
            - weekend_ratio: 周末发帖占比 (0-1)
            - night_owl_index: 夜猫子指数 (22:00-6:00 占比, 0-1)
            - early_bird_index: 早起指数 (6:00-9:00 占比, 0-1)
            - workday_index: 工作日指数 (周一至周五 9:00-18:00 占比, 0-1)
        """
        if not self.db_connection:
            logger.error("数据库连接未提供")
            return {}

        try:
            conn = self.db_connection.get_connection()

            # 构建查询
            if author_name:
                base_query = """
                    FROM posts
                    JOIN authors ON posts.author_id = authors.id
                    WHERE authors.name = ? AND publish_hour IS NOT NULL
                """
                params = (author_name,)
            else:
                base_query = """
                    FROM posts
                    WHERE publish_hour IS NOT NULL
                """
                params = ()

            # 1. 最活跃小时
            query_hour = f"SELECT publish_hour, COUNT(*) as count {base_query} GROUP BY publish_hour ORDER BY count DESC LIMIT 1"
            cursor = conn.execute(query_hour, params)
            row = cursor.fetchone()
            most_active_hour = row['publish_hour'] if row else None

            # 2. 最活跃星期
            query_weekday = f"SELECT publish_weekday, COUNT(*) as count {base_query} GROUP BY publish_weekday ORDER BY count DESC LIMIT 1"
            cursor = conn.execute(query_weekday, params)
            row = cursor.fetchone()
            most_active_weekday = row['publish_weekday'] if row else None

            # 3. 总帖子数
            query_total = f"SELECT COUNT(*) as total {base_query}"
            cursor = conn.execute(query_total, params)
            total_posts = cursor.fetchone()['total']

            if total_posts == 0:
                logger.warning("无时间数据")
                return {}

            # 4. 周末占比（周六=5, 周日=6）
            query_weekend = f"SELECT COUNT(*) as count {base_query} AND publish_weekday IN (5, 6)"
            cursor = conn.execute(query_weekend, params)
            weekend_posts = cursor.fetchone()['count']
            weekend_ratio = weekend_posts / total_posts

            # 5. 夜猫子指数（22:00-6:00）
            query_night = f"SELECT COUNT(*) as count {base_query} AND (publish_hour >= 22 OR publish_hour < 6)"
            cursor = conn.execute(query_night, params)
            night_posts = cursor.fetchone()['count']
            night_owl_index = night_posts / total_posts

            # 6. 早起指数（6:00-9:00）
            query_early = f"SELECT COUNT(*) as count {base_query} AND publish_hour >= 6 AND publish_hour < 9"
            cursor = conn.execute(query_early, params)
            early_posts = cursor.fetchone()['count']
            early_bird_index = early_posts / total_posts

            # 7. 工作日指数（周一至周五 9:00-18:00）
            query_workday = f"SELECT COUNT(*) as count {base_query} AND publish_weekday < 5 AND publish_hour >= 9 AND publish_hour < 18"
            cursor = conn.execute(query_workday, params)
            workday_posts = cursor.fetchone()['count']
            workday_index = workday_posts / total_posts

            # 星期名称映射
            weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

            result = {
                'most_active_hour': most_active_hour,
                'most_active_weekday': most_active_weekday,
                'most_active_weekday_name': weekday_names[most_active_weekday] if most_active_weekday is not None else None,
                'weekend_ratio': round(weekend_ratio, 3),
                'night_owl_index': round(night_owl_index, 3),
                'early_bird_index': round(early_bird_index, 3),
                'workday_index': round(workday_index, 3),
                'total_posts': total_posts
            }

            logger.info(f"活跃度分析完成: {result}")
            return result

        except Exception as e:
            logger.error(f"活跃度分析失败: {e}")
            return {}

    def plot_camera_ranking(
        self,
        limit: int = 10,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        绘制相机使用排行图（横向柱状图）

        Args:
            limit: 显示前 N 个相机（默认 10）
            output_path: 输出路径（默认 data/analysis/camera_ranking.png）

        Returns:
            输出文件路径，失败返回 None
        """
        if not self.db_connection:
            logger.error("数据库连接未提供")
            return None

        try:
            from ..database.query import get_camera_ranking

            # 查询相机统计
            rankings = get_camera_ranking(limit=limit, db=self.db_connection)

            if not rankings:
                logger.warning("无相机数据")
                return None

            # 准备数据
            labels = [f"{r['make']} {r['model']}" for r in rankings]
            counts = [r['photo_count'] for r in rankings]

            # 获取中文字体
            from matplotlib.font_manager import FontProperties
            font_prop = None
            if _chinese_font_path:
                font_prop = FontProperties(fname=_chinese_font_path)

            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))

            # 横向柱状图
            y_pos = np.arange(len(labels))
            ax.barh(y_pos, counts, color='steelblue')

            # 添加数值标签
            for i, count in enumerate(counts):
                ax.text(count + max(counts) * 0.01, i, str(count), va='center', fontsize=10)

            # 设置标签
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels)
            ax.invert_yaxis()  # 降序排列

            # 设置标签（使用中文字体）
            if font_prop:
                ax.set_xlabel('照片数量', fontsize=12, fontproperties=font_prop)
                ax.set_title(f'相机使用排行 (Top {limit})', fontsize=16, fontweight='bold', fontproperties=font_prop)
            else:
                ax.set_xlabel('Photo Count', fontsize=12)
                ax.set_title(f'Camera Ranking (Top {limit})', fontsize=16, fontweight='bold')

            # 网格
            ax.grid(axis='x', alpha=0.3, linestyle='--')

            # 紧凑布局
            plt.tight_layout()

            # 保存图片
            if output_path is None:
                output_dir = Path(__file__).parent.parent.parent / 'data' / 'analysis'
                output_path = str(output_dir / "camera_ranking.png")

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"相机排行图生成成功: {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"相机排行图生成失败: {e}")
            return None


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.DEBUG)

    from ..database.connection import get_default_connection

    db = get_default_connection()
    analyzer = TimeAnalyzer(db)

    # 测试月度趋势
    df = analyzer.get_monthly_trend()
    print(f"月度趋势数据:\n{df}")

    # 测试活跃度分析
    patterns = analyzer.analyze_active_patterns()
    print(f"\n活跃度分析:\n{patterns}")
