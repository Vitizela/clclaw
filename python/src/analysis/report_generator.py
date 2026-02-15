#!/usr/bin/env python3
"""
报告生成器 - HTML 数据分析报告生成

功能:
- 生成包含所有图表的 HTML 报告
- 图表使用 base64 编码嵌入（单文件，便于分享）
- 响应式设计，支持打印
- 自动收集统计数据

设计模式: Builder 模式（逐步构建复杂对象）
"""

import logging
import base64
from typing import Optional, Dict
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from .visualizer import Visualizer

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器 - HTML 数据分析报告"""

    def __init__(self, db_connection=None, output_dir: Optional[str] = None):
        """
        初始化报告生成器

        Args:
            db_connection: 数据库连接（可选）
            output_dir: 输出目录（默认 data/reports）
        """
        self.db_connection = db_connection
        self.visualizer = Visualizer(db_connection=db_connection)

        # 设置输出目录
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent.parent / 'data' / 'reports'
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置 Jinja2 模板环境
        template_dir = Path(__file__).parent.parent / 'templates'
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    def _encode_image_base64(self, image_path: str) -> Optional[str]:
        """
        将图片编码为 base64

        Args:
            image_path: 图片文件路径

        Returns:
            base64 编码字符串，失败返回 None
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            logger.error(f"图片编码失败 ({image_path}): {e}")
            return None

    def _collect_basic_info(self, author_name: Optional[str] = None) -> Dict:
        """
        收集基本信息

        Args:
            author_name: 作者名（None=全局）

        Returns:
            基本信息字典
        """
        info = {}

        if author_name:
            # 作者统计
            from ..database.models import Author, Post
            Author._db = self.db_connection
            Post._db = self.db_connection

            author = Author.get_by_name(author_name)
            if author:
                posts = Post.get_by_author(author.id)
                info['作者名'] = author.name
                info['归档帖子数'] = len(posts)
                info['论坛总帖子数'] = author.forum_total_posts or '未知'
                info['添加日期'] = author.added_date
                info['最后更新'] = author.last_update
        else:
            # 全局统计
            from ..database.query import get_global_stats
            stats = get_global_stats(db=self.db_connection)
            if stats:
                info['总作者数'] = stats.get('total_authors', 0)
                info['总帖子数'] = stats.get('total_posts', 0)
                info['总图片数'] = stats.get('total_images', 0)
                info['总视频数'] = stats.get('total_videos', 0)
                info['数据库大小'] = f"{stats.get('db_size_mb', 0):.1f} MB"

        return info

    def generate_report(
        self,
        author_name: Optional[str] = None,
        output_filename: Optional[str] = None,
        include_wordcloud: bool = True,
        include_camera: bool = True
    ) -> Optional[str]:
        """
        生成完整的分析报告

        Args:
            author_name: 作者名（None=全局）
            output_filename: 输出文件名（可选）
            include_wordcloud: 是否包含词云（仅作者模式有效）
            include_camera: 是否包含相机排行（仅全局模式有效）

        Returns:
            输出文件路径，失败返回 None
        """
        try:
            logger.info(f"开始生成报告（作者: {author_name or '全局'}）")

            # 1. 生成所有图表
            chart_results = self.visualizer.generate_all_charts(
                author_name=author_name,
                include_wordcloud=include_wordcloud,
                include_camera=include_camera
            )

            # 2. 编码图表为 base64
            charts_base64 = {}
            for chart_name, chart_path in chart_results.items():
                if chart_name == 'activity_patterns':
                    continue  # 跳过活跃度分析（不是图表）

                if chart_path and Path(chart_path).exists():
                    encoded = self._encode_image_base64(chart_path)
                    if encoded:
                        charts_base64[chart_name] = encoded
                        logger.debug(f"图表已编码: {chart_name}")

            # 3. 收集数据
            basic_info = self._collect_basic_info(author_name)
            activity_patterns = chart_results.get('activity_patterns', {})

            # 4. 准备模板数据
            template_data = {
                'title': f"{author_name} 的数据分析" if author_name else "全局数据分析",
                'subtitle': "T66Y 论坛归档系统",
                'generate_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'basic_info': basic_info,
                'activity_patterns': activity_patterns,
                'charts': charts_base64
            }

            # 5. 渲染 HTML
            template = self.jinja_env.get_template('analysis_report.html')
            html_content = template.render(**template_data)

            # 6. 保存文件
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                suffix = f"_{author_name}" if author_name else "_global"
                output_filename = f"report{suffix}_{timestamp}.html"

            output_path = self.output_dir / output_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"报告生成成功: {output_path} ({file_size_mb:.2f} MB)")

            return str(output_path)

        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_author_report(self, author_name: str) -> Optional[str]:
        """
        生成作者报告（快捷方法）

        Args:
            author_name: 作者名

        Returns:
            输出文件路径，失败返回 None
        """
        return self.generate_report(author_name=author_name, include_wordcloud=True)

    def generate_global_report(self) -> Optional[str]:
        """
        生成全局报告（快捷方法）

        Returns:
            输出文件路径，失败返回 None
        """
        return self.generate_report(author_name=None, include_camera=True)


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    from ..database.connection import get_default_connection

    db = get_default_connection()
    generator = ReportGenerator(db_connection=db)

    # 测试全局报告
    print("\n=== 生成全局报告 ===")
    output = generator.generate_global_report()
    if output:
        print(f"✅ 报告已生成: {output}")
    else:
        print("❌ 报告生成失败")
