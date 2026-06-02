#===============================================================================
# CMakeLists.txt для PaperGoose Engine
#===============================================================================

cmake_minimum_required(VERSION 3.21)   # Минимальная версия (3.21 нужен для C17)

#-------------------------------------------------------------------------------
# Проект: PaperGoose — 2D игровой движок с редактором пиксель-арта,
#        разрушаемой физикой и ECS.
#-------------------------------------------------------------------------------
project(PaperGoose
    VERSION 0.1.0
    DESCRIPTION "2D game engine with pixel-art editor, destructible physics, and ECS"
    LANGUAGES C          # Используем только C (не C++)
)

#-------------------------------------------------------------------------------
# Стандарт языка C17 (строгий режим, без расширений компилятора)
#-------------------------------------------------------------------------------
set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Проверка компилятора: требуется только GCC (для совместимости с Vulkan и GLFW)
if(NOT CMAKE_C_COMPILER_ID STREQUAL "GNU")
    message(FATAL_ERROR "PaperGoose требует компилятор GCC. Обнаружен: ${CMAKE_C_COMPILER_ID}")
endif()

#-------------------------------------------------------------------------------
# Пользовательские опции сборки
#-------------------------------------------------------------------------------
option(USE_VULKAN   "Enable Vulkan renderer" ON)   # Включить Vulkan (по умолч. ON)
option(BUILD_TESTS  "Build unit tests"       ON)   # Включить тесты

#-------------------------------------------------------------------------------
# Флаги компиляции для Debug/Release (без -Werror для всех)
#-------------------------------------------------------------------------------
set(CMAKE_C_FLAGS_DEBUG   "-g")               # Отладочная информация
set(CMAKE_C_FLAGS_RELEASE "-O3")              # Оптимизация по скорости

if(MINGW)   # Windows (MinGW): статическая линковка библиотек GCC
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -static-libgcc -static-libstdc++")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static")
endif()

#-------------------------------------------------------------------------------
# Поиск Vulkan SDK (без REQUIRED, чтобы можно было падать на софтовый рендерер)
#-------------------------------------------------------------------------------
if(USE_VULKAN)
    find_package(Vulkan QUIET)          # Ищем Vulkan, но не требуем обязательно
    if(Vulkan_FOUND)
        message(STATUS "Vulkan найден: ${Vulkan_VERSION}")
        message(STATUS "Vulkan include: ${Vulkan_INCLUDE_DIRS}")
        message(STATUS "Vulkan library: ${Vulkan_LIBRARIES}")
        add_compile_definitions(USE_VULKAN=1)
    else()
        message(WARNING "Vulkan не найден! Будет использован софтовый рендерер.")
        add_compile_definitions(USE_VULKAN=0)
    endif()
else()
    message(STATUS "Vulkan рендерер отключён пользователем.")
    add_compile_definitions(USE_VULKAN=0)
endif()

#-------------------------------------------------------------------------------
# GLFW — подключение через FetchContent (скачивается и собирается автоматически)
#-------------------------------------------------------------------------------
include(FetchContent)

FetchContent_Declare(
    glfw
    GIT_REPOSITORY https://github.com/glfw/glfw.git
    GIT_TAG 3.4                    # правильный тег (существует в репозитории)
)

# Настройки сборки GLFW (отключаем ненужное)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "")
set(GLFW_BUILD_TESTS    OFF CACHE BOOL "")
set(GLFW_BUILD_DOCS     OFF CACHE BOOL "")
set(GLFW_INSTALL        OFF CACHE BOOL "")

FetchContent_MakeAvailable(glfw)   # Скачивает, конфигурирует и добавляет цель glfw

#-------------------------------------------------------------------------------
# Исходные файлы движка
#-------------------------------------------------------------------------------
set(SOURCES
    src/main.c
)

#-------------------------------------------------------------------------------
# Исполняемый файл
#-------------------------------------------------------------------------------
add_executable(papergoose ${SOURCES})

#-------------------------------------------------------------------------------
# Строгие флаги компиляции применяем ТОЛЬКО к нашей цели (не к GLFW)
#-------------------------------------------------------------------------------
target_compile_options(papergoose PRIVATE 
    -Wall -Wextra -Wpedantic -Werror
)

#-------------------------------------------------------------------------------
# Линковка с библиотеками
#-------------------------------------------------------------------------------
# GLFW — обязательная (создание окна, ввод)
target_link_libraries(papergoose glfw)

# Для Windows: GLFW требует OpenGL и GDI
if(WIN32)
    target_link_libraries(papergoose opengl32 gdi32)
endif()

# Vulkan — если найден и включён
if(USE_VULKAN AND Vulkan_FOUND)
    target_link_libraries(papergoose ${Vulkan_LIBRARIES})
    target_include_directories(papergoose PRIVATE ${Vulkan_INCLUDE_DIRS})
endif()

#-------------------------------------------------------------------------------
# Подключение тестов (если включено)
#-------------------------------------------------------------------------------
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

#-------------------------------------------------------------------------------
# Итоговая информация о конфигурации
#-------------------------------------------------------------------------------
message(STATUS "PaperGoose ${PROJECT_VERSION} настроена:")
message(STATUS "    Компилятор: ${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}")
message(STATUS "    Стандарт C: C${CMAKE_C_STANDARD}")
message(STATUS "    Vulkan: ${USE_VULKAN}")
if(USE_VULKAN AND Vulkan_FOUND)
    message(STATUS "    Vulkan версия: ${Vulkan_VERSION}")
endif()
message(STATUS "    Тесты: ${BUILD_TESTS}")