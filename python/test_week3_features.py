#!/usr/bin/env python3
"""
Week 3 功能测试脚本

测试内容:
1. Visualizer 统一接口
2. 报告生成器
3. HTML 报告验证

作者: Claude Sonnet 4.5
日期: 2026-02-15
"""

import sys
import logging
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.analysis.visualizer import Visualizer
from src.analysis.report_generator import ReportGenerator
from src.database.connection import get_default_connection
from src.database.models import Author

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_visualizer():
    """测试 1: Visualizer 统一接口"""
    print("\n" + "=" * 60)
    print("测试 1: Visualizer 统一接口")
    print("=" * 60)

    try:
        db = get_default_connection()
        visualizer = Visualizer(db_connection=db)

        # 测试批量生成（全局）
        print("  生成全局图表...")
        results = visualizer.generate_all_charts(author_name=None, include_camera=True)

        # 验证结果
        if results and 'monthly_trend' in results and results['monthly_trend']:
            summary = visualizer.get_chart_summary(results)
            print(f"  ✅ 生成了 {len(summary)} 个图表")
            for chart in summary:
                print(f"     - {chart['name']}: {chart['size_kb']:.1f} KB")
            return True
        else:
            print("  ❌ 图表生成失败")
            return False

    except Exception as e:
        print(f"  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_global_report():
    """测试 2: 全局报告生成"""
    print("\n" + "=" * 60)
    print("测试 2: 全局报告生成")
    print("=" * 60)

    try:
        db = get_default_connection()
        generator = ReportGenerator(db_connection=db)

        # 生成全局报告
        print("  生成全局报告...")
        output_path = generator.generate_global_report()

        if output_path and Path(output_path).exists():
            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"  ✅ 报告生成成功")
            print(f"     文件: {output_path}")
            print(f"     大小: {file_size:.2f} MB")

            # 验证 HTML 内容
            with open(output_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 检查关键内容
            checks = [
                ('<!DOCTYPE html>' in html_content, 'HTML 结构'),
                ('data:image/png;base64' in html_content, 'Base64 图片嵌入'),
                ('月度发帖趋势' in html_content, '图表标题'),
                ('活跃度分析' in html_content, '活跃度指标'),
            ]

            all_passed = True
            for passed, name in checks:
                if passed:
                    print(f"     ✓ {name}")
                else:
                    print(f"     ✗ {name}")
                    all_passed = False

            return all_passed
        else:
            print("  ❌ 报告生成失败")
            return False

    except Exception as e:
        print(f"  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_author_report():
    """测试 3: 作者报告生成"""
    print("\n" + "=" * 60)
    print("测试 3: 作者报告生成")
    print("=" * 60)

    try:
        db = get_default_connection()
        generator = ReportGenerator(db_connection=db)

        # 获取第一个作者
        Author._db = db
        authors = Author.get_all()
        if not authors:
            print("  ⚠️  数据库无作者，跳过测试")
            return True

        test_author = authors[0].name
        print(f"  测试作者: {test_author}")

        # 生成作者报告
        print("  生成作者报告...")
        output_path = generator.generate_author_report(test_author)

        if output_path and Path(output_path).exists():
            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"  ✅ 报告生成成功")
            print(f"     文件: {output_path}")
            print(f"     大小: {file_size:.2f} MB")

            # 验证 HTML 内容
            with open(output_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 检查关键内容（作者模式应该有词云）
            checks = [
                ('<!DOCTYPE html>' in html_content, 'HTML 结构'),
                ('data:image/png;base64' in html_content, 'Base64 图片嵌入'),
                (test_author in html_content, '作者名'),
                ('词云分析' in html_content or '月度发帖趋势' in html_content, '图表内容'),
            ]

            all_passed = True
            for passed, name in checks:
                if passed:
                    print(f"     ✓ {name}")
                else:
                    print(f"     ✗ {name}")
                    all_passed = False

            return all_passed
        else:
            print("  ❌ 报告生成失败")
            return False

    except Exception as e:
        print(f"  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_size():
    """测试 4: 报告文件大小合理性"""
    print("\n" + "=" * 60)
    print("测试 4: 报告文件大小验证")
    print("=" * 60)

    try:
        reports_dir = Path(__file__).parent / 'data' / 'reports'
        if not reports_dir.exists():
            print("  ⚠️  报告目录不存在，跳过测试")
            return True

        reports = list(reports_dir.glob("*.html"))
        if not reports:
            print("  ⚠️  无报告文件，跳过测试")
            return True

        print(f"  找到 {len(reports)} 个报告文件")

        all_valid = True
        for report in reports:
            file_size_mb = report.stat().st_size / (1024 * 1024)

            # 报告大小应该在 0.1 MB 到 10 MB 之间（合理范围）
            if 0.1 <= file_size_mb <= 10:
                print(f"  ✓ {report.name}: {file_size_mb:.2f} MB")
            else:
                print(f"  ✗ {report.name}: {file_size_mb:.2f} MB (异常)")
                all_valid = False

        return all_valid

    except Exception as e:
        print(f"  ❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(" Week 3 功能测试")
    print("=" * 60)

    # 运行所有测试
    tests = [
        ("Visualizer 统一接口", test_visualizer),
        ("全局报告生成", test_global_report),
        ("作者报告生成", test_author_report),
        ("报告文件大小", test_report_size),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试崩溃: {e}")
            results.append((test_name, False))

    # 汇总结果
    print("\n" + "=" * 60)
    print(" 测试汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status:10} {test_name}")

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
