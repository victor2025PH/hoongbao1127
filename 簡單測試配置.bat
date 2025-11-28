@echo off
chcp 65001 >nul
echo ========================================
echo 簡單配置測試
echo ========================================
echo.

cd /d C:\hbgm001\api
python -c "import sys; sys.path.insert(0, '..'); import os; from dotenv import load_dotenv; from pathlib import Path; env_file = Path('..') / '.env'; print('ENV_FILE:', env_file); print('存在:', env_file.exists()); load_dotenv(env_file, override=True); print('環境變量 BOT_TOKEN:', os.getenv('BOT_TOKEN', '空')[:30] if os.getenv('BOT_TOKEN') else '空'); from shared.config.settings import get_settings; s = get_settings(); print('Settings BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')"

echo.
pause

