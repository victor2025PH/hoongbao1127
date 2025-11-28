@echo off
REM ========================================
REM 診斷 BOT_TOKEN 讀取問題
REM ========================================
chcp 65001 >nul

echo.
echo ========================================
echo   診斷 BOT_TOKEN 讀取問題
echo ========================================
echo.

cd /d "%~dp0"

REM 檢查 .env 文件
echo [1] 檢查 .env 文件...
if not exist ".env" (
    echo ❌ .env 文件不存在！
    echo.
    echo 請在 %~dp0 創建 .env 文件
    pause
    exit /b 1
)
echo ✅ .env 文件存在
echo.

REM 顯示 .env 文件內容（隱藏敏感信息）
echo [2] 檢查 .env 文件內容...
python -c "with open('.env', 'r', encoding='utf-8') as f: lines = f.readlines(); print('文件行數:', len(lines)); [print(f'  行{i+1}: {line[:50]}...' if len(line) > 50 else f'  行{i+1}: {line.rstrip()}') for i, line in enumerate(lines[:10])]"
echo.

REM 檢查 BOT_TOKEN 環境變量
echo [3] 檢查環境變量...
python -c "import os; token = os.getenv('BOT_TOKEN', ''); print('環境變量 BOT_TOKEN 長度:', len(token)); print('環境變量 BOT_TOKEN:', token[:30] if token else '未設置')"
echo.

REM 測試 dotenv 加載
echo [4] 測試 dotenv 加載...
python -c "from dotenv import load_dotenv; import os; load_dotenv('.env', override=True); token = os.getenv('BOT_TOKEN', ''); print('dotenv 加載後 BOT_TOKEN 長度:', len(token)); print('dotenv 加載後 BOT_TOKEN:', token[:30] if token else '未設置')"
echo.

REM 測試 Settings 類讀取
echo [5] 測試 Settings 類讀取...
cd api
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('Settings.BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('Settings.BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')"
echo.

REM 檢查文件編碼
echo [6] 檢查文件編碼...
cd ..
python -c "with open('.env', 'rb') as f: content = f.read(); print('文件前 100 字節:', content[:100]); print('是否包含 BOM:', content.startswith(b'\xef\xbb\xbf'))"
echo.

echo ========================================
echo   診斷完成
echo ========================================
echo.
pause

