#!/bin/bash
# scripts/run_tests.sh - Запуск тестов PaperGoose Engine

set -e

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

# Проверка наличия build директории
if [ ! -d "build" ]; then
    print_error "Build directory not found!"
    print_info "Please run ./scripts/build.sh first"
    exit 1
fi

cd build

print_info "Running tests..."

# Запуск CTest
if command -v ctest &> /dev/null; then
    ctest --output-on-failure --verbose
else
    print_error "CTest not found!"
    exit 1
fi

# Ручной запуск тестов (если нужно)
if [ -f "ci_test_dir.exe" ] || [ -f "ci_test_dir" ]; then
    print_info "Running basic test manually..."
    if [ -f "ci_test_dir.exe" ]; then
        ./ci_test_dir.exe
    else
        ./ci_test_dir
    fi
fi

cd ..
print_info "All tests completed!"