cmake_minimum_required(VERSION 3.21)

project(PaperGoose
    VERSION 0.1.0
    DESCRIPTION "2D game engine with pixel-art editor, destructible physics, and ECS"
    LANGUAGES C
)

# 1. Стандарт языка и компилятор
set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)  # строгий C17, без расширений GCC

if(NOT CMAKE_C_COMPILER_ID STREQUAL "GNU")  # Требовать именно GCC
    message(FATAL_ERROR "PaperGoose требует компилятор GCC. Обнаружен: ${CMAKE_C_COMPILER_ID}")
endif()

# 2. Глобальные флаги компилятора для GCC
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

# 3. Исходные файлы движка
set(SOURCES
    src/main.c
)

# 4. Исполняемый файл
add_executable(papergoose
    ${SOURCES}
)

# 5. Информационное сообщение
message(STATUS "PaperGoose ${PROJECT_VERSION} настроена:")
message(STATUS "    Компилятор: ${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}")
message(STATUS "    Стандарт C: C${CMAKE_C_STANDARD}")