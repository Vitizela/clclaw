"""HTML 内容清理和格式化

功能：
1. 移除复杂的 div 嵌套
2. 转换连续 <br> 为段落
3. 提取章节标题
4. 移除图片/视频标签（单独列表展示）
5. 优化 w3m 浏览体验
"""
import re


def clean_html_content(raw_html: str) -> str:
    """
    清理原始 HTML，转换为适合阅读的格式

    Args:
        raw_html: 从网页提取的原始 HTML

    Returns:
        清理后的 HTML（段落结构、章节标题）
    """
    if not raw_html or not raw_html.strip():
        return '<p>（无内容）</p>'

    html = raw_html

    # ========== 新增：更彻底的图片/视频清理 ==========

    # 1. 移除所有 <img> 标签（不管是否有包裹）
    html = re.sub(
        r'<img[^>]*>',
        '',
        html,
        flags=re.IGNORECASE
    )

    # 2. 移除图片链接（<a href="xxx.jpg"><img></a> 或 <a href="xxx.jpg">查看图片</a>）
    html = re.sub(
        r'<a\s+[^>]*href=["\'][^"\']*\.(jpg|jpeg|png|gif|webp|bmp)["\'][^>]*>.*?</a>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 3. 移除图片 div 容器（各种可能的 class 名称）
    html = re.sub(
        r'<div\s+class=["\']?(image-big|image|img-container|pic)["\']?[^>]*>.*?</div>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 4. 移除视频标签（会在底部单独列出）
    html = re.sub(
        r'<video[^>]*>.*?</video>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 5. 移除 <source> 标签（视频源）
    html = re.sub(
        r'<source[^>]*>',
        '',
        html,
        flags=re.IGNORECASE
    )

    # ========== 新增：清理残留标签 ==========

    # 6. 移除孤立的 </div> 标签
    html = re.sub(r'</div>\s*', ' ', html, flags=re.IGNORECASE)

    # 7. 移除孤立的 <div> 开始标签（没有对应的结束标签）
    html = re.sub(r'<div[^>]*>\s*', ' ', html, flags=re.IGNORECASE)

    # 8. 移除空的 <a> 标签
    html = re.sub(r'<a[^>]*>\s*</a>', '', html, flags=re.IGNORECASE)

    # ========== 原有逻辑 ==========

    # 9. 移除点赞按钮等无关元素
    html = re.sub(
        r'<div\s+onclick="clickLike.*?</div>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 10. 转换连续 <br> 为段落分隔
    html = re.sub(r'(<br\s*/?>){2,}', '</p>\n<p>', html, flags=re.IGNORECASE)

    # 11. 移除剩余的单个 <br>（段落内换行）
    html = re.sub(r'<br\s*/?>', ' ', html, flags=re.IGNORECASE)

    # 12. 识别章节标题（如 "01." "一、" 开头）
    html = re.sub(
        r'<p>\s*(\d+\.|\d+、|[一二三四五六七八九十]+、)\s*([^<]+?)\s*</p>',
        r'<h2>\1 \2</h2>',
        html
    )

    # 13. 包裹段落（如果还没有）
    if not html.strip().startswith('<p>') and not html.strip().startswith('<h'):
        html = f'<p>{html}</p>'

    # 14. 清理多余空格
    html = re.sub(r'\s{2,}', ' ', html)

    # 15. 清理多余空行
    html = re.sub(r'\n{3,}', '\n\n', html)

    # 16. 清理空段落
    html = re.sub(r'<p>\s*</p>', '', html)

    # 17. 去除首尾空白
    html = html.strip()

    return html


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化字符串（如 "1.2 MB"）
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
