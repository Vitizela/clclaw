# Phase 2 测试与验收指南

> **状态**: 待测试
> **依赖**: Phase 1 ✅
> **目标**: Python 爬虫核心功能等价替换 Node.js

---

## 📋 测试前准备

### 1. 确认 Phase 1 通过

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 确认菜单系统正常
python main.py

# 应该能看到菜单并正常操作
```

### 2. 更新 Python 依赖

```bash
# 确保在 python/ 目录
cd /home/ben/gemini-work/gemini-t66y/python

# 备份当前 requirements.txt
cp requirements.txt requirements.txt.phase1.backup

# 安装 Phase 2 新增依赖
pip install playwright aiohttp beautifulsoup4 tqdm requests

# 验证安装
python -c "from playwright.async_api import async_playwright; print('✓ Playwright 已安装')"
python -c "import aiohttp; print('✓ aiohttp 已安装')"
python -c "from bs4 import BeautifulSoup; print('✓ BeautifulSoup4 已安装')"
python -c "from tqdm import tqdm; print('✓ tqdm 已安装')"
```

### 3. 安装 Playwright 浏览器

```bash
# 安装 Chromium 浏览器
playwright install chromium

# 验证安装
playwright install --dry-run chromium
# 应该显示 "already installed" 或类似信息
```

预期输出：
```
Downloading Chromium 123.0.6312.4...
[==============================] 100% complete
Chromium 123.0.6312.4 downloaded to /home/ben/.cache/ms-playwright/chromium-1091/chrome-linux
```

### 4. 运行依赖检查脚本

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 运行检查脚本
python check_dependencies.py
```

预期输出：
```
✓ PyYAML
✓ questionary
✓ rich
✓ click
✓ python-dateutil
✓ playwright
✓ aiohttp
✓ beautifulsoup4
✓ tqdm
✓ requests
✓ Playwright 浏览器已安装

✅ 所有依赖已就绪
```

---

## 🧪 测试清单

### Test 1: 文件名安全化一致性 🔴 P0

**目的**: 确保 Python 版本生成的文件名与 Node.js 完全一致

```bash
cd /home/ben/gemini-work/gemini-t66y/python

python3 -c "
from src.scraper.utils import sanitize_filename

# 测试用例（与 Node.js 对比）
test_cases = [
    ('正常标题', '正常标题'),
    ('标题<含>特殊:字符', '标题_含_特殊_字符'),
    ('a' * 150, 'a' * 100),
    ('标题/', '标题_'),
    ('  空格标题  ', '空格标题'),
]

print('文件名安全化测试:')
for input_name, expected in test_cases:
    result = sanitize_filename(input_name)
    status = '✓' if result == expected else '✗'
    print(f'{status} {repr(input_name[:20])} -> {repr(result[:20])}')
    if result != expected:
        print(f'  预期: {repr(expected[:20])}')
        print(f'  实际: {repr(result[:20])}')
"
```

**验收标准**:
- ✅ 所有测试用例通过
- ✅ 与 Node.js `sanitizeFilename()` 输出完全一致

**对比验证**（可选）：
```bash
# Node.js 版本输出
cd /home/ben/gemini-work/gemini-t66y
node -e "
function sanitizeFilename(name) {
    return name.replace(/[<>:\"/\\\\|?*]/g, '_').substring(0, 100);
}
console.log(sanitizeFilename('标题<含>特殊:字符'));
"

# 应该输出: 标题_含_特殊_字符
```

---

### Test 2: Playwright 基础功能测试

**目的**: 验证 Playwright 能正常访问论坛页面

```bash
cd /home/ben/gemini-work/gemini-t66y/python

python3 -c "
import asyncio
from playwright.async_api import async_playwright

async def test_forum_access():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print('访问论坛页面...')
        await page.goto('https://t66y.com/thread0806.php?fid=7', timeout=60000)

        # 检查页面标题
        title = await page.title()
        print(f'页面标题: {title}')

        # 检查关键元素
        tbody = await page.query_selector('#tbody')
        if tbody:
            print('✓ 找到 #tbody 元素')
        else:
            print('✗ 未找到 #tbody 元素')

        await browser.close()
        print('✓ Playwright 测试通过')

asyncio.run(test_forum_access())
"
```

**验收标准**:
- ✅ 能成功访问论坛页面
- ✅ 找到 `#tbody` 元素
- ✅ 无超时或连接错误

---

### Test 3: 增量检查逻辑测试

**目的**: 验证增量检查逻辑正确工作

```bash
cd /home/ben/gemini-work/gemini-t66y/python

python3 -c "
from pathlib import Path
from src.scraper.utils import check_post_exists, mark_post_complete

# 创建测试目录
test_dir = Path('test_output/test_author/2026/02/test_post')
test_dir.mkdir(parents=True, exist_ok=True)

test_url = 'https://example.com/post/123'

# 测试 1: 空目录应该返回 False
print('测试 1: 空目录（缺少标记文件）')
result = check_post_exists(test_dir, test_url)
print(f'结果: {result} (预期: False)')
assert result == False, '应该返回 False'

# 测试 2: 创建标记后应该返回 True
print('\n测试 2: 创建完整性标记')
(test_dir / 'index.md').write_text('# Test')
mark_post_complete(test_dir, test_url, {'title': 'Test', 'author': 'Test'})
result = check_post_exists(test_dir, test_url)
print(f'结果: {result} (预期: True)')
assert result == True, '应该返回 True'

# 测试 3: URL 不匹配应该返回 False
print('\n测试 3: URL 不匹配')
result = check_post_exists(test_dir, 'https://example.com/post/456')
print(f'结果: {result} (预期: False)')
assert result == False, 'URL 不匹配应该返回 False'

# 清理
import shutil
shutil.rmtree('test_output')
print('\n✓ 所有增量检查测试通过')
"
```

**验收标准**:
- ✅ 空目录返回 False（需要归档）
- ✅ 有完整标记返回 True（跳过）
- ✅ URL 不匹配返回 False（防止冲突）

---

### Test 4: 帖子收集一致性测试 🔴 P0

**目的**: 对比 Python 和 Node.js 收集的帖子列表是否一致

**准备工作**：
```bash
cd /home/ben/gemini-work/gemini-t66y

# 1. 使用 Node.js 版本收集帖子（修改脚本输出为 JSON）
# 创建测试脚本
cat > test_collect_nodejs.js << 'EOF'
const { chromium } = require('playwright');
const fs = require('fs');

async function collectPosts() {
    const browser = await chromium.launch();
    const page = await browser.newPage();

    await page.goto('https://t66y.com/thread0806.php?fid=7', {
        waitUntil: 'domcontentloaded',
        timeout: 60000
    });

    await page.waitForSelector('#tbody', { timeout: 60000 });

    const postInfos = await page.$$eval('#tbody tr', rows => {
        return rows.slice(0, 10).map(row => {  // 只取前10个
            const authorElement = row.querySelector('.bl');
            const titleElement = row.querySelector('h3 > a');
            if (authorElement && titleElement) {
                return {
                    author: authorElement.textContent.trim(),
                    title: titleElement.textContent.trim(),
                    url: titleElement.href
                };
            }
            return null;
        }).filter(Boolean);
    });

    await browser.close();

    fs.writeFileSync('nodejs_posts.json', JSON.stringify(postInfos, null, 2));
    console.log(`收集到 ${postInfos.length} 个帖子`);
}

collectPosts();
EOF

node test_collect_nodejs.js
```

**Python 版本测试**：
```bash
cd /home/ben/gemini-work/gemini-t66y/python

python3 -c "
import asyncio
import json
from playwright.async_api import async_playwright

async def collect_posts_python():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto('https://t66y.com/thread0806.php?fid=7',
            wait_until='domcontentloaded',
            timeout=60000
        )

        await page.wait_for_selector('#tbody', timeout=60000)

        rows = await page.query_selector_all('#tbody tr')

        post_infos = []
        for row in rows[:10]:  # 只取前10个
            author_el = await row.query_selector('.bl')
            title_el = await row.query_selector('h3 > a')

            if author_el and title_el:
                author = (await author_el.text_content()).strip()
                title = (await title_el.text_content()).strip()
                url = await title_el.get_attribute('href')

                post_infos.append({
                    'author': author,
                    'title': title,
                    'url': url
                })

        await browser.close()

        with open('../python_posts.json', 'w', encoding='utf-8') as f:
            json.dump(post_infos, f, ensure_ascii=False, indent=2)

        print(f'收集到 {len(post_infos)} 个帖子')

asyncio.run(collect_posts_python())
"
```

**对比结果**：
```bash
cd /home/ben/gemini-work/gemini-t66y

# 使用 Python 对比两个 JSON 文件
python3 << 'EOF'
import json

with open('nodejs_posts.json', 'r', encoding='utf-8') as f:
    nodejs_posts = json.load(f)

with open('python_posts.json', 'r', encoding='utf-8') as f:
    python_posts = json.load(f)

print(f'Node.js 收集: {len(nodejs_posts)} 个帖子')
print(f'Python 收集:  {len(python_posts)} 个帖子')

# 对比 URL
nodejs_urls = set(p['url'] for p in nodejs_posts)
python_urls = set(p['url'] for p in python_posts)

if nodejs_urls == python_urls:
    print('✓ URL 列表完全一致')
else:
    print('✗ URL 列表不一致')
    print(f'  Node.js 独有: {nodejs_urls - python_urls}')
    print(f'  Python 独有:  {python_urls - nodejs_urls}')

# 对比详细信息
for i, (n, p) in enumerate(zip(nodejs_posts, python_posts)):
    if n['url'] == p['url']:
        if n['title'] == p['title'] and n['author'] == p['author']:
            print(f'✓ 帖子 {i+1} 完全一致')
        else:
            print(f'✗ 帖子 {i+1} 元数据不一致:')
            print(f'  标题: {n["title"]} vs {p["title"]}')
            print(f'  作者: {n["author"]} vs {p["author"]}')
    else:
        print(f'✗ 帖子 {i+1} URL 不匹配')
EOF
```

**验收标准**:
- ✅ 收集的帖子数量相同
- ✅ 所有 URL 完全一致
- ✅ 标题、作者信息一致

---

### Test 5: 内容提取一致性测试 🔴 P0

**目的**: 验证 Python 版本提取的内容与 Node.js 一致

**选择一个固定帖子进行测试**：

```bash
# 从上一步的 nodejs_posts.json 中选择第一个帖子
cd /home/ben/gemini-work/gemini-t66y

TEST_URL=$(python3 -c "import json; posts = json.load(open('nodejs_posts.json')); print(posts[0]['url'])")
echo "测试 URL: $TEST_URL"

# Node.js 版本提取
node -e "
const { chromium } = require('playwright');
const fs = require('fs');

async function extract() {
    const browser = await chromium.launch();
    const page = await browser.newPage();

    await page.goto('$TEST_URL', { waitUntil: 'domcontentloaded', timeout: 60000 });

    const title = await page.\$eval('h4.f16', el => el.textContent.trim()).catch(() => '');
    const author = await page.\$eval('.tr1.do_not_catch b', el => el.textContent.trim()).catch(() => '');
    const content = await page.\$eval('.tpc_content', el => el.textContent).catch(() => '');

    await browser.close();

    const result = {
        title,
        author,
        content_length: content.length
    };

    fs.writeFileSync('nodejs_extract.json', JSON.stringify(result, null, 2));
    console.log('Node.js 提取完成');
}

extract();
"
```

**Python 版本提取**：
```bash
cd /home/ben/gemini-work/gemini-t66y/python

python3 << EOF
import asyncio
import json
from playwright.async_api import async_playwright

async def extract():
    test_url = '''$TEST_URL'''

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(test_url, wait_until='domcontentloaded', timeout=60000)

        # 提取标题
        try:
            title_el = await page.query_selector('h4.f16')
            title = (await title_el.text_content()).strip() if title_el else ''
        except:
            title = ''

        # 提取作者
        try:
            author_el = await page.query_selector('.tr1.do_not_catch b')
            author = (await author_el.text_content()).strip() if author_el else ''
        except:
            author = ''

        # 提取内容
        try:
            content_el = await page.query_selector('.tpc_content')
            content = await content_el.text_content() if content_el else ''
        except:
            content = ''

        await browser.close()

        result = {
            'title': title,
            'author': author,
            'content_length': len(content)
        }

        with open('../python_extract.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print('Python 提取完成')

asyncio.run(extract())
EOF
```

**对比结果**：
```bash
cd /home/ben/gemini-work/gemini-t66y

python3 << 'EOF'
import json

nodejs = json.load(open('nodejs_extract.json'))
python = json.load(open('python_extract.json'))

print('提取结果对比:')
print(f'标题: {"✓" if nodejs["title"] == python["title"] else "✗"}')
print(f'  Node.js: {nodejs["title"]}')
print(f'  Python:  {python["title"]}')

print(f'\n作者: {"✓" if nodejs["author"] == python["author"] else "✗"}')
print(f'  Node.js: {nodejs["author"]}')
print(f'  Python:  {python["author"]}')

print(f'\n内容长度: {"✓" if abs(nodejs["content_length"] - python["content_length"]) < 10 else "✗"}')
print(f'  Node.js: {nodejs["content_length"]}')
print(f'  Python:  {python["content_length"]}')
print(f'  差异:    {abs(nodejs["content_length"] - python["content_length"])}')
EOF
```

**验收标准**:
- ✅ 标题完全一致
- ✅ 作者完全一致
- ✅ 内容长度差异 < 10 字符（允许空格差异）

---

### Test 6: 完整归档流程测试

**目的**: 端到端测试完整的归档流程

**前置条件**: 已有至少一个关注的作者

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 1. 查看当前关注列表
python3 -c "
from src.config.manager import ConfigManager
cm = ConfigManager()
config = cm.load()

if config['followed_authors']:
    print(f'当前关注: {len(config[\"followed_authors\"])} 位作者')
    for author in config['followed_authors'][:3]:
        print(f'  - {author[\"name\"]}')
else:
    print('无关注作者，请先使用菜单添加')
"

# 2. 运行 Python 版本归档（测试模式）
python3 << 'EOF'
import asyncio
from src.config.manager import ConfigManager
from src.scraper.archiver import Archiver
from src.utils.logger import setup_logger

async def test_archive():
    cm = ConfigManager()
    config = cm.load()

    # 设置日志
    logger = setup_logger(config)

    # 创建归档器
    archiver = Archiver(config)

    # 选择一个作者测试
    if not config['followed_authors']:
        print('没有关注的作者')
        return

    test_author = config['followed_authors'][0]['name']
    print(f'测试归档作者: {test_author}')

    # 执行归档
    stats = await archiver.archive_authors([test_author])

    print(f'\n归档统计:')
    print(f'  总计: {stats["total"]}')
    print(f'  新增: {stats["new"]}')
    print(f'  跳过: {stats["skipped"]}')
    print(f'  失败: {stats["failed"]}')

    return stats

stats = asyncio.run(test_archive())
EOF
```

**验收标准**:
- ✅ 归档过程无异常
- ✅ 新增帖子正确保存到文件系统
- ✅ 目录结构正确：`{作者}/{年}/{月}/{标题}/`
- ✅ 包含 `index.md` 和 `.complete` 文件
- ✅ 图片/视频正确下载到 `photo/` 和 `video/` 子目录
- ✅ 再次运行时正确跳过已归档帖子

**手动检查**：
```bash
cd /home/ben/gemini-work/gemini-t66y

# 查看归档目录结构
tree -L 4 论坛存档/ | head -30

# 检查第一个帖子的内容
find 论坛存档 -name "index.md" | head -1 | xargs cat | head -20
```

---

### Test 7: 性能基准测试

**目的**: 确保 Python 版本性能不低于 Node.js

```bash
cd /home/ben/gemini-work/gemini-t66y

# 清空归档目录（谨慎！）
# rm -rf 论坛存档/*

# 1. 测试 Node.js 版本
time node archive_posts.js "测试作者" > nodejs_perf.log 2>&1

# 2. 测试 Python 版本
cd python
time python3 -c "
import asyncio
from src.scraper.archiver import Archiver
from src.config.manager import ConfigManager

async def benchmark():
    config = ConfigManager().load()
    archiver = Archiver(config)
    await archiver.archive_authors(['测试作者'])

asyncio.run(benchmark())
" > ../python_perf.log 2>&1

# 3. 对比时间
echo "Node.js 耗时:"
grep "real" nodejs_perf.log

echo "Python 耗时:"
grep "real" python_perf.log
```

**验收标准**:
- ✅ Python 版本耗时不超过 Node.js 版本的 120%
- ✅ 内存使用合理（< 500MB）

---

### Test 8: 菜单集成测试

**目的**: 验证 Python 爬虫集成到菜单系统

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 修改配置开启 Python 爬虫
python3 -c "
from src.config.manager import ConfigManager

cm = ConfigManager()
config = cm.load()

# 开启实验性 Python 爬虫
config.setdefault('experimental', {})['use_python_scraper'] = True

cm.save(config)
print('✓ 已开启 use_python_scraper')
"

# 运行主菜单
python main.py
# 手动测试：
# 1. 选择 [3] 立即更新所有作者
# 2. 观察是否调用 Python 版本（而非 Node.js）
# 3. 检查归档结果
```

**验收标准**:
- ✅ 菜单显示正确
- ✅ "立即更新"调用 Python 爬虫（而非 NodeJSBridge）
- ✅ 实时显示进度
- ✅ 归档成功

---

### Test 9: 回滚机制测试

**目的**: 验证出错时能自动回退到 Node.js

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 1. 确保配置了回退机制
python3 -c "
from src.config.manager import ConfigManager

cm = ConfigManager()
config = cm.load()

config.setdefault('experimental', {})['use_python_scraper'] = True
config['experimental']['fallback_to_nodejs'] = True

cm.save(config)
print('✓ 已配置回退机制')
"

# 2. 手动制造错误（修改 Archiver 代码抛出异常）
# 3. 运行菜单，观察是否自动回退
```

**验收标准**:
- ✅ Python 版本出错时显示警告
- ✅ 自动切换到 Node.js 版本
- ✅ 功能仍然可用

---

### Test 10: 清理 Node.js 桥接代码

**目的**: 确认 Python 版本完全替换后可以安全移除 Node.js

```bash
cd /home/ben/gemini-work/gemini-t66y/python

# 1. 移除配置中的 legacy 设置
python3 -c "
from src.config.manager import ConfigManager

cm = ConfigManager()
config = cm.load()

# 移除 legacy 配置
if 'legacy' in config:
    del config['legacy']

# 移除 experimental（已成为默认）
if 'experimental' in config:
    del config['experimental']

cm.save(config)
print('✓ 已清理配置')
"

# 2. 移除桥接代码
# rm -rf src/bridge/

# 3. 从 main_menu.py 移除桥接相关代码
# 4. 测试所有功能仍然正常
```

**验收标准**:
- ✅ 配置文件不再包含 `legacy` 和 `experimental`
- ✅ 桥接代码已删除
- ✅ 所有菜单功能正常工作
- ✅ 无 Node.js 依赖

---

## 📊 完整验收清单

```
Phase 2 验收清单
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ 环境与依赖
  □ Playwright 安装成功
  □ Playwright 浏览器安装成功
  □ 所有 Python 依赖安装成功
  □ 依赖检查脚本通过

□ 核心功能一致性
  □ 文件名安全化与 Node.js 一致 (P0)
  □ 帖子收集结果一致 (P0)
  □ 内容提取结果一致 (P0)
  □ 媒体下载功能正常
  □ Markdown 生成格式正确

□ 增量逻辑
  □ 空目录正确识别为需要归档
  □ 已完成目录正确跳过
  □ URL hash 验证工作
  □ 重复运行不会重复下载

□ 错误处理
  □ 网络错误时正确重试
  □ 下载失败时正确记录
  □ 日志文件正确生成
  □ 异常有详细堆栈信息

□ 性能
  □ 归档速度不低于 Node.js 版本 80%
  □ 内存使用合理
  □ 并发下载工作正常
  □ 防反爬延迟生效

□ 集成测试
  □ 菜单正确调用 Python 爬虫
  □ 实时进度显示正常
  □ 配置开关工作正常
  □ 回滚机制工作（如果实现）

□ 清理工作
  □ Node.js 桥接代码已移除
  □ 配置文件已清理
  □ 文档已更新
  □ 无残留调试代码
```

---

## 🐛 常见问题

### 问题 1: Playwright 浏览器下载失败

```
Error: Failed to download Chromium
```

**解决**:
```bash
# 设置代理（如果在国内）
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

# 重新安装
playwright install chromium
```

---

### 问题 2: 帖子收集数量不一致

**原因**: 论坛内容动态变化

**解决**: 在相同时间点运行对比测试，或使用固定的测试数据

---

### 问题 3: 内容长度有微小差异

**原因**: 空格、换行符处理差异

**解决**: 接受 < 10 字符的差异，重点检查内容完整性

---

### 问题 4: 性能明显慢于 Node.js

**可能原因**:
1. 未使用异步并发下载
2. 浏览器未使用 headless 模式
3. 延迟设置过大

**解决**:
```python
# 检查配置
config['advanced']['browser_headless'] = True
config['advanced']['parallel_downloads'] = 5
config['advanced']['rate_limit_delay'] = 0.5  # 不要设太大
```

---

## 📝 测试报告模板

```
Phase 2 测试报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试日期: 2026-02-__
测试人员: ____________
环境: Linux, Python 3.10, Playwright 1.42

━━━ 一致性测试 ━━━
[✅/❌] 文件名安全化一致
[✅/❌] 帖子收集一致
[✅/❌] 内容提取一致
[✅/❌] Markdown 生成一致

━━━ 功能测试 ━━━
[✅/❌] 增量检查逻辑
[✅/❌] 媒体下载
[✅/❌] 错误处理
[✅/❌] 日志记录

━━━ 性能测试 ━━━
Node.js 耗时: ____ 秒
Python 耗时:  ____ 秒
性能比率:     ____% (目标 < 120%)

━━━ 集成测试 ━━━
[✅/❌] 菜单集成
[✅/❌] 配置开关
[✅/❌] 实时显示

━━━ 发现的问题 ━━━
1.
2.
3.

━━━ 总体评价 ━━━
□ 通过，可以切换到 Python 版本
□ 通过，但有轻微问题需修复
□ 不通过，需要重大修复

备注:
```

---

## 🎯 Phase 2 完成标志

当以下条件全部满足时，Phase 2 验收通过：

1. ✅ 所有 P0 测试（文件名、收集、提取）100% 一致
2. ✅ 性能不低于 Node.js 版本 80%
3. ✅ 增量逻辑正确工作
4. ✅ 无严重 bug
5. ✅ 日志和错误处理完善
6. ✅ 文档完整更新

**验收通过后**，可以：
- 将 `use_python_scraper` 默认改为 `true`
- 移除 Node.js 桥接代码
- 进入 Phase 3 - 数据库开发

---

**文档版本**: 1.0
**最后更新**: 2026-02-11
**下一步**: 参考 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) 开始 Phase 2 实施
