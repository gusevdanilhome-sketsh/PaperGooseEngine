# Инструкция по установке зависимостей и сборке PaperGoose Engine

В этом документе описан процесс подготовки окружения и сборки игрового движка PaperGoose из исходного кода.

## Поддерживаемые платформы

- **Windows 10/11** с MSYS2 (MinGW-w64 GCC) или нативным окружением MinGW
- **Linux** (Ubuntu 22.04+, Debian, Fedora и др.) с GCC

## Требования

- **Git** для клонирования репозитория и подмодулей
- **CMake >= 3.21**
- **Компилятор GCC** (актуальная стабильная версия, поддержка C17)
- **Vulkan SDK 1.2+** (для аппаратного рендеринга)
- **GLFW** (поставляется как подмодуль, собирается автоматически)

---

## Установка зависимостей

### Windows (MSYS2 MinGW-w64)

1. **Установите MSYS2**  
   Скачайте установщик с [официального сайта](https://www.msys2.org/) и выполните шаги до шага «Update the package database and base packages».  
   Запустите **MSYS2 MinGW 64-bit** (или `mingw64.exe`) из меню Пуск.

2. **Обновите систему и установите инструменты разработки**
   ```bash
   pacman -Syu
   pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake mingw-w64-x86_64-make mingw-w64-x86_64-gdb
   ```

3. **Установите Vulkan SDK**
    Есть два варианта:
    - Рекомендуемый: Скачайте Vulkan SDK с сайта LunarG (версия для Windows), установите и убедитесь, что путь к bin (например, C:\VulkanSDK\1.x.x.x\Bin) добавлен в переменную PATH.
    - Через pacman (альтернатива):
        ```bash
        pacman -S mingw-w64-x86_64-vulkan-headers mingw-w64-x86_64-vulkan-loader mingw-w64-x86_64-vulkan-validation-layers mingw-w64-x86_64-spirv-tools
        ```
    В этом случае заголовочные файлы и библиотеки будут в стандартных путях MSYS2, но CMake должен найти их автоматически.


4. **Добавьте путь к GCC и CMake в переменную PATH (если их нет)**
    Обычно MSYS2 уже прописывает все необходимые переменные при запуске терминала MinGW64.

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install build-essential cmake git libvulkan-dev
```
Для других дистрибутивов используйте соответствующий пакетный менеджер (dnf, pacman, zypper), имена пакетов аналогичны.

### Клонирование репозитория
```bash
git clone https://github.com/your-username/papergoose-engine.git
cd papergoose-engine
git submodule update --init --recursive
```
Если вы планируете разрабатывать, сделайте форк и клонируйте свой репозиторий.

### Сборка
1. Конфигурация (CMake)
    Windows (MSYS2 MinGW):
    ```bash
    cmake -B build -G "MinGW Makefiles" -DUSE_VULKAN=ON -DBUILD_TESTS=OFF
    ```

    Linux:
    ```bash
    cmake -B build -DUSE_VULKAN=ON -DBUILD_TESTS=OFF
    ```

    Доступные опции:
    - USE_VULKAN — включить Vulkan-рендерер (по умолчанию ON). Если Vulkan не нужен или недоступен, поставьте OFF — тогда будет собран только software-рендерер.
    - BUILD_TESTS — сборка модульных тестов (пока отключена, так как тесты не реализованы).

2. Сборка
    ```bash
    cmake --build build
    ```
    Или:
    Windows:
    ```bash
    cd build
    mingw32-make
    ```
    Linux:
    ```bash
    cd build
    make
    ```

3. Запуск
    ```bash
    ./build/papergoose.exe   # Windows
    ./build/papergoose       # Linux
    ```

    Если всё настроено правильно, вы увидите сообщение PaperGoose engine started.. Окно пока не создаётся, потому что код-заглушка только выводит текст в консоль.

### Проверка Vulkan
Чтобы убедиться, что Vulkan SDK установлен корректно, выполните команду:
```bash
vulkaninfo
```

Если команда не найдена, убедитесь, что путь к SDK добавлен в PATH.

### Возможные проблемы
- Ошибка «CMAKE_C_COMPILER not set» — компилятор GCC не найден. Установите GCC и добавьте его в PATH. Для MSYS2 проверьте, что запущен терминал MinGW64, а не обычный MSYS2.
- CMake не находит Vulkan — укажите путь к Vulkan SDK вручную через переменную VULKAN_SDK или добавьте флаг -DVulkan_INCLUDE_DIR=... -DVulkan_LIBRARY=....
- Ошибка линковки GLFW — удалите папку build, затем заново выполните cmake ... Убедитесь, что подмодуль external/glfw инициализирован (git submodule update --init).
- Предупреждения при сборке — не мешают работе, это нормальное поведение для стороннего кода (GLFW). Ошибки компиляции (-Werror) применяются только к исходникам движка.

## Установка Vulkan SDK в папку external/
Для ручной установки Vulkan SDK в папку `external/` выполните:

### Windows:
```bash
# Скачайте Vulkan SDK с https://vulkan.lunarg.com/
# Установите в папку external/vulkan
# Или используйте скрипт:
./scripts/setup_vulkan_win.bat
```

### Linux:
```bash
# Сделайте скрипт исполняемым
chmod +x scripts/setup_vulkan_linux.sh
# Запустите установку
./scripts/setup_vulkan_linux.sh
```

### Проверка Vulkan:
```bash
vulkaninfo
```

## Быстрая установка всех зависимостей
### Windows (MSYS2 MinGW64):
```bash
./scripts/setup_win.bat
```

### Linux:
```bash
chmod +x scripts/setup_linux.sh
./scripts/setup_linux.sh
```

## Тестирование сборки с Vulkan
```bash
# Конфигурация с Vulkan
cmake -B build -G "MinGW Makefiles" -DUSE_VULKAN=ON

# Сборка
cmake --build build

# Запуск
./build/papergoose.exe

# Конфигурация без Vulkan (software renderer)
cmake -B build -G "MinGW Makefiles" -DUSE_VULKAN=OFF
cmake --build build
```