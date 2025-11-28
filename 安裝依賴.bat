@echo off
REM ========================================
REM 安裝所有必要的 Python 依賴
REM ========================================
chcp 65001 >nul

echo.
echo ========================================
echo   安裝 Python 依賴
echo ========================================
echo.

cd /d "%~dp0api"

echo 正在檢查並安裝依賴...
echo.

python -m pip install --upgrade pip
echo.

echo [1/3] 安裝 python-dotenv...
python -m pip install python-dotenv
echo.

echo [2/3] 安裝 pydantic-settings...
python -m pip install pydantic-settings
echo.

echo [3/3] 安裝 uvicorn...
python -m pip install uvicorn[standard]
echo.

echo ========================================
echo   安裝完成
echo ========================================
echo.

echo 驗證安裝...
python -c "import dotenv; print('✅ python-dotenv')" || echo "❌ python-dotenv 安裝失敗"
python -c "import pydantic_settings; print('✅ pydantic-settings')" || echo "❌ pydantic-settings 安裝失敗"
python -c "import uvicorn; print('✅ uvicorn')" || echo "❌ uvicorn 安裝失敗"

echo.
pause


