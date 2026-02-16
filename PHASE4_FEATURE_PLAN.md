# Phase 4 功能规划：数据分析 + 可视化

**文档版本**: v1.0
**创建日期**: 2026-02-14
**预计工期**: 2-3 周
**优先级**: P1（核心功能）
**前置依赖**: Phase 3 完成 ✅

---

## 📑 目录

1. [功能总览](#1-功能总览)
2. [功能分类详解](#2-功能分类详解)
3. [技术栈](#3-技术栈)
4. [实施优先级](#4-实施优先级)
5. [数据库扩展](#5-数据库扩展)
6. [模块架构](#6-模块架构)
7. [实施步骤](#7-实施步骤)
8. [工作量估算](#8-工作量估算)
9. [风险评估](#9-风险评估)
10. [验收标准](#10-验收标准)

---

## 1. 功能总览

Phase 4 的核心目标是将 Phase 3 采集的数据转化为有价值的洞察和可视化报告，包括：

### 核心功能模块（6 个）

| 模块 | 功能 | 优先级 | 工作量 |
|------|------|--------|--------|
| **A. 图片元数据分析** | EXIF 提取、水印显示、GPS 分析 | P0（必做） | 3-4 天 ✅ |
| **B. 文本分析** | 词云生成、关键词提取、内容分析 | P1（必做） | 2-3 天 |
| **C. 时间分析** | 趋势图、热力图、活跃度分析 | P1（必做） | 2-3 天 |
| **D. 可视化增强** | 图表美化、交互式展示 | P1（必做） | 2 天 |
| **E. 报告生成** | HTML 报告、PDF 导出（可选） | P2（推荐） | 2 天 |
| **F. 相机使用分析** | 相机作者关联、使用时间线、统计报告 | P1（必做） | 1-2 天 |

**总工作量**: 13-18 天（3 周）

---

## 2. 功能分类详解

### A. 图片元数据分析 ⭐ 新增（用户需求）

**功能描述**：提取和分析图片的 EXIF 元数据，增强内容展示

#### A.1 EXIF 数据提取（必做）

**采集字段**：
- 📷 **相机信息**
  - `exif_make`: 相机品牌（Canon/Nikon/Sony/Apple 等）
  - `exif_model`: 相机型号（EOS R5/iPhone 14 Pro 等）

- 📅 **拍摄时间**
  - `exif_datetime`: 拍摄日期时间（2026-02-14 14:30:00）
  - 用于分析拍摄时间分布

- 📸 **拍摄参数**
  - `exif_iso`: ISO 感光度（100/400/800 等）
  - `exif_aperture`: 光圈值（f/1.8, f/2.8 等）
  - `exif_shutter_speed`: 快门速度（1/1000s 等）
  - `exif_focal_length`: 焦距（24mm/50mm/85mm 等）

**实现方式**：
```python
from PIL import Image
from PIL.ExifTags import TAGS

def extract_exif(image_path):
    """提取图片 EXIF 元数据"""
    img = Image.open(image_path)
    exif_data = img.getexif()

    result = {}
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        result[tag_name] = value

    return result
```

**集成点**：
1. **下载时提取**：`downloader.py` - 下载后立即提取
2. **历史扫描**：`migrate.py` - 扫描已有图片提取 EXIF
3. **数据库存储**：扩展 `media` 表字段

#### A.2 GPS 位置分析（推荐做）

**采集字段**：
- 📍 **GPS 坐标**
  - `exif_gps_lat`: 纬度（39.9042）
  - `exif_gps_lng`: 经度（116.4074）

- 🗺️ **地理位置**
  - `exif_location`: 地名（北京市朝阳区）
  - 使用 `geopy` 库反查坐标

**应用场景**：
1. 拍摄地点统计（最常拍摄的城市/地区）
2. 地图可视化（在地图上显示拍摄位置）
3. 旅行轨迹分析（如果是旅拍）

**技术方案**：
```python
from geopy.geocoders import Nominatim

def reverse_geocode(lat, lng):
    """GPS 坐标反查地理位置"""
    geolocator = Nominatim(user_agent="t66y-archiver")
    location = geolocator.reverse(f"{lat}, {lng}")
    return location.address
```

#### A.3 照片水印显示（必做）

**功能描述**：在归档页面显示照片元数据，类似手机照片水印

**显示方案 A**：图片下方信息栏（推荐）
```html
<div class="photo-info">
  <span class="camera">📷 Canon EOS R5</span>
  <span class="datetime">📅 2026-02-14 14:30</span>
  <span class="location">📍 北京市朝阳区</span>
  <span class="params">ISO 400 · f/2.8 · 1/1000s · 50mm</span>
</div>
```

**显示方案 B**：图片右下角悬浮水印
```html
<div class="photo-watermark">
  Canon EOS R5 | 2026-02-14 14:30
</div>
```

**CSS 样式参考**：
- 半透明背景（`background: rgba(0,0,0,0.6)`）
- 小图标 + 文字
- 响应式设计（手机友好）
- 可点击展开详情

**集成点**：修改 `archiver.py` 的 HTML 生成逻辑

#### A.4 相机统计分析（可选）

**统计维度**：
1. **最常用相机排行**
   - Top 5 相机型号
   - 按图片数量排序

2. **拍摄参数偏好**
   - ISO 分布（低感光/高感光）
   - 光圈分布（大光圈/小光圈）
   - 焦距分布（广角/标准/长焦）

3. **拍摄时间模式**
   - 清晨/白天/黄昏/夜晚分布
   - 结合 EXIF 时间戳分析

**可视化**：
- 饼图：相机型号占比
- 柱状图：拍摄参数分布
- 时间轴：拍摄时间分布

---

### B. 文本分析（原有规划）

**功能描述**：分析帖子标题和内容，生成词云和关键词

#### B.1 词云生成（必做）

**功能**：
1. **中文分词**
   - 使用 `jieba` 库
   - 加载停用词表（过滤"的"、"是"等）

2. **词频统计**
   - 统计高频词汇
   - 按频率排序

3. **词云图生成**
   - 使用 `wordcloud` 库
   - 支持中文字体
   - 自定义颜色方案

**生成维度**：
- 单个作者词云
- 多作者对比词云
- 全局词云（所有帖子）
- 时间段词云（如 2026 年 1 月）

**技术方案**：
```python
import jieba
from wordcloud import WordCloud

def generate_wordcloud(text, output_path):
    """生成词云图"""
    # 中文分词
    words = jieba.cut(text)
    words_filtered = [w for w in words if len(w) > 1 and w not in stopwords]

    # 生成词云
    wordcloud = WordCloud(
        font_path='simhei.ttf',  # 中文字体
        width=1920,
        height=1080,
        background_color='white'
    ).generate(' '.join(words_filtered))

    wordcloud.to_file(output_path)
```

#### B.2 关键词提取（可选）

**功能**：
- 提取帖子关键词（TF-IDF 算法）
- 分析作者常用词汇
- 发现热门话题

**应用**：
- 在统计页面显示"热门关键词"
- 标签云展示
- 内容分类

#### B.3 内容长度分析（可选）

**统计**：
- 平均帖子长度
- 图文比例
- 内容丰富度

---

### C. 时间分析（原有规划）

**功能描述**：分析发帖时间规律，生成趋势图和热力图

#### C.1 发帖趋势分析（必做）

**分析维度**：
1. **月度趋势**
   - 每月发帖数量
   - 折线图展示

2. **年度趋势**
   - 每年发帖数量
   - 柱状图展示

3. **增长率分析**
   - 计算环比增长
   - 预测未来趋势

**可视化**：
```python
import matplotlib.pyplot as plt

def plot_monthly_trend(data):
    """绘制月度趋势图"""
    plt.figure(figsize=(12, 6))
    plt.plot(data['months'], data['post_counts'], marker='o')
    plt.title('发帖月度趋势', fontproperties=font)
    plt.xlabel('月份', fontproperties=font)
    plt.ylabel('帖子数', fontproperties=font)
    plt.savefig('monthly_trend.png', dpi=300)
```

#### C.2 时间分布热力图（必做）

**功能**：
- **小时 x 星期 热力图**
  - 横轴：0-23 小时
  - 纵轴：周一至周日
  - 颜色深度：帖子数量

- **发现活跃时段**
  - 最活跃的时间段
  - 最活跃的星期

**数据来源**：
- Phase 3 已准备好 `publish_hour` 和 `publish_weekday` 字段
- 直接查询数据库即可

**可视化**：
```python
import seaborn as sns

def plot_time_heatmap(data):
    """绘制时间热力图"""
    pivot = data.pivot(index='weekday', columns='hour', values='count')

    plt.figure(figsize=(14, 6))
    sns.heatmap(pivot, cmap='YlOrRd', annot=True, fmt='d')
    plt.title('发帖时间热力图', fontproperties=font)
    plt.savefig('time_heatmap.png', dpi=300)
```

#### C.3 活跃度分析（推荐）

**指标**：
- 最活跃作者（按发帖频率）
- 活跃时段识别（工作日 vs 周末）
- 发帖规律发现（是否有周期性）

---

### D. 可视化增强（原有规划）

**功能描述**：美化图表，提升可视化质量

#### D.1 图表美化（必做）

**优化项**：
1. **中文字体配置**
   - 使用 SimHei（黑体）或 微软雅黑
   - 解决中文乱码问题

2. **配色方案**
   - 统一色彩风格
   - 支持深色/浅色主题

3. **高清输出**
   - DPI 300+
   - 适配打印

**技术方案**：
```python
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False
```

#### D.2 图表类型（必做）

支持的图表类型：
- 📊 柱状图（Bar Chart）- 作者排行、月度统计
- 📈 折线图（Line Chart）- 趋势分析
- 🥧 饼图（Pie Chart）- 占比分析
- 🌡️ 热力图（Heatmap）- 时间分布
- 📉 散点图（Scatter Plot）- 相关性分析（可选）

#### D.3 交互式图表（可选，Phase 4.5）

**技术栈**：
- `plotly` 库（交互式图表）
- 支持缩放、悬停显示
- 导出为 HTML

**优势**：
- 更好的用户体验
- 可以嵌入网页

**权衡**：
- 增加依赖
- 文件体积较大

**建议**：Phase 4 先用 matplotlib，Phase 4.5 可选升级

---

### E. 报告生成（原有规划）

**功能描述**：自动生成分析报告，支持 HTML 和 Markdown

#### E.1 HTML 报告（必做）

**报告内容**：
1. **概览页**
   - 全局统计数据
   - 关键指标卡片

2. **作者分析页**
   - 每个作者的详细分析
   - 词云、趋势图、时间分布
   - 相机使用统计（新增）

3. **时间分析页**
   - 月度趋势图
   - 时间热力图
   - 活跃度分析

4. **图片分析页**（新增）
   - 相机型号统计
   - 拍摄地点分布
   - 拍摄参数偏好

**技术方案**：
```python
from jinja2 import Template

def generate_html_report(data):
    """生成 HTML 报告"""
    template = Template(html_template)
    html = template.render(
        stats=data['stats'],
        charts=data['charts'],
        authors=data['authors']
    )

    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html)
```

**报告样式**：
- 响应式设计（手机/平板/电脑适配）
- 图表嵌入（base64 或外部文件）
- 打印友好

#### E.2 Markdown 报告（可选）

**用途**：
- 简洁的文本报告
- 易于分享和版本控制
- 可转为 PDF（使用 pandoc）

**格式**：
```markdown
# 论坛归档分析报告

## 1. 全局统计
- 关注作者: 9 位
- 归档帖子: 350 篇
- 总图片: 1,000 张

## 2. 作者排行
1. 独醉笑清风: 80 篇
2. 清风皓月: 77 篇
...

## 3. 词云
![词云图](wordcloud.png)
```

#### E.3 PDF 导出（可选，低优先级）

**技术方案**：
- HTML → PDF（使用 `weasyprint` 或 `pdfkit`）
- Markdown → PDF（使用 `pandoc`）

**权衡**：
- 增加复杂度
- 依赖外部工具

**建议**：Phase 5 再考虑

---

### F. 相机使用分析 ⭐ 新增（用户需求，2026-02-16）

**功能描述**：统计相机型号被哪些作者使用，在哪些日期的帖子中使用，提供多维度相机使用分析

#### F.1 数据基础

**数据来源**：
- Phase 4 Week 1 已实现的 EXIF 提取功能 ✅
- `media` 表包含 10 个 EXIF 字段（make, model, datetime 等）
- 已有索引优化（idx_media_exif_make/model）

**三表关联**：
```sql
media (exif_make, exif_model, post_id)
  → posts (author_id, publish_date)
    → authors (name)
```

#### F.2 核心查询功能（必做）

##### F.2.1 相机 → 作者使用查询

**功能**：查询指定相机型号被哪些作者使用

**输入**：
- 相机制造商（如 vivo）
- 相机型号（如 X Fold3 Pro）

**输出**：
```
相机型号: vivo X Fold3 Pro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
┃ 作者   ┃照片数┃帖子数┃首次使用 ┃最后使用 ┃
┡━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
│同花顺心 │ 300 │  20  │2024-01  │2024-12  │
│cyruscc │ 100 │   8  │2024-03  │2024-11  │
└────────┴─────┴──────┴─────────┴─────────┘

EXIF 统计: ISO 400 | 光圈 f/2.2 | 焦距 50mm
```

**实现方式**：
- 创建视图 `v_camera_author_usage`
- 查询函数 `get_camera_usage_by_authors()`

##### F.2.2 作者 → 相机使用查询

**功能**：查询指定作者使用了哪些相机型号

**输入**：作者名称（如 同花顺心）

**输出**：
```
作者: 同花顺心
使用了 3 种相机，共 450 张照片

┏━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━━━┓
┃ 相机型号        ┃照片数┃ 占比 ┃使用期间 ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━━━┩
│vivo X Fold3 Pro │ 300 │66.7%│2024-01至今│
│Canon EOS 5D     │ 100 │22.2%│2024-03-06│
└─────────────────┴─────┴──────┴─────────┘
```

**实现方式**：
- 创建视图 `v_author_camera_summary`
- 查询函数 `get_author_camera_usage()`

##### F.2.3 相机使用时间线

**功能**：查询相机型号在不同日期的使用情况

**输入**：
- 相机制造商 + 型号
- 可选：年份/月份过滤

**输出**：
```
相机: vivo X Fold3 Pro | 时间: 2024年
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2024-12 ████████████████ 60张 (同花顺心)
2024-11 ████████████     45张 (同花顺心, cyruscc)
2024-10 ████████         30张 (cyruscc)
...

总计: 450张照片 | 30篇帖子 | 3位作者
```

**实现方式**：
- 创建视图 `v_camera_daily_usage`
- 查询函数 `get_camera_usage_timeline()`

##### F.2.4 相机型号排行

**功能**：显示所有相机型号的使用统计排行

**输出**：
```
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━┓
┃ 相机型号          ┃照片数┃帖子数┃ 作者数 ┃首次使用  ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━┩
│vivo X Fold3 Pro   │ 450 │  30  │   3   │2024-01   │
│Canon EOS 5D       │ 320 │  25  │   2   │2024-02   │
│iPhone 15 Pro      │ 280 │  18  │   4   │2024-03   │
└───────────────────┴─────┴──────┴───────┴──────────┘
```

**实现方式**：
- 扩展现有视图 `v_camera_stats`
- 查询函数 `get_camera_ranking()`

#### F.3 数据库设计（必做）

##### 新增视图（3 个）

**视图 1: v_camera_author_usage**
```sql
CREATE VIEW v_camera_author_usage AS
SELECT
    m.exif_make, m.exif_model,
    a.id as author_id, a.name as author_name,
    COUNT(DISTINCT m.id) as photo_count,
    COUNT(DISTINCT p.id) as post_count,
    MIN(p.publish_date) as first_use_date,
    MAX(p.publish_date) as last_use_date,
    ROUND(AVG(m.exif_iso), 0) as avg_iso,
    ROUND(AVG(m.exif_aperture), 1) as avg_aperture
FROM media m
JOIN posts p ON m.post_id = p.id
JOIN authors a ON p.author_id = a.id
WHERE m.type = 'image'
  AND m.exif_make IS NOT NULL
  AND m.exif_model IS NOT NULL
GROUP BY m.exif_make, m.exif_model, a.id;
```

**视图 2: v_camera_daily_usage**
```sql
CREATE VIEW v_camera_daily_usage AS
SELECT
    m.exif_make, m.exif_model,
    DATE(p.publish_date) as date,
    p.publish_year, p.publish_month,
    COUNT(DISTINCT m.id) as photo_count,
    COUNT(DISTINCT p.id) as post_count,
    GROUP_CONCAT(DISTINCT a.name) as authors
FROM media m
JOIN posts p ON m.post_id = p.id
JOIN authors a ON p.author_id = a.id
WHERE m.type = 'image'
  AND m.exif_make IS NOT NULL
  AND m.exif_model IS NOT NULL
GROUP BY m.exif_make, m.exif_model, DATE(p.publish_date);
```

**视图 3: v_author_camera_summary**
```sql
CREATE VIEW v_author_camera_summary AS
SELECT
    a.id as author_id, a.name as author_name,
    COUNT(DISTINCT m.exif_make || '-' || m.exif_model) as camera_count,
    GROUP_CONCAT(DISTINCT m.exif_make || ' ' || m.exif_model) as camera_list,
    COUNT(DISTINCT m.id) as total_photos
FROM authors a
JOIN posts p ON a.id = p.author_id
JOIN media m ON p.id = m.post_id
WHERE m.type = 'image' AND m.exif_make IS NOT NULL
GROUP BY a.id;
```

##### 查询函数（3 个）

**函数 1**: `get_camera_usage_by_authors(camera_make, camera_model, ...)`
- 参数：相机制造商、型号、作者名（可选）、限制数量
- 返回：作者使用统计列表

**函数 2**: `get_camera_usage_timeline(camera_make, camera_model, ...)`
- 参数：相机制造商、型号、年份（可选）、月份（可选）
- 返回：时间线数据列表

**函数 3**: `get_author_camera_usage(author_name)`
- 参数：作者名称
- 返回：包含相机列表和统计的字典

#### F.4 菜单界面（必做）

**菜单位置**：主菜单 → 查看统计 → 相机使用分析

**子菜单结构**：
```
📷 相机使用分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 查看所有相机型号排行
  2. 查询相机被哪些作者使用
  3. 查询作者使用了哪些相机
  4. 查看相机使用时间线
  0. 返回上级菜单
```

**交互流程**：
1. 用户选择功能类型
2. 输入查询参数（相机型号或作者名）
3. 显示 Rich Table 格式化结果
4. 可选：生成图表（时间线图）

#### F.5 性能考虑

**查询性能**（预估，基于 1000 张图片）：
- 相机排行：<50ms（已有索引）
- 相机→作者：<100ms（3表 JOIN）
- 作者→相机：<80ms（外键优化）
- 时间线：<100ms（日期聚合）

**优化措施**：
- 已有索引：`idx_media_exif_make`, `idx_media_exif_model`
- 视图缓存：可选物化视图（如查询慢）
- 结果缓存：使用 `@lru_cache` 装饰器

#### F.6 技术方案选择

**推荐方案**：视图 + 查询函数混合

**优点**：
- 视图：性能好、代码简洁
- 函数：灵活、支持动态过滤
- 混合：兼顾性能和灵活性

**不推荐**：
- 纯动态查询：每次都 JOIN，性能较差
- 纯视图：缺乏灵活性，需要多个视图

#### F.7 实施优先级

**高优先级（必做）**：
1. 创建 3 个数据库视图
2. 实现 3 个查询函数
3. 创建相机使用菜单
4. Rich Table 显示

**中优先级（推荐）**：
5. 时间线图表（matplotlib）
6. 相机作者饼图

**低优先级（可选）**：
7. 相机使用报告（HTML）
8. 导出功能（CSV/Excel）

#### F.8 测试要求

**单元测试**：
- `test_get_camera_usage_by_authors()` - 查询正确性
- `test_get_camera_usage_timeline()` - 时间线数据
- `test_get_author_camera_usage()` - 作者相机统计

**集成测试**：
- `test_camera_usage_menu()` - 菜单交互流程

**性能测试**：
- 查询响应时间 <200ms（1000+ 照片数据集）

#### F.9 工作量估算

| 任务 | 工作量 | 描述 |
|------|--------|------|
| 创建 3 个视图 | 0.5 天 | SQL 编写 + 测试 |
| 实现 3 个查询函数 | 1 天 | Python 函数 + 单元测试 |
| 创建菜单界面 | 0.5 天 | Rich Table 显示 |
| 集成测试 | 0.25 天 | 菜单流程测试 |
| 文档更新 | 0.25 天 | 用户指南 + API 文档 |

**总计**: 2.5 天（约 2 个工作日）

#### F.10 验收标准

**功能验收**：
- ✅ 能查询相机被哪些作者使用
- ✅ 能查询作者使用了哪些相机
- ✅ 能查看相机使用时间线
- ✅ 显示准确的统计数据
- ✅ Rich Table 格式美观

**性能验收**：
- ✅ 查询响应时间 <200ms
- ✅ 支持 1000+ 照片数据集

**用户体验验收**：
- ✅ 菜单交互流畅
- ✅ 数据易于理解
- ✅ 错误提示友好

---

## 3. 技术栈

### 核心依赖

| 库名 | 用途 | 优先级 | 版本 |
|------|------|--------|------|
| **Pillow** | 图片处理、EXIF 提取 | P0 | 10.0+ |
| **jieba** | 中文分词 | P1 | 0.42+ |
| **wordcloud** | 词云生成 | P1 | 1.9+ |
| **matplotlib** | 图表绘制 | P1 | 3.7+ |
| **seaborn** | 高级可视化（热力图） | P1 | 0.12+ |
| **pandas** | 数据处理 | P1 | 2.0+ |
| **jinja2** | HTML 模板 | P1 | 3.1+ |
| **geopy** | GPS 反查 | P2 | 2.3+ |
| **plotly** | 交互式图表（可选） | P3 | 5.17+ |

### 字体依赖

**中文字体**（必需）：
- Linux: `apt install fonts-wqy-zenhei` 或 `fonts-noto-cjk`
- macOS: 系统自带黑体
- Windows: 系统自带微软雅黑

**配置文件** (`requirements.txt` 更新)：
```
# Phase 4: 数据分析 + 可视化
Pillow>=10.0.0
jieba>=0.42.0
wordcloud>=1.9.0
matplotlib>=3.7.0
seaborn>=0.12.0
pandas>=2.0.0
jinja2>=3.1.0
geopy>=2.3.0

# 可选依赖
# plotly>=5.17.0  # 交互式图表
```

---

## 4. 实施优先级

### 优先级分级

**P0 - 必须立即做（核心功能）**：
1. ✅ A.1 EXIF 数据提取（3 天）
2. ✅ A.3 照片水印显示（1 天）
3. ✅ B.1 词云生成（2 天）
4. ✅ C.1 发帖趋势分析（2 天）
5. ✅ C.2 时间分布热力图（1 天）
6. ✅ D.1 图表美化（1 天）
7. ✅ E.1 HTML 报告（2 天）

**小计**: 12 天（2.4 周）

---

**P1 - 强烈推荐做（增强功能）**：
1. 🔸 A.2 GPS 位置分析（1 天）
2. 🔸 A.4 相机统计分析（1 天）
3. 🔸 C.3 活跃度分析（1 天）

**小计**: 3 天

---

**P2 - 可选做（锦上添花）**：
1. 🔹 B.2 关键词提取（1 天）
2. 🔹 B.3 内容长度分析（0.5 天）
3. 🔹 E.2 Markdown 报告（0.5 天）

**小计**: 2 天

---

**P3 - 暂不做（Phase 4.5 或 Phase 5）**：
1. ⚪ D.3 交互式图表（plotly）
2. ⚪ E.3 PDF 导出

---

### 推荐实施方案

**方案 A - 完整版（推荐）**：P0 + P1 = 15 天（3 周）
- 包含所有核心功能
- GPS 分析和相机统计
- 最完整的用户体验

**方案 B - 精简版**：P0 = 12 天（2.4 周）
- 只做核心功能
- 快速上线

**方案 C - 豪华版**：P0 + P1 + P2 = 17 天（3.4 周）
- 包含所有推荐功能
- 最全面的分析能力

**建议**：选择**方案 A（完整版）**，平衡功能与工期

---

## 5. 数据库扩展

### 扩展 `media` 表（必做）

**新增字段（10 个）**：

```sql
-- EXIF 基础信息
ALTER TABLE media ADD COLUMN exif_make TEXT;           -- 相机品牌
ALTER TABLE media ADD COLUMN exif_model TEXT;          -- 相机型号
ALTER TABLE media ADD COLUMN exif_datetime TEXT;       -- 拍摄时间

-- EXIF 拍摄参数
ALTER TABLE media ADD COLUMN exif_iso INTEGER;         -- ISO
ALTER TABLE media ADD COLUMN exif_aperture REAL;       -- 光圈
ALTER TABLE media ADD COLUMN exif_shutter_speed TEXT;  -- 快门速度
ALTER TABLE media ADD COLUMN exif_focal_length REAL;   -- 焦距

-- GPS 信息
ALTER TABLE media ADD COLUMN exif_gps_lat REAL;        -- GPS 纬度
ALTER TABLE media ADD COLUMN exif_gps_lng REAL;        -- GPS 经度
ALTER TABLE media ADD COLUMN exif_location TEXT;       -- 地理位置

-- 创建索引（优化查询）
CREATE INDEX idx_media_exif_make ON media(exif_make);
CREATE INDEX idx_media_exif_model ON media(exif_model);
CREATE INDEX idx_media_exif_datetime ON media(exif_datetime);
```

**数据迁移**：
- 扫描已有图片提取 EXIF
- 使用 `migrate.py` 批量处理
- 进度条显示

---

## 6. 模块架构

### 新增模块结构

```
python/src/
├── analysis/                    # 新增：分析模块
│   ├── __init__.py
│   ├── exif_analyzer.py        # EXIF 分析器（新增）
│   ├── text_analyzer.py        # 文本分析器
│   ├── time_analyzer.py        # 时间分析器
│   ├── visualizer.py           # 可视化器
│   └── report_generator.py     # 报告生成器
│
├── database/                    # 扩展：数据库模块
│   ├── schema_v2.sql           # Schema 扩展脚本
│   └── migrate_exif.py         # EXIF 数据迁移脚本
│
└── utils/                       # 扩展：工具模块
    └── exif_utils.py           # EXIF 工具函数
```

### 模块职责

#### `exif_analyzer.py`（新增）
```python
class ExifAnalyzer:
    """EXIF 数据分析器"""

    def extract_exif(self, image_path: str) -> dict:
        """提取 EXIF 数据"""

    def reverse_geocode(self, lat: float, lng: float) -> str:
        """GPS 反查地理位置"""

    def analyze_camera_usage(self) -> dict:
        """统计相机使用情况"""

    def analyze_shooting_params(self) -> dict:
        """分析拍摄参数分布"""
```

#### `text_analyzer.py`
```python
class TextAnalyzer:
    """文本分析器"""

    def generate_wordcloud(self, author_name: str = None) -> str:
        """生成词云图"""

    def extract_keywords(self, text: str, top_n: int = 10) -> list:
        """提取关键词"""

    def analyze_content_length(self) -> dict:
        """分析内容长度"""
```

#### `time_analyzer.py`
```python
class TimeAnalyzer:
    """时间分析器"""

    def plot_monthly_trend(self, author_name: str = None) -> str:
        """绘制月度趋势图"""

    def plot_time_heatmap(self, author_name: str = None) -> str:
        """绘制时间热力图"""

    def analyze_active_patterns(self) -> dict:
        """分析活跃模式"""
```

#### `visualizer.py`
```python
class Visualizer:
    """可视化器"""

    def setup_chinese_font(self):
        """配置中文字体"""

    def plot_bar_chart(self, data: dict, title: str) -> str:
        """绘制柱状图"""

    def plot_pie_chart(self, data: dict, title: str) -> str:
        """绘制饼图"""

    def plot_heatmap(self, data: pd.DataFrame, title: str) -> str:
        """绘制热力图"""
```

#### `report_generator.py`
```python
class ReportGenerator:
    """报告生成器"""

    def generate_html_report(self, output_path: str):
        """生成 HTML 报告"""

    def generate_markdown_report(self, output_path: str):
        """生成 Markdown 报告"""

    def render_template(self, template_name: str, data: dict) -> str:
        """渲染模板"""
```

---

## 7. 实施步骤

### 建议分阶段实施（3 周计划）

#### Week 1: 图片元数据 + 数据库扩展（5 天）

**Day 1-2**: EXIF 提取与数据库扩展
- [ ] 扩展 `media` 表 schema
- [ ] 实现 `exif_analyzer.py` - EXIF 提取
- [ ] 修改 `downloader.py` - 下载时提取 EXIF
- [ ] 单元测试

**Day 3**: 历史数据 EXIF 扫描
- [ ] 实现 `migrate_exif.py` - 批量扫描
- [ ] 进度条显示
- [ ] 错误处理和重试
- [ ] 测试（扫描已有 1,000 张图片）

**Day 4**: GPS 位置分析
- [ ] GPS 坐标提取
- [ ] geopy 反查地理位置
- [ ] 位置统计功能
- [ ] 测试

**Day 5**: 照片水印显示
- [ ] 修改 `archiver.py` - HTML 生成
- [ ] 水印 CSS 样式设计
- [ ] 响应式适配
- [ ] 测试（多种设备）

**Week 1 验收**：
- ✅ 所有图片 EXIF 数据提取完成
- ✅ 归档页面显示水印
- ✅ GPS 位置反查正常

---

#### Week 2: 文本分析 + 时间分析（5 天）

**Day 6-7**: 词云生成
- [ ] jieba 分词集成
- [ ] 停用词表加载
- [ ] 词云生成器实现
- [ ] 中文字体配置
- [ ] 多维度词云（作者/全局/时间段）
- [ ] 测试

**Day 8-9**: 时间分析
- [ ] 月度趋势图
- [ ] 时间热力图（小时 x 星期）
- [ ] 活跃度分析
- [ ] 测试

**Day 10**: 相机统计分析
- [ ] 相机型号排行
- [ ] 拍摄参数分布
- [ ] 可视化图表
- [ ] 测试

**Week 2 验收**：
- ✅ 词云生成正常，中文显示无乱码
- ✅ 时间热力图清晰美观
- ✅ 相机统计数据准确

---

#### Week 3: 可视化 + 报告生成（5 天）

**Day 11-12**: 可视化增强
- [ ] 图表美化（配色、字体、DPI）
- [ ] 统一可视化风格
- [ ] 所有图表类型实现
- [ ] 高清输出（DPI 300）
- [ ] 测试

**Day 13-14**: HTML 报告生成
- [ ] Jinja2 模板设计
- [ ] 报告数据准备
- [ ] 图表嵌入（base64 或外部）
- [ ] 响应式样式
- [ ] 测试（多浏览器）

**Day 15**: 菜单集成 + 综合测试
- [ ] 分析菜单实现
- [ ] 参数配置界面
- [ ] 报告查看功能
- [ ] 综合测试
- [ ] 文档更新

**Week 3 验收**：
- ✅ HTML 报告完整美观
- ✅ 菜单集成无 bug
- ✅ 所有功能正常工作

---

## 8. 工作量估算

### 详细任务清单（35 个任务）

| 任务 ID | 任务名称 | 工作量 | 优先级 | 依赖 |
|---------|----------|--------|--------|------|
| **A. 图片元数据分析** | | **5 天** | | |
| A.1.1 | 扩展 media 表 schema | 0.5 天 | P0 | - |
| A.1.2 | 实现 EXIF 提取器 | 1 天 | P0 | A.1.1 |
| A.1.3 | 修改 downloader.py | 0.5 天 | P0 | A.1.2 |
| A.1.4 | 历史数据 EXIF 扫描 | 1 天 | P0 | A.1.2 |
| A.2.1 | GPS 坐标提取 | 0.5 天 | P1 | A.1.2 |
| A.2.2 | geopy 反查地理位置 | 0.5 天 | P1 | A.2.1 |
| A.3.1 | 照片水印 HTML 生成 | 0.5 天 | P0 | A.1.3 |
| A.3.2 | 照片水印 CSS 样式 | 0.5 天 | P0 | A.3.1 |
| A.4.1 | 相机统计分析 | 1 天 | P1 | A.1.4 |
| **B. 文本分析** | | **3 天** | | |
| B.1.1 | jieba 分词集成 | 0.5 天 | P1 | - |
| B.1.2 | 停用词表加载 | 0.5 天 | P1 | B.1.1 |
| B.1.3 | 词频统计 | 0.5 天 | P1 | B.1.2 |
| B.1.4 | 词云生成器 | 0.5 天 | P1 | B.1.3 |
| B.1.5 | 中文字体配置 | 0.5 天 | P1 | B.1.4 |
| B.1.6 | 多维度词云 | 0.5 天 | P1 | B.1.5 |
| B.2.1 | 关键词提取 | 1 天 | P2 | B.1.3 |
| **C. 时间分析** | | **3 天** | | |
| C.1.1 | 月度趋势分析 | 0.5 天 | P0 | - |
| C.1.2 | 年度趋势分析 | 0.5 天 | P0 | C.1.1 |
| C.1.3 | 趋势图可视化 | 1 天 | P0 | C.1.2 |
| C.2.1 | 时间热力图数据准备 | 0.5 天 | P0 | - |
| C.2.2 | 时间热力图绘制 | 0.5 天 | P0 | C.2.1 |
| C.3.1 | 活跃度分析 | 1 天 | P1 | C.2.2 |
| **D. 可视化增强** | | **2 天** | | |
| D.1.1 | 中文字体全局配置 | 0.5 天 | P0 | - |
| D.1.2 | 配色方案设计 | 0.5 天 | P0 | - |
| D.1.3 | 高清输出配置 | 0.5 天 | P0 | - |
| D.2.1 | 所有图表类型实现 | 0.5 天 | P0 | D.1.1 |
| **E. 报告生成** | | **2 天** | | |
| E.1.1 | Jinja2 模板设计 | 0.5 天 | P0 | - |
| E.1.2 | 报告数据准备 | 0.5 天 | P0 | E.1.1 |
| E.1.3 | 图表嵌入 | 0.5 天 | P0 | E.1.2 |
| E.1.4 | 报告样式美化 | 0.5 天 | P0 | E.1.3 |
| **F. 集成与测试** | | **1 天** | | |
| F.1 | 菜单集成 | 0.5 天 | P0 | 所有 |
| F.2 | 综合测试 | 0.5 天 | P0 | F.1 |

**总计**：16 天（实际工作日）

**缓冲时间**：20%（3 天）

**预计总工期**：19 天 ≈ **3 周**

---

## 9. 风险评估

### 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **中文乱码问题** | 高 | 中 | 提前配置字体，多平台测试 |
| **EXIF 数据缺失** | 中 | 高 | 容错处理，部分字段可选 |
| **GPS 反查失败** | 低 | 中 | 缓存结果，失败时显示坐标 |
| **词云生成慢** | 中 | 低 | 缓存结果，异步生成 |
| **matplotlib 内存占用** | 中 | 低 | 及时释放资源，批量生成 |
| **依赖库冲突** | 高 | 低 | 锁定版本，虚拟环境隔离 |

### 进度风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **功能蔓延** | 高 | 中 | 严格按 P0/P1/P2 优先级 |
| **测试不充分** | 高 | 中 | 预留测试时间，自动化测试 |
| **文档滞后** | 中 | 高 | 边开发边写文档 |

---

## 10. 验收标准

### 功能验收

| 验收项 | 标准 | 优先级 |
|--------|------|--------|
| EXIF 提取 | 所有图片 EXIF 数据提取完整 | P0 |
| 照片水印 | 归档页面正确显示水印，样式美观 | P0 |
| GPS 反查 | 坐标反查成功率 > 90% | P1 |
| 词云生成 | 中文显示正常，无乱码 | P0 |
| 时间热力图 | 数据准确，颜色区分清晰 | P0 |
| 趋势图 | 折线清晰，标签完整 | P0 |
| HTML 报告 | 包含所有分析内容，样式美观 | P0 |
| 相机统计 | 数据准确，可视化清晰 | P1 |

### 性能验收

| 指标 | 目标 | 测试方法 |
|------|------|----------|
| EXIF 提取速度 | < 0.1s/张 | 批量提取 100 张 |
| 词云生成时间 | < 5s | 生成单作者词云 |
| 热力图生成时间 | < 2s | 生成全局热力图 |
| HTML 报告生成 | < 10s | 生成完整报告 |
| 报告文件大小 | < 10MB | 包含所有图表 |

### 质量验收

| 指标 | 目标 | 测试方法 |
|------|------|----------|
| 代码覆盖率 | > 80% | pytest --cov |
| 单元测试通过率 | 100% | pytest |
| 中文显示 | 无乱码 | 多平台测试 |
| 响应式设计 | 支持手机/平板/桌面 | 多设备测试 |

---

## 11. 后续规划（Phase 4.5 可选）

如果 Phase 4 完成后还有时间和精力，可以考虑以下增强功能：

### 4.5.1 交互式可视化
- 使用 `plotly` 替代 `matplotlib`
- 图表支持缩放、悬停、筛选
- 更好的用户体验

### 4.5.2 地图可视化
- 基于 GPS 数据生成地图
- 使用 `folium` 库
- 显示拍摄位置分布

### 4.5.3 PDF 报告导出
- HTML 转 PDF
- 打印优化
- 适合分享

### 4.5.4 数据导出功能
- 导出为 CSV/Excel
- 供其他工具分析
- 数据备份

---

## 12. 总结

### Phase 4 核心价值

1. **数据增强**：通过 EXIF 元数据，丰富图片信息
2. **深度洞察**：通过词云和趋势图，发现内容规律
3. **可视化展示**：通过精美图表，直观呈现数据
4. **报告生成**：通过 HTML 报告，一键生成分析

### 关键亮点

- 📷 **图片元数据**：相机、GPS、拍摄参数全方位分析
- 📊 **多维度分析**：文本、时间、设备三大维度
- 🎨 **高质量可视化**：配色精美、支持中文、高清输出
- 📄 **自动化报告**：一键生成，响应式设计，易于分享

### 下一步行动

1. **用户确认**：确认功能范围和优先级
2. **环境准备**：安装依赖库和中文字体
3. **开始实施**：按 3 周计划逐步实施
4. **持续测试**：边开发边测试，确保质量

---

**文档结束**

**创建时间**: 2026-02-14
**作者**: Claude Sonnet 4.5
**下一步**: 等待用户确认后开始实施
