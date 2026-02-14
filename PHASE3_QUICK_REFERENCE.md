# Phase 3 快速参考

**完整设计文档**: [PHASE3_DETAILED_PLAN.md](./PHASE3_DETAILED_PLAN.md) (46KB)

---

## ⚡ 核心信息

**目标**: 数据库 + 基础统计
**预计工期**: 3-4 天
**状态**: 📝 设计完成，待实施

---

## 📊 数据库设计（速查）

### 4 个核心表

```sql
-- 1. authors 表（13 字段）
CREATE TABLE authors (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    url TEXT,
    total_posts INTEGER DEFAULT 0,      -- 冗余统计
    total_images INTEGER DEFAULT 0,     -- 冗余统计
    total_videos INTEGER DEFAULT 0,     -- 冗余统计
    forum_total_posts INTEGER DEFAULT 0,
    tags TEXT,  -- JSON 数组
    ...
);

-- 2. posts 表（20 字段）
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    author_id INTEGER NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    publish_year INTEGER,       -- 冗余字段（加速 Phase 4）
    publish_month INTEGER,       -- 冗余字段
    publish_hour INTEGER,        -- 冗余字段
    publish_weekday INTEGER,     -- 冗余字段
    image_count INTEGER,
    video_count INTEGER,
    file_path TEXT NOT NULL,
    ...
);

-- 3. media 表（13 字段）
CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,
    type TEXT NOT NULL,  -- 'image' or 'video'
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    ...
);

-- 4. sync_history 表（可选）
CREATE TABLE sync_history (...);
```

---

## 🔧 6 个核心模块

```
database/
├── connection.py    # 单例数据库连接
├── models.py        # Author/Post/Media 类（轻量 ORM）
├── query.py         # 统计查询函数
├── migrate.py       # 历史数据导入（<15 秒）
├── sync.py          # 实时同步（归档时自动写入）
└── integrity.py     # 数据完整性检查
```

---

## ⏱️ 4 天实施计划

| Day | 任务 | 时长 |
|-----|------|------|
| **1** | schema.sql + connection.py + models.py | 6-8h |
| **2** | migrate.py（历史数据导入） | 6-8h |
| **3** | query.py + sync.py + integrity.py | 6-8h |
| **4** | 菜单集成 + 测试 + 文档 | 4-6h |

---

## 🎯 关键设计决策

1. **不存储 content**
   - ✅ 只存储元数据（<10MB）
   - ✅ content.html 保持在文件系统

2. **冗余统计字段**
   - ✅ authors 表存储 total_posts/images/videos
   - ✅ 触发器自动维护（无需手动更新）

3. **时间冗余字段**
   - ✅ posts 表存储 year/month/hour/weekday
   - ✅ 为 Phase 4 分析准备（避免运行时解析）

4. **轻量级 ORM**
   - ✅ 不使用 SQLAlchemy
   - ✅ 手写简单封装（避免重依赖）

---

## 📈 性能目标

| 操作 | 目标时间 |
|------|---------|
| 全量导入 350 篇帖子 | < 15 秒 |
| 查询全局统计 | < 1 秒 |
| 查询作者排行 | < 1 秒 |
| 同步单篇帖子 | < 0.1 秒 |

**优化手段**:
- 批量插入（100 条/批）
- 禁用触发器（导入时）
- WAL 模式（并发读写）
- 事务批处理

---

## ✅ 验收标准（P0）

- [ ] 数据库创建成功
- [ ] 历史数据导入 >90%
- [ ] 统计功能正常（全局统计、排行榜）
- [ ] 数据同步正常（新归档自动写入）
- [ ] 菜单集成完成

---

## 📋 任务清单

已创建 9 个任务（#17-#25）:

1. #17 - 设计数据库 schema
2. #18 - 实现数据库连接管理
3. #19 - 实现数据模型（ORM）
4. #20 - 实现历史数据导入工具
5. #21 - 实现查询与统计函数
6. #22 - 实现数据同步机制
7. #23 - 实现数据完整性检查
8. #24 - 菜单集成与用户界面
9. #25 - 综合测试与文档

---

## 🎨 用户界面预览

### 统计菜单
```
╔════════════════════════════════════════╗
║            📊 统计信息                  ║
╠════════════════════════════════════════╣
║  总关注作者: 7                         ║
║  总归档帖子: 245                       ║
║  总下载图片: 1,245                     ║
║  总下载视频: 67                        ║
║  占用空间: 2.3 GB                      ║
╚════════════════════════════════════════╝

作者排行榜（按帖子数）
─────────────────────────────────────
1. 独醉笑清风    80 篇  245 图  8 视频
2. 清风皓月      77 篇  189 图  5 视频
3. 厦门一只狼    70 篇  301 图  12 视频
```

---

## 🚀 快速开始实施

### Day 1 - 第一个任务

1. **创建 schema.sql**
   ```bash
   touch python/src/database/schema.sql
   ```

2. **定义 authors 表**
   - 13 个字段
   - 1 个唯一索引

3. **定义 posts 表**
   - 20 个字段
   - 5 个索引
   - 1 个外键

4. **定义 media 表**
   - 13 个字段
   - 3 个索引
   - 1 个外键

5. **测试 SQL**
   ```bash
   sqlite3 test.db < python/src/database/schema.sql
   ```

---

## 📚 深入了解

- **完整设计**: [PHASE3_DETAILED_PLAN.md](./PHASE3_DETAILED_PLAN.md)
  - 第 3 节：数据库架构设计（详细字段说明）
  - 第 4 节：模块架构设计（6 个模块详细职责）
  - 第 5 节：数据迁移策略（导入流程）
  - 第 7 节：实施步骤（4 天详细分解）
  - 第 9 节：风险评估（5 大风险及应对）

- **总体规划**: [ADR-002](./ADR-002_Python_Migration_Plan.md)
  - 第 5.3 节：Phase 3 规划

---

**准备好了就开始 Day 1 Task 1！** 🚀
