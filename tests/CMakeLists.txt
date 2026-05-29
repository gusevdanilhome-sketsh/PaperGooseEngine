cmake_minimum_required(VERSION 3.21)

# Простейший тест
add_executable(ci_test_dir ci_test_dir.c)
add_test(NAME CITestDir COMMAND ci_test_dir)

# Тест проверки компиляции main
add_executable(ci_test_main ../src/main.c)
add_test(NAME CITestMain COMMAND ci_test_main)

# Включить вывод при ошибках
set_tests_properties(CITestDir CITestMain PROPERTIES 
    PASS_REGULAR_EXPRESSION ""
)