@echo off
chcp 65001
title 啟動 API 服務器 - 查看錯誤

echo ========================================
echo   啟動 API 服務器
echo ========================================
echo.

cd /d C:\hbgm001\api

echo [步驟 1] 檢查 Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python 未找到
    pause
    exit /b 1
)

echo.
echo [步驟 2] 安裝依賴...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ⚠️  依賴安裝可能失敗
)

echo.
echo [步驟 3] 測試導入...
python -c "from loguru import logger; print('✅ loguru OK')"
python -c "from fastapi import FastAPI; print('✅ fastapi OK')"
python -c "import sys; sys.path.insert(0, '.'); from api.routers import chats; print('✅ chats OK')"

echo.
echo [步驟 4] 啟動服務器...
echo.
echo 服務器將在 http://127.0.0.1:8000 啟動
echo 請查看下面的輸出，找出錯誤原因
echo 如果看到 'Application startup complete' 表示成功
echo 按 Ctrl+C 停止服務器
echo.
echo ========================================
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

echo.
echo ========================================
echo   服務器已停止
echo ========================================
pause

