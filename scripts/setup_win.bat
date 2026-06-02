@echo off
setlocal enabledelayedexpansion

set MSYS2_PATH=C:\msys64

if not exist "%MSYS2_PATH%\usr\bin\bash.exe" (
    echo MSYS2 не найден
    exit /b 1
)

:: Запускаем MSYS2 и устанавливаем пакеты через pacman
"%MSYS2_PATH%\usr\bin\bash.exe" -lc "pacman -S --noconfirm --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake mingw-w64-x86_64-make mingw-w64-x86_64-vulkan-headers mingw-w64-x86_64-vulkan-loader"