@echo off
REM 解決 PowerShell 輸出被抑制的問題
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   顯示輸出測試工具
echo ========================================
echo.

REM 設置輸出文件
set OUTPUT_FILE=%~dp0命令輸出_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set OUTPUT_FILE=!OUTPUT_FILE: =0!

echo 所有輸出將同時顯示在屏幕上並保存到文件
echo 輸出文件: %OUTPUT_FILE%
echo.

REM 測試 1: 基本輸出
echo [測試 1] 基本輸出
echo 這是一條測試消息
echo 當前目錄: %CD%
echo.

REM 測試 2: Python 版本
echo [測試 2] Python 版本
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python 未安裝或不在 PATH 中
) else (
    echo ✅ Python 可用
)
echo.

REM 測試 3: 配置讀取
echo [測試 3] 配置讀取
cd /d %~dp0api
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')"
set CONFIG_RESULT=!ERRORLEVEL!
if !CONFIG_RESULT! EQU 0 (
    echo ✅ 配置讀取成功
) else (
    echo ❌ 配置讀取失敗
)
echo.

REM 將所有輸出保存到文件
(
    echo ========================================
    echo   輸出測試結果
    echo   時間: %date% %time%
    echo ========================================
    echo.
    echo [測試 1] 基本輸出
    echo 當前目錄: %CD%
    echo.
    echo [測試 2] Python 版本
    python --version
    echo.
    echo [測試 3] 配置讀取
    cd /d %~dp0api
    python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')"
) > "%OUTPUT_FILE%" 2>&1

echo.
echo ========================================
echo 所有輸出已保存到: %OUTPUT_FILE%
echo ========================================
echo.

pause


