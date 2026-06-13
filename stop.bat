@echo off
REM Stop reversing-mcp fleet ports
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0reversing-webapp\stop.ps1"
if errorlevel 1 pause

