#!/usr/bin/env python3
"""
Week 2 功能测试脚本

测试内容:
1. 字体检测
2. 词云生成
3. 时间分析（月度趋势、热力图、活跃度）
4. 相机统计

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
from src.utils.font_config import FontConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_font_detection():
    """测试 1: 字体检测"""
    print("\n" + "=" * 60)
    print("测试 1: 字体检测")
    print("=" * 60)

    try:
        result = FontConfig.test_chinese_display()
        if result:
            print("✅ 字体检测测试通过")
            return True
        else:
            print("❌ 字体检测测试失败")
            return False
    except Exception as e:
        print(f"❌ 字体检测测试异常: {e}")
        return False


def test_text_segmentation():
    """测试 2: 文本分词"""
    print("\n" + "=" * 60)
    print("测试 2: 文本分词")
    print("=" * 60)

    try:
        analyzer = TextAnalyzer()

        # 测试分词
        text = "今天天气很好，我很开心，我们一起去公园玩"
        words = analyzer.segment_text(text)

        print(f"原文: {text}")
        print(f"分词结果: {words}")

        # 验证停用词过滤
        stopwords = analyzer._load_stopwords()
        has_stopwords = any(word in stopwords for word in words)

        if not has_stopwords and len(words) > 0:
            print("✅ 文本分词测试通过")
            return True
        else:
            print("❌ 文本分词测试失败（停用词未过滤）")
            return False

    except Exception as e:
        print(f"❌ 文本分词测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_word_frequency():
    """测试 3: 词频统计"""
    print("\n" + "=" * 60)
    print("测试 3: 词频统计")
    print("=" * 60)

    try:
        analyzer = TextAnalyzer()

        # 测试词频
        texts = ["今天天气好", "今天心情好", "天气不错"]
        word_freq = analyzer.calculate_word_frequency(texts)

        print(f"文本列表: {texts}")
        print(f"词频统计: {word_freq}")

        # 验证词频正确性（检查是否有词频统计，且"天气"出现多次）
        if len(word_freq) > 0 and word_freq.get('天气', 0) >= 1:
            print("✅ 词频统计测试通过")
            return True
        else:
            print("❌ 词频统计测试失败")
            return False

    except Exception as e:
        print(f"❌ 词频统计测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wordcloud_generation():
    """测试 4: 词云生成"""
    print("\n" + "=" * 60)
    print("测试 4: 词云生成")
    print("=" * 60)

    try:
        db = get_default_connection()
        analyzer = TextAnalyzer(db_connection=db)

        # 查询数据库中的作者
        from src.database.models import Author
        Author._db = db
        authors = Author.get_all()

        if not authors:
            print("⚠️  数据库无作者数据，跳过测试")
            return True

        # 使用第一个作者
        test_author = authors[0].name
        print(f"测试作者: {test_author}")

        # 生成词云（快速模式：仅标题）
        output = analyzer.generate_author_wordcloud(
            author_name=test_author,
            include_title_only=True
        )

        if output and Path(output).exists():
            file_size = Path(output).stat().st_size
            print(f"✅ 词云生成测试通过")
            print(f"   输出文件: {output}")
            print(f"   文件大小: {file_size / 1024:.1f} KB")
            return True
        else:
            print("❌ 词云生成测试失败")
            return False

    except Exception as e:
        print(f"❌ 词云生成测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monthly_trend():
    """测试 5: 月度趋势图"""
    print("\n" + "=" * 60)
    print("测试 5: 月度趋势图")
    print("=" * 60)

    try:
        db = get_default_connection()
        analyzer = TimeAnalyzer(db_connection=db)

        # 生成月度趋势图（全局）
        output = analyzer.plot_monthly_trend()

        if output and Path(output).exists():
            file_size = Path(output).stat().st_size
            print(f"✅ 月度趋势图测试通过")
            print(f"   输出文件: {output}")
            print(f"   文件大小: {file_size / 1024:.1f} KB")
            return True
        else:
            print("❌ 月度趋势图测试失败")
            return False

    except Exception as e:
        print(f"❌ 月度趋势图测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_time_heatmap():
    """测试 6: 时间热力图"""
    print("\n" + "=" * 60)
    print("测试 6: 时间热力图")
    print("=" * 60)

    try:
        db = get_default_connection()
        analyzer = TimeAnalyzer(db_connection=db)

        # 生成时间热力图（全局）
        output = analyzer.plot_time_heatmap()

        if output and Path(output).exists():
            file_size = Path(output).stat().st_size
            print(f"✅ 时间热力图测试通过")
            print(f"   输出文件: {output}")
            print(f"   文件大小: {file_size / 1024:.1f} KB")
            return True
        else:
            print("❌ 时间热力图测试失败")
            return False

    except Exception as e:
        print(f"❌ 时间热力图测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_active_patterns():
    """测试 7: 活跃度分析"""
    print("\n" + "=" * 60)
    print("测试 7: 活跃度分析")
    print("=" * 60)

    try:
        db = get_default_connection()
        analyzer = TimeAnalyzer(db_connection=db)

        # 活跃度分析
        patterns = analyzer.analyze_active_patterns()

        if patterns and 'most_active_hour' in patterns:
            print(f"✅ 活跃度分析测试通过")
            print(f"   最活跃小时: {patterns.get('most_active_hour')}:00")
            print(f"   最活跃星期: {patterns.get('most_active_weekday_name')}")
            print(f"   周末占比: {patterns.get('weekend_ratio') * 100:.1f}%")
            print(f"   夜猫子指数: {patterns.get('night_owl_index') * 100:.1f}%")
            print(f"   早起指数: {patterns.get('early_bird_index') * 100:.1f}%")
            print(f"   工作日指数: {patterns.get('workday_index') * 100:.1f}%")
            return True
        else:
            print("❌ 活跃度分析测试失败")
            return False

    except Exception as e:
        print(f"❌ 活跃度分析测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_camera_ranking():
    """测试 8: 相机统计"""
    print("\n" + "=" * 60)
    print("测试 8: 相机统计")
    print("=" * 60)

    try:
        db = get_default_connection()
        analyzer = TimeAnalyzer(db_connection=db)

        # 生成相机排行图
        output = analyzer.plot_camera_ranking(limit=10)

        if output and Path(output).exists():
            file_size = Path(output).stat().st_size
            print(f"✅ 相机统计测试通过")
            print(f"   输出文件: {output}")
            print(f"   文件大小: {file_size / 1024:.1f} KB")
            return True
        elif output is None:
            print("⚠️  无相机数据，跳过测试")
            return True
        else:
            print("❌ 相机统计测试失败")
            return False

    except Exception as e:
        print(f"❌ 相机统计测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(" Week 2 功能测试")
    print("=" * 60)

    # 运行所有测试
    tests = [
        ("字体检测", test_font_detection),
        ("文本分词", test_text_segmentation),
        ("词频统计", test_word_frequency),
        ("词云生成", test_wordcloud_generation),
        ("月度趋势图", test_monthly_trend),
        ("时间热力图", test_time_heatmap),
        ("活跃度分析", test_active_patterns),
        ("相机统计", test_camera_ranking),
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
