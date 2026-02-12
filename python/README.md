# Python 版本使用说明

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行系统

```bash
# 菜单模式（推荐）
python main.py
```

首次运行会启动配置向导，按提示完成配置。

## 功能说明

### Phase 1（当前）

- ✅ 菜单式交互界面
- ✅ 配置管理（YAML 格式）
- ✅ 从 config.json 自动迁移
- ✅ 关注新作者（通过 Node.js 桥接）
- ✅ 查看关注列表
- ✅ 立即更新所有作者
- ✅ 取消关注作者
- ✅ 系统设置

### Phase 2-5（开发中）

- ⚪ Python 爬虫核心
- ⚪ 数据库与统计
- ⚪ 数据分析（词云、趋势图）
- ⚪ 完整命令行模式

## 目录结构

```
python/
├── main.py              # 主入口
├── requirements.txt     # 依赖清单
├── config.yaml          # 配置文件（自动生成）
│
└── src/
    ├── config/          # 配置管理
    │   ├── manager.py   # 配置读写
    │   └── wizard.py    # 配置向导
    ├── menu/            # 菜单系统
    │   └── main_menu.py
    ├── bridge/          # Node.js 桥接（临时）
    │   └── nodejs_bridge.py
    ├── cli/             # 命令行接口
    ├── utils/           # 工具模块
    └── ...
```

## 故障排除

### 问题1：导入错误

```
ModuleNotFoundError: No module named 'src'
```

**解决**：确保在 `python/` 目录下运行
```bash
cd python
python main.py
```

### 问题2：依赖未安装

```
ModuleNotFoundError: No module named 'yaml'
```

**解决**：安装依赖
```bash
pip install -r requirements.txt
```

### 问题3：Node.js 脚本找不到

```
FileNotFoundError: Node.js 目录不存在
```

**解决**：检查 Node.js 脚本位置，修改 config.yaml：
```yaml
legacy:
  nodejs_path: "../"  # 相对于 python/ 的路径
```

## 更多文档

- **完整文档**：见项目根目录的 `ADR-002_Python_Migration_Plan.md`
- **实施指南**：见 `MIGRATION_GUIDE.md`
- **进度追踪**：见 `MIGRATION_PROGRESS.md`
