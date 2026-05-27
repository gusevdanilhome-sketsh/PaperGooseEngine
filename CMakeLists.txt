cmake_minimum_required(VERSION 3.21)

project(PaperGoose
        VERSION 0.1.0
        DESCRIPTION "2D game engine with pixel-art editor, destructible physics, and ECS"
        LANGUAGES C)

# 1. Стандарт языка и компилятор
set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)  # строгий C17, без расширений GCC

# Требовать именно GCC (как указано в ТЗ)
if(NOT CMAKE_C_COMPILER_ID STREQUAL "GNU")
    message(FATAL_ERROR "PaperGoose требует компилятор GCC. Обнаружен: ${CMAKE_C_COMPILER_ID}")
endif()

# 2. Опции сборки
option(USE_VULKAN "Сборка с поддержкой Vulkan-рендерера" ON)
option(BUILD_TESTS "Сборка тестов" OFF)
option(BUILD_EDITOR "Сборка редактора" OFF)

# 3. Глобальные флаги компилятора для GCC
if(CMAKE_C_COMPILER_ID STREQUAL "GNU")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
    # Оптимизации (только для Release)
    set(CMAKE_C_FLAGS_DEBUG "-g")
    # Отладочная информация и защита стека в Debug
    set(CMAKE_C_FLAGS_RELEASE "-O3")
    # Статическая линковка runtime (MinGW)
    if(MINGW)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -static-libgcc")
    endif()
endif()

# 4. Зависимости
# Vulkan SDK
if(USE_VULKAN)
    find_package(Vulkan REQUIRED)
    if(NOT Vulkan_FOUND)
        message(FATAL_ERROR "Vulkan SDK не найден. Установите Vulkan SDK и укажите путь.")
    endif()
    add_compile_definitions(PG_USE_VULKAN)
endif()

# GLFW (внешняя зависимость для окон и ввода)
# Предполагается, что GLFW добавлен как submodule в external/glfw или находится в системе
if(NOT TARGET glfw)
    find_package(glfw3 QUIET)
    if(NOT glfw3_FOUND)
        message(STATUS "GLFW не найден в системе, будет собрана из external/glfw")
        add_subdirectory(external/glfw)
        # Убираем -Werror для стороннего кода GLFW
        target_compile_options(glfw PRIVATE -Wno-error)
    endif()
endif()

# 5. Исходные файлы движка (пока минимальный набор для этапа 1)
set(SOURCES
    src/main.c
)

# 6. Исполняемый файл (заглушка главного приложения)
add_executable(papergoose
    ${SOURCES}
)

# Линковка зависимостей
target_link_libraries(papergoose PRIVATE
    glfw
    ${Vulkan_LIBRARIES}
)

# Каталоги заголовков
target_include_directories(papergoose PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${Vulkan_INCLUDE_DIRS}
)

# 7. Тесты (если включены)
if(BUILD_TESTS)
    enable_testing()
    # add_subdirectory(tests)  # раскомментировать, когда появятся тесты
endif()

# 8. Редактор (будет добавлен позже)
if(BUILD_EDITOR)
    # На первом этапе редактор не собирается, оставлена заготовка
    # add_subdirectory(src/editor)
endif()

# 9. Информационное сообщение
message(STATUS "PaperGoose ${PROJECT_VERSION} настроена:")
message(STATUS "  Компилятор: ${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}")
message(STATUS "  Стандарт C: C${CMAKE_C_STANDARD}")
message(STATUS "  Vulkan: ${USE_VULKAN}")
message(STATUS "  Сборка тестов: ${BUILD_TESTS}")