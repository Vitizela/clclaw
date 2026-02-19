# 便携模式设计规范

> **版本**: v1.0  
> **状态**: 设计阶段  
> **创建日期**: 2026-02-18  
> **适用于**: AI 编程实施

---

## 1. 概述

### 1.1 目标

- 允许配置文件和数据库存储在归档目录中
- 支持多台电脑共享同一归档目录（移动硬盘、云同步等）
- 与传统模式完全兼容，可随时切换

### 1.2 适用场景

| 场景 | 描述 |
|------|------|
| 移动硬盘 | 在电脑A下载帖子，移动硬盘插到电脑B继续使用 |
| 云同步 | 归档目录放在 Dropbox/OneDrive，多电脑同步 |
| 备份迁移 | 整体复制归档目录即可完成数据迁移 |

### 1.3 术语定义

| 术语 | 说明 |
|------|------|
| 传统模式 | 配置在 `python/config.yaml`，数据库在 `python/data/` |
| 便携模式 | 配置和数据都在归档目录的 `.t66y/` 子目录 |
| 归档目录 | 存储帖子内容的根目录，如 `/media/usb/t66y` |
| 系统目录 | 归档目录下的 `.t66y/` 目录，存储配置和数据库 |

---

## 2. 架构设计

### 2.1 目录结构对比

#### 传统模式

```
项目目录/
├── python/
│   ├── config.yaml          # 配置文件
│   └── data/
│       └── forum_data.db    # 数据库
└── 论坛存档/                 # 归档内容（独立路径）
    └── 作者/YYYY/MM/帖子/
```

#### 便携模式

```
归档目录/                      # 用户指定，如 /media/usb/t66y
├── .t66y/                    # 系统目录（隐藏）
│   ├── config.yaml           # 配置文件
│   └── forum_data.db         # 数据库
├── 作者1/
│   └── YYYY/MM/帖子/
├── 作者2/
│   └── YYYY/MM/帖子/
└── ...
```

### 2.2 配置文件位置

**查找优先级**：

```
1. 命令行参数 --target 指定的路径/.t66y/config.yaml
2. 传统模式 python/config.yaml
```

### 2.3 数据库路径

**计算逻辑**：

```python
if target_path:  # 便携模式
    db_path = target_path / '.t66y' / 'forum_data.db'
else:  # 传统模式
    db_path = config['storage']['database_path']
```

### 2.4 参数传递流程

```
run.sh --target /path [其他参数]
    ↓
main.py --target /path [其他参数]
    ↓
ConfigManager(archive_path=/path)
    ↓
加载 /path/.t66y/config.yaml
    ↓
数据库路径 = /path/.t66y/forum_data.db
```

---

## 3. 启动参数

### 3.1 命令行参数

```bash
# 便携模式
python main.py --target /path/to/archive
python main.py -t /path/to/archive

# 传统模式
python main.py

# 参数透传
python main.py --target /path -- --help
python main.py --target /path -- --version
```

### 3.2 参数优先级

```
1. --target / -t    → 便携模式，使用指定路径
2. 无参数           → 传统模式
```

### 3.3 参数透传

`--` 之后的所有参数透传给 `main.py`：

```bash
bash run.sh --target /path -- --help
# 等同于：python main.py --target /path --help

bash run.sh --target /path -- update --author "作者名"
# 等同于：python main.py --target /path update --author "作者名"
```

---

## 4. 脚本设计

### 4.1 setup.sh

**位置**: 项目根目录  
**用途**: 创建运行环境

```bash
#!/bin/bash
# 用法：
#   bash setup.sh          # 完整安装
#   bash setup.sh --quick  # 快速安装（跳过 Playwright）
#   bash setup.sh --help   # 显示帮助
```

**功能清单**：

| 步骤 | 说明 | 失败处理 |
|------|------|----------|
| 1. 检查 Python | 版本 >= 3.10 | 提示安装 |
| 2. 创建 venv | `python/venv/` | 提示权限问题 |
| 3. 安装依赖 | `pip install -r requirements.txt` | 提示网络问题 |
| 4. 安装 Playwright | `playwright install chromium` | 可选，--quick 跳过 |
| 5. 检测字体 | 检查中文字体 | 提示安装命令 |
| 6. 显示后续步骤 | 使用说明 | - |

### 4.2 run.sh

**位置**: 项目根目录  
**用途**: 运行程序

```bash
#!/bin/bash
# 用法：
#   bash run.sh --target /path/to/archive   # 便携模式
#   bash run.sh --setup                     # 配置向导
#   bash run.sh                             # 检测模式
#   bash run.sh --help                      # 显示帮助
```

**参数说明**：

| 参数 | 说明 |
|------|------|
| `-t, --target PATH` | 指定归档目录（便携模式） |
| `--setup` | 启动配置向导（传统模式） |
| `--` | 后续参数透传给 main.py |
| `-h, --help` | 显示帮助 |

**逻辑流程**：

```
1. 检查 venv 是否存在
   └─ 不存在 → 提示运行 setup.sh，退出

2. 解析命令行参数
   ├─ --target PATH → 设置便携模式
   ├─ --setup → 启动配置向导
   └─ 无参数 → 检测已有配置

3. 无 --target 时
   ├─ 检测便携配置是否存在
   │   ├─ 存在 → 使用便携模式
   │   └─ 不存在 → 显示首次运行提示
   └─ 显示迁移说明

4. 激活 venv

5. 运行 python main.py [参数]

6. 处理退出状态
```

---

## 5. 代码修改清单

### 5.1 main.py

**文件**: `python/main.py`

**修改 1**: 添加参数解析

```python
# 在文件开头添加
import argparse

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='论坛作者订阅归档系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py --target /media/usb/t66y    # 便携模式
  python main.py --target ~/archive          # 便携模式
  python main.py                              # 传统模式
        '''
    )
    parser.add_argument(
        '-t', '--target',
        type=str,
        default=None,
        metavar='PATH',
        help='归档目录路径（便携模式）'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='启动配置向导'
    )
    return parser.parse_args()
```

**修改 2**: 更新 main() 函数

```python
def main():
    """主入口"""
    args = parse_args()
    
    try:
        # 确定 ConfigManager 参数
        archive_path = None
        if args.target:
            archive_path = Path(args.target).resolve()
            if not archive_path.exists():
                print(f"❌ 归档目录不存在: {archive_path}")
                sys.exit(1)
        
        # 检查配置文件
        config_manager = ConfigManager(archive_path=archive_path)
        
        # --setup 强制启动配置向导
        if args.setup or not config_manager.config_exists():
            if not args.setup:
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print("  检测到首次运行，启动配置向导...")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print()
            
            wizard = ConfigWizard(archive_path=archive_path)
            wizard.run()
            print()
            print("配置完成！即将进入主菜单...")
            input("按 Enter 继续...")
        
        # 加载配置
        config = config_manager.load()
        
        # 设置数据库路径
        db_path = config_manager.get_database_path()
        
        # 判断模式
        if len(sys.argv) > 1:
            # 命令行模式（过滤掉 --target 参数）
            cli = CLI(config)
            cli.run()
        else:
            # 菜单模式
            menu = MainMenu(config)
            menu.run()

    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
```

### 5.2 config/manager.py

**文件**: `python/src/config/manager.py`

**修改 1**: 更新 `__init__` 方法

```python
from pathlib import Path
from typing import Dict, Any, Optional, Union

class ConfigManager:
    """配置文件管理器"""

    DEFAULT_CONFIG = {
        # ... 保持不变 ...
    }

    def __init__(
        self, 
        config_path: str = "config.yaml",
        archive_path: Optional[Union[str, Path]] = None
    ):
        """初始化配置管理器

        Args:
            config_path: 配置文件名
            archive_path: 归档目录路径（便携模式）
        """
        self.archive_path = Path(archive_path) if archive_path else None
        
        if self.archive_path:
            # 便携模式：配置在 归档目录/.t66y/config.yaml
            self.portable_dir = self.archive_path / '.t66y'
            self.config_path = self.portable_dir / config_path
        else:
            # 传统模式：配置在 python/config.yaml
            self.config_path = Path(__file__).parent.parent.parent / config_path
            self.portable_dir = None

        # 旧配置文件路径（项目根目录/config.json）
        self.legacy_json_path = self.config_path.parent.parent / "config.json"
```

**修改 2**: 更新 `save` 方法

```python
def save(self, config: Dict[str, Any]) -> None:
    """保存配置

    Args:
        config: 配置字典
    """
    # 更新时间戳
    config['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 确保目录存在
    self.config_path.parent.mkdir(parents=True, exist_ok=True)

    # 便携模式下更新路径配置
    if self.archive_path:
        config.setdefault('storage', {})
        config['storage']['archive_path'] = str(self.archive_path)
        config['storage']['database_path'] = str(self.portable_dir / 'forum_data.db')

    with open(self.config_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            config,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            indent=2
        )
```

**修改 3**: 新增 `get_database_path` 方法

```python
def get_database_path(self) -> Path:
    """获取数据库文件路径

    Returns:
        数据库文件路径
    """
    if self.archive_path:
        # 便携模式
        return self.portable_dir / 'forum_data.db'
    else:
        # 传统模式：从配置读取
        config = self.load()
        db_path = config.get('storage', {}).get('database_path', './data/forum_data.db')
        return Path(db_path)
```

**修改 4**: 新增 `is_portable_mode` 属性

```python
@property
def is_portable_mode(self) -> bool:
    """是否为便携模式"""
    return self.archive_path is not None
```

### 5.3 database/connection.py

**文件**: `python/src/database/connection.py`

**修改**: 更新 `get_default_connection` 函数

```python
def get_default_connection(
    db_path: Optional[str] = None,
    config_manager: Optional['ConfigManager'] = None
) -> DatabaseConnection:
    """获取默认数据库连接

    Args:
        db_path: 数据库路径（可选）
        config_manager: 配置管理器（可选，用于获取路径）

    Returns:
        DatabaseConnection 实例
    """
    if db_path is None:
        if config_manager is None:
            # 延迟导入避免循环依赖
            from config.manager import ConfigManager
            config_manager = ConfigManager()
        
        db_path = str(config_manager.get_database_path())
    
    return DatabaseConnection.get_instance(db_path)
```

### 5.4 config/wizard.py

**文件**: `python/src/config/wizard.py`

**修改**: 更新 `__init__` 和保存逻辑

```python
class ConfigWizard:
    """配置向导"""

    def __init__(self, archive_path: Optional[Path] = None):
        """初始化配置向导

        Args:
            archive_path: 归档目录路径（便携模式）
        """
        self.archive_path = archive_path
        self.config_manager = ConfigManager(archive_path=archive_path)

    def run(self):
        """运行配置向导"""
        # ... 现有逻辑 ...
        
        # 保存时使用 ConfigManager
        self.config_manager.save(config)
```

### 5.5 tools/migrate_to_portable.py

**文件**: `python/tools/migrate_to_portable.py`（新建）

```python
#!/usr/bin/env python3
"""
迁移工具：将传统模式数据迁移到便携模式

用法：
  python tools/migrate_to_portable.py --target /path/to/archive
"""

import sys
import shutil
from pathlib import Path

def migrate_to_portable(target_path: str):
    """
    迁移现有数据到便携模式
    
    Args:
        target_path: 目标归档目录
    """
    target = Path(target_path).resolve()
    
    # 检查目标目录
    if not target.exists():
        print(f"创建归档目录: {target}")
        target.mkdir(parents=True, exist_ok=True)
    
    # 创建系统目录
    portable_dir = target / '.t66y'
    portable_dir.mkdir(exist_ok=True)
    
    # 源路径
    project_root = Path(__file__).parent.parent
    python_dir = project_root / 'python'
    
    old_config = python_dir / 'config.yaml'
    old_db = python_dir / 'data' / 'forum_data.db'
    
    # 迁移配置
    if old_config.exists():
        new_config = portable_dir / 'config.yaml'
        if new_config.exists():
            print(f"⚠️  目标配置已存在: {new_config}")
            print("   跳过配置迁移")
        else:
            shutil.copy2(old_config, new_config)
            print(f"✓ 配置已迁移: {new_config}")
            
            # 更新配置中的路径
            import yaml
            with open(new_config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            config['storage']['archive_path'] = str(target)
            config['storage']['database_path'] = str(portable_dir / 'forum_data.db')
            
            with open(new_config, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
            
            print(f"✓ 配置路径已更新")
    
    # 迁移数据库
    if old_db.exists():
        new_db = portable_dir / 'forum_data.db'
        if new_db.exists():
            print(f"⚠️  目标数据库已存在: {new_db}")
            print("   跳过数据库迁移")
        else:
            shutil.copy2(old_db, new_db)
            print(f"✓ 数据库已迁移: {new_db}")
    
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  迁移完成！")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("使用以下命令启动便携模式：")
    print(f"  bash run.sh --target {target}")
    print()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='迁移到便携模式')
    parser.add_argument(
        '-t', '--target',
        required=True,
        help='目标归档目录路径'
    )
    
    args = parser.parse_args()
    migrate_to_portable(args.target)
```

---

## 6. 数据迁移

### 6.1 迁移工具

**工具**: `python/tools/migrate_to_portable.py`

```bash
# 迁移到便携模式
python python/tools/migrate_to_portable.py --target /media/usb/t66y
```

### 6.2 迁移步骤

```
1. 创建 归档目录/.t66y/ 目录
2. 复制 python/config.yaml → .t66y/config.yaml
3. 复制 python/data/forum_data.db → .t66y/forum_data.db
4. 更新 config.yaml 中的路径配置
5. 显示使用说明
```

### 6.3 回退方案

便携模式下仍可使用传统模式：

```bash
# 不带 --target 参数即为传统模式
python main.py
```

原配置文件不会被删除，只是复制。

---

## 7. 兼容性设计

### 7.1 两种模式共存

| 模式 | 命令 | 配置位置 | 数据库位置 |
|------|------|----------|------------|
| 传统 | `python main.py` | `python/config.yaml` | `python/data/forum_data.db` |
| 便携 | `python main.py --target /path` | `/path/.t66y/config.yaml` | `/path/.t66y/forum_data.db` |

### 7.2 配置文件格式

便携模式下的 `config.yaml` 示例：

```yaml
version: '2.0'
storage:
  archive_path: /media/usb/t66y        # 绝对路径
  database_path: /media/usb/t66y/.t66y/forum_data.db
  # ...
```

### 7.3 版本兼容

- 便携模式配置增加 `portable_mode: true` 标记（可选）
- 系统自动检测并适配

---

## 8. 测试计划

### 8.1 单元测试

| 测试项 | 说明 |
|--------|------|
| ConfigManager 初始化 | 测试传统模式和便携模式 |
| 配置路径计算 | 验证 `.t66y/config.yaml` 路径 |
| 数据库路径计算 | 验证 `get_database_path()` |

### 8.2 集成测试

| 测试项 | 说明 |
|--------|------|
| 首次运行（便携模式） | 创建配置向导 |
| 已有配置运行 | 正确加载配置 |
| 数据库初始化 | 在正确位置创建数据库 |

### 8.3 迁移测试

| 测试项 | 说明 |
|--------|------|
| 迁移工具执行 | 配置和数据库正确复制 |
| 迁移后运行 | 便携模式正常工作 |
| 数据完整性 | 迁移后数据完整 |

---

## 9. 实施检查清单

- [ ] 创建 `setup.sh` 脚本
- [ ] 创建 `run.sh` 脚本
- [ ] 修改 `main.py` 添加参数解析
- [ ] 修改 `config/manager.py` 支持便携模式
- [ ] 修改 `database/connection.py` 动态路径
- [ ] 修改 `config/wizard.py` 支持便携模式
- [ ] 创建 `tools/migrate_to_portable.py`
- [ ] 更新文档
- [ ] 测试传统模式兼容性
- [ ] 测试便携模式功能
- [ ] 测试迁移工具

---

**文档版本**: v1.0  
**最后更新**: 2026-02-18
