@echo off
echo ===========================================
echo   Industrial Security Monitor
echo ===========================================
echo   [1] Network Camera
echo   [2] USB Camera
echo ===========================================
set /p mode="Enter 1 or 2: "
if "%mode%"=="1" goto camera
if "%mode%"=="2" goto usb
goto end

:camera
echo.
echo Starting Network Camera mode...
echo.
%CONDA_PREFIX%\python.exe main.py
goto end

:usb
echo.
echo Starting USB Camera mode...
%CONDA_PREFIX%\python.exe main.py 0
goto end

:end
pause
