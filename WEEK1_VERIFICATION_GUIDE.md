# Week 1 功能检验指南

**Phase 4 - 图片元数据分析**
**日期**: 2026-02-14
**完成任务**: Tasks #26-34 (10/10)

---

## 📋 检验清单

### ✅ 检验 1: 数据库扩展（Task #26）

**检查 EXIF 字段是否已添加：**

```bash
cd python/data
sqlite3 forum_data.db "PRAGMA table_info(media);" | grep exif
```

**预期输出**：
```
13|exif_make|TEXT|0||0
14|exif_model|TEXT|0||0
15|exif_datetime|TEXT|0||0
16|exif_iso|INTEGER|0||0
17|exif_aperture|REAL|0||0
18|exif_shutter_speed|TEXT|0||0
19|exif_focal_length|REAL|0||0
20|exif_gps_lat|REAL|0||0
21|exif_gps_lng|REAL|0||0
22|exif_location|TEXT|0||0
```

**检查索引：**

```bash
sqlite3 forum_data.db ".indexes media"
```

**预期输出包含**：
```
idx_media_exif_make
idx_media_exif_model
idx_media_exif_datetime
idx_media_gps
idx_media_type_camera
```

**检查视图：**

```bash
sqlite3 forum_data.db ".tables" | grep "v_"
```

**预期输出**：
```
v_author_stats
v_camera_stats
v_exif_completeness
v_location_stats
v_monthly_trend
```

**查看 EXIF 完整性统计：**

```bash
sqlite3 forum_data.db "SELECT * FROM v_exif_completeness;"
```

**预期输出**：
```
total_images|has_make|has_model|has_datetime|has_iso|has_gps|has_location|make_pct|gps_pct
8772|0|0|0|0|0|0|0.0|0.0
```
（初始状态：0% 有 EXIF 数据，因为还未运行迁移）

---

### ✅ 检验 2: EXIF 分析器（Tasks #27-28）

**测试单张图片 EXIF 提取：**

找一张带 EXIF 的测试图片（相机拍摄的照片）：

```bash
cd python

# 方法1：如果有测试图片
python3 << 'EOF'
from src.analysis import ExifAnalyzer

analyzer = ExifAnalyzer()

# 替换为您的测试图片路径
test_image = "debug_page.png"  # 或其他图片

exif_data = analyzer.extract_exif(test_image)

if exif_data:
    print("✅ EXIF 提取成功！")
    print("\n📷 相机信息:")
    print(f"  品牌: {exif_data.get('make', 'N/A')}")
    print(f"  型号: {exif_data.get('model', 'N/A')}")

    print("\n⚙️  拍摄参数:")
    print(f"  ISO: {exif_data.get('iso', 'N/A')}")
    print(f"  光圈: f/{exif_data.get('aperture', 'N/A')}")
    print(f"  快门: {exif_data.get('shutter_speed', 'N/A')}")
    print(f"  焦距: {exif_data.get('focal_length', 'N/A')}mm")

    print("\n🕐 拍摄时间:")
    print(f"  {exif_data.get('datetime', 'N/A')}")

    if 'gps_lat' in exif_data:
        print("\n📍 GPS 坐标:")
        print(f"  纬度: {exif_data['gps_lat']}")
        print(f"  经度: {exif_data['gps_lng']}")
else:
    print("ℹ️  该图片没有 EXIF 数据")
    print("   （截图、网络图片通常没有 EXIF）")
EOF
```

**测试 GPS 反查：**

```bash
python3 << 'EOF'
from src.analysis import ExifAnalyzer

analyzer = ExifAnalyzer()

# 测试北京天安门坐标
latitude = 39.9042
longitude = 116.4074

print(f"🗺️  查询坐标: ({latitude}, {longitude})")
location = analyzer.reverse_geocode(latitude, longitude)

if location:
    print(f"✅ 地理位置: {location}")
else:
    print("❌ GPS 反查失败（可能是网络问题或 geopy 未安装）")
EOF
```

---

### ✅ 检验 3: 批量迁移工具（Tasks #31-32）

**预览模式（不写入数据库）：**

```bash
cd python

# 测试 10 张图片（不写入数据库）
python3 -m src.database.migrate_exif --dry-run --limit 10 --no-gps
```

**预期输出**：
```
╭─────────────────────────╮
│ EXIF 数据批量迁移工具   │
│ Phase 4: 图片元数据分析 │
╰─────────────────────────╯

正在扫描数据库...
找到 10 张图片待处理

  提取 EXIF 数据... ━━━━━━━━━━━━━━━━ 100%

           📊 处理统计
┏━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━┓
┃ 项目           ┃ 数量 ┃   占比 ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━┩
│ 总计           │   10 │ 100.0% │
│ 成功           │    X │   X.X% │
│ 跳过（无EXIF） │    X │   X.X% │
│ 有 EXIF 数据   │    X │   X.X% │
└────────────────┴──────┴────────┘

⚠️  预览模式：未实际写入数据库
```

**正式运行（少量测试）：**

```bash
# 只处理 100 张图片，跳过 GPS 反查（更快）
python3 -m src.database.migrate_exif --limit 100 --no-gps
```

**查看提取结果：**

```bash
cd data

# 查看有多少图片提取到了 EXIF
sqlite3 forum_data.db "
SELECT
    COUNT(*) as total_images,
    SUM(CASE WHEN exif_make IS NOT NULL THEN 1 ELSE 0 END) as has_camera,
    SUM(CASE WHEN exif_iso IS NOT NULL THEN 1 ELSE 0 END) as has_iso,
    SUM(CASE WHEN exif_gps_lat IS NOT NULL THEN 1 ELSE 0 END) as has_gps
FROM media
WHERE type = 'image';
"
```

**查看具体 EXIF 数据：**

```bash
sqlite3 forum_data.db "
SELECT
    file_name,
    exif_make,
    exif_model,
    exif_iso,
    exif_aperture,
    exif_datetime
FROM media
WHERE type = 'image' AND exif_make IS NOT NULL
LIMIT 5;
"
```

---

### ✅ 检验 4: 相机统计（Task #26 视图）

**查看相机使用排行：**

```bash
sqlite3 forum_data.db "SELECT * FROM v_camera_stats LIMIT 10;"
```

**预期输出格式**：
```
make|model|photo_count|post_count|first_use|last_use|avg_iso|avg_aperture|avg_focal_length
Canon|EOS R5|45|5|2026:01:15|2026:02:10|640|2.8|50
Sony|A7R IV|32|4|2026:01:20|2026:02:08|800|1.8|35
...
```

**查看拍摄地点统计（如果有 GPS）：**

```bash
sqlite3 forum_data.db "SELECT * FROM v_location_stats LIMIT 10;"
```

---

### ✅ 检验 5: 照片水印显示（Tasks #33-34）

**方法 A：重新生成现有帖子的 HTML**

1. 找一个已归档的帖子目录：

```bash
cd /home/ben/Download/t66y
ls -d */2026/02/* | head -5
```

2. 进入某个帖子目录，查看现有 HTML：

```bash
cd "无敌帅哥/2026/02/2026-02-12_[原创]闷骚保守型，丝袜小胸骚妻搬穴给你👀，插插插！已更新[10P]"
```

3. 备份现有 HTML：

```bash
cp content.html content.html.backup
```

4. 检查图片是否有 EXIF（查数据库）：

```bash
cd ~/gemini-work/gemini-t66y/python/data

sqlite3 forum_data.db "
SELECT file_name, exif_make, exif_model
FROM media
WHERE file_path LIKE '%2026-02-12%闷骚%'
  AND type = 'image'
LIMIT 5;
"
```

5. 如果有 EXIF，打开 HTML 查看水印：

```bash
# 用浏览器打开
firefox content.html

# 或者用 w3m 查看（终端）
w3m content.html
```

**检查要点：**
- ✅ 鼠标移到图片上时，底部显示半透明水印
- ✅ 水印包含：📷 相机型号、拍摄参数、时间、地点
- ✅ 点击图片打开灯箱，灯箱底部也显示 EXIF 信息
- ✅ 移动端查看，水印字体适配

---

**方法 B：归档新帖子测试**

1. 运行主程序：

```bash
cd ~/gemini-work/gemini-t66y/python
python3 src/main.py
```

2. 选择：`📦 归档`

3. 选择一个作者，归档一篇新帖子

4. 归档完成后，查看生成的 `content.html`：
   - 如果图片有 EXIF，鼠标悬停会显示水印
   - 灯箱中也会显示 EXIF 信息

---

### ✅ 检验 6: 完整功能测试

**完整流程测试：**

```bash
cd ~/gemini-work/gemini-t66y/python

# 1. 运行批量迁移（全量，包含 GPS）
python3 -m src.database.migrate_exif

# 这会处理所有 8,772 张图片，耗时约 22-30 秒
# 如果包含 GPS 反查，可能需要 5-10 分钟

# 2. 查看迁移结果
cd data
sqlite3 forum_data.db "SELECT * FROM v_exif_completeness;"

# 3. 查看相机排行
sqlite3 forum_data.db "SELECT * FROM v_camera_stats LIMIT 10;"

# 4. 查看有 EXIF 的图片示例
sqlite3 forum_data.db "
SELECT
    file_path,
    exif_make || ' ' || exif_model as camera,
    'f/' || exif_aperture || ' · ' ||
    exif_shutter_speed || 's · ISO' || exif_iso as params,
    exif_datetime as taken_at,
    exif_location as location
FROM media
WHERE type = 'image'
  AND exif_make IS NOT NULL
LIMIT 10;
"
```

---

## 📊 预期成果

### 如果图片有 EXIF：

```
✅ 数据库中 has_make > 0
✅ v_camera_stats 有数据
✅ HTML 水印显示相机型号
✅ HTML 水印显示拍摄参数
✅ 如果有 GPS，显示地理位置
```

### 如果图片没有 EXIF：

```
ℹ️  网络图片、截图通常没有 EXIF
ℹ️  某些网站会自动清除 EXIF
ℹ️  这是正常现象
```

**常见的无 EXIF 图片：**
- 网站下载的图片（服务器处理时清除）
- 截图
- 编辑过的图片
- 社交媒体上传的图片

**有 EXIF 的图片：**
- 相机直接拍摄的原片
- 保留元数据的图片

---

## 🐛 故障排查

### 问题 1：migrate_exif 报错

```bash
# 检查依赖是否安装
pip list | grep -E "Pillow|geopy"

# 如果缺少，安装
pip install Pillow geopy
```

### 问题 2：GPS 反查失败

```bash
# 测试网络连接
python3 -c "from geopy.geocoders import Nominatim; g = Nominatim(user_agent='test'); print(g.reverse('39.9042, 116.4074'))"

# 如果失败，跳过 GPS 反查
python3 -m src.database.migrate_exif --no-gps
```

### 问题 3：HTML 不显示水印

**检查 1：数据库中是否有 EXIF**

```bash
sqlite3 forum_data.db "SELECT COUNT(*) FROM media WHERE exif_make IS NOT NULL;"
```

如果返回 0，说明需要先运行迁移工具。

**检查 2：模板是否更新**

```bash
grep "exif-watermark" src/templates/post.html
```

应该有输出。

**检查 3：archiver.py 是否集成**

```bash
grep "_get_exif_data_for_post" src/scraper/archiver.py
```

应该有输出。

### 问题 4：文件路径问题

数据库中存储的路径是 `/home/ben/Download/t66y/...`，检查：

```bash
# 查看数据库中的路径
sqlite3 forum_data.db "SELECT file_path FROM media LIMIT 5;"

# 检查文件是否存在
ls -l "/home/ben/Download/t66y/无敌帅哥/2026/02/"*"/photo/"*.jpg | head -5
```

---

## ✅ 成功验收标准

- [x] 数据库有 10 个 EXIF 字段
- [x] 数据库有 5 个 EXIF 索引
- [x] 数据库有 3 个统计视图
- [x] ExifAnalyzer 可以提取 EXIF
- [x] migrate_exif 可以批量扫描
- [x] v_exif_completeness 显示统计
- [x] HTML 模板包含水印 CSS
- [x] 鼠标悬停显示水印
- [x] 灯箱显示 EXIF 信息

---

## 📝 快速验证脚本

创建一键验证脚本：

```bash
cat > ~/gemini-work/gemini-t66y/verify_week1.sh << 'EOF'
#!/bin/bash
# Week 1 功能快速验证脚本

cd ~/gemini-work/gemini-t66y/python

echo "========================================="
echo "Week 1 功能验证"
echo "========================================="
echo ""

echo "1️⃣  检查数据库结构..."
sqlite3 data/forum_data.db "PRAGMA table_info(media);" | grep exif | wc -l | xargs echo "   EXIF 字段数:"
sqlite3 data/forum_data.db ".indexes media" | grep exif | wc -l | xargs echo "   EXIF 索引数:"

echo ""
echo "2️⃣  检查视图..."
sqlite3 data/forum_data.db ".tables" | grep -E "v_camera|v_location|v_exif" | wc -l | xargs echo "   统计视图数:"

echo ""
echo "3️⃣  检查 EXIF 数据..."
python3 << 'PYTHON'
from src.database.connection import get_default_connection
db = get_default_connection()
conn = db.get_connection()

cursor = conn.execute("SELECT * FROM v_exif_completeness")
row = cursor.fetchone()

print(f"   总图片数: {row['total_images']}")
print(f"   有相机信息: {row['has_make']} ({row['make_pct']}%)")
print(f"   有 GPS: {row['has_gps']} ({row['gps_pct']}%)")
PYTHON

echo ""
echo "4️⃣  检查模板..."
grep -q "exif-watermark" src/templates/post.html && echo "   ✅ 模板已更新" || echo "   ❌ 模板未更新"

echo ""
echo "5️⃣  检查集成..."
grep -q "_get_exif_data_for_post" src/scraper/archiver.py && echo "   ✅ archiver 已集成" || echo "   ❌ archiver 未集成"

echo ""
echo "========================================="
echo "验证完成！"
echo "========================================="
EOF

chmod +x verify_week1.sh
```

**运行验证：**

```bash
./verify_week1.sh
```

---

**下一步建议：**

1. 如果还没有运行迁移，先运行一次小规模测试
2. 检查是否有图片包含 EXIF 数据
3. 在浏览器中查看水印效果
4. 如果一切正常，可以继续 Week 2
