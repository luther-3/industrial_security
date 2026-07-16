@echo off
chcp 65001 >nul
title 工业安防监测系统

echo ===========================================
echo   工业安防监测系统
echo ===========================================
echo.
echo [1] 网络摄像头模式 (10.122.139.196)
echo [2] USB摄像头模式
echo [3] 退出
echo.
choice /c 123 /n /m "请选择 (1/2/3): "

if errorlevel 3 exit /b
if errorlevel 2 goto usb
if errorlevel 1 goto camera

:camera
echo.
echo === 启动网络摄像头模式 ===
echo 请确保摄像头上的 Flask 服务已启动!
echo.
call %CONDA_ROOT%\Scripts\activate.bat yolo26_env
python main.py
goto end

:usb
echo.
echo === 启动 USB 摄像头模式 ===
call %CONDA_ROOT%\Scripts\activate.bat yolo26_env
python main.py 0
goto end

:end
pause
