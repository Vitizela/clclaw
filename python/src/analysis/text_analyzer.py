#!/usr/bin/env python3
"""
文本分析器 - 中文分词与词云生成

功能:
- 中文文本分词（jieba）
- 停用词过滤
- 词频统计
- 词云生成（WordCloud）
- 作者词云生成（基于数据库数据）

设计模式: 遵循 ExifAnalyzer 模式（可选 db_connection）
"""

import logging
from typing import List, Dict, Optional, Set
from pathlib import Path
from collections import Counter
import jieba

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """文本分析器 - 中文分词与词云生成"""

    def __init__(self, db_connection=None):
        """
        初始化文本分析器

        Args:
            db_connection: 可选的数据库连接（遵循 ExifAnalyzer 模式）
        """
        self.db_connection = db_connection
        self._stopwords: Optional[Set[str]] = None
        self._font_path: Optional[str] = None

    def segment_text(self, text: str) -> List[str]:
        """
        中文文本分词（jieba）+ 停用词过滤

        Args:
            text: 待分词文本

        Returns:
            过滤后的词列表
        """
        if not text or not text.strip():
            return []

        # 加载停用词（延迟加载）
        if self._stopwords is None:
            self._stopwords = self._load_stopwords()

        # jieba 分词
        words = jieba.cut(text)

        # 停用词过滤 + 长度过滤（>=2 字符）
        filtered_words = [
            word.strip() for word in words
            if word.strip()
            and len(word.strip()) >= 2
            and word.strip() not in self._stopwords
        ]

        return filtered_words

    def calculate_word_frequency(self, texts: List[str]) -> Dict[str, int]:
        """
        计算词频统计（Counter）

        Args:
            texts: 文本列表

        Returns:
            词频字典 {词: 出现次数}
        """
        all_words = []
        for text in texts:
            words = self.segment_text(text)
            all_words.extend(words)

        # Counter 统计
        word_freq = Counter(all_words)

        return dict(word_freq)

    def generate_wordcloud(
        self,
        word_freq: Dict[str, int],
        output_path: str,
        width: int = 1200,
        height: int = 800,
        background_color: str = 'white',
        max_words: int = 200
    ) -> Optional[str]:
        """
        生成词云图片（WordCloud）

        Args:
            word_freq: 词频字典
            output_path: 输出文件路径
            width: 图片宽度（默认 1200）
            height: 图片高度（默认 800）
            background_color: 背景色（默认白色）
            max_words: 最大词数（默认 200）

        Returns:
            输出文件路径，失败返回 None
        """
        if not word_freq:
            logger.warning("词频字典为空，无法生成词云")
            return None

        try:
            from wordcloud import WordCloud

            # 获取中文字体路径
            font_path = self._get_font_path()
            if not font_path:
                logger.error("未找到中文字体，无法生成词云")
                logger.info("请安装中文字体: sudo apt install fonts-wqy-zenhei")
                return None

            # 生成词云
            wordcloud = WordCloud(
                font_path=font_path,
                width=width,
                height=height,
                background_color=background_color,
                max_words=max_words,
                relative_scaling=0.5,
                min_font_size=10
            ).generate_from_frequencies(word_freq)

            # 保存图片（DPI 300）
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            wordcloud.to_file(str(output_file))

            logger.info(f"词云生成成功: {output_file}")
            return str(output_file)

        except ImportError:
            logger.error("WordCloud 库未安装: pip install wordcloud")
            return None
        except Exception as e:
            logger.error(f"词云生成失败: {e}")
            return None

    def generate_author_wordcloud(
        self,
        author_name: str,
        output_path: Optional[str] = None,
        include_title_only: bool = True
    ) -> Optional[str]:
        """
        生成作者词云（基于数据库数据）

        Args:
            author_name: 作者名
            output_path: 输出路径（默认 data/analysis/wordcloud_{作者名}.png）
            include_title_only: 是否仅使用标题（True=快速模式，False=完整模式）

        Returns:
            输出文件路径，失败返回 None
        """
        if not self.db_connection:
            logger.error("数据库连接未提供，无法生成作者词云")
            return None

        try:
            # 查询作者帖子
            from ..database.models import Author, Post

            # 设置数据库
            Author._db = self.db_connection
            Post._db = self.db_connection

            # 获取作者 ID
            author = Author.get_by_name(author_name)
            if not author:
                logger.warning(f"作者 {author_name} 不存在")
                return None

            # 获取帖子列表
            posts = Post.get_by_author(author.id)

            if not posts:
                logger.warning(f"作者 {author_name} 无帖子数据")
                return None

            logger.info(f"找到作者 {author_name} 的 {len(posts)} 篇帖子")

            # 提取文本
            texts = []
            for post in posts:
                # 标题总是添加
                if post.title:
                    texts.append(post.title)

                # 完整模式：解析 content.html
                if not include_title_only and post.file_path:
                    content = self._read_post_content(post.file_path)
                    if content:
                        texts.append(content)

            if not texts:
                logger.warning(f"作者 {author_name} 无文本数据")
                return None

            # 计算词频
            word_freq = self.calculate_word_frequency(texts)

            if not word_freq:
                logger.warning(f"作者 {author_name} 词频统计为空")
                return None

            # 生成词云
            if output_path is None:
                output_dir = Path(__file__).parent.parent.parent / 'data' / 'analysis'
                output_path = str(output_dir / f"wordcloud_{author_name}.png")

            result = self.generate_wordcloud(word_freq, output_path)

            if result:
                logger.info(f"作者词云生成成功: {result} (词数: {len(word_freq)})")

            return result

        except Exception as e:
            logger.error(f"作者词云生成失败: {e}")
            return None

    def _read_post_content(self, file_path: str) -> Optional[str]:
        """
        读取帖子内容（BeautifulSoup 解析 HTML）

        Args:
            file_path: 相对路径（如 '同花顺心/123456/content.html'）

        Returns:
            纯文本内容，失败返回 None
        """
        try:
            from bs4 import BeautifulSoup

            # 构建完整路径
            data_dir = Path(__file__).parent.parent.parent / 'data'
            full_path = data_dir / file_path

            if not full_path.exists():
                logger.warning(f"文件不存在: {full_path}")
                return None

            # 读取 HTML
            with open(full_path, 'r', encoding='utf-8') as f:
                html = f.read()

            # BeautifulSoup 解析
            soup = BeautifulSoup(html, 'html.parser')

            # 提取纯文本
            text = soup.get_text(separator=' ', strip=True)

            return text

        except ImportError:
            logger.debug("BeautifulSoup 未安装，跳过内容解析")
            return None
        except Exception as e:
            logger.warning(f"读取帖子内容失败: {e}")
            return None

    def _load_stopwords(self) -> Set[str]:
        """
        加载停用词表（延迟加载）

        Returns:
            停用词集合
        """
        try:
            stopwords_path = Path(__file__).parent.parent / 'utils' / 'stopwords.txt'

            if not stopwords_path.exists():
                logger.warning(f"停用词表不存在: {stopwords_path}")
                return set()

            with open(stopwords_path, 'r', encoding='utf-8') as f:
                stopwords = set(line.strip() for line in f if line.strip())

            logger.debug(f"停用词加载完成: {len(stopwords)} 个")
            return stopwords

        except Exception as e:
            logger.error(f"停用词加载失败: {e}")
            return set()

    def _get_font_path(self) -> Optional[str]:
        """
        获取中文字体路径（延迟加载）

        Returns:
            字体文件路径，未找到返回 None
        """
        if self._font_path is not None:
            return self._font_path

        try:
            from ..utils.font_config import FontConfig
            self._font_path = FontConfig.get_chinese_font()
            return self._font_path
        except Exception as e:
            logger.error(f"字体路径获取失败: {e}")
            return None


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.DEBUG)

    analyzer = TextAnalyzer()

    # 测试分词
    text = "今天天气很好，我很开心，我们一起去公园玩"
    words = analyzer.segment_text(text)
    print(f"分词结果: {words}")

    # 测试词频
    texts = ["今天天气好", "今天心情好", "天气不错"]
    word_freq = analyzer.calculate_word_frequency(texts)
    print(f"词频统计: {word_freq}")
