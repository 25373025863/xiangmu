@echo off
where py >nul 2>nul
if %errorlevel% equ 0 (
    py main.py
    exit /b 0
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python main.py
    exit /b 0
)

echo 未检测到 Python 3.10+，请安装后重试。
pause
