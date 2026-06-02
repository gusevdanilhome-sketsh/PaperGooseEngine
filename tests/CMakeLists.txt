cmake_minimum_required(VERSION 3.21)

# Простейший тест
add_executable(ci_test_dir ci_test_dir.c)
add_test(NAME CITestDir COMMAND ci_test_dir)