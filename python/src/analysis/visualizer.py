#!/usr/bin/env python3
"""
可视化器 - 统一的可视化接口

功能:
- 提供统一的图表生成接口
- 整合 TextAnalyzer 和 TimeAnalyzer
- 批量生成图表
- 一致的样式和错误处理

设计模式: Facade 模式（简化复杂子系统的接口）
"""

import logging
from typing import Optional, Dict, List
from pathlib import Path

from .text_analyzer import TextAnalyzer
from .time_analyzer import TimeAnalyzer

logger = logging.getLogger(__name__)


class Visualizer:
    """可视化器 - 统一的可视化接口"""

    def __init__(self, db_connection=None, output_dir: Optional[str] = None):
        """
        初始化可视化器

        Args:
            db_connection: 数据库连接（可选）
            output_dir: 输出目录（默认 data/analysis）
        """
        self.db_connection = db_connection
        self.text_analyzer = TextAnalyzer(db_connection=db_connection)
        self.time_analyzer = TimeAnalyzer(db_connection=db_connection)

        # 设置输出目录
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent.parent / 'data' / 'analysis'
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_wordcloud(
        self,
        author_name: str,
        output_path: Optional[str] = None,
        include_title_only: bool = True
    ) -> Optional[str]:
        """
        生成词云图

        Args:
            author_name: 作者名
            output_path: 输出路径（可选）
            include_title_only: 是否仅使用标题（默认 True）

        Returns:
            输出文件路径，失败返回 None
        """
        if output_path is None:
            output_path = str(self.output_dir / f"wordcloud_{author_name}.png")

        return self.text_analyzer.generate_author_wordcloud(
            author_name=author_name,
            output_path=output_path,
            include_title_only=include_title_only
        )

    def generate_monthly_trend(
        self,
        author_name: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        生成月度趋势图

        Args:
            author_name: 作者名（None=全局）
            output_path: 输出路径（可选）

        Returns:
            输出文件路径，失败返回 None
        """
        if output_path is None:
            suffix = f"_{author_name}" if author_name else "_global"
            output_path = str(self.output_dir / f"monthly_trend{suffix}.png")

        return self.time_analyzer.plot_monthly_trend(
            author_name=author_name,
            output_path=output_path
        )

    def generate_time_heatmap(
        self,
        author_name: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        生成时间热力图

        Args:
            author_name: 作者名（None=全局）
            output_path: 输出路径（可选）

        Returns:
            输出文件路径，失败返回 None
        """
        if output_path is None:
            suffix = f"_{author_name}" if author_name else "_global"
            output_path = str(self.output_dir / f"time_heatmap{suffix}.png")

        return self.time_analyzer.plot_time_heatmap(
            author_name=author_name,
            output_path=output_path
        )

    def generate_camera_ranking(
        self,
        limit: int = 10,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        生成相机排行图

        Args:
            limit: 显示前 N 个相机（默认 10）
            output_path: 输出路径（可选）

        Returns:
            输出文件路径，失败返回 None
        """
        if output_path is None:
            output_path = str(self.output_dir / "camera_ranking.png")

        return self.time_analyzer.plot_camera_ranking(
            limit=limit,
            output_path=output_path
        )

    def analyze_activity_patterns(
        self,
        author_name: Optional[str] = None
    ) -> Dict:
        """
        分析活跃度模式

        Args:
            author_name: 作者名（None=全局）

        Returns:
            活跃度指标字典
        """
        return self.time_analyzer.analyze_active_patterns(author_name=author_name)

    def generate_all_charts(
        self,
        author_name: Optional[str] = None,
        include_wordcloud: bool = True,
        include_camera: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        批量生成所有图表

        Args:
            author_name: 作者名（None=全局）
            include_wordcloud: 是否包含词云（仅作者模式有效）
            include_camera: 是否包含相机排行（仅全局模式有效）

        Returns:
            字典 {图表名: 文件路径}
        """
        results = {}

        logger.info(f"开始生成图表（作者: {author_name or '全局'}）")

        # 1. 词云（仅作者模式）
        if author_name and include_wordcloud:
            logger.info("生成词云...")
            results['wordcloud'] = self.generate_wordcloud(author_name)

        # 2. 月度趋势图
        logger.info("生成月度趋势图...")
        results['monthly_trend'] = self.generate_monthly_trend(author_name)

        # 3. 时间热力图
        logger.info("生成时间热力图...")
        results['time_heatmap'] = self.generate_time_heatmap(author_name)

        # 4. 相机排行（仅全局模式）
        if not author_name and include_camera:
            logger.info("生成相机排行图...")
            results['camera_ranking'] = self.generate_camera_ranking()

        # 5. 活跃度分析
        logger.info("分析活跃度模式...")
        results['activity_patterns'] = self.analyze_activity_patterns(author_name)

        # 统计成功数
        chart_count = sum(1 for k, v in results.items() if k != 'activity_patterns' and v is not None)
        logger.info(f"图表生成完成: {chart_count} 个图表")

        return results

    def get_chart_summary(self, results: Dict[str, Optional[str]]) -> List[Dict]:
        """
        获取图表摘要信息

        Args:
            results: generate_all_charts() 返回的结果

        Returns:
            图表摘要列表 [{'name': '...', 'path': '...', 'size_kb': ...}, ...]
        """
        summary = []

        chart_names = {
            'wordcloud': '词云',
            'monthly_trend': '月度趋势图',
            'time_heatmap': '时间热力图',
            'camera_ranking': '相机排行图'
        }

        for key, path in results.items():
            if key == 'activity_patterns':
                continue  # 跳过活跃度分析（不是图表）

            if path and Path(path).exists():
                size_kb = Path(path).stat().st_size / 1024
                summary.append({
                    'name': chart_names.get(key, key),
                    'path': path,
                    'size_kb': size_kb
                })

        return summary


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    from ..database.connection import get_default_connection

    db = get_default_connection()
    visualizer = Visualizer(db_connection=db)

    # 测试批量生成（全局）
    print("\n=== 测试全局图表生成 ===")
    results = visualizer.generate_all_charts()
    summary = visualizer.get_chart_summary(results)

    print(f"\n生成了 {len(summary)} 个图表:")
    for chart in summary:
        print(f"  - {chart['name']}: {chart['size_kb']:.1f} KB")
