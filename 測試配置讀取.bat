@echo off
chcp 65001 >nul
echo ========================================
echo 測試配置讀取
echo ========================================
echo.

cd /d C:\hbgm001\api
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings, ENV_FILE; print('ENV_FILE:', ENV_FILE); print('文件存在:', ENV_FILE.exists()); s = get_settings(); print('BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('BOT_TOKEN 前20字符:', repr(s.BOT_TOKEN[:20]) if s.BOT_TOKEN else '空')"

echo.
echo ========================================
pause

