cmake_minimum_required(VERSION 3.21)

project(PaperGoose
    VERSION 0.1.0
    DESCRIPTION "2D game engine with pixel-art editor, destructible physics, and ECS"
    LANGUAGES C
)

# 1. Опции сборки
option(USE_VULKAN "Enable Vulkan renderer" ON)
option(BUILD_TESTS "Build unit tests" ON)

# 2. Стандарт языка и компилятор
set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)  # строгий C17, без расширений GCC

if(NOT CMAKE_C_COMPILER_ID STREQUAL "GNU")  # Требовать именно GCC
    message(FATAL_ERROR "PaperGoose требует компилятор GCC. Обнаружен: ${CMAKE_C_COMPILER_ID}")
endif()

# 3. Глобальные флаги компилятора для GCC
if(CMAKE_C_COMPILER_ID STREQUAL "GNU")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
    
    set(CMAKE_C_FLAGS_DEBUG "-g")   # Оптимизации (только для Release)
    
    set(CMAKE_C_FLAGS_RELEASE "-O3")    # Отладочная информация и защита стека в Debug

    if(MINGW)   # Статическая линковка runtime (MinGW)
        # Полная статическая линковка runtime и всех библиотек
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -static-libgcc -static-libstdc++")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static")
    endif()
endif()

# 4. Поиск Vulkan SDK
if(USE_VULKAN)
    # Пробуем найти Vulkan через стандартный find_package
    find_package(Vulkan REQUIRED)
    
    if(Vulkan_FOUND)
        message(STATUS "Vulkan found: ${Vulkan_VERSION}")
        message(STATUS "Vulkan include: ${Vulkan_INCLUDE_DIRS}")
        message(STATUS "Vulkan library: ${Vulkan_LIBRARIES}")
        
        # Определяем макрос для условной компиляции
        add_compile_definitions(USE_VULKAN=1)
    else()
        message(WARNING "Vulkan not found! Falling back to software renderer")
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

# Если Vulkan включен и найден, добавляем заглушку для Vulkan
if(USE_VULKAN AND Vulkan_FOUND)
    message(STATUS "Vulkan renderer will be compiled")
else()
    message(STATUS "Using software renderer (stub)")
endif()

# 6. Исполняемый файл
add_executable(papergoose
    ${SOURCES}
)

# 7. Линковка с Vulkan
if(USE_VULKAN AND Vulkan_FOUND)
    target_link_libraries(papergoose ${Vulkan_LIBRARIES})
    target_include_directories(papergoose PRIVATE ${Vulkan_INCLUDE_DIRS})
endif()

# 7. Подключение тестов
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