#!/usr/bin/env python3
"""
简单演示脚本 - 一键生成所有分析图表

使用方法:
    python demo_analysis.py           # 生成全局统计
    python demo_analysis.py 同花顺心   # 生成指定作者的统计

作者: Claude Sonnet 4.5
日期: 2026-02-15
"""

import sys
import logging
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.analysis.text_analyzer import TextAnalyzer
from src.analysis.time_analyzer import TimeAnalyzer
from src.database.connection import get_default_connection
from src.database.models import Author

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  📊 T66Y 论坛归档系统 - 数据分析演示")
    print("=" * 60 + "\n")

    # 获取数据库连接
    db = get_default_connection()

    # 检查是否指定了作者
    author_name = None
    if len(sys.argv) > 1:
        author_name = sys.argv[1]
        print(f"📌 分析作者: {author_name}\n")
    else:
        print("📌 分析范围: 全局统计\n")
        print("💡 提示: 运行 'python demo_analysis.py 作者名' 可分析指定作者\n")

    # 如果指定了作者，验证作者是否存在
    if author_name:
        Author._db = db
        author = Author.get_by_name(author_name)
        if not author:
            print(f"❌ 错误: 作者 '{author_name}' 不存在")
            print("\n可用的作者列表:")
            authors = Author.get_all()[:10]  # 显示前 10 个
            for a in authors:
                print(f"  - {a.name}")
            if len(Author.get_all()) > 10:
                print(f"  ... 还有 {len(Author.get_all()) - 10} 个作者")
            return 1

    # 创建输出目录
    output_dir = Path(__file__).parent / 'data' / 'analysis'
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    # 1. 词云生成
    if author_name:
        print("🔤 [1/5] 生成词云...")
        text_analyzer = TextAnalyzer(db_connection=db)
        output = text_analyzer.generate_author_wordcloud(
            author_name=author_name,
            include_title_only=True
        )
        if output:
            results.append(("词云", output))
            print(f"    ✅ 完成: {output}")
        else:
            print("    ⚠️  跳过（无数据）")
    else:
        print("🔤 [1/5] 跳过词云（全局模式不支持词云）")

    # 2. 月度趋势图
    print("📈 [2/5] 生成月度趋势图...")
    time_analyzer = TimeAnalyzer(db_connection=db)
    output = time_analyzer.plot_monthly_trend(author_name=author_name)
    if output:
        results.append(("月度趋势图", output))
        print(f"    ✅ 完成: {output}")
    else:
        print("    ⚠️  失败")

    # 3. 时间热力图
    print("🔥 [3/5] 生成时间热力图...")
    output = time_analyzer.plot_time_heatmap(author_name=author_name)
    if output:
        results.append(("时间热力图", output))
        print(f"    ✅ 完成: {output}")
    else:
        print("    ⚠️  失败")

    # 4. 活跃度分析
    print("⚡ [4/5] 分析活跃度模式...")
    patterns = time_analyzer.analyze_active_patterns(author_name=author_name)
    if patterns:
        print(f"    ✅ 完成:")
        print(f"       - 最活跃小时: {patterns.get('most_active_hour')}:00")
        print(f"       - 最活跃星期: {patterns.get('most_active_weekday_name')}")
        print(f"       - 周末占比: {patterns.get('weekend_ratio', 0) * 100:.1f}%")
        print(f"       - 夜猫子指数: {patterns.get('night_owl_index', 0) * 100:.1f}%")
        print(f"       - 早起指数: {patterns.get('early_bird_index', 0) * 100:.1f}%")
        print(f"       - 工作日指数: {patterns.get('workday_index', 0) * 100:.1f}%")
    else:
        print("    ⚠️  失败")

    # 5. 相机排行图
    if not author_name:
        print("📷 [5/5] 生成相机排行图...")
        output = time_analyzer.plot_camera_ranking(limit=10)
        if output:
            results.append(("相机排行图", output))
            print(f"    ✅ 完成: {output}")
        else:
            print("    ⚠️  跳过（无相机数据）")
    else:
        print("📷 [5/5] 跳过相机排行图（作者模式不支持相机统计）")

    # 汇总结果
    print("\n" + "=" * 60)
    print("  ✅ 分析完成！")
    print("=" * 60)

    if results:
        print(f"\n生成了 {len(results)} 个图表：\n")
        for name, path in results:
            size_kb = Path(path).stat().st_size / 1024
            print(f"  📊 {name:12} {size_kb:6.1f} KB")
            print(f"     {path}")
            print()

        print(f"📁 所有文件保存在: {output_dir}")
        print(f"💡 您可以用图片查看器打开这些 PNG 文件\n")
    else:
        print("\n⚠️  未生成任何图表\n")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
