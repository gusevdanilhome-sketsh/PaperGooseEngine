# Тесты для PaperGoose Engine (этап 1)

add_executable(test_runner
    test_main.c
    # Добавьте сюда файлы с тестами, когда они появятся
    # test_ecs.c
    # test_memory.c
)

# Вместо линковки с исполняемым файлом papergoose,
# просто компилируем нужные исходники прямо в тестовый бинарник.
# Это временное решение, пока не выделена библиотека ядра.
target_sources(test_runner PRIVATE
    ${CMAKE_SOURCE_DIR}/src/core/ecs.c
    ${CMAKE_SOURCE_DIR}/src/core/memory.c
    # При необходимости добавьте другие .c файлы ядра
)

target_include_directories(test_runner PRIVATE ${CMAKE_SOURCE_DIR}/src)

# Линкуем зависимости, которые нужны тестируемому коду (если есть)
target_link_libraries(test_runner PRIVATE
    glfw
    ${Vulkan_LIBRARIES}
)

# Включаем тесты CTest
enable_testing()
add_test(NAME test_runner COMMAND test_runner)