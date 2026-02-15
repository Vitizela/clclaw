# EXIF 静态显示功能（v2.7）

## 📝 变更说明

根据您的反馈"我想显示在图片下面，就是'下载'的上面，就像手机里看的那样"，已重构 EXIF 显示为**静态模式**。

### 之前（v2.6）
- 半透明水印覆盖在图片底部
- 需要鼠标**悬停**才能看到
- `opacity: 0 → 1` 渐变效果

### 现在（v2.7）
- 静态显示在图片信息和下载按钮之间
- **始终可见**，无需悬停
- 灰色背景（#f5f5f5），清晰易读
- 布局：`图片 → 图片信息 → EXIF 信息 → 下载按钮`

## 🎨 显示效果

```
┌─────────────────────┐
│                     │
│     [图片内容]       │
│                     │
├─────────────────────┤
│ [1]          256KB  │  ← 图片信息
├─────────────────────┤
│ 📷 vivo X Fold3 Pro │  ← EXIF 信息（灰色背景）
│ ⚙️ f/1.7 · 1/50s · ISO50  │
│ 🕐 2024:08:15 10:30:25    │
│ 📍 中国广东省深圳市       │
├─────────────────────┤
│    ⬇ 下载            │
└─────────────────────┘
```

## 🚀 快速测试

### 方法 1：一键测试（推荐）

```bash
python3 python/test_exif_display.py
```

自动完成：
1. 查找有 EXIF 数据的帖子
2. 重新生成 HTML（使用新模板 v2.7）
3. 打开浏览器预览

### 方法 2：手动重新生成

```bash
# 指定帖子 URL
python3 python/regenerate_html.py "https://t66y.com/htm_data/7/2602/12345.html"

# 自动查找有 EXIF 的帖子（最近 5 个）
python3 python/regenerate_html.py
```

### 方法 3：归档新帖子

```bash
python3 python/main.py
# 选择 "2) 更新追踪的作者"
# 选择作者 → 开始更新
```

新归档的帖子会自动：
- 提取 EXIF 数据（如有）
- 写入数据库
- 生成带 EXIF 的 HTML（v2.7 模板）

## 📊 技术细节

### 提交历史

```
cc381f2 - feat(phase4): 重构 EXIF 显示为静态模式（模板 v2.7）
b7115d4 - feat(phase4): 添加 HTML 重新生成和测试工具
b3e7cc4 - fix(critical): 添加归档时的数据库自动同步功能
```

### CSS 变更

**新增类：**
- `.exif-info` - EXIF 容器（灰色背景）
- `.exif-line` - 每一行（flexbox 布局）
- `.exif-icon` - 图标（18px 宽度，居中）
- `.exif-text` - 文本内容（自动换行）

**移除类：**
- `.exif-watermark` - 悬停水印（已废弃）
- `.line` - 水印行
- `.icon` - 水印图标
- `.sep` - 水印分隔符

### HTML 结构

```html
<div class="image-item">
    <img src="photo/xxx.jpg" />

    <div class="image-info">
        <span class="index">[1]</span>
        <span class="size">256KB</span>
    </div>

    <!-- 新增：EXIF 静态显示 -->
    <div class="exif-info">
        <div class="exif-line">
            <span class="exif-icon">📷</span>
            <span class="exif-text">vivo X Fold3 Pro</span>
        </div>
        <!-- ... 更多行 ... -->
    </div>

    <a href="photo/xxx.jpg" class="download-link">⬇ 下载</a>
</div>
```

## ✅ 验证清单

重新生成 HTML 后，打开浏览器检查：

- [ ] EXIF 信息在图片**下方**、下载按钮**上方**
- [ ] 灰色背景（不是透明覆盖）
- [ ] **始终可见**（无需悬停）
- [ ] 显示相机型号（📷）
- [ ] 显示拍摄参数（⚙️ f/光圈、快门、ISO、焦距）
- [ ] 显示拍摄时间（🕐）
- [ ] 显示拍摄位置（📍，如有 GPS）
- [ ] 移动端正常显示（可选）

## 🔧 工具说明

### regenerate_html.py

重新生成帖子的 `content.html`（带 EXIF 水印）。

**用途：**
- 已归档的帖子提取 EXIF 后重新生成 HTML
- 测试新模板效果
- 修复旧模板生成的 HTML

**特点：**
- 自动备份旧文件（.backup.时间戳）
- 从数据库读取 EXIF 数据
- 显示详细统计（图片数、视频数、EXIF 数）

### test_exif_display.py

一键测试 EXIF 静态显示功能。

**流程：**
1. 连接数据库
2. 查找最近有 EXIF 的帖子
3. 调用 `regenerate_html.py` 重新生成
4. 自动打开浏览器（xdg-open）

**优势：**
- 零配置，开箱即用
- 自动选择最佳测试用例
- 显示期望效果说明

## 📚 相关文件

- `python/src/templates/post.html` - HTML 模板（v2.7）
- `python/src/scraper/archiver.py` - 归档器（获取 EXIF）
- `python/src/database/sync.py` - 数据库同步（写入 EXIF）
- `python/src/analysis/exif_analyzer.py` - EXIF 提取器
- `python/regenerate_html.py` - HTML 重新生成工具
- `python/test_exif_display.py` - EXIF 显示测试工具

## 🎯 下一步

完成测试后，可以：

1. **批量重新生成**：为所有有 EXIF 的帖子重新生成 HTML
   ```bash
   python3 python/regenerate_html.py  # 默认处理最近 5 个
   ```

2. **继续 Phase 4 Week 2**：文本分析、词云、时间热力图（任务 #35-#54）

3. **优化 EXIF 显示**：
   - 自定义颜色主题
   - 添加更多 EXIF 字段（白平衡、闪光灯等）
   - 地图集成（GPS 位置点击显示地图）

## ❓ 常见问题

**Q: 为什么我看不到 EXIF？**

A: 按以下顺序检查：
1. 运行 `./verify_exif.sh` 检查数据库中是否有 EXIF 数据
2. 如果 Media 记录为 0，参考 **TROUBLESHOOTING.md** → "数据库同步问题"
3. 如果有 Media 但无 EXIF，检查 HTML 模板版本（应为 v2.7）
4. 运行 `python3 python/regenerate_html.py` 重新生成 HTML
5. 如果仍无 EXIF，可能是图片本身无 EXIF（网络图片通常被剥离）

**Q: 如何为旧帖子添加 EXIF？**

A: 运行批量提取工具：
```bash
python3 -m src.database.migrate_exif --limit 100
```

**Q: Media 记录为 0 怎么办？**

A: 这是 Phase 4 Week 1 最常见的问题。详细诊断流程见：
- **TROUBLESHOOTING.md** → "数据库同步问题"
- **MEMORY.md** → "常见陷阱 → 4. 数据库同步陷阱"

快速修复：
```bash
./clean_test_post.sh  # 清理旧数据
# 重新归档帖子
python3 python/main.py
./verify_exif.sh      # 验证结果
```

**Q: 悬停水印还能用吗？**

A: v2.7 已移除悬停功能，改为静态显示（用户反馈更符合使用习惯）。如需恢复，可查看 `git show cc381f2^:python/src/templates/post.html` 获取 v2.6 代码。

## 📞 反馈

如果静态显示效果不符合预期，请提供：
- 生成的 HTML 截图
- 期望的显示效果描述
- 需要调整的部分（布局、颜色、字体等）
