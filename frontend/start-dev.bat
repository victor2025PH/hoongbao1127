@echo off
echo Starting frontend development server...
cd /d %~dp0
call npm run dev
pause
