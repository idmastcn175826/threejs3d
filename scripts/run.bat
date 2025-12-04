@echo off
REM GestureControlPC 运行脚本

cd /d %~dp0..

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo 警告: 未找到虚拟环境，使用系统 Python
)

REM 运行程序
python main.py %*
