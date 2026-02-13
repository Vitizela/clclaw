# 超时问题修复分析

**问题**: 归档"厦门一只狼"时所有帖子都因 `Timeout 30000ms exceeded` 失败

**日期**: 2026-02-12

---

## 🔍 问题根因

### 1. `wait_until='networkidle'` 太严格

**当前代码** (`extractor.py:215`):
```python
await self.page.goto(post_url, wait_until='networkidle', timeout=30000)
```

**问题**:
- `networkidle` 等待所有网络连接完成（包括图片、广告、追踪脚本）
- 如果有任何资源加载慢或失败，会一直等到超时
- 对于包含大量媒体资源的帖子非常不友好

**Playwright 的 wait_until 选项**:
| 选项 | 含义 | 适用场景 |
|------|------|---------|
| `'load'` | 等待 `load` 事件 | 需要等待所有资源（包括图片、CSS） |
| `'domcontentloaded'` | 等待 DOM 加载完成 | ⭐ **推荐**：只需要 HTML 内容 |
| `'networkidle'` | 等待网络空闲（0.5秒内无新请求） | ❌ **不推荐**：容易超时 |
| `'commit'` | 等待导航提交 | 最快，但可能内容未加载 |

### 2. 超时时间硬编码

**当前设置**: 30 秒（30000ms）

**问题**:
- 对于网络慢或内容多的帖子不够
- 无法根据情况调整
- 没有从配置文件读取

---

## 💡 解决方案

### 方案 A: 快速修复（推荐） ⭐⭐⭐⭐⭐

**修改内容**:
1. 将 `wait_until='networkidle'` 改为 `'domcontentloaded'`
2. 增加超时时间到 60 秒
3. 从配置读取超时时间

**优点**:
- 立即解决问题
- 不改变核心逻辑
- 向下兼容

**缺点**:
- 没有重试机制

**实施步骤**:

#### Step 1: 修改 `config.yaml`
```yaml
advanced:
  page_load_timeout: 60  # 页面加载超时（秒）
  wait_until: domcontentloaded  # load | domcontentloaded | networkidle
```

#### Step 2: 修改 `extractor.py`

**位置 1**: `__init__` 方法（约第 26 行）
```python
def __init__(self, base_url: str, log_dir: Path, config: dict = None):
    """Initialize extractor

    Args:
        base_url: Forum base URL (e.g., https://example.com)
        log_dir: Directory for log files
        config: Configuration dict (optional)
    """
    self.base_url = base_url.rstrip('/')
    self.logger = setup_logger('extractor', log_dir)
    self.playwright: Optional[Playwright] = None
    self.browser: Optional[Browser] = None
    self.page: Optional[Page] = None

    # 从配置读取超时和等待策略
    self.config = config or {}
    self.page_timeout = self.config.get('advanced', {}).get('page_load_timeout', 60) * 1000  # 转为毫秒
    self.wait_until = self.config.get('advanced', {}).get('wait_until', 'domcontentloaded')

    self.logger.info(f"页面超时: {self.page_timeout}ms, 等待策略: {self.wait_until}")
```

**位置 2**: `collect_post_urls` 方法（第 118 行）
```python
# 修改前
await self.page.goto(current_url, wait_until='networkidle', timeout=30000)

# 修改后
await self.page.goto(current_url, wait_until=self.wait_until, timeout=self.page_timeout)
```

**位置 3**: `extract_post_details` 方法（第 215 行）
```python
# 修改前
await self.page.goto(post_url, wait_until='networkidle', timeout=30000)

# 修改后
await self.page.goto(post_url, wait_until=self.wait_until, timeout=self.page_timeout)
```

#### Step 3: 修改 `archiver.py`

**位置**: `__init__` 方法（约第 66 行）
```python
# 修改前
self.extractor = PostExtractor(self.base_url, log_dir)

# 修改后
self.extractor = PostExtractor(self.base_url, log_dir, config)
```

---

### 方案 B: 完整优化（可选） ⭐⭐⭐⭐

在方案 A 基础上增加：

#### 1. 添加重试机制

```python
async def extract_post_details(self, post_url: str, retry: int = 3) -> Optional[Dict]:
    """提取单个帖子的详细信息（带重试）"""

    for attempt in range(retry):
        try:
            await self.page.goto(post_url, wait_until=self.wait_until, timeout=self.page_timeout)

            # 提取内容...
            return post_data

        except Exception as e:
            if attempt < retry - 1:
                self.logger.warning(f"提取失败 (尝试 {attempt+1}/{retry}): {str(e)}")
                await asyncio.sleep(2)  # 等待 2 秒后重试
            else:
                self.logger.error(f"提取失败 {post_url}: {str(e)}")
                return None
```

#### 2. 添加备用等待策略

```python
async def _safe_goto(self, url: str) -> bool:
    """安全的页面导航（带降级策略）"""

    strategies = [
        ('domcontentloaded', self.page_timeout),
        ('load', self.page_timeout * 1.5),
        ('commit', self.page_timeout * 0.5)
    ]

    for wait_until, timeout in strategies:
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            return True
        except Exception as e:
            self.logger.warning(f"等待策略 {wait_until} 失败: {str(e)}")

    return False
```

---

## 🧪 测试方案

### 测试 1: 验证配置生效

```bash
# 1. 修改 config.yaml
advanced:
  page_load_timeout: 60
  wait_until: domcontentloaded

# 2. 运行归档
cd python && python main.py
# 选择"厦门一只狼"，限制 1 篇帖子

# 3. 检查日志
grep "页面超时" logs/extractor.log
# 应该看到: 页面超时: 60000ms, 等待策略: domcontentloaded
```

### 测试 2: 超时设置对比

| 设置 | 成功率 | 平均耗时 |
|------|--------|---------|
| `networkidle` + 30s | 0/10（全部超时） | N/A |
| `domcontentloaded` + 30s | 预计 8/10 | ~10s |
| `domcontentloaded` + 60s | 预计 10/10 | ~10s |

---

## 📋 实施检查清单

- [ ] 修改 `config.yaml` 添加 `page_load_timeout` 和 `wait_until`
- [ ] 修改 `extractor.py` 的 `__init__` 方法
- [ ] 修改 `extractor.py` 的 `collect_post_urls` 方法（第 118 行）
- [ ] 修改 `extractor.py` 的 `extract_post_details` 方法（第 215 行）
- [ ] 修改 `archiver.py` 的 `__init__` 方法（第 66 行）
- [ ] 测试归档"厦门一只狼"（1 篇帖子）
- [ ] 检查日志确认配置生效
- [ ] 全量测试（10 篇帖子）
- [ ] Git 提交

---

## 🎯 预期效果

**修复前**:
```
INFO - 提取帖子详情: https://t66y.com/...
ERROR - Timeout 30000ms exceeded.  ❌
```

**修复后**:
```
INFO - 页面超时: 60000ms, 等待策略: domcontentloaded
INFO - 提取帖子详情: https://t66y.com/...
INFO - 提取成功: 标题 | 4 图片 | 0 视频  ✅
```

---

## 📚 参考资料

- [Playwright wait_until 文档](https://playwright.dev/python/docs/api/class-page#page-goto)
- [Playwright 最佳实践](https://playwright.dev/docs/best-practices)

---

**推荐行动**: 立即实施方案 A（快速修复），预计 10 分钟完成。
