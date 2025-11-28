@echo off
REM ========================================
REM 快速檢查配置讀取
REM ========================================
chcp 65001 >nul

echo.
echo ========================================
echo   快速配置檢查
echo ========================================
echo.

cd /d "%~dp0api"

echo 測試配置讀取...
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空'); exit(0 if s.BOT_TOKEN else 1)" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 配置讀取成功！
) else (
    echo.
    echo ❌ 配置讀取失敗！
    echo.
    echo 請檢查:
    echo   1. .env 文件是否存在於 %~dp0.env
    echo   2. .env 文件是否包含 BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs
    echo   3. 確保沒有引號和空格
)

echo.
pause


