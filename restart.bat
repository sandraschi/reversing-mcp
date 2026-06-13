@echo off
REM Hard restart reversing-mcp
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0reversing-webapp\stop.ps1"
if errorlevel 1 (
    echo stop failed
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0reversing-webapp\start.ps1"
pause

