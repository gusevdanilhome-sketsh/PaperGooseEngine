#!/bin/bash
# scripts/build.sh - Сборка PaperGoose Engine

set -e

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Параметры по умолчанию
BUILD_TYPE="Debug"
USE_VULKAN="ON"
CLEAN_BUILD="OFF"

# Разбор аргументов командной строки
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--release)
            BUILD_TYPE="Release"
            shift
            ;;
        -d|--debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        --no-vulkan)
            USE_VULKAN="OFF"
            shift
            ;;
        --clean)
            CLEAN_BUILD="ON"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -r, --release      Build in Release mode"
            echo "  -d, --debug        Build in Debug mode (default)"
            echo "  --no-vulkan        Disable Vulkan renderer"
            echo "  --clean            Clean build directory before building"
            echo "  -h, --help         Show this help"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_info "Building PaperGoose Engine..."
print_info "Build type: $BUILD_TYPE"
print_info "Vulkan: $USE_VULKAN"
echo ""

# Определение генератора CMake
detect_generator() {
    if [ -n "$MSYSTEM" ]; then
        echo "MinGW Makefiles"
    elif [ "$(uname)" == "Linux" ]; then
        echo "Unix Makefiles"
    else
        echo "Unix Makefiles"
    fi
}

GENERATOR=$(detect_generator)

# Очистка build директории
if [ "$CLEAN_BUILD" == "ON" ]; then
    print_info "Cleaning build directory..."
    rm -rf build
fi

# Создание build директории
mkdir -p build
cd build

# Конфигурация CMake
print_info "Configuring CMake..."
cmake .. \
    -G "$GENERATOR" \
    -DCMAKE_BUILD_TYPE=$BUILD_TYPE \
    -DUSE_VULKAN=$USE_VULKAN

# Сборка
print_info "Building project..."
cmake --build . --config $BUILD_TYPE -j $(nproc)

# Определение имени исполняемого файла
if [ -n "$MSYSTEM" ]; then
    EXECUTABLE="papergoose.exe"
else
    EXECUTABLE="papergoose"
fi

if [ -f "$EXECUTABLE" ]; then
    print_info "Build successful!"
    print_info "Executable: build/$EXECUTABLE"
    echo ""
    print_info "To run: ./build/$EXECUTABLE"
else
    print_error "Build failed - executable not found!"
    exit 1
fi

cd ..