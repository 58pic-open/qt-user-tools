#!/bin/bash
# 多平台打包脚本
# 支持：macOS M1 (ARM64), macOS Intel (x86_64), Windows EXE

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 版本信息
VERSION="0.0.1"
APP_NAME="千图网问题解决工具"
APP_NAME_EN="QiantuTroubleshooter"  # 英文名称，用于文件名
# Qt5 / PyQt5 旧系统包（与主包区分显示名与产物目录）
APP_LEGACY_NAME="千图网问题解决工具(10.14+)"

# 输出目录
DIST_DIR="dist"
BUILD_DIR="build"

# 生成平台特定的文件名
# 格式: 应用名_版本_平台.扩展名
get_output_name() {
    local platform=$1
    local format=$2  # app, dmg, exe, zip
    
    case "$platform" in
        "mac-arm64")
            case "$format" in
                "app") echo "${APP_NAME}.app" ;;
                "dmg") echo "${APP_NAME_EN}_v${VERSION}_macOS-ARM64.dmg" ;;
                "zip") echo "${APP_NAME_EN}_v${VERSION}_macOS-ARM64.zip" ;;
            esac
            ;;
        "mac-intel")
            case "$format" in
                "app") echo "${APP_NAME}.app" ;;
                "dmg") echo "${APP_NAME_EN}_v${VERSION}_macOS-Intel.dmg" ;;
                "zip") echo "${APP_NAME_EN}_v${VERSION}_macOS-Intel.zip" ;;
            esac
            ;;
        "mac-intel-legacy")
            case "$format" in
                "app") echo "${APP_LEGACY_NAME}.app" ;;
                "dmg") echo "${APP_NAME_EN}_v${VERSION}_macOS-Intel-10.14plus.dmg" ;;
                "zip") echo "${APP_NAME_EN}_v${VERSION}_macOS-Intel-10.14plus.zip" ;;
            esac
            ;;
        "windows")
            case "$format" in
                "exe") echo "${APP_NAME_EN}_v${VERSION}_Windows-x64.exe" ;;
                "zip") echo "${APP_NAME_EN}_v${VERSION}_Windows-x64.zip" ;;
            esac
            ;;
    esac
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  多平台打包脚本${NC}"
echo -e "${BLUE}  版本: ${VERSION}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检测当前平台
CURRENT_OS=$(uname -s)
CURRENT_ARCH=$(uname -m)

echo -e "${GREEN}当前平台: ${CURRENT_OS} ${CURRENT_ARCH}${NC}"
echo ""

# 解析命令行参数
BUILD_MAC_ARM64=false
BUILD_MAC_INTEL=false
BUILD_MAC_INTEL_LEGACY=false
BUILD_WINDOWS=false
BUILD_ALL=false

if [ $# -eq 0 ]; then
    # 如果没有参数，根据当前平台自动选择
    if [ "$CURRENT_OS" = "Darwin" ]; then
        BUILD_MAC_ARM64=true
        BUILD_MAC_INTEL=true
        echo -e "${YELLOW}未指定平台，将打包当前平台的所有架构${NC}"
    else
        echo -e "${RED}错误: 请在 macOS 上运行此脚本以打包 macOS 版本${NC}"
        echo -e "${YELLOW}提示: 在 Windows 上请使用 build_windows.bat${NC}"
        exit 1
    fi
else
    for arg in "$@"; do
        case $arg in
            --mac-arm64|--m1)
                BUILD_MAC_ARM64=true
                ;;
            --mac-intel|--intel)
                BUILD_MAC_INTEL=true
                ;;
            --mac-intel-legacy|--intel-legacy)
                BUILD_MAC_INTEL_LEGACY=true
                ;;
            --windows|--win)
                BUILD_WINDOWS=true
                ;;
            --all)
                BUILD_ALL=true
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --mac-arm64, --m1     打包 macOS ARM64 (M1/M2)"
                echo "  --mac-intel, --intel   打包 macOS Intel (x86_64)"
                echo "  --mac-intel-legacy     打包 macOS Intel 旧系统版（PyQt5，兼容 10.14+）"
                echo "  --windows, --win       打包 Windows EXE (需要 Wine)"
                echo "  --all                  打包所有平台"
                echo "  --help, -h             显示此帮助信息"
                echo ""
                echo "示例:"
                echo "  $0 --mac-arm64          # 只打包 macOS ARM64"
                echo "  $0 --mac-intel          # 只打包 macOS Intel"
                echo "  $0 --mac-intel-legacy   # 仅旧系统 Intel 包（勿与 --mac-intel 同环境混打）"
                echo "  $0 --mac-arm64 --mac-intel  # 打包 macOS 两种架构"
                echo "  $0 --all                # 打包所有平台"
                exit 0
                ;;
            *)
                echo -e "${RED}未知选项: $arg${NC}"
                echo "使用 --help 查看帮助"
                exit 1
                ;;
        esac
    done
fi

if [ "$BUILD_ALL" = true ]; then
    BUILD_MAC_ARM64=true
    BUILD_MAC_INTEL=true
    BUILD_WINDOWS=true
fi

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}检查依赖...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ 未找到 python3${NC}"
        exit 1
    fi
    
    if ! python3 -c "import PyInstaller" 2>/dev/null; then
        echo -e "${YELLOW}PyInstaller 未安装，正在安装...${NC}"
        python3 -m pip install pyinstaller --quiet
    fi
    
    echo -e "${GREEN}✓ 依赖检查完成${NC}"
}

# 安装 Python 依赖
install_dependencies() {
    echo -e "${BLUE}安装 Python 依赖...${NC}"
    
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt --quiet
    else
        python3 -m pip install PyQt6 PyQt6-Qt6 beautifulsoup4 lxml requests netifaces pyinstaller --quiet
    fi
    
    # 验证关键模块
    python3 -c "import PyQt6; import bs4; import requests; import lxml; print('✓ 所有依赖已安装')" 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ 依赖安装失败${NC}"
        exit 1
    fi
}

# 查找指定架构的 Python
find_python_by_arch() {
    local target_arch=$1
    local python_bin=""
    
    for py in python3 python3.11 python3.12 python3.13; do
        if command -v $py &> /dev/null; then
            local arch=$($py -c "import platform; print(platform.machine())" 2>/dev/null)
            if [ "$arch" = "$target_arch" ]; then
                python_bin=$(which $py)
                echo "$python_bin"
                return 0
            fi
        fi
    done
    
    return 1
}

# 打包 macOS ARM64
build_mac_arm64() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  打包 macOS ARM64 (M1/M2)${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # 查找 ARM64 Python（优先使用系统 Python，避免 conda 污染导致 PyInstaller 失败）
    PYTHON_BASE=$(find_python_by_arch "arm64")
    if [ -z "$PYTHON_BASE" ] && [ -x "/usr/bin/python3" ]; then
        # macOS 自带 python3 通常可用，且更“干净”
        SYS_ARCH=$(/usr/bin/python3 -c "import platform; print(platform.machine())" 2>/dev/null || echo "")
        if [ "$SYS_ARCH" = "arm64" ]; then
            PYTHON_BASE="/usr/bin/python3"
        fi
    fi
    if [ -z "$PYTHON_BASE" ]; then
        echo -e "${YELLOW}未找到干净的 ARM64 Python，尝试使用当前 python3（可能受 conda 影响）...${NC}"
        PYTHON_BASE=$(which python3)
    fi

    echo -e "${GREEN}基础 Python: $PYTHON_BASE${NC}"
    
    # 创建构建目录
    BUILD_SUBDIR="$BUILD_DIR/mac_arm64"
    mkdir -p "$BUILD_SUBDIR"

    # 在构建目录中创建独立 venv，避免 conda/site-packages 污染
    VENV_DIR="$BUILD_SUBDIR/venv"
    PYTHON_BIN="$VENV_DIR/bin/python3"
    if [ ! -x "$PYTHON_BIN" ]; then
        echo -e "${BLUE}创建独立虚拟环境（venv）...${NC}"
        "$PYTHON_BASE" -m venv "$VENV_DIR"
    fi
    echo -e "${GREEN}使用 venv Python: $PYTHON_BIN${NC}"

    echo -e "${BLUE}在 venv 中安装依赖...${NC}"
    "$PYTHON_BIN" -m pip install --upgrade pip --quiet 2>/dev/null || true
    if [ -f "requirements.txt" ]; then
        "$PYTHON_BIN" -m pip install -r requirements.txt --quiet
    fi
    "$PYTHON_BIN" -m pip install pyinstaller --quiet
    
    # 使用 PyInstaller 打包
    echo -e "${BLUE}正在打包...${NC}"
    echo -e "${YELLOW}Python: $PYTHON_BIN${NC}"
    echo -e "${YELLOW}工作目录: $BUILD_SUBDIR${NC}"
    echo -e "${YELLOW}输出目录: $DIST_DIR/mac_arm64${NC}"
    
    if ! $PYTHON_BIN -m PyInstaller build_app.spec \
        --workpath "$BUILD_SUBDIR" \
        --distpath "$DIST_DIR/mac_arm64" \
        --clean \
        --noconfirm 2>&1 | tee /tmp/pyinstaller_arm64.log; then
        echo -e "${RED}✗ PyInstaller 打包失败${NC}"
        echo -e "${YELLOW}最后 50 行日志:${NC}"
        tail -50 /tmp/pyinstaller_arm64.log || true
        return 1
    fi
    
    # 检查结果
    if [ -d "$DIST_DIR/mac_arm64/$APP_NAME.app" ]; then
        echo -e "${GREEN}✓ macOS ARM64 打包成功${NC}"
        echo -e "  输出: $DIST_DIR/mac_arm64/$APP_NAME.app"
        
        # 创建 DMG
        echo -e "${BLUE}创建 DMG 安装包...${NC}"
        APP_PATH="$DIST_DIR/mac_arm64/$APP_NAME.app"
        DMG_NAME=$(get_output_name "mac-arm64" "dmg")
        DMG_OUT="$DIST_DIR/mac_arm64/$DMG_NAME"
        DMG_TEMP_DIR="$BUILD_SUBDIR/dmg_temp_dir"
        
        rm -rf "$DMG_TEMP_DIR" "$DMG_OUT" 2>/dev/null || true
        mkdir -p "$DMG_TEMP_DIR"
        
        echo -e "${BLUE}复制 App Bundle...${NC}"
        cp -R "$APP_PATH" "$DMG_TEMP_DIR/"
        echo -e "${BLUE}创建 Applications 链接...${NC}"
        ln -s /Applications "$DMG_TEMP_DIR/Applications" || true
        
        cat > "$DMG_TEMP_DIR/README.txt" << EOF
${APP_NAME} V${VERSION}
============================

安装说明：
1. 将"${APP_NAME}.app"拖拽到"Applications"文件夹
2. 在应用程序中找到并打开"${APP_NAME}"
3. 如果提示"无法打开"，请：
   - 右键点击应用，选择"打开"
   - 或在"系统设置" > "隐私与安全性"中允许

注意：
- 修改hosts文件时会提示输入密码
- 应用启动不需要管理员权限
EOF
        
        echo -e "${BLUE}创建 DMG 文件...${NC}"
        if hdiutil create -volname "$APP_NAME" \
            -srcfolder "$DMG_TEMP_DIR" \
            -ov -format UDZO \
            "$DMG_OUT" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ DMG 创建成功: $DMG_OUT${NC}"
        else
            echo -e "${YELLOW}⚠ DMG 创建失败（已跳过，不影响 ZIP/APP 产物）${NC}"
        fi
        rm -rf "$DMG_TEMP_DIR" 2>/dev/null || true
        
        # 创建 ZIP 压缩包（可选）
        echo -e "${BLUE}创建 ZIP 压缩包...${NC}"
        ZIP_NAME=$(get_output_name "mac-arm64" "zip")
        cd "$DIST_DIR/mac_arm64"
        zip -r -q "$ZIP_NAME" "$APP_NAME.app" 2>/dev/null || zip -r "$ZIP_NAME" "$APP_NAME.app"
        cd - > /dev/null
        if [ -f "$DIST_DIR/mac_arm64/$ZIP_NAME" ]; then
            echo -e "${GREEN}✓ ZIP 创建成功: $DIST_DIR/mac_arm64/$ZIP_NAME${NC}"
        fi
    else
        echo -e "${RED}✗ macOS ARM64 打包失败${NC}"
        return 1
    fi
}

# 打包 macOS Intel
build_mac_intel() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  打包 macOS Intel (x86_64)${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # 在 Apple Silicon Mac 上，可以使用 arch -x86_64 运行 x86_64 Python
    # 或者查找 Rosetta 2 环境中的 Python
    
    if [ "$CURRENT_ARCH" = "arm64" ]; then
        echo -e "${YELLOW}检测到 Apple Silicon，尝试使用 Rosetta 2...${NC}"
        
        # 优先检查虚拟环境（通过 Rosetta 2 运行）
        if [ -d "venv_x86_64" ] && [ -f "venv_x86_64/bin/python3" ]; then
            # 通过 arch -x86_64 运行虚拟环境中的 Python
            PYTHON_BIN="arch -x86_64 venv_x86_64/bin/python3"
            echo -e "${GREEN}使用 x86_64 虚拟环境（通过 Rosetta 2）: $PYTHON_BIN${NC}"
            # 验证虚拟环境的架构
            VENV_ARCH=$(arch -x86_64 venv_x86_64/bin/python3 -c "import platform; print(platform.machine())" 2>/dev/null)
            if [ "$VENV_ARCH" = "x86_64" ]; then
                echo -e "${GREEN}✓ 虚拟环境架构验证通过: $VENV_ARCH${NC}"
            else
                echo -e "${YELLOW}警告: 虚拟环境架构验证失败，将使用系统 Python${NC}"
                PYTHON_BIN=""
            fi
        fi
        
        # 如果没有虚拟环境或虚拟环境不可用，使用 Rosetta 2
        if [ -z "$PYTHON_BIN" ]; then
            # 检查是否有 x86_64 Python（通过 Rosetta 2）
            # 尝试使用 arch -x86_64 运行当前 Python
            if command -v arch &> /dev/null; then
                # 测试 arch 命令是否可用
                ARCH_TEST=$(arch -x86_64 python3 -c "import platform; print(platform.machine())" 2>/dev/null)
                if [ "$ARCH_TEST" = "x86_64" ]; then
                    # 检查是否有隔离的 x86_64 依赖
                    X86_64_INSTALL_DIR="$HOME/.local/python_x86_64"
                    if [ -d "$X86_64_INSTALL_DIR" ]; then
                        export PYTHONUSERBASE="$X86_64_INSTALL_DIR"
                        export PATH="$X86_64_INSTALL_DIR/bin:$PATH"
                        PYTHON_BIN="arch -x86_64 python3"
                        echo -e "${GREEN}使用 Rosetta 2 运行 x86_64 Python（使用隔离依赖）${NC}"
                    else
                        PYTHON_BIN="arch -x86_64 python3"
                        echo -e "${GREEN}使用 Rosetta 2 运行 x86_64 Python${NC}"
                        echo -e "${YELLOW}提示: 如果依赖架构不匹配，请先运行: ./install_x86_64_deps.sh${NC}"
                        echo -e "${YELLOW}或创建虚拟环境: arch -x86_64 python3 -m venv venv_x86_64${NC}"
                    fi
                else
                    echo -e "${YELLOW}尝试查找 x86_64 Python...${NC}"
                    # 尝试查找通过 Rosetta 安装的 Python
                    PYTHON_BIN=$(find_python_by_arch "x86_64")
                    if [ -z "$PYTHON_BIN" ]; then
                        echo -e "${RED}✗ 无法在 Apple Silicon 上打包 x86_64 版本${NC}"
                        echo -e "${YELLOW}提示: 需要安装 x86_64 版本的 Python（通过 Rosetta 2）${NC}"
                        echo -e "${YELLOW}或者: 在 Intel Mac 上运行此脚本${NC}"
                        return 1
                    fi
                fi
            else
                echo -e "${RED}✗ arch 命令不可用${NC}"
                echo -e "${YELLOW}提示: 需要在 Intel Mac 上运行，或安装 x86_64 Python${NC}"
                return 1
            fi
        fi
    else
        # Intel Mac
        PYTHON_BIN=$(find_python_by_arch "x86_64")
        if [ -z "$PYTHON_BIN" ]; then
            PYTHON_BIN=$(which python3)
        fi
        echo -e "${GREEN}使用 Python: $PYTHON_BIN${NC}"
    fi
    
    # 安装依赖
    echo -e "${BLUE}安装依赖...${NC}"
    echo -e "${YELLOW}注意：在 M1 Mac 上打包 Intel 版本需要 x86_64 依赖${NC}"
    echo -e "${YELLOW}如果依赖安装失败，请先运行: ./setup_x86_64_env.sh${NC}"
    
    # 在 x86_64 环境中安装依赖
    if [[ "$PYTHON_BIN" == "arch -x86_64"* ]]; then
        echo -e "${BLUE}在 x86_64 环境中安装依赖...${NC}"
        $PYTHON_BIN -m pip install --upgrade pip --quiet 2>/dev/null || true
        $PYTHON_BIN -m pip install -r requirements.txt --force-reinstall --no-binary :all: --quiet 2>&1 | grep -E "(Installing|Successfully|ERROR|WARNING)" || true
    else
        $PYTHON_BIN -m pip install -r requirements.txt --quiet 2>/dev/null || true
    fi
    
    # 创建构建目录
    BUILD_SUBDIR="$BUILD_DIR/mac_intel"
    mkdir -p "$BUILD_SUBDIR"
    
    # 使用 PyInstaller 打包
    echo -e "${BLUE}正在打包...${NC}"
    echo -e "${YELLOW}Python: $PYTHON_BIN${NC}"
    echo -e "${YELLOW}工作目录: $BUILD_SUBDIR${NC}"
    echo -e "${YELLOW}输出目录: $DIST_DIR/mac_intel${NC}"
    
    if ! $PYTHON_BIN -m PyInstaller build_app.spec \
        --workpath "$BUILD_SUBDIR" \
        --distpath "$DIST_DIR/mac_intel" \
        --clean \
        --noconfirm 2>&1 | tee /tmp/pyinstaller_intel.log; then
        echo -e "${RED}✗ PyInstaller 打包失败${NC}"
        echo -e "${YELLOW}最后 50 行日志:${NC}"
        tail -50 /tmp/pyinstaller_intel.log || true
        return 1
    fi
    
    # 检查结果
    if [ -d "$DIST_DIR/mac_intel/$APP_NAME.app" ]; then
        echo -e "${GREEN}✓ macOS Intel 打包成功${NC}"
        echo -e "  输出: $DIST_DIR/mac_intel/$APP_NAME.app"
        
        # 创建 DMG
        echo -e "${BLUE}创建 DMG 安装包...${NC}"
        APP_PATH="$DIST_DIR/mac_intel/$APP_NAME.app"
        DMG_NAME=$(get_output_name "mac-intel" "dmg")
        DMG_OUT="$DIST_DIR/mac_intel/$DMG_NAME"
        DMG_TEMP_DIR="$BUILD_SUBDIR/dmg_temp_dir"
        
        rm -rf "$DMG_TEMP_DIR" "$DMG_OUT" 2>/dev/null || true
        mkdir -p "$DMG_TEMP_DIR"
        
        echo -e "${BLUE}复制 App Bundle...${NC}"
        cp -R "$APP_PATH" "$DMG_TEMP_DIR/"
        echo -e "${BLUE}创建 Applications 链接...${NC}"
        ln -s /Applications "$DMG_TEMP_DIR/Applications" || true
        
        cat > "$DMG_TEMP_DIR/README.txt" << EOF
${APP_NAME} V${VERSION}
============================

安装说明：
1. 将"${APP_NAME}.app"拖拽到"Applications"文件夹
2. 在应用程序中找到并打开"${APP_NAME}"
3. 如果提示"无法打开"，请：
   - 右键点击应用，选择"打开"
   - 或在"系统设置" > "隐私与安全性"中允许

注意：
- 修改hosts文件时会提示输入密码
- 应用启动不需要管理员权限
EOF
        
        echo -e "${BLUE}创建 DMG 文件...${NC}"
        if hdiutil create -volname "$APP_NAME" \
            -srcfolder "$DMG_TEMP_DIR" \
            -ov -format UDZO \
            "$DMG_OUT" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ DMG 创建成功: $DMG_OUT${NC}"
        else
            echo -e "${YELLOW}⚠ DMG 创建失败（已跳过，不影响 ZIP/APP 产物）${NC}"
        fi
        rm -rf "$DMG_TEMP_DIR" 2>/dev/null || true
        
        # 创建 ZIP 压缩包（可选）
        echo -e "${BLUE}创建 ZIP 压缩包...${NC}"
        ZIP_NAME=$(get_output_name "mac-intel" "zip")
        cd "$DIST_DIR/mac_intel"
        zip -r -q "$ZIP_NAME" "$APP_NAME.app" 2>/dev/null || zip -r "$ZIP_NAME" "$APP_NAME.app"
        cd - > /dev/null
        if [ -f "$DIST_DIR/mac_intel/$ZIP_NAME" ]; then
            echo -e "${GREEN}✓ ZIP 创建成功: $DIST_DIR/mac_intel/$ZIP_NAME${NC}"
        fi
    else
        echo -e "${RED}✗ macOS Intel 打包失败${NC}"
        return 1
    fi
}

# 打包 macOS Intel（Qt5 / PyQt5，兼容 macOS 10.14+）
build_mac_intel_legacy() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  打包 macOS Intel 旧系统版 (PyQt5 / 10.14+)${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}提示：不要与「标准 Intel(Qt6)」在同一次命令里混打，以免共用同一 Python 环境冲突。${NC}"

    PYTHON_BIN=""
    if [ "$CURRENT_ARCH" = "arm64" ]; then
        echo -e "${YELLOW}检测到 Apple Silicon，尝试使用 Rosetta 2...${NC}"
        if [ -d "venv_x86_64" ] && [ -f "venv_x86_64/bin/python3" ]; then
            PYTHON_BIN="arch -x86_64 venv_x86_64/bin/python3"
            echo -e "${GREEN}使用 x86_64 虚拟环境（通过 Rosetta 2）: $PYTHON_BIN${NC}"
            VENV_ARCH=$(arch -x86_64 venv_x86_64/bin/python3 -c "import platform; print(platform.machine())" 2>/dev/null)
            if [ "$VENV_ARCH" != "x86_64" ]; then
                PYTHON_BIN=""
            fi
        fi
        if [ -z "$PYTHON_BIN" ] && command -v arch &> /dev/null; then
            ARCH_TEST=$(arch -x86_64 python3 -c "import platform; print(platform.machine())" 2>/dev/null)
            if [ "$ARCH_TEST" = "x86_64" ]; then
                PYTHON_BIN="arch -x86_64 python3"
                echo -e "${GREEN}使用 Rosetta 2 运行 x86_64 Python${NC}"
            else
                PYTHON_BIN=$(find_python_by_arch "x86_64")
            fi
        fi
        if [ -z "$PYTHON_BIN" ]; then
            echo -e "${RED}✗ 无法在 Apple Silicon 上打包 x86_64 旧系统版${NC}"
            return 1
        fi
    else
        PYTHON_BIN=$(find_python_by_arch "x86_64")
        if [ -z "$PYTHON_BIN" ]; then
            PYTHON_BIN=$(which python3)
        fi
        echo -e "${GREEN}使用 Python: $PYTHON_BIN${NC}"
    fi

    export QT_USER_TOOLS_USE_PYQT5=1
    export MACOSX_DEPLOYMENT_TARGET=10.14

    echo -e "${BLUE}安装旧系统依赖（PyQt5）...${NC}"
    $PYTHON_BIN -m pip install --upgrade pip --quiet 2>/dev/null || true
    $PYTHON_BIN -m pip uninstall -y PyQt6 PyQt6-Qt6 2>/dev/null || true
    $PYTHON_BIN -m pip install -r requirements-legacy.txt pyinstaller --quiet 2>/dev/null || \
        $PYTHON_BIN -m pip install -r requirements-legacy.txt pyinstaller

    BUILD_SUBDIR="$BUILD_DIR/mac_intel_legacy"
    mkdir -p "$BUILD_SUBDIR"
    mkdir -p "$DIST_DIR/mac_intel_legacy"

    echo -e "${BLUE}正在打包（build_app_legacy.spec）...${NC}"
    if ! $PYTHON_BIN -m PyInstaller build_app_legacy.spec \
        --workpath "$BUILD_SUBDIR" \
        --distpath "$DIST_DIR/mac_intel_legacy" \
        --clean \
        --noconfirm 2>&1 | tee /tmp/pyinstaller_intel_legacy.log; then
        echo -e "${RED}✗ PyInstaller 旧系统版打包失败${NC}"
        tail -50 /tmp/pyinstaller_intel_legacy.log || true
        return 1
    fi

    if [ -d "$DIST_DIR/mac_intel_legacy/${APP_LEGACY_NAME}.app" ]; then
        echo -e "${GREEN}✓ macOS Intel 旧系统版打包成功${NC}"
        APP_PATH="$DIST_DIR/mac_intel_legacy/${APP_LEGACY_NAME}.app"
        DMG_NAME=$(get_output_name "mac-intel-legacy" "dmg")
        DMG_OUT="$DIST_DIR/mac_intel_legacy/$DMG_NAME"
        DMG_TEMP_DIR="$BUILD_SUBDIR/dmg_temp_dir_legacy"
        rm -rf "$DMG_TEMP_DIR" "$DMG_OUT" 2>/dev/null || true
        mkdir -p "$DMG_TEMP_DIR"
        cp -R "$APP_PATH" "$DMG_TEMP_DIR/"
        ln -s /Applications "$DMG_TEMP_DIR/Applications" || true
        cat > "$DMG_TEMP_DIR/README.txt" << EOF
${APP_LEGACY_NAME} V${VERSION}（兼容 macOS 10.14+，Intel）
====================================

安装说明：
1. 将「${APP_LEGACY_NAME}.app」拖到「应用程序」
2. 首次打开如被拦截，请右键 → 打开

说明：本包使用 Qt5，用于无法在 macOS 11+ 上安装标准 Qt6 版的旧系统。
EOF
        if hdiutil create -volname "$APP_LEGACY_NAME" \
            -srcfolder "$DMG_TEMP_DIR" \
            -ov -format UDZO \
            "$DMG_OUT" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ DMG 创建成功: $DMG_OUT${NC}"
        else
            echo -e "${YELLOW}⚠ DMG 创建失败（已跳过）${NC}"
        fi
        rm -rf "$DMG_TEMP_DIR" 2>/dev/null || true

        ZIP_NAME=$(get_output_name "mac-intel-legacy" "zip")
        cd "$DIST_DIR/mac_intel_legacy"
        zip -r -q "$ZIP_NAME" "${APP_LEGACY_NAME}.app" 2>/dev/null || zip -r "$ZIP_NAME" "${APP_LEGACY_NAME}.app"
        cd - > /dev/null
        if [ -f "$DIST_DIR/mac_intel_legacy/$ZIP_NAME" ]; then
            echo -e "${GREEN}✓ ZIP 创建成功: $DIST_DIR/mac_intel_legacy/$ZIP_NAME${NC}"
        fi
    else
        echo -e "${RED}✗ 未找到输出: $DIST_DIR/mac_intel_legacy/${APP_LEGACY_NAME}.app${NC}"
        return 1
    fi
}

# 打包 Windows EXE
build_windows() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  打包 Windows EXE${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    if [ "$CURRENT_OS" != "Darwin" ] && [ "$CURRENT_OS" != "Linux" ]; then
        echo -e "${RED}✗ 当前平台不支持打包 Windows 版本${NC}"
        echo -e "${YELLOW}提示: 请在 Windows 上运行 build_windows.bat${NC}"
        return 1
    fi
    
    # 检查 Wine
    if ! command -v wine &> /dev/null; then
        echo -e "${YELLOW}未找到 Wine，无法在 macOS/Linux 上打包 Windows 版本${NC}"
        echo -e "${YELLOW}提示: 请在 Windows 上运行 build_windows.bat${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}注意: 在 macOS/Linux 上打包 Windows 版本需要 Wine，可能不稳定${NC}"
    echo -e "${YELLOW}建议: 在 Windows 上直接运行 build_windows.bat${NC}"
    
    # 创建 Windows spec 文件
    cat > build_windows.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-
# Windows 打包配置

import os

block_cipher = None

a = Analysis(
    ['gui/main.py'],
    pathex=[os.path.dirname(os.path.abspath(SPEC))],
    binaries=[],
    datas=[
        ('gui/resources', 'gui/resources'),
        ('config', 'config'),
        ('resources/images', 'resources/images'),
    ],
    hiddenimports=[
        'hosts', 'hosts.bind_hosts', 'hosts.unbind_hosts', 'hosts.check_hosts', 'hosts.get_domain_ip',
        'browser', 'browser.clear_cache', 'browser.clear_dns', 'browser.check_browser',
        'download', 'download.check_download',
        'utils', 'utils.system_info', 'utils.elevate_permission',
        'gui.image_viewer',
        'bs4', 'bs4.builder', 'bs4.builder._htmlparser', 'bs4.builder._lxml', 'bs4.element', 'bs4.formatter',
        'beautifulsoup4', 'lxml', 'lxml.etree', 'lxml.html',
        'requests', 'netifaces',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='千图网问题解决工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
EOF
    
    # 创建构建目录
    BUILD_SUBDIR="$BUILD_DIR/windows"
    mkdir -p "$BUILD_SUBDIR"
    
    echo -e "${YELLOW}使用 Wine 打包 Windows 版本（实验性功能）...${NC}"
    echo -e "${RED}建议在 Windows 上直接打包${NC}"
    
    # 这里需要 Wine + Windows Python + PyInstaller
    # 由于复杂度较高，建议用户直接在 Windows 上打包
    echo -e "${YELLOW}跳过 Windows 打包（请在 Windows 上运行 build_windows.bat）${NC}"
    
    # 如果 Windows 打包完成，重命名文件
    WINDOWS_DIST="$DIST_DIR/windows"
    if [ -f "$WINDOWS_DIST/${APP_NAME}.exe" ]; then
        EXE_NAME=$(get_output_name "windows" "exe")
        mv "$WINDOWS_DIST/${APP_NAME}.exe" "$WINDOWS_DIST/$EXE_NAME"
        echo -e "${GREEN}✓ Windows EXE 已重命名: $WINDOWS_DIST/$EXE_NAME${NC}"
        
        # 创建 ZIP 压缩包
        ZIP_NAME=$(get_output_name "windows" "zip")
        cd "$WINDOWS_DIST"
        zip -q "$ZIP_NAME" "$EXE_NAME" 2>/dev/null || zip "$ZIP_NAME" "$EXE_NAME"
        cd - > /dev/null
        if [ -f "$WINDOWS_DIST/$ZIP_NAME" ]; then
            echo -e "${GREEN}✓ ZIP 创建成功: $WINDOWS_DIST/$ZIP_NAME${NC}"
        fi
    fi
}

# 主函数
main() {
    check_dependencies
    # 仅打旧系统 Intel 包时跳过默认 PyQt6 依赖安装，避免与 PyQt5 环境互相干扰
    if [ "$BUILD_MAC_INTEL_LEGACY" = true ] && [ "$BUILD_MAC_ARM64" != true ] && [ "$BUILD_MAC_INTEL" != true ] && [ "$BUILD_WINDOWS" != true ] && [ "$BUILD_ALL" != true ]; then
        echo -e "${YELLOW}仅构建旧系统 Intel 包：跳过 requirements.txt（PyQt6）安装${NC}"
    else
        install_dependencies
    fi
    
    # 创建输出目录
    mkdir -p "$DIST_DIR"
    
    SUCCESS_COUNT=0
    FAIL_COUNT=0
    
    # 打包 macOS ARM64
    if [ "$BUILD_MAC_ARM64" = true ]; then
        if build_mac_arm64; then
            ((SUCCESS_COUNT++))
        else
            ((FAIL_COUNT++))
        fi
    fi
    
    # 打包 macOS Intel
    if [ "$BUILD_MAC_INTEL" = true ]; then
        if build_mac_intel; then
            ((SUCCESS_COUNT++))
        else
            ((FAIL_COUNT++))
        fi
    fi

    if [ "$BUILD_MAC_INTEL_LEGACY" = true ]; then
        if build_mac_intel_legacy; then
            ((SUCCESS_COUNT++))
        else
            ((FAIL_COUNT++))
        fi
    fi
    
    # 打包 Windows
    if [ "$BUILD_WINDOWS" = true ]; then
        if build_windows; then
            ((SUCCESS_COUNT++))
        else
            ((FAIL_COUNT++))
        fi
    fi
    
    # 总结
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  打包完成${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}成功: $SUCCESS_COUNT${NC}"
    if [ $FAIL_COUNT -gt 0 ]; then
        echo -e "${RED}失败: $FAIL_COUNT${NC}"
    fi
    # 输出总结
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  输出文件列表${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # macOS ARM64
    if [ "$BUILD_MAC_ARM64" = true ] && [ -d "$DIST_DIR/mac_arm64" ]; then
        echo -e "${GREEN}macOS ARM64:${NC}"
        ls -lh "$DIST_DIR/mac_arm64" | grep -E "\.(app|dmg|zip)" | awk '{print "  " $9 " (" $5 ")"}'
        echo ""
    fi
    
    # macOS Intel
    if [ "$BUILD_MAC_INTEL" = true ] && [ -d "$DIST_DIR/mac_intel" ]; then
        echo -e "${GREEN}macOS Intel:${NC}"
        ls -lh "$DIST_DIR/mac_intel" | grep -E "\.(app|dmg|zip)" | awk '{print "  " $9 " (" $5 ")"}'
        echo ""
    fi

    if [ "$BUILD_MAC_INTEL_LEGACY" = true ] && [ -d "$DIST_DIR/mac_intel_legacy" ]; then
        echo -e "${GREEN}macOS Intel（10.14+ 旧系统版）:${NC}"
        ls -lh "$DIST_DIR/mac_intel_legacy" | grep -E "\.(app|dmg|zip)" | awk '{print "  " $9 " (" $5 ")"}'
        echo ""
    fi
    
    # Windows
    if [ "$BUILD_WINDOWS" = true ] && [ -d "$DIST_DIR/windows" ]; then
        echo -e "${GREEN}Windows:${NC}"
        ls -lh "$DIST_DIR/windows" | grep -E "\.(exe|zip)" | awk '{print "  " $9 " (" $5 ")"}'
        echo ""
    fi
    
    echo -e "${BLUE}文件命名规范:${NC}"
    echo "  macOS: ${APP_NAME_EN}_v${VERSION}_macOS-{架构}.{dmg|zip}"
    echo "  Windows: ${APP_NAME_EN}_v${VERSION}_Windows-x64.{exe|zip}"
    echo ""
}

# 运行主函数
main
