cmake_minimum_required(VERSION 3.15)
project(AtomyEngine LANGUAGES C)

# C11, без расширений
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Поиск библиотек
find_package(SDL2 REQUIRED)
find_package(SDL2_image REQUIRED)

# Исходники
set(SOURCES
    src/main.c
    src/core/ecs.c
    src/core/memory.c
    src/core/resource.c
    src/systems/movement.c
    src/systems/render.c
    src/platform/window.c
)

add_executable(atomy_engine ${SOURCES})

target_include_directories(atomy_engine PRIVATE src)
target_link_libraries(atomy_engine PRIVATE
    SDL2::SDL2main
    SDL2::SDL2
    SDL2_image::SDL2_image
)

# Предупреждения как ошибки, MISRA-подобный стиль
if(MSVC)
    target_compile_options(atomy_engine PRIVATE /W4 /WX)
else()
    target_compile_options(atomy_engine PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()