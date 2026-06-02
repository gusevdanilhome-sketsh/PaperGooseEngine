set -e  # прерывать выполнение при любой ошибке

# Проверяем, запущен ли скрипт с sudo
if [ "$EUID" -ne 0 ]; then
    echo "Недостаточно прав"
    exit 1
fi

apt-get update

apt-get install -y \
    build-essential \
    cmake \
    gcc \
    libvulkan-dev \
    git \
    pkg-config