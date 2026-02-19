#!/bin/bash
# =============================================================================
# T66Y 论坛归档系统 - 程序运行脚本
# =============================================================================
# 版本: v1.1
# 用法:
#   ./run.sh --target /path/to/archive   # 便携模式
#   ./run.sh --setup                     # 配置向导
#   ./run.sh                             # 检测模式
#   ./run.sh --help                      # 显示帮助
#
# 说明: 首次运行会自动创建虚拟环境并安装依赖
# =============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_DIR="$SCRIPT_DIR/python"

# 解析后的参数
TARGET_PATH=""
FORCE_SETUP=false
EXTRA_ARGS=()

# =============================================================================
# 帮助信息
# =============================================================================
show_help() {
    echo "T66Y 论坛归档系统 - 程序运行脚本"
    echo ""
    echo "用法:"
    echo "  ./run.sh --target <PATH>    便携模式（推荐）"
    echo "  ./run.sh --setup            启动配置向导"
    echo "  ./run.sh                    检测模式"
    echo ""
    echo "参数:"
    echo "  -t, --target PATH    指定归档目录（便携模式）"
    echo "  --setup              启动配置向导"
    echo "  --                   后续参数透传给 main.py"
    echo "  -h, --help           显示此帮助"
    echo ""
    echo "示例:"
    echo "  # 便携模式"
    echo "  ./run.sh --target /media/usb/t66y"
    echo "  ./run.sh -t ~/Dropbox/t66y"
    echo ""
    echo "  # 参数透传"
    echo "  ./run.sh --target /path -- --help"
    echo ""
    echo "  # 传统模式"
    echo "  ./run.sh --setup    # 首次运行配置向导"
    echo "  ./run.sh            # 后续运行"
    echo ""
    echo "说明:"
    echo "  首次运行时会自动创建虚拟环境并安装依赖"
    echo ""
    echo "文档:"
    echo "  便携模式指南: PORTABLE_MODE_GUIDE.md"
    echo "  详细设计: PORTABLE_MODE_DESIGN.md"
    echo ""
}

# =============================================================================
# 显示首次运行提示
# =============================================================================
show_first_run_hint() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  📂 归档路径设置${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "本系统支持两种模式："
    echo ""
    echo -e "${GREEN}【便携模式】推荐 - 配置和数据存储在归档目录${NC}"
    echo "  ./run.sh --target /path/to/archive"
    echo ""
    echo "  示例："
    echo "  ./run.sh --target /media/usb/t66y_archive"
    echo "  ./run.sh --target ~/Dropbox/t66y_archive"
    echo "  ./run.sh --target /mnt/data/t66y -- --help"
    echo ""
    echo "【传统模式】- 配置存储在程序目录"
    echo "  首次使用需要运行配置向导："
    echo "  ./run.sh --setup"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  💡 新环境迁移提示${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "如果您从其他电脑迁移过来："
    echo ""
    echo "1. 确保归档目录已复制到本机（包含 .t66y/ 子目录）"
    echo "2. 使用 --target 参数指定归档目录"
    echo "3. 系统会自动加载已有的配置和数据库"
    echo ""
    echo "  ./run.sh --target /path/to/copied/archive"
    echo ""
    echo "注意："
    echo "  • 避免两台电脑同时写入同一数据库"
    echo "  • 数据库文件：归档目录/.t66y/forum_data.db"
    echo "  • 配置文件：归档目录/.t66y/config.yaml"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "更多选项："
    echo "  ./run.sh --help     查看完整帮助"
    echo "  ./run.sh --target /path -- --help  查看 main.py 参数"
    echo ""
}

# =============================================================================
# 检查并创建虚拟环境
# =============================================================================
check_venv() {
    if [[ ! -f "$PYTHON_DIR/venv/bin/activate" ]]; then
        echo ""
        echo -e "${YELLOW}⚠ 虚拟环境不存在，正在自动创建...${NC}"
        echo ""
        
        # 检查 Python
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}❌ Python 3 未安装${NC}"
            echo "请先安装 Python 3.10 或更高版本"
            exit 1
        fi
        
        # 创建虚拟环境
        cd "$PYTHON_DIR"
        python3 -m venv venv
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}❌ 创建虚拟环境失败${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
        
        # 激活并安装依赖
        source venv/bin/activate
        pip install --upgrade pip -q
        
        if [[ -f "requirements.txt" ]]; then
            echo "正在安装依赖..."
            pip install -r requirements.txt -q
            echo -e "${GREEN}✓ 依赖安装成功${NC}"
        else
            echo -e "${RED}❌ 未找到 requirements.txt${NC}"
            exit 1
        fi
        
        # 安装 Playwright 浏览器
        if command -v playwright &> /dev/null; then
            echo "正在安装 Playwright 浏览器..."
            playwright install chromium 2>/dev/null || true
            echo -e "${GREEN}✓ Playwright 浏览器安装完成${NC}"
        fi
        
        cd "$SCRIPT_DIR"
        echo ""
    fi
}

# =============================================================================
# 解析命令行参数
# =============================================================================
parse_args() {
    local parsing_extra=false
    
    while [[ $# -gt 0 ]]; do
        if [[ "$parsing_extra" == true ]]; then
            EXTRA_ARGS+=("$1")
            shift
        else
            case $1 in
                -t|--target)
                    if [[ -z "$2" || "$2" == -* ]]; then
                        echo -e "${RED}❌ --target 需要指定路径${NC}"
                        exit 1
                    fi
                    TARGET_PATH="$2"
                    shift 2
                    ;;
                --setup)
                    FORCE_SETUP=true
                    shift
                    ;;
                --)
                    parsing_extra=true
                    shift
                    ;;
                -h|--help)
                    show_help
                    exit 0
                    ;;
                *)
                    echo -e "${RED}❌ 未知参数: $1${NC}"
                    echo "运行 bash run.sh --help 查看帮助"
                    exit 1
                    ;;
            esac
        fi
    done
}

# =============================================================================
# 检查便携模式配置
# =============================================================================
check_portable_config() {
    # 如果指定了 --target，检查路径是否存在
    if [[ -n "$TARGET_PATH" ]]; then
        if [[ ! -d "$TARGET_PATH" ]]; then
            echo -e "${RED}❌ 归档目录不存在: $TARGET_PATH${NC}"
            echo ""
            echo "请确保目录存在，或使用正确的路径"
            exit 1
        fi
        
        # 检查便携配置是否存在
        local portable_config="$TARGET_PATH/.t66y/config.yaml"
        if [[ ! -f "$portable_config" ]]; then
            echo -e "${YELLOW}⚠ 未找到便携配置，将启动配置向导${NC}"
            echo "  配置将保存到: $TARGET_PATH/.t66y/"
            echo ""
            FORCE_SETUP=true
        fi
    fi
}

# =============================================================================
# 运行程序
# =============================================================================
run_program() {
    cd "$PYTHON_DIR"
    source venv/bin/activate
    
    # 构建 Python 命令参数
    local python_args=()
    
    if [[ -n "$TARGET_PATH" ]]; then
        # 转换为绝对路径
        local abs_path=$(cd "$TARGET_PATH" 2>/dev/null && pwd)
        if [[ -z "$abs_path" ]]; then
            abs_path="$TARGET_PATH"
        fi
        python_args+=("--target" "$abs_path")
    fi
    
    if [[ "$FORCE_SETUP" == true ]]; then
        python_args+=("--setup")
    fi
    
    # 添加透传参数
    if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
        python_args+=("${EXTRA_ARGS[@]}")
    fi
    
    # 运行
    python main.py "${python_args[@]}"
}

# =============================================================================
# 主函数
# =============================================================================
main() {
    # 无参数时检查是否需要显示提示
    if [[ $# -eq 0 ]]; then
        # 检查是否存在传统模式配置
        if [[ ! -f "$PYTHON_DIR/config.yaml" ]]; then
            show_first_run_hint
            exit 0
        fi
    fi
    
    parse_args "$@"
    check_venv
    check_portable_config
    run_program
}

main "$@"
