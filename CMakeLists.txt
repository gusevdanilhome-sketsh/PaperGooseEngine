cmake_minimum_required(VERSION 3.21)    # CMake минимальная версия (3.21 нужен для C17 поддержки)

project(PaperGoose  # Проект: PaperGoose
    VERSION 0.1.0
    DESCRIPTION "2D game engine with pixel-art editor, destructible physics, and ECS"
    LANGUAGES C   # Используем только C (не C++)
)

# 1. Стандарт языка и компилятор
set(CMAKE_C_STANDARD 17)    # Требуем стандарт C17 (C11 + асинхронный I/O, атомарные операции)
set(CMAKE_C_STANDARD_REQUIRED ON)   # Обязательно использовать этот стандарт (не понижать)
set(CMAKE_C_EXTENSIONS OFF)  # Запрещаем расширения компилятора (строгий стандарт)

if(NOT CMAKE_C_COMPILER_ID STREQUAL "GNU")  # Проверка компилятора - требуется только GCC
    message(FATAL_ERROR "PaperGoose требует компилятор GCC. Обнаружен: ${CMAKE_C_COMPILER_ID}") # FATAL_ERROR останавливает конфигурацию с сообщением об ошибке
endif()

# 2. Опции сборки
option(USE_VULKAN "Enable Vulkan renderer" ON)  # Опция: использовать Vulkan (по умолчанию ON)
option(BUILD_TESTS "Build unit tests" ON)

# 3. Глобальные флаги компилятора для GCC
if(CMAKE_C_COMPILER_ID STREQUAL "GNU")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)   # Предупреждения (-Wall -Wextra -Wpedantic): -Werror превращает предупреждения в ошибки
    set(CMAKE_C_FLAGS_DEBUG "-g")   # Настройки для Debug сборки: отладочная информация (-g)
    set(CMAKE_C_FLAGS_RELEASE "-O3")    # Настройки для Release сборки: оптимизация по скорости (-O3)
    if(MINGW)   # Windows специфичные настройки (MinGW)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -static-libgcc -static-libstdc++")  # Статическая линковка GCC библиотек (не нужны DLL)
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static") # Полная статическая линковка (все зависимости в одном EXE)
    endif()
endif()

# 4. Поиск Vulkan SDK
if(USE_VULKAN)
    # Ищем Vulkan в системе
    find_package(Vulkan REQUIRED)   # QUIET - не выводить сообщения об ошибке, если не найден
    if(Vulkan_FOUND)
        message(STATUS "Vulkan found: ${Vulkan_VERSION}")   # Vulkan найден - добавляем define для кода
        message(STATUS "Vulkan include: ${Vulkan_INCLUDE_DIRS}")
        message(STATUS "Vulkan library: ${Vulkan_LIBRARIES}")
        add_compile_definitions(USE_VULKAN=1)   
    else()
        message(WARNING "Vulkan not found! Falling back to software renderer")  # Vulkan найден - добавляем define для кода
        add_compile_definitions(USE_VULKAN=0)
    endif()
else()
    message(STATUS "Vulkan renderer disabled by user")
    add_compile_definitions(USE_VULKAN=0)
endif()

# 5. Исходные файлы движка
set(SOURCES
    src/main.c
)

# 6. Исполняемый файл
add_executable(papergoose
    ${SOURCES}
)

# 7. Линковка с Vulkan
if(USE_VULKAN AND Vulkan_FOUND)
    target_link_libraries(papergoose ${Vulkan_LIBRARIES})
    target_include_directories(papergoose PRIVATE ${Vulkan_INCLUDE_DIRS})
endif()

# 8. Подключение тестов
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# 8. Информационное сообщение
message(STATUS "PaperGoose ${PROJECT_VERSION} настроена:")
message(STATUS "    Компилятор: ${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}")
message(STATUS "    Стандарт C: C${CMAKE_C_STANDARD}")
message(STATUS "    Vulkan: ${USE_VULKAN}")
if(USE_VULKAN AND Vulkan_FOUND)
    message(STATUS "    Vulkan версия: ${Vulkan_VERSION}")
endif()
message(STATUS "    Тесты: ${BUILD_TESTS}")