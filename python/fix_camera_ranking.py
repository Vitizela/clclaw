#!/usr/bin/env python3
"""
修复相机排行图中文显示

这个脚本会重新生成相机排行图，确保中文正确显示。

使用方法:
    python fix_camera_ranking.py

作者: Claude Sonnet 4.5
日期: 2026-02-15
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from src.database.connection import get_default_connection
from src.database.query import get_camera_ranking


def generate_camera_ranking_chart(limit=10):
    """生成相机排行图（修复版）"""

    print("正在生成相机排行图...")

    # 获取数据
    db = get_default_connection()
    rankings = get_camera_ranking(limit=limit, db=db)

    if not rankings:
        print("❌ 无相机数据")
        return None

    # 准备数据
    labels = [f"{r['make']} {r['model']}" for r in rankings]
    counts = [r['photo_count'] for r in rankings]

    print(f"找到 {len(rankings)} 个相机")

    # 获取中文字体
    font_path = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
    if not Path(font_path).exists():
        print(f"⚠️  字体文件不存在: {font_path}")
        print("   图表将使用英文标签")
        font_path = None

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

    # 设置中文标签（如果字体可用）
    if font_path:
        font_prop = fm.FontProperties(fname=font_path, size=12)
        title_prop = fm.FontProperties(fname=font_path, size=16)

        ax.set_xlabel('照片数量', fontproperties=font_prop)
        ax.set_title(f'相机使用排行 (Top {limit})', fontproperties=title_prop, fontweight='bold')
        print("✓ 使用中文标签")
    else:
        ax.set_xlabel('Photo Count', fontsize=12)
        ax.set_title(f'Camera Ranking (Top {limit})', fontsize=16, fontweight='bold')
        print("✓ 使用英文标签")

    # 网格
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # 紧凑布局
    plt.tight_layout()

    # 保存图片
    output_dir = Path(__file__).parent / 'data' / 'analysis'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "camera_ranking.png"

    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close(fig)

    file_size = output_file.stat().st_size / 1024

    print(f"\n✅ 相机排行图已生成!")
    print(f"   文件: {output_file}")
    print(f"   大小: {file_size:.1f} KB")
    print(f"\n💡 用图片查看器打开查看效果")

    return str(output_file)


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  修复相机排行图中文显示")
    print("=" * 60 + "\n")

    try:
        output = generate_camera_ranking_chart()
        if output:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
