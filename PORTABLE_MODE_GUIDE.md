# 便携模式使用指南

> **版本**: v1.0  
> **更新日期**: 2026-02-18

---

## 快速开始

### 新用户

```bash
# 1. 安装环境
bash setup.sh

# 2. 运行程序（便携模式）
bash run.sh --target /media/usb/t66y

# 首次运行会启动配置向导
```

### 现有用户迁移

```bash
# 1. 安装环境（如果尚未安装）
bash setup.sh

# 2. 迁移现有数据
python python/tools/migrate_to_portable.py --target /media/usb/t66y

# 3. 使用便携模式运行
bash run.sh --target /media/usb/t66y
```

---

## 使用场景

### 场景 1：移动硬盘多电脑使用

```
电脑 A：
  bash run.sh --target /media/usb/t66y
  → 下载帖子到移动硬盘

电脑 B：
  bash run.sh --target /mnt/disk1/t66y
  → 继续使用，配置和数据都在移动硬盘
```

### 场景 2：云同步

```
归档目录放在 Dropbox：
  ~/Dropbox/t66y/

运行命令：
  bash run.sh --target ~/Dropbox/t66y

多台电脑自动同步配置和数据
```

### 场景 3：备份与恢复

```
备份：直接复制整个归档目录

恢复：
  1. 复制归档目录到新位置
  2. bash run.sh --target /新位置
  3. 完成！配置和数据自动加载
```

---

## 脚本使用

### setup.sh - 环境安装

```bash
# 完整安装
bash setup.sh

# 快速安装（跳过 Playwright 浏览器）
bash setup.sh --quick

# 显示帮助
bash setup.sh --help
```

### run.sh - 运行程序

```bash
# 便携模式
bash run.sh --target /path/to/archive
bash run.sh -t /path/to/archive

# 传统模式
bash run.sh

# 启动配置向导
bash run.sh --setup

# 参数透传
bash run.sh --target /path -- --help

# 显示帮助
bash run.sh --help
```

---

## 目录结构

```
归档目录/                    # 您指定的路径
├── .t66y/                   # 系统目录（隐藏）
│   ├── config.yaml          # 配置文件
│   └── forum_data.db        # 数据库
├── 作者1/
│   └── 2026/02/帖子标题/
│       ├── content.html
│       ├── photo/
│       └── video/
└── 作者2/
    └── ...
```

---

## 常见问题

### Q: 如何切回传统模式？

```bash
# 不带 --target 参数即可
bash run.sh
```

### Q: 两台电脑同时使用会怎样？

SQLite 数据库会在写入时锁定。建议：
- 避免两台电脑同时写入
- 读取操作可以并发进行
- 如果提示数据库锁定，等待几秒后重试

### Q: 如何备份数据？

直接复制整个归档目录即可，包含：
- `.t66y/` - 配置和数据库
- 作者目录 - 帖子内容

### Q: 归档目录可以改名或移动吗？

可以！只需要：
1. 移动/重命名目录
2. 使用新路径运行：`bash run.sh --target /新路径`

### Q: 如何查看当前使用的配置？

```bash
# 查看配置文件
cat /归档目录/.t66y/config.yaml

# 或在程序内选择 [7] 系统设置 → 查看当前配置
```

---

## 故障排查

### 问题：提示 "归档目录不存在"

```bash
# 检查路径是否正确
ls /media/usb/t66y

# 如果是相对路径，先转换为绝对路径
bash run.sh --target $(pwd)/archive
```

### 问题：提示 "虚拟环境不存在"

```bash
# 先运行安装脚本
bash setup.sh
```

### 问题：数据库锁定

```
错误：database is locked

解决：
1. 确认没有其他程序在使用数据库
2. 等待几秒后重试
3. 如果持续锁定，删除 .t66y/forum_data.db-wal 文件
```

### 问题：配置丢失

```bash
# 检查配置文件
ls -la /归档目录/.t66y/

# 如果丢失，重新运行配置向导
bash run.sh --target /path --setup
```

---

## 对比：传统模式 vs 便携模式

| 项目 | 传统模式 | 便携模式 |
|------|----------|----------|
| 配置位置 | `python/config.yaml` | `归档目录/.t66y/config.yaml` |
| 数据库位置 | `python/data/` | `归档目录/.t66y/` |
| 多电脑使用 | 需手动同步 | 移动硬盘即插即用 |
| 备份复杂度 | 需备份多个位置 | 复制一个目录 |
| 启动命令 | `bash run.sh` | `bash run.sh --target /path` |

---

**文档版本**: v1.0  
**最后更新**: 2026-02-18
