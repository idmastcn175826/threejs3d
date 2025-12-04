@echo off
REM GestureControlPC 构建脚本
REM 使用 PyInstaller 打包为可执行文件

echo ========================================
echo GestureControlPC Build Script
echo ========================================

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo 错误: 未找到虚拟环境，请先运行 python -m venv venv
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装 PyInstaller
pip install pyinstaller

REM 清理旧构建
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM 构建
echo 正在构建...
pyinstaller --name GestureControlPC ^
    --onedir ^
    --windowed ^
    --icon=assets/icon.ico ^
    --add-data "config;config" ^
    --hidden-import=mediapipe ^
    --hidden-import=cv2 ^
    --hidden-import=PyQt5 ^
    main.py

echo ========================================
echo 构建完成！
echo 输出目录: dist\GestureControlPC
echo ========================================

pause
