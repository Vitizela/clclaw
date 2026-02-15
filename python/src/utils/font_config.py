#!/usr/bin/env python3
"""
字体配置工具 - 跨平台中文字体检测

功能:
- 自动检测操作系统
- 查找可用的中文字体
- 提供测试功能验证字体
"""

import logging
import platform
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class FontConfig:
    """字体配置工具 - 跨平台中文字体检测"""

    # 字体路径优先级（Linux/macOS/Windows）
    FONT_PRIORITY = {
        'Linux': [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            '/usr/share/fonts/truetype/arphic/uming.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        ],
        'Darwin': [  # macOS
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
        ],
        'Windows': [
            'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',  # 黑体
            'C:/Windows/Fonts/simsun.ttc',  # 宋体
            'C:/Windows/Fonts/simfang.ttf',  # 仿宋
        ]
    }

    @classmethod
    def get_chinese_font(cls) -> Optional[str]:
        """
        自动检测中文字体

        Returns:
            字体文件路径，未找到返回 None
        """
        system = platform.system()

        font_paths = cls.FONT_PRIORITY.get(system, [])

        for font_path in font_paths:
            if Path(font_path).exists():
                logger.info(f"找到中文字体: {font_path}")
                return font_path

        logger.warning(f"未找到中文字体 (系统: {system})")
        logger.info("请安装中文字体:")
        if system == 'Linux':
            logger.info("  Ubuntu/Debian: sudo apt install fonts-wqy-zenhei")
            logger.info("  Fedora/CentOS: sudo yum install wqy-zenhei-fonts")
        elif system == 'Darwin':
            logger.info("  macOS: 中文字体通常已预装")
        elif system == 'Windows':
            logger.info("  Windows: 中文字体通常已预装")

        return None

    @classmethod
    def test_chinese_display(cls) -> bool:
        """
        测试中文显示（生成测试词云）

        Returns:
            True=成功，False=失败
        """
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt

            # 获取字体
            font_path = cls.get_chinese_font()

            if not font_path:
                print("❌ 未找到中文字体")
                return False

            # 测试数据
            test_data = {
                '中文': 100,
                '测试': 80,
                '词云': 60,
                '显示': 50,
                '正常': 40,
            }

            # 生成词云
            wordcloud = WordCloud(
                font_path=font_path,
                width=800,
                height=400,
                background_color='white'
            ).generate_from_frequencies(test_data)

            # 保存测试图片
            test_output = '/tmp/font_test.png'
            wordcloud.to_file(test_output)

            print(f"✅ 中文字体可用: {font_path}")
            print(f"   测试图片: {test_output}")

            return True

        except ImportError as e:
            print(f"❌ 依赖库缺失: {e}")
            print("   请安装: pip install wordcloud matplotlib")
            return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False

    @classmethod
    def list_available_fonts(cls) -> List[str]:
        """
        列出所有可用的中文字体

        Returns:
            字体路径列表
        """
        system = platform.system()
        font_paths = cls.FONT_PRIORITY.get(system, [])

        available_fonts = []
        for font_path in font_paths:
            if Path(font_path).exists():
                available_fonts.append(font_path)

        return available_fonts


if __name__ == '__main__':
    # 测试字体检测
    logging.basicConfig(level=logging.INFO)

    print("=== 字体检测测试 ===\n")

    # 检测字体
    font = FontConfig.get_chinese_font()
    if font:
        print(f"✅ 找到中文字体: {font}\n")
    else:
        print("❌ 未找到中文字体\n")

    # 列出所有可用字体
    available = FontConfig.list_available_fonts()
    if available:
        print(f"可用字体 ({len(available)} 个):")
        for f in available:
            print(f"  - {f}")
        print()

    # 测试中文显示
    print("=== 中文显示测试 ===\n")
    FontConfig.test_chinese_display()
