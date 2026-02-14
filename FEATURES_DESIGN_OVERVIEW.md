# 功能设计总览

**文档版本**：v1.0
**最后更新**：2026-02-13
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

## 🚀 待实施功能

### 新增功能

#### NF-001：刷新检测新帖
**状态**：📝 设计完成，待实施
**优先级**：P1（用户强需求）
**预计工期**：3-4天
**设计日期**：2026-02-13

**功能描述**：
在"立即更新所有作者"子菜单中增加"刷新检测新帖"功能：
- 快速检测每个作者自上次更新后是否有新帖
- 在列表中标记有新帖的作者（🆕标记）
- 显示新帖数量：`🆕(5)` 表示约5篇新帖
- **不下载内容**，仅检测和标记
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
1. 阶段1：数据层（第1天）- 实现 PostTracker 类
2. 阶段2：检测层（第2天）- 实现 PostChecker 类
3. 阶段3：界面层（第3天）- 菜单集成
4. 阶段4：测试与优化（第4天）

**性能指标**：
- 检测速度：<30秒（7个作者，并发+限制3页）
- 准确率：100%（基于hash精确对比）
- 数据文件：<10KB（7个作者×80篇）

**AI编程实施提示**：
```
实施此功能时，请按以下顺序：

1. 首先阅读详细设计文档：
   REFRESH_NEW_POSTS_FEATURE_DESIGN.md

2. 按阶段实施：
   阶段1 → 阶段2 → 阶段3 → 阶段4

3. 每个阶段完成后运行测试

4. 注意事项：
   - Hash算法使用MD5前8位
   - 使用set进行O(1)查找
   - 限制扫描深度（max_pages=3）
   - 并发数限制（max_concurrent=2）
   - 归档时批量记录hash（性能优化）

5. 验收标准：
   - 能准确检测新帖
   - 显示🆕标记正确
   - "只更新有新帖的"功能正常
   - 性能满足要求（<30秒）
```

---

## 📊 功能状态统计

### 总览

| 状态 | 数量 | 百分比 |
|------|------|--------|
| ✅ 已完成 | 9 | 90% |
| 📝 待实施 | 1 | 10% |
| **总计** | **10** | **100%** |

### 按分类统计

| 分类 | 已完成 | 待实施 | 总计 |
|------|-------|--------|------|
| 核心功能 | 2 | 0 | 2 |
| 用户体验 | 2 | 0 | 2 |
| 数据显示 | 1 | 0 | 1 |
| 内容优化 | 4 | 0 | 4 |
| 新增功能 | 0 | 1 | 1 |

---

## 🎯 下一步行动

### 近期计划（1-2周）

1. **实施 NF-001：刷新检测新帖**
   - 优先级：P1
   - 预计：3-4天
   - 负责人：待分配

### 中期计划（1-2月）

2. **Phase 3：数据分析功能**
   - 统计分析
   - 可视化报告
   - 参考：[ADR-002](./ADR-002_Python_Migration_Plan.md)

3. **Phase 4：定时任务**
   - 自动更新
   - 通知功能
   - 参考：[ADR-002](./ADR-002_Python_Migration_Plan.md)

### 长期计划（2-3月）

4. **Phase 5：Web界面**
   - 浏览归档
   - 在线配置
   - 参考：[ADR-002](./ADR-002_Python_Migration_Plan.md)

---

## 📚 相关文档索引

### 架构设计
- [ADR-001：Phase 1 论坛爬虫计划](./ADR-001_Phase1_Forum_Scraping_Plan.md)
- [ADR-002：Python迁移方案](./ADR-002_Python_Migration_Plan.md) ⭐ 核心

### 实施指南
- [迁移指南](./MIGRATION_GUIDE.md)
- [迁移进度](./MIGRATION_PROGRESS.md)
- [实施状态](./python/IMPLEMENTATION_STATUS.md)

### 完成报告
- [Phase 1 完成报告](./PHASE1_COMPLETED.md)
- [Phase 2 完成报告](./python/PHASE2_COMPLETION_REPORT.md)
- [Phase 2-B 完成报告](./PHASE2B_COMPLETION_REPORT.md)

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

**下一步**：
1. 实施工程师：阅读 [刷新检测新帖功能详细设计](./REFRESH_NEW_POSTS_FEATURE_DESIGN.md)
2. 代码审查：参考本文档的功能状态和设计链接
3. 项目经理：跟踪功能状态统计
