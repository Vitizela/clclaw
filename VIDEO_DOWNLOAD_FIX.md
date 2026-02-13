# 视频下载问题修复

**问题**: 视频无法页内播放，下载的"视频"实际上是 HTML 错误页面

**日期**: 2026-02-12

---

## 🔍 问题表现

### 现象
- 用户报告：视频无法页内播放
- 视频文件只有 594 字节
- 文件类型：`HTML document` 而不是 `video/mp4`

### 实际内容
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>imgly.net has expired</title>
</head>
<body>
    <h1>imgly.net has expired</h1>
</body>
</html>
```

---

## 🔎 根因分析

### 1. 外部图床问题 🔴
论坛使用外部图床（imgly.net）托管视频：
- ❌ 图床已过期/删除
- ❌ 返回 HTML 错误页面而不是视频
- ❌ HTTP 状态码仍然是 200 OK

### 2. 下载器未验证内容类型 ⚠️

**当前代码** (`downloader.py:130-147`):
```python
async with session.get(url, headers=headers) as response:
    # 206 表示部分内容（断点续传），200 表示完整下载
    if response.status in (200, 206):
        # 206 表示服务器支持断点续传，追加写入
        mode = 'ab' if response.status == 206 else 'wb'

        with open(temp_path, mode) as f:
            async for chunk in response.content.iter_chunked(8192):
                f.write(chunk)

        # 下载完成，重命名临时文件
        temp_path.rename(output_path)

        # 创建完成标记
        self._mark_download_complete(output_path)

        return True
```

**问题点**:
- ✅ 检查 HTTP 状态码（200, 206）
- ❌ **未检查 Content-Type**（可能是 text/html）
- ❌ **未检查文件大小**（HTML 错误页面通常很小）
- ❌ **未验证文件格式**（文件魔数）

---

## 💡 解决方案

### 方案 A: 添加内容类型验证（推荐） ⭐⭐⭐⭐⭐

修改 `downloader.py` 的 `_download_single` 方法：

```python
async def _download_single(self, url: str, output_path: Path) -> bool:
    """下载单个文件（带重试和内容验证）

    Args:
        url: File URL
        output_path: Output file path

    Returns:
        True if successful, False otherwise
    """
    async with self.semaphore:
        # 检查文件是否已完整下载
        if self._is_download_complete(output_path):
            self.logger.debug(f"文件已存在，跳过: {output_path.name}")
            return True

        # 获取已下载的大小（断点续传）
        downloaded_size = 0
        temp_path = output_path.with_suffix(output_path.suffix + '.downloading')

        if temp_path.exists():
            downloaded_size = temp_path.stat().st_size
            self.logger.info(
                f"继续下载 {output_path.name}，已下载 {downloaded_size} 字节"
            )

        for attempt in range(self.retry_count):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # 设置 Range 头实现断点续传
                    headers = {}
                    if downloaded_size > 0:
                        headers['Range'] = f'bytes={downloaded_size}-'

                    async with session.get(url, headers=headers) as response:
                        # 206 表示部分内容（断点续传），200 表示完整下载
                        if response.status in (200, 206):
                            # ========== 新增：内容类型验证 ==========
                            content_type = response.headers.get('Content-Type', '').lower()

                            # 检查是否是 HTML 错误页面
                            if 'text/html' in content_type:
                                self.logger.warning(
                                    f"下载失败 {url}: 返回 HTML 页面而不是媒体文件 "
                                    f"(Content-Type: {content_type})"
                                )
                                # 清理临时文件
                                if temp_path.exists():
                                    temp_path.unlink()
                                return False

                            # 验证是否是预期的媒体类型
                            expected_types = [
                                'image/', 'video/', 'application/octet-stream'
                            ]
                            if not any(t in content_type for t in expected_types):
                                self.logger.warning(
                                    f"下载失败 {url}: 意外的 Content-Type: {content_type}"
                                )
                                if temp_path.exists():
                                    temp_path.unlink()
                                return False

                            # ========== 新增：文件大小验证 ==========
                            content_length = response.headers.get('Content-Length')
                            if content_length:
                                file_size = int(content_length)
                                # 如果文件小于 1KB，可能是错误页面
                                if file_size < 1024:
                                    self.logger.warning(
                                        f"下载失败 {url}: 文件太小 ({file_size} 字节)，"
                                        f"可能是错误页面"
                                    )
                                    if temp_path.exists():
                                        temp_path.unlink()
                                    return False

                            # ========== 原有下载逻辑 ==========
                            # 206 表示服务器支持断点续传，追加写入
                            mode = 'ab' if response.status == 206 else 'wb'

                            with open(temp_path, mode) as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)

                            # ========== 新增：下载后验证 ==========
                            # 检查最终文件大小
                            if temp_path.exists():
                                final_size = temp_path.stat().st_size
                                if final_size < 1024:
                                    self.logger.warning(
                                        f"下载失败 {url}: 最终文件太小 ({final_size} 字节)"
                                    )
                                    temp_path.unlink()
                                    return False

                                # 验证文件魔数（可选但推荐）
                                if not self._verify_file_type(temp_path, output_path.suffix):
                                    self.logger.warning(
                                        f"下载失败 {url}: 文件格式验证失败"
                                    )
                                    temp_path.unlink()
                                    return False

                            # 下载完成，重命名临时文件
                            temp_path.rename(output_path)

                            # 创建完成标记
                            self._mark_download_complete(output_path)

                            self.logger.debug(f"下载成功: {output_path.name}")
                            return True

                        # ... 其他状态码处理 ...

            except Exception as e:
                if attempt < self.retry_count - 1:
                    self.logger.warning(f"重试 {attempt+1}/{self.retry_count}: {url}")
                    if temp_path.exists():
                        downloaded_size = temp_path.stat().st_size
                    await asyncio.sleep(1)
                else:
                    self.logger.error(f"下载失败 {url}: {str(e)}")

        return False

def _verify_file_type(self, file_path: Path, expected_ext: str) -> bool:
    """验证文件类型（通过魔数）

    Args:
        file_path: 文件路径
        expected_ext: 预期的文件扩展名（如 .jpg, .mp4）

    Returns:
        True if valid, False otherwise
    """
    try:
        # 读取文件头（前 12 字节足够识别大多数格式）
        with open(file_path, 'rb') as f:
            header = f.read(12)

        if not header:
            return False

        # 文件魔数映射
        magic_numbers = {
            # 图片格式
            '.jpg': [b'\xFF\xD8\xFF'],
            '.jpeg': [b'\xFF\xD8\xFF'],
            '.png': [b'\x89\x50\x4E\x47'],
            '.gif': [b'GIF87a', b'GIF89a'],
            '.webp': [b'RIFF'],
            '.bmp': [b'BM'],

            # 视频格式
            '.mp4': [b'\x00\x00\x00', b'ftyp'],  # MP4 容器
            '.webm': [b'\x1A\x45\xDF\xA3'],      # WebM/Matroska
            '.avi': [b'RIFF'],
            '.mov': [b'\x00\x00\x00', b'ftyp'],  # QuickTime
        }

        expected_magics = magic_numbers.get(expected_ext.lower(), [])
        if not expected_magics:
            # 未知格式，暂时通过
            return True

        # 检查文件头是否匹配任意一个魔数
        for magic in expected_magics:
            if header.startswith(magic) or magic in header[:8]:
                return True

        # 特殊处理：HTML 文件（明确拒绝）
        if header.startswith(b'<!DOCTYPE') or header.startswith(b'<html'):
            self.logger.warning(f"检测到 HTML 文件: {file_path.name}")
            return False

        return False

    except Exception as e:
        self.logger.error(f"文件类型验证失败: {str(e)}")
        return True  # 验证失败时暂时通过，避免误杀
```

### 关键改进点

| 改进项 | 旧版 | 新版 |
|--------|------|------|
| Content-Type 检查 | ❌ | ✅ 拒绝 text/html |
| 文件大小验证 | ❌ | ✅ 拒绝 < 1KB |
| 文件魔数验证 | ❌ | ✅ 验证文件格式 |
| HTML 明确拒绝 | ❌ | ✅ 检测 `<!DOCTYPE` |
| 错误清理 | ❌ | ✅ 删除无效文件 |

---

## 📋 实施步骤

### Step 1: 备份文件
```bash
cp python/src/scraper/downloader.py python/src/scraper/downloader.py.backup
```

### Step 2: 修改 `downloader.py`
1. 在 `_download_single` 方法中添加内容类型验证
2. 添加文件大小验证
3. 添加 `_verify_file_type` 方法

### Step 3: 清理无效文件
```bash
# 查找所有小于 1KB 的视频文件（可能是错误页面）
find /home/ben/Download/t66y -name "video_*.mp4" -size -1k

# 查找所有 HTML 类型的媒体文件
find /home/ben/Download/t66y -name "*.mp4" -o -name "*.jpg" | xargs file | grep HTML
```

### Step 4: 重新下载
删除无效文件和 `.complete` 标记，重新归档

---

## 🧪 测试用例

### Test 1: HTML 错误页面检测
**场景**: 下载 URL 返回 HTML 错误页面

**预期**:
```
WARNING - 下载失败 xxx: 返回 HTML 页面而不是媒体文件 (Content-Type: text/html)
```

### Test 2: 文件大小验证
**场景**: 下载的文件只有 500 字节

**预期**:
```
WARNING - 下载失败 xxx: 文件太小 (500 字节)，可能是错误页面
```

### Test 3: 文件魔数验证
**场景**: 文件扩展名是 .mp4 但内容是 HTML

**预期**:
```
WARNING - 检测到 HTML 文件: video_1.mp4
WARNING - 下载失败 xxx: 文件格式验证失败
```

### Test 4: 正常文件下载
**场景**: 下载真实的视频文件

**预期**:
```
DEBUG - 下载成功: video_1.mp4
```

---

## 🎯 预期效果

**修复前**:
```
✅ 下载成功: video_1.mp4 (594 B)  ← 实际上是 HTML 错误页面
❌ 视频无法播放
```

**修复后**:
```
⚠️  下载失败: 返回 HTML 页面而不是媒体文件
❌ 不创建无效文件
ℹ️  页面显示: "视频不可用"或隐藏视频部分
```

---

## 🚨 处理策略

### 对于无法下载的视频

**选项 1**: 显示友好的错误信息
```html
<div class="video-error">
    ⚠️ 视频不可用（外部链接已失效）
    <a href="原始URL">查看原始链接</a>
</div>
```

**选项 2**: 完全隐藏视频部分
```python
# 在模板中
{% if videos and valid_videos %}
<section>
    <h2>🎬 视频</h2>
    ...
</section>
{% endif %}
```

**选项 3**: 保留原始 URL 链接
```html
<div class="video-unavailable">
    <p>视频托管在外部平台，点击查看：</p>
    <a href="原始URL">观看视频</a>
</div>
```

---

**推荐行动**: 立即实施方案 A，预计 15 分钟完成。
