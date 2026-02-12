# Phase 2.5 进度追踪

> **开始日期**: 待定
> **预计工期**: 1 小时
> **当前状态**: 🔴 待开始
> **文档版本**: v1.0

---

## 📊 总体进度

```
Step 1: 创建模板 (15min)    ░░░░░░░░░░░░░░░░░░░░  0% (0/2)
Step 2: 创建过滤器 (15min)  ░░░░░░░░░░░░░░░░░░░░  0% (0/1)
Step 3: 修改 Archiver (20min) ░░░░░░░░░░░░░░░░░░░░  0% (0/4)
Step 4: 测试验证 (10min)    ░░░░░░░░░░░░░░░░░░░░  0% (0/5)
Step 5: 清理数据 (5min)     ░░░░░░░░░░░░░░░░░░░░  0% (0/3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总计 (65min):              ░░░░░░░░░░░░░░░░░░░░  0% (0/15)
```

---

## Step 1: 创建模板文件（0/2）⏱️ 15 分钟

**目标**：创建 Jinja2 模板和目录结构

### 任务清单

- [ ] **1.1 创建目录和初始化文件**
  ```bash
  mkdir -p python/src/templates
  touch python/src/templates/__init__.py
  ```
  - 验证：`ls -la python/src/templates/`
  - 预期：目录存在，__init__.py 创建成功

- [ ] **1.2 创建主模板 post.html**
  - 文件路径：`python/src/templates/post.html`
  - 行数：约 80 行
  - 内容：完整的 HTML 模板（见 PHASE2_5_DESIGN.md）
  - 验证：`wc -l python/src/templates/post.html`
  - 预期：输出约 80 行

### 验收标准

✅ 目录 `python/src/templates/` 存在
✅ 文件 `__init__.py` 存在
✅ 文件 `post.html` 存在且约 80 行
✅ 模板包含完整的 HTML 结构（DOCTYPE, head, body）
✅ 模板使用 Jinja2 语法（{{ }}, {% %}）

---

## Step 2: 创建过滤器（0/1）⏱️ 15 分钟

**目标**：实现 HTML 内容清理函数

### 任务清单

- [ ] **2.1 创建 filters.py**
  - 文件路径：`python/src/templates/filters.py`
  - 行数：约 60 行
  - 内容：
    - `clean_html_content(html)` - 清理 HTML
    - `format_file_size(bytes)` - 格式化文件大小
  - 验证：
    ```bash
    cd python
    python3 -c "from src.templates.filters import clean_html_content, format_file_size; print('✓')"
    ```
  - 预期：输出 `✓`，无错误

### 验收标准

✅ 文件 `filters.py` 存在且约 60 行
✅ 函数 `clean_html_content` 可导入
✅ 函数 `format_file_size` 可导入
✅ 单元测试通过（见测试清单）

---

## Step 3: 修改 Archiver（0/4）⏱️ 20 分钟

**目标**：集成模板引擎到归档流程

### 任务清单

- [ ] **3.1 添加导入语句**
  - 文件：`python/src/scraper/archiver.py`
  - 添加：
    ```python
    from jinja2 import Environment, FileSystemLoader
    from templates.filters import clean_html_content, format_file_size
    ```
  - 验证：`python3 -c "from src.scraper.archiver import ForumArchiver; print('✓')"`

- [ ] **3.2 修改 __init__ 方法**
  - 初始化 Jinja2 环境
  - 注册自定义过滤器
  - 代码：见 PHASE2_5_DESIGN.md Step 3.2

- [ ] **3.3 添加 _prepare_media_list 方法**
  - 准备图片/视频列表数据
  - 代码：见 PHASE2_5_DESIGN.md Step 3.3

- [ ] **3.4 添加/修改 _save_content_html 方法**
  - 使用模板渲染 HTML
  - 保存到 content.html
  - 代码：见 PHASE2_5_DESIGN.md Step 3.4

### 验收标准

✅ Archiver 可以正常导入（无语法错误）
✅ 模板引擎初始化成功
✅ `_save_content_html` 方法存在
✅ 可以生成 content.html（后续测试验证）

---

## Step 4: 测试验证（0/5）⏱️ 10 分钟

**目标**：验证功能正确性和 w3m 浏览效果

### 任务清单

- [ ] **4.1 单元测试：过滤器**
  ```bash
  cd python
  python3 << 'EOF'
  from src.templates.filters import clean_html_content

  # 测试段落转换
  html = "第一段<br><br>第二段"
  result = clean_html_content(html)
  assert '<p>' in result
  print("✓ 测试通过")
  EOF
  ```
  - 预期：输出 `✓ 测试通过`

- [ ] **4.2 单元测试：模板渲染**
  ```bash
  cd python
  python3 << 'EOF'
  from jinja2 import Environment, FileSystemLoader
  env = Environment(loader=FileSystemLoader('src/templates'))
  template = env.get_template('post.html')
  html = template.render(title='测试', author='测试', publish_time='2026-02-12',
                          archive_time='2026-02-12', url='https://test.com',
                          content='<p>测试</p>', content_length=10, images=[], videos=[])
  assert '<!DOCTYPE html>' in html
  print("✓ 模板渲染成功")
  EOF
  ```
  - 预期：输出 `✓ 模板渲染成功`

- [ ] **4.3 集成测试：归档帖子**
  ```bash
  cd python
  python main.py
  # 手动操作：
  # - 选择 [3] 立即更新
  # - 选择 1 位作者
  # - 设置 1 页
  ```
  - 预期：归档成功，无错误

- [ ] **4.4 验证 HTML 结构**
  ```bash
  LATEST=$(find /home/ben/Download/t66y -name "content.html" -type f | head -1)
  grep -q "<!DOCTYPE html>" "$LATEST" && echo "✓ DOCTYPE 存在"
  grep -q "<h1>" "$LATEST" && echo "✓ 标题存在"
  grep -q "作者:" "$LATEST" && echo "✓ 元数据可见"
  ```
  - 预期：所有检查通过

- [ ] **4.5 w3m 浏览测试**
  ```bash
  LATEST=$(find /home/ben/Download/t66y -name "content.html" -type f | head -1)
  w3m "$LATEST"
  ```
  - 手动验证：
    - ✅ 标题清晰
    - ✅ 元数据可见（作者、时间）
    - ✅ 正文段落分明
    - ✅ 链接可点击

### 验收标准

✅ 所有单元测试通过
✅ 归档成功，生成 content.html
✅ HTML 结构完整（DOCTYPE, head, body）
✅ 元数据在页面中可见（不在注释中）
✅ w3m 浏览体验良好

---

## Step 5: 清理测试数据（0/3）⏱️ 5 分钟

**目标**：删除旧格式的测试数据，准备使用新格式

### 任务清单

- [ ] **5.1 备份配置（可选）**
  ```bash
  cp python/config.yaml python/config.yaml.backup
  cp config.json config.json.backup
  ```
  - 验证：`ls -la python/*.backup config.json.backup`

- [ ] **5.2 清空归档目录**
  ```bash
  rm -rf /home/ben/Download/t66y/*
  ```
  - 验证：`ls -la /home/ben/Download/t66y/`
  - 预期：目录为空

- [ ] **5.3 验证配置完整**
  ```bash
  cat python/config.yaml | grep -A 5 "followed_authors:"
  cat python/config.yaml | grep "database_path"
  ```
  - 预期：关注列表和配置正常

### 验收标准

✅ 归档目录已清空
✅ config.yaml 配置完整
✅ 关注作者列表保留
✅ 准备好重新归档（使用新格式）

---

## 🎯 最终验收（所有任务完成后）

### P0 标准（必须通过）

- [ ] ✅ 模板文件创建成功（post.html, filters.py）
- [ ] ✅ Archiver 修改成功（可导入，无语法错误）
- [ ] ✅ 新归档使用新模板（包含 <!DOCTYPE html>）
- [ ] ✅ w3m 浏览正常（标题、正文、链接可点击）

### P1 标准（强烈建议）

- [ ] ✅ 正文格式正确（段落、章节标题识别）
- [ ] ✅ 媒体列表完整（图片/视频文件名）
- [ ] ✅ 统计信息正确（字符数、图片数、视频数）

### P2 标准（可选）

- [ ] ⭕ 浏览器显示美观（Firefox/Chrome）
- [ ] ⭕ 文件大小显示（MB/KB）

---

## 📝 提交检查清单

完成所有任务后，执行以下操作：

### Git 提交

```bash
# 1. 查看修改
git status

# 2. 添加文件
git add python/src/templates/
git add python/src/scraper/archiver.py
git add PHASE2_5_DESIGN.md
git add PHASE2_5_PROGRESS.md

# 3. 提交
git commit -m "feat(phase2.5): unified HTML template for content.html

- Create post.html template with Jinja2
- Add content cleaning filters
- Integrate template rendering in archiver
- Optimized for w3m terminal browser

Benefits:
- Unified format for all posts
- Better w3m reading experience
- Visible metadata in header
- Local media file listing
- Simplifies Phase 3 implementation

Testing:
- Unit tests pass for filters
- Template rendering works
- w3m browsing experience verified

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 4. 打标签
git tag -a v2.5 -m "Phase 2.5: HTML Template Optimization"

# 5. 查看提交
git log --oneline -1
git show v2.5
```

### 文档更新

- [ ] ✅ PHASE2_5_DESIGN.md 已创建
- [ ] ✅ PHASE2_5_PROGRESS.md 已创建
- [ ] ⏳ MIGRATION_PROGRESS.md 待更新（标记 Phase 2.5 完成）
- [ ] ⏳ README.md 待更新（可选）
- [ ] ⏳ CHANGELOG.md 待更新（记录 v2.5）

---

## 🚀 下一步

Phase 2.5 完成后：

1. ✅ **清理完成** - 测试数据已删除
2. ✅ **新格式启用** - 所有归档使用新模板
3. ⏭️ **启动 Phase 3** - 数据库 + 统计（2-3 天）

**Phase 3 简化收益**：
- 历史数据导入工具：不需要（节省 2 小时）
- 解析逻辑：简化（节省 1 小时）
- 测试验证：简化（节省 0.5 小时）
- **总节省：3.5 小时**

---

## 📊 时间记录

| 任务 | 预计时间 | 实际时间 | 差异 |
|------|---------|---------|------|
| Step 1: 创建模板 | 15 分钟 | - | - |
| Step 2: 创建过滤器 | 15 分钟 | - | - |
| Step 3: 修改 Archiver | 20 分钟 | - | - |
| Step 4: 测试验证 | 10 分钟 | - | - |
| Step 5: 清理数据 | 5 分钟 | - | - |
| **总计** | **65 分钟** | - | - |

**开始时间**：-
**完成时间**：-
**实际耗时**：-

---

## 🐛 问题记录

### 遇到的问题

（暂无）

### 解决方案

（暂无）

---

**Phase 2.5 进度追踪文档**
**版本**：v1.0
**创建**：2026-02-12
**状态**：🔴 待开始
