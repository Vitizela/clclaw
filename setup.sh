#!/bin/bash
# =============================================================================
# T66Y 论坛归档系统 - 环境安装脚本
# =============================================================================
# 版本: v1.0
# 用法:
#   bash setup.sh          # 完整安装
#   bash setup.sh --quick  # 快速安装（跳过 Playwright）
#   bash setup.sh --help   # 显示帮助
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_DIR="$SCRIPT_DIR/python"

# 默认设置
SKIP_PLAYWRIGHT=false

# =============================================================================
# 帮助信息
# =============================================================================
show_help() {
    echo "T66Y 论坛归档系统 - 环境安装脚本"
    echo ""
    echo "用法:"
    echo "  bash setup.sh              完整安装（推荐）"
    echo "  bash setup.sh --quick      快速安装（跳过 Playwright 浏览器）"
    echo "  bash setup.sh --help       显示此帮助"
    echo ""
    echo "说明:"
    echo "  完整安装包括：Python 依赖 + Playwright 浏览器（约 500MB）"
    echo "  快速安装只包括：Python 依赖（约 50MB）"
    echo "  如果不需要爬虫功能，可以使用快速安装"
    echo ""
}

# =============================================================================
# 解析参数
# =============================================================================
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick|-q)
                SKIP_PLAYWRIGHT=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}未知参数: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
}

# =============================================================================
# 检查 Python 版本
# =============================================================================
check_python() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  步骤 1/6: 检查 Python 环境${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 未安装${NC}"
        echo ""
        echo "请先安装 Python 3.10 或更高版本："
        echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
        echo "  macOS: brew install python@3.11"
        echo "  Windows: 访问 https://www.python.org/downloads/"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 10 ]]; then
        echo -e "${RED}❌ Python 版本过低: $PYTHON_VERSION${NC}"
        echo "需要 Python 3.10 或更高版本"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Python 版本: $PYTHON_VERSION${NC}"
}

# =============================================================================
# 创建虚拟环境
# =============================================================================
create_venv() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  步骤 2/6: 创建虚拟环境${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [[ -d "$PYTHON_DIR/venv" ]]; then
        echo -e "${YELLOW}⚠ 虚拟环境已存在，跳过创建${NC}"
        return
    fi
    
    cd "$PYTHON_DIR"
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
}

# =============================================================================
# 安装依赖
# =============================================================================
install_dependencies() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  步骤 3/6: 安装 Python 依赖${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # 检查虚拟环境是否存在
    if [[ ! -f "$PYTHON_DIR/venv/bin/activate" ]]; then
        echo -e "${RED}❌ 虚拟环境不存在，请先运行 create_venv${NC}"
        exit 1
    fi
    
    cd "$PYTHON_DIR"
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip -q
    
    # 安装依赖
    if [[ -f "requirements.txt" ]]; then
        echo "正在安装依赖..."
        pip install -r requirements.txt -q
        echo -e "${GREEN}✓ 依赖安装成功${NC}"
    else
        echo -e "${RED}❌ 未找到 requirements.txt${NC}"
        exit 1
    fi
}

# =============================================================================
# 安装 Playwright
# =============================================================================
install_playwright() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  步骤 4/6: 安装 Playwright 浏览器${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [[ "$SKIP_PLAYWRIGHT" == true ]]; then
        echo -e "${YELLOW}⚠ 跳过 Playwright 安装（--quick 模式）${NC}"
        echo "  如需爬虫功能，请稍后运行："
        echo "  source python/venv/bin/activate && playwright install chromium"
        return
    fi
    
    # 检查虚拟环境是否存在
    if [[ ! -f "$PYTHON_DIR/venv/bin/activate" ]]; then
        echo -e "${RED}❌ 虚拟环境不存在${NC}"
        return
    fi
    
    cd "$PYTHON_DIR"
    source venv/bin/activate
    
    echo "正在安装 Chromium 浏览器（约 150MB）..."
    if playwright install chromium 2>/dev/null; then
        echo -e "${GREEN}✓ Playwright 浏览器安装成功${NC}"
    else
        echo -e "${YELLOW}⚠ Playwright 安装失败，可能需要手动安装${NC}"
        echo "  手动安装命令：source python/venv/bin/activate && playwright install chromium"
    fi
}

# =============================================================================
# 检查中文字体
# =============================================================================
check_font() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  步骤 5/6: 检查中文字体${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if command -v fc-list &> /dev/null; then
        if fc-list :lang=zh 2>/dev/null | grep -q .; then
            echo -e "${GREEN}✓ 检测到中文字体${NC}"
        else
            echo -e "${YELLOW}⚠ 未检测到中文字体${NC}"
            echo "  图表中的中文可能显示为方块"
            echo "  安装方法："
            echo "    Ubuntu/Debian: sudo apt install fonts-wqy-zenhei"
            echo "    macOS: 系统自带中文字体"
            echo "    Windows: 系统自带中文字体"
        fi
    else
        echo -e "${YELLOW}⚠ 无法检测字体（fc-list 不可用）${NC}"
    fi
}

# =============================================================================
# 显示完成信息
# =============================================================================
show_complete() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  步骤 6/6: 安装完成${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}✅ 环境安装完成！${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  📚 使用说明"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "【便携模式】推荐"
    echo "  bash run.sh --target /path/to/archive"
    echo ""
    echo "  示例："
    echo "  bash run.sh --target /media/usb/t66y"
    echo "  bash run.sh --target ~/Dropbox/t66y"
    echo ""
    echo "【传统模式】"
    echo "  bash run.sh"
    echo ""
    echo "【迁移现有数据】"
    echo "  python python/tools/migrate_to_portable.py --target /path/to/archive"
    echo ""
    echo "【帮助】"
    echo "  bash run.sh --help"
    echo ""
}

# =============================================================================
# 主函数
# =============================================================================
main() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   T66Y 论坛归档系统 - 环境安装        ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    parse_args "$@"
    check_python
    create_venv
    install_dependencies
    install_playwright
    check_font
    show_complete
}

main "$@"
