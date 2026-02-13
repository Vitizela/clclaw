#!/bin/bash
# 清理无效的视频文件（HTML 错误页面）

echo "🔍 查找无效的视频文件..."

# 查找小于 1KB 的视频文件
invalid_videos=$(find /home/ben/Download/t66y -type f -name "video_*.mp4" -size -1k)

if [ -z "$invalid_videos" ]; then
    echo "✅ 没有发现无效的视频文件"
    exit 0
fi

echo "发现以下无效文件:"
echo "$invalid_videos" | while read file; do
    size=$(stat -c%s "$file" 2>/dev/null)
    echo "  - $file ($size bytes)"
done

echo ""
read -p "是否删除这些文件？[y/N] " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🗑️  删除无效文件..."

    echo "$invalid_videos" | while read file; do
        # 删除视频文件
        rm -f "$file"
        echo "  ✓ 已删除: $file"

        # 删除 .done 标记
        done_file="${file}.done"
        if [ -f "$done_file" ]; then
            rm -f "$done_file"
            echo "  ✓ 已删除: $done_file"
        fi

        # 删除所在目录的 .complete 标记（以便重新归档）
        post_dir=$(dirname $(dirname "$file"))
        complete_file="$post_dir/.complete"
        if [ -f "$complete_file" ]; then
            rm -f "$complete_file"
            echo "  ✓ 已删除: $complete_file"
        fi
    done

    echo ""
    echo "✅ 清理完成！现在可以重新归档这些帖子了。"
    echo ""
    echo "💡 提示: 运行 'cd python && python main.py' 重新归档"
else
    echo "❌ 取消清理"
fi
