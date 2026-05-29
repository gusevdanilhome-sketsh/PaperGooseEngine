#!/bin/bash
# scripts/setup.sh - Установка всех зависимостей PaperGoose Engine

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info "Setting up PaperGoose Engine dependencies..."
echo ""

# Определение ОС
detect_os() {
    if [ -n "$MSYSTEM" ]; then
        echo "msys2"
    elif [ "$(uname)" == "Linux" ]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)

if [ "$OS" == "msys2" ]; then
    print_info "Detected MSYS2 environment: $MSYSTEM"
    echo ""
    
    # Проверка что это MINGW64
    if [ "$MSYSTEM" != "MINGW64" ]; then
        print_error "This script requires MINGW64 environment!"
        print_error "Current MSYSTEM: $MSYSTEM"
        print_error "Please run from 'MSYS2 MinGW 64-bit' terminal"
        exit 1
    fi
    
    # Обновление пакетов
    print_info "Updating package database..."
    pacman -Syu --noconfirm
    
    # Установка инструментов разработки
    print_info "Installing development tools..."
    pacman -S --noconfirm \
        mingw-w64-x86_64-gcc \
        mingw-w64-x86_64-cmake \
        mingw-w64-x86_64-make \
        mingw-w64-x86_64-gdb
    
    # Установка Git
    if ! command -v git &> /dev/null; then
        print_info "Installing git..."
        pacman -S --noconfirm git
    fi
    
    # Установка Vulkan
    print_info "Installing Vulkan SDK..."
    pacman -S --noconfirm \
        mingw-w64-x86_64-vulkan-headers \
        mingw-w64-x86_64-vulkan-loader \
        mingw-w64-x86_64-vulkan-validation-layers \
        mingw-w64-x86_64-vulkan-tools
    
elif [ "$OS" == "linux" ]; then
    print_info "Detected Linux system"
    echo ""
    
    # Определение дистрибутива
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        print_error "Cannot detect Linux distribution"
        exit 1
    fi
    
    print_info "Detected distribution: $DISTRO"
    
    case $DISTRO in
        ubuntu|debian)
            print_info "Installing dependencies for Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y \
                build-essential \
                cmake \
                git \
                libvulkan-dev \
                vulkan-tools
            ;;
        fedora|rhel)
            print_info "Installing dependencies for Fedora/RHEL..."
            sudo dnf groupinstall -y "Development Tools"
            sudo dnf install -y \
                cmake \
                git \
                vulkan-devel \
                vulkan-tools
            ;;
        arch|manjaro)
            print_info "Installing dependencies for Arch Linux..."
            sudo pacman -S --noconfirm \
                base-devel \
                cmake \
                git \
                vulkan-headers \
                vulkan-icd-loader \
                vulkan-tools
            ;;
        *)
            print_error "Unsupported distribution: $DISTRO"
            exit 1
            ;;
    esac
else
    print_error "Unsupported operating system"
    exit 1
fi

# Инициализация подмодулей
if [ -d ".git" ]; then
    print_info "Initializing git submodules..."
    git submodule update --init --recursive
else
    print_warning "Not in git repository root, skipping submodules"
fi

# Проверка установки
echo ""
print_info "========================================"
print_info "Installation completed successfully!"
print_info "========================================"
echo ""

print_info "Installed versions:"
if command -v gcc &> /dev/null; then
    echo "  $(gcc --version | head -n1)"
fi
if command -v cmake &> /dev/null; then
    echo "  $(cmake --version | head -n1)"
fi
if command -v make &> /dev/null; then
    echo "  $(make --version | head -n1)"
fi

echo ""
print_info "To verify Vulkan installation:"
if command -v vulkaninfo &> /dev/null; then
    echo "  Run: vulkaninfo"
else
    echo "  vulkaninfo not found, but Vulkan headers are installed"
fi

echo ""
print_info "Next steps:"
echo "  1. Run build script: ./scripts/build.sh"
echo "  2. Or manually: cmake -B build -G \"MinGW Makefiles\" -DUSE_VULKAN=ON"
echo "  3. Then: cmake --build build"
echo ""