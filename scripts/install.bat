@echo off
REM GestureControlPC 安装脚本

echo ========================================
echo GestureControlPC 安装脚本
echo ========================================

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 创建虚拟环境
echo 创建虚拟环境...
python -m venv venv

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 升级 pip
echo 升级 pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt

echo ========================================
echo 安装完成！
echo.
echo 运行方式:
echo   1. 激活虚拟环境: venv\Scripts\activate
echo   2. 运行程序: python main.py
echo.
echo 或者直接运行: scripts\run.bat
echo ========================================

pause
