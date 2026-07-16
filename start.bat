@echo off
title 工业安防监测系统

echo ===========================================
echo   工业安防监测系统
echo ===========================================
echo   [1] 网络摄像头 (10.122.139.196)
echo   [2] USB摄像头
echo ===========================================

set /p mode="请输入 1 或 2: "

if "%mode%"=="1" (
    echo.
    echo === 启动网络摄像头模式 ===
    echo 请确保摄像头上的 Flask 服务已启动!
    echo.
    call %CONDA_ROOT%\Scripts\activate.bat yolo26_env
    python main.py
)

if "%mode%"=="2" (
    echo.
    echo === 启动 USB 摄像头模式 ===
    call %CONDA_ROOT%\Scripts\activate.bat yolo26_env
    python main.py 0
)

pause
