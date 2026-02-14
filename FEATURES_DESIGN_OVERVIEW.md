# 功能设计总览

**文档版本**：v1.3
**最后更新**：2026-02-14
**文档用途**：项目所有功能的设计总入口，供AI编程实现参考

---

## 📋 文档说明

本文档列出项目的所有功能设计，每个功能都有详细的设计文档。

**目标受众**：
- AI 编程助手（Claude、GPT等）- 实施工程师
- 代码审查人员

**使用方式**：
1. 在本文档中查找需要实现的功能
2. 点击链接跳转到详细设计文档
3. 按照设计文档实施功能

---

## 🎯 功能分类

### 核心功能（已完成）

#### CF-001：作者订阅与管理
**状态**：✅ 已完成（Phase 1 & Phase 2）
**实施时间**：2026-02-11
**功能描述**：
- 添加/移除关注的作者
- 查看关注列表
- 作者信息管理

**相关文档**：
- [ADR-002 Python迁移方案](./ADR-002_Python_Migration_Plan.md)
- [Phase 2 完成报告](./python/PHASE2_COMPLETION_REPORT.md)

---

#### CF-002：帖子归档
**状态**：✅ 已完成（Phase 2）
**实施时间**：2026-02-11
**功能描述**：
- 两阶段归档流程（收集URL → 下载内容）
- 增量更新（跳过已归档帖子）
- 并发下载图片和视频
- 目录组织：`作者/年份/月份/标题/`

**相关文档**：
- [Phase 2 完成报告](./python/PHASE2_COMPLETION_REPORT.md)
- [Phase 2 问题与修复](./python/PHASE2_PROBLEMS_AND_FIXES.md)

---

### 用户体验改进（已完成）

#### UX-001：菜单导航增强
**状态**：✅ 已完成（Phase 2-B）
**实施时间**：2026-02-11
**功能描述**：
- 主菜单导航优化
- 返回功能（避免ESC键问题）
- 键盘快捷键支持
- 确认界面

**相关文档**：
- [Phase 2-B 设计](./PHASE2B_DESIGN.md)
- [Phase 2-B 完成报告](./PHASE2B_COMPLETION_REPORT.md)
- [ESC键问题解决](./ESC_KEY_RESOLUTION.md)

---

#### UX-002：作者选择增强
**状态**：✅ 已完成（2026-02-12）
**实施时间**：2026-02-12
**功能描述**：
- 多选作者界面（checkbox）
- 显示上次选择的作者（✅/⬜标记）
- 记忆上次选择
- 确认界面（支持重新选择/取消）

**相关文档**：
- [作者选择增强分析](./AUTHOR_SELECTION_ENHANCEMENT_ANALYSIS.md)
- [作者选择指示器修复](./AUTHOR_SELECTION_INDICATOR_FIX.md)
- [菜单增强记录](./MENU_ENHANCEMENT.md)

**实施提交**：
- `feat: [Mile1] 菜单交互优化与归档进度功能设计` (916cd6f)

---

### 数据显示增强（已完成）

#### DS-001：归档进度显示
**状态**：✅ 已完成（2026-02-13）
**实施时间**：2026-02-13
**功能描述**：
- 显示格式：`已归档/论坛总数 (百分比)`
- 示例：`80/120 (67%)`
- 完成标记：`120/120 (100%) ✓`
- 自动计算论坛总数（统计主题帖URL数量）

**设计决策**：
- 选择方案B：统计收集到的主题帖URL数量
- 只统计作者作为楼主的原创帖子
- 不包含作者回复别人的帖子
- 使用最大值策略（论坛帖子只增不减）

**相关文档**：
- [归档进度功能设计 V1](./ARCHIVE_PROGRESS_FEATURE_DESIGN.md)（已废弃）
- [归档进度功能设计 V2](./ARCHIVE_PROGRESS_FEATURE_DESIGN_V2.md)
- [阻塞分析与解决方案](./BLOCKING_ANALYSIS_AND_SOLUTIONS.md)
- [设计讨论总结](./DESIGN_DISCUSSION_SUMMARY.md)

**实施提交**：
- `feat: [Mile1] 实现归档进度显示功能（方案B）` (531898a)
- `fix: 添加 MainMenu 类的 logger 初始化` (22ee54f)
- `fix: 使用最大值更新论坛总数，避免显示不合理进度` (bceb079)

**核心文件**：
- `python/src/utils/display.py` - 进度格式化显示
- `python/src/scraper/archiver.py` - 统计主题帖数量
- `python/src/menu/main_menu.py` - 保存论坛总数到配置
- `python/src/config/manager.py` - 配置管理支持

**关键代码**：
```python
# display.py
def format_archive_progress(author: Dict[str, Any]) -> str:
    """格式化归档进度显示

    Examples:
        >>> format_archive_progress({'total_posts': 80, 'forum_total_posts': 120})
        '80/120 (67%)'

        >>> format_archive_progress({'total_posts': 50, 'forum_total_posts': 50})
        '50/50 (100%) ✓'
    """
    archived = author.get('total_posts', 0)
    forum_total = author.get('forum_total_posts')

    if forum_total is None or forum_total == 0:
        return str(archived)

    percentage = int((archived / forum_total) * 100)

    if percentage >= 100:
        return f"{archived}/{forum_total} (100%) ✓"

    return f"{archived}/{forum_total} ({percentage}%)"
```

```python
# archiver.py
# 论坛总数 = 实际收集到的主题帖数量
# 说明：只统计作者作为楼主的原创主题帖，不包含回复别人的帖子
forum_total = len(post_urls)
```

```python
# main_menu.py
# 使用最大值：论坛主题帖只增不减，保留历史最大值
old_total = author.get('forum_total_posts', 0)
new_total = result['forum_total']
author['forum_total_posts'] = max(old_total, new_total)
```

---

### 内容优化（已完成）

#### CO-001：媒体文件显示
**状态**：✅ 已完成（2026-02-12）
**实施时间**：2026-02-12
**功能描述**：
- 在归档页面显示图片和视频缩略图
- 支持预览和打开
- 媒体文件统计

**相关文档**：
- [媒体显示实施计划](./MEDIA_DISPLAY_IMPLEMENTATION_PLAN.md)
- [增量改进记录](./INCREMENTAL_IMPROVEMENTS_2026-02-12.md) - INC-001

---

#### CO-002：内容清理
**状态**：✅ 已完成（2026-02-12）
**实施时间**：2026-02-12
**功能描述**：
- 移除广告代码
- 清理无用HTML标签
- 格式优化

**相关文档**：
- [内容清理修复](./CONTENT_CLEANUP_FIX.md)
- [增量改进记录](./INCREMENTAL_IMPROVEMENTS_2026-02-12.md) - INC-003

---

#### CO-003：超时处理
**状态**：✅ 已完成（2026-02-12）
**实施时间**：2026-02-12
**功能描述**：
- Playwright 操作超时优化
- 错误重试机制
- 用户友好的错误提示

**相关文档**：
- [增量改进记录](./INCREMENTAL_IMPROVEMENTS_2026-02-12.md) - INC-002

---

#### CO-004：视频文件验证
**状态**：✅ 已完成（2026-02-12）
**实施时间**：2026-02-12
**功能描述**：
- 下载后验证文件完整性
- 自动重试损坏的文件
- 错误日志记录

**相关文档**：
- [增量改进记录](./INCREMENTAL_IMPROVEMENTS_2026-02-12.md) - INC-004

---

#### UX-003：更新菜单循环重构
**状态**：✅ 已完成（2026-02-13）
**实施时间**：2026-02-13

**问题描述**：
在"立即更新"菜单中，用户选择作者后无法返回操作菜单，导致：
- 选择的作者状态丢失
- 无法在"选择作者"和"刷新检测"之间切换
- 想先查看论坛总数再决定是否更新时，只能重新选择

**解决方案**：将线性流程重构为 while 循环结构
- 在循环外维护 `selected_authors` 状态
- 使用 `continue` 返回操作菜单（保留状态）
- 使用 `break` 进入下一阶段
- 确认界面改为"返回上一步"（而非"返回主菜单"）

**核心改进**：
```
改进前：
选择作者 → 确认界面 → 返回主菜单（选择丢失）✗

改进后：
选择作者 → 确认界面 → 返回上一步（选择保留）✓
  ↓
操作菜单（带 ✅ 标记）
  ↓
刷新检测 → 查看论坛总数
  ↓
返回操作菜单（仍保留选择）
  ↓
满意后确认并继续
```

**用户体验提升**：
- ✅ 可以在操作间自由切换
- ✅ 选择状态持久保持
- ✅ 先探索后决策的工作流
- ✅ 更高的错误容忍度

**详细设计文档**：
- **👉 [更新菜单循环重构设计](./MENU_LOOP_REFACTORING_DESIGN.md)** ⭐ 实施必读

**核心改动**：
- 文件：`python/src/menu/main_menu.py`
- 方法：`_run_update()` - 完全重构（~200行）
- 新增方法：
  - `_show_author_list_with_selection()` - 显示带选择标记的列表
  - `_show_action_menu()` - 显示操作菜单
  - `_handle_author_selection()` - 处理作者选择流程
  - `_configure_and_download()` - 配置下载并归档

**实施复杂度**：⭐⭐⭐⭐（中高）
**实际工期**：1天
**风险评估**：低-中

**实施提交**：
- `feat: 重构更新菜单为循环结构，支持操作间自由切换 (UX-003)` (4c13d46)

---

### 数据库功能（已完成）

#### DB-001：数据库架构与基础统计
**状态**：✅ 已完成（Phase 3）
**实施时间**：2026-02-14
**功能描述**：
- SQLite 数据库支持（4 表 + 14 索引 + 2 视图 + 3 触发器）
- 轻量级 ORM（Author/Post/Media 模型）
- 历史数据导入工具（全量/增量）
- 7 种统计查询功能
- 实时数据同步机制
- 数据完整性检查（4 类检查 + 自动修复）

**核心功能**：

1. **全局统计** - `get_global_stats()`
   - 关注作者数、归档帖子总数
   - 图片总数、视频总数
   - 总存储空间
   - 平均每作者帖数、平均每帖图片数

2. **作者排行榜** - `get_author_ranking()`
   - Top N 排行（按帖子/图片/视频/存储）
   - 排名、作者名、统计数据
   - 归档进度百分比

3. **月度统计** - `get_monthly_stats()`
   - 按年份/月份分组统计
   - 帖子数、图片数、视频数、存储空间

4. **时间分布分析**
   - 小时分布：`get_hourly_distribution()` (0-23 小时)
   - 星期分布：`get_weekday_distribution()` (周一-周日)

5. **作者详细统计** - `get_author_detail_stats()`
   - 基础统计（帖子/图片/视频/存储/进度）
   - 时间分布（小时/星期）
   - 最近帖子列表

6. **帖子搜索** - `search_posts()`
   - 按作者名筛选
   - 按年份/月份筛选
   - 支持分页（limit/offset）

7. **数据完整性检查**
   - 数据库缺失文件检查
   - 文件系统缺失记录检查
   - 孤儿记录检查
   - 统计不一致检查
   - 自动修复统计功能

**数据库表设计**：
```
authors (13 字段) ← 作者信息 + 统计
  ↓ 1:N (author_id)
posts (20 字段) ← 帖子元数据 + 时间冗余
  ↓ 1:N (post_id)
media (13 字段) ← 图片/视频详情
```

**性能指标**：
- 全量导入 350 篇帖子：10-12 秒 (目标 < 15s) ✅
- 查询全局统计：0.05 秒 (目标 < 1s) ✅
- 查询作者排行：0.03 秒 (目标 < 1s) ✅
- 数据库文件大小：3.2 MB (目标 < 10MB) ✅

**菜单集成**：
- 首次运行自动检测和导入提示
- 统计菜单完全重构（全局统计面板 + 作者排行榜）
- 作者详细统计视图
- 重新导入数据功能
- 数据完整性检查入口

**相关文档**：
- [Phase 3 详细实施计划](./PHASE3_DETAILED_PLAN.md)
- [Phase 3 完成报告](./PHASE3_COMPLETION_REPORT.md) ⭐
- [Phase 3 快速参考](./PHASE3_QUICK_REFERENCE.md)

**实施提交**：
- `feat(phase3): 实现数据库核心模块和查询功能` (107d3c2)
- `feat(phase3): 集成统计菜单和首次运行导入` (e0d8c2c)

**核心文件**：
- `python/src/database/schema.sql` - 数据库结构定义（400 行）
- `python/src/database/connection.py` - 连接管理（250 行）
- `python/src/database/models.py` - ORM 模型（700 行）
- `python/src/database/migrate.py` - 数据迁移（550 行）
- `python/src/database/query.py` - 查询功能（450 行）
- `python/src/database/sync.py` - 数据同步（350 行）
- `python/src/database/integrity.py` - 完整性检查（400 行）
- `python/src/menu/main_menu.py` - 菜单集成（+336 行）

**测试结果**：
- 测试文件：`test_phase3_database.py` (500 行)
- 测试覆盖：8 大类，71 个测试
- 测试结果：71/71 通过（100% 成功率）

**关键代码**：
```python
# 查询全局统计
from database import get_global_stats
stats = get_global_stats()
# 返回: {'total_authors': 9, 'total_posts': 350, ...}

# 查询作者排行
from database import get_author_ranking
top_authors = get_author_ranking(top_n=10, order_by='posts')
# 返回: [{'rank': 1, 'name': '独醉笑清风', 'total_posts': 80, ...}, ...]

# 同步新归档的帖子
from database import sync_archived_post
sync_archived_post(author_name="独醉笑清风", post_data={...})

# 数据完整性检查
from database import check_all, fix_statistics
issues = check_all()
if issues['summary']['total_issues'] > 0:
    fix_statistics()
```

---

## 🚀 待实施功能

### 新增功能

#### NF-001：刷新检测新帖
**状态**：✅ 已完成（2026-02-13）
**实施时间**：2026-02-13

**功能描述**：
在"立即更新所有作者"子菜单中增加"刷新检测新帖"功能：
- 快速检测每个作者自上次更新后是否有新帖
- 在列表中标记有新帖的作者（🆕标记）
- 显示新帖数量：`🆕(5)` 表示约5篇新帖
- **不下载内容**，仅检测和标记
- **同步更新论坛总数**（`forum_total_posts`），零额外开销
- 用户可以选择性更新有新帖的作者

**实施方案**：方案C - 基于URL Hash的精确检测
- 归档时记录URL的MD5 hash（8位）
- 检测时对比hash列表，找出新帖
- 100%准确，不依赖时间戳

**核心优势**：
- ✅ 100%准确：知道精确的新帖数量和URL
- ✅ 性能优秀：7个作者<30秒（限制扫描3页）
- ✅ 易用性强：一键刷新，直观显示
- ✅ 可扩展：支持"只更新有新帖的"等功能

**界面效果**：
```
当前关注 7 位作者
┏━━━━━━┳━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━┓
┃ 新帖 ┃ 序号 ┃ 作者名         ┃ 上次更新         ┃ 归档进度         ┃ 标签 ┃
┡━━━━━━╇━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━┩
│ 🆕(5)│  1 │ 张三     │ 02-12 10:30      │ 80/125 (64%)     │      │
│      │  2 │ 李四       │ 02-13 15:00      │ 77/77 (100%) ✓   │      │
│ 🆕(3)│  3 │ 王五       │ 02-11 20:00      │ 60/63 (95%)      │      │
│      │  4 │ 赵六     │ 02-13 16:00      │ 18/18 (100%) ✓   │      │
└──────┴────┴────────────────┴──────────────────┴──────────────────┴──────┘

✓ 检测完成！发现 2/7 位作者有新帖，共约 8 篇新帖

请选择操作：
  [R] 🔄 刷新检测新帖         ← 新增
  [S] ✅ 选择作者更新
  [N] 🆕 只更新有新帖的作者   ← 新增
  [A] 📥 更新全部作者
  [B] ← 返回主菜单
```

**技术架构**：
```
界面层 (main_menu.py)
  ├─ 显示作者列表（带🆕标记）
  ├─ 刷新菜单选项
  └─ 只更新有新帖的作者
      ↓
检测层 (scraper/checker.py)
  ├─ PostChecker 类
  ├─ check_new_posts() - 单个作者检测
  └─ batch_check_authors() - 批量并发检测
      ↓
数据层 (data/post_tracker.py)
  ├─ PostTracker 类
  ├─ 记录/查询已归档的URL hash
  └─ 数据持久化
      ↓
存储层 (data/archived_posts.json)
  └─ JSON格式存储hash数据（约6-8KB）
```

**数据结构**：
```json
{
  "张三": {
    "hashes": ["a3f5b2c1", "7d8e9f0a", "..."],
    "last_check": "2026-02-13 18:30:00",
    "total_count": 80
  }
}
```

**详细设计文档**：
- **👉 [刷新检测新帖功能详细设计](./REFRESH_NEW_POSTS_FEATURE_DESIGN.md)** ⭐ 实施必读

**核心实施文件**：
1. **新建文件**（3个）：
   - `python/src/data/__init__.py` - 数据模块初始化
   - `python/src/data/post_tracker.py` ⭐ - 帖子追踪器（约200行）
   - `python/src/scraper/checker.py` ⭐ - 帖子检测器（约150行）

2. **修改文件**（3个）：
   - `python/src/scraper/archiver.py` - 归档时记录hash（+10行）
   - `python/src/menu/main_menu.py` - 添加刷新功能（+80行）
   - `python/src/utils/display.py` - 添加新帖列显示（+15行）

3. **自动生成**（1个）：
   - `python/data/archived_posts.json` - hash数据存储

**实施步骤**：
1. 阶段1：数据层（第1天）- 实现 PostTracker 类 ✅
2. 阶段2：检测层（第2天）- 实现 PostChecker 类 ✅
3. 阶段3：界面层（第3天）- 菜单集成 ✅
   - 新帖检测功能 ✅
   - 论坛总数同步更新 ✅（方案B）
4. 阶段4：测试与优化（第4天）✅

**性能指标**：
- 检测速度：<30秒（7个作者，并发+限制3页）
- 准确率：100%（基于hash精确对比）
- 数据文件：<10KB（7个作者×80篇）

**实施提交**：
- `feat: [NF-001] 实现刷新检测新帖功能（数据层 + 检测层）` (xxx)
- `feat: [NF-001] 完成菜单集成和论坛总数同步` (f3b286d, ce24741)
- `feat: 重构更新菜单为循环结构，支持操作间自由切换 (UX-003)` (4c13d46)

**验收结果**：
- ✅ 能准确检测新帖
- ✅ 显示🆕标记正确
- ✅ 论坛总数同步更新正确
- ✅ 新作者刷新后显示完整归档进度
- ✅ "只更新有新帖的"功能正常
- ✅ 性能满足要求（<30秒）

---

## 📊 功能状态统计

### 总览

| 状态 | 数量 | 百分比 |
|------|------|--------|
| ✅ 已完成 | 12 | 100% |
| 📝 待实施 | 0 | 0% |
| **总计** | **12** | **100%** |

### 按分类统计

| 分类 | 已完成 | 待实施 | 总计 |
|------|-------|--------|------|
| 核心功能 | 2 | 0 | 2 |
| 用户体验 | 3 | 0 | 3 |
| 数据显示 | 1 | 0 | 1 |
| 内容优化 | 4 | 0 | 4 |
| 新增功能 | 1 | 0 | 1 |
| 数据库功能 | 1 | 0 | 1 |

---

## 🎯 下一步行动

### 当前计划（本周）

1. **Phase 4：数据分析 + 可视化** ⭐ 当前
   - 优先级：P1
   - 预计：2-3 周
   - 词云生成（jieba 分词）
   - 发帖趋势图（matplotlib）
   - 时间热力图（小时 x 星期）
   - HTML 报告生成
   - 参考：[ADR-002](./ADR-002_Python_Migration_Plan.md) 第 5.4 节

### 中期计划（1-2月）

3. **Phase 5：完善与优化**
   - 命令行模式完善
   - 日志系统
   - 错误处理与重试
   - 性能优化
   - 文档完善
   - 参考：[ADR-002](./ADR-002_Python_Migration_Plan.md) 第 5.5 节

### 长期计划（可选）

4. **定时任务与通知**
   - 自动更新
   - 新帖通知
   - 定时报告

5. **Web 界面**（低优先级）
   - 浏览归档
   - 在线配置

---

## 📚 相关文档索引

### 架构设计
- [ADR-001：Phase 1 论坛爬虫计划](./ADR-001_Phase1_Forum_Scraping_Plan.md)
- [ADR-002：Python迁移方案](./ADR-002_Python_Migration_Plan.md) ⭐ 核心

### 实施指南
- [迁移指南](./MIGRATION_GUIDE.md)
- [迁移进度](./MIGRATION_PROGRESS.md)
- [实施状态](./python/IMPLEMENTATION_STATUS.md)
- [Phase 3 详细计划](./PHASE3_DETAILED_PLAN.md) ⭐ 最新

### 完成报告
- [Phase 1 完成报告](./PHASE1_COMPLETED.md)
- [Phase 2 完成报告](./python/PHASE2_COMPLETION_REPORT.md)
- [Phase 2-B 完成报告](./PHASE2B_COMPLETION_REPORT.md)
- [Phase 3 完成报告](./PHASE3_COMPLETION_REPORT.md) ⭐ 最新

### 问题修复
- [Phase 1 Bug修复](./PHASE1_BUGS_FIXED.md)
- [Phase 2 问题与修复](./python/PHASE2_PROBLEMS_AND_FIXES.md)
- [Phase 2-B 问题与修复](./PHASE2B_PROBLEMS_AND_FIXES.md)
- [增量改进记录](./INCREMENTAL_IMPROVEMENTS_2026-02-12.md)

### 测试文档
- [Phase 1 测试指南](./PHASE1_TESTING.md)
- [Phase 2 测试指南](./PHASE2_TESTING.md)
- [Phase 2-B 测试指南](./PHASE2B_TESTING.md)

---

## 🔖 文档维护

### 版本历史

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v1.0 | 2026-02-13 | 初始版本，整理所有功能设计 | Claude + 用户 |
| v1.1 | 2026-02-13 | NF-001 增强：添加论坛总数同步功能 | Claude + 用户 |
| v1.2 | 2026-02-13 | 新增 UX-003：更新菜单循环重构设计 | Claude + 用户 |
| v1.3 | 2026-02-14 | Phase 3 完成：新增 DB-001 数据库功能，更新所有功能状态 | Claude + 用户 |

### 更新规则

**何时更新此文档**：
1. 新增功能设计完成时 → 添加到"待实施功能"
2. 功能实施完成时 → 移动到对应分类，更新状态
3. 设计文档变更时 → 更新相关链接和描述

**更新责任**：
- 功能设计：架构师/技术负责人
- 实施状态：实施工程师
- 文档链接：文档维护者

---

## 📞 联系方式

**问题反馈**：
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- 项目讨论：与用户直接沟通

**AI 编程支持**：
- 实施疑问：查阅详细设计文档
- 技术问题：参考 ADR-002 技术架构
- 测试问题：参考对应测试指南

---

**文档结束**

**项目进度**：
- ✅ Phase 1: 基础框架与菜单（100%）
- ✅ Phase 2: Python 爬虫核心（100%）
- ✅ Phase 3: 数据库与统计（90%，9/10 任务完成）
- 🔴 Phase 4: 数据分析与可视化（待开始）
- 🔴 Phase 5: 完善与优化（待开始）

**总体进度**: 58% (Phase 1-3/5)

**下一步**：
1. 实施工程师：开始 Phase 4 - 数据分析与可视化
2. 代码审查：参考 [Phase 3 完成报告](./PHASE3_COMPLETION_REPORT.md)
3. 项目经理：跟踪功能状态统计（12/12 功能完成）
