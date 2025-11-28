#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""診斷配置讀取問題"""
import sys
import os
from pathlib import Path

# 結果文件
result_file = Path(__file__).parent / "診斷報告.txt"

with open(result_file, 'w', encoding='utf-8') as f:
    f.write("=" * 60 + "\n")
    f.write("  配置讀取診斷報告\n")
    f.write("=" * 60 + "\n\n")
    
    # 1. 檢查 .env 文件
    f.write("[1] 檢查 .env 文件\n")
    env_file = Path(__file__).parent / ".env"
    f.write(f"  路徑: {env_file}\n")
    f.write(f"  存在: {env_file.exists()}\n")
    
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as ef:
                content = ef.read()
                f.write(f"  文件大小: {len(content)} 字節\n")
                if 'BOT_TOKEN' in content:
                    for line in content.split('\n'):
                        if line.strip().startswith('BOT_TOKEN='):
                            token = line.split('=', 1)[1].strip()
                            f.write(f"  BOT_TOKEN 值: {token[:30]}...\n")
                            f.write(f"  BOT_TOKEN 長度: {len(token)}\n")
                            break
                else:
                    f.write("  ❌ 文件中沒有 BOT_TOKEN\n")
        except Exception as e:
            f.write(f"  ❌ 讀取失敗: {e}\n")
    else:
        f.write("  ❌ 文件不存在\n")
    
    f.write("\n")
    
    # 2. 測試 dotenv 加載
    f.write("[2] 測試 dotenv 加載\n")
    try:
        from dotenv import load_dotenv
        f.write("  ✅ dotenv 模組已導入\n")
        if env_file.exists():
            load_dotenv(env_file, override=True)
            f.write("  ✅ 已執行 load_dotenv\n")
            bot_token_env = os.getenv("BOT_TOKEN")
            if bot_token_env:
                f.write(f"  ✅ 環境變量 BOT_TOKEN: {bot_token_env[:30]}...\n")
                f.write(f"  環境變量長度: {len(bot_token_env)}\n")
            else:
                f.write("  ❌ 環境變量 BOT_TOKEN 為空\n")
    except ImportError:
        f.write("  ❌ dotenv 模組未安裝\n")
    except Exception as e:
        f.write(f"  ❌ 加載失敗: {e}\n")
        import traceback
        f.write(traceback.format_exc())
    
    f.write("\n")
    
    # 3. 測試 Settings 讀取
    f.write("[3] 測試 Settings 讀取\n")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from shared.config.settings import get_settings, ENV_FILE
        f.write(f"  ENV_FILE 路徑: {ENV_FILE}\n")
        f.write(f"  ENV_FILE 存在: {ENV_FILE.exists()}\n")
        
        settings = get_settings()
        f.write(f"  Settings 對象創建成功\n")
        f.write(f"  BOT_TOKEN 長度: {len(settings.BOT_TOKEN)}\n")
        if settings.BOT_TOKEN:
            f.write(f"  ✅ BOT_TOKEN: {settings.BOT_TOKEN[:30]}...\n")
        else:
            f.write("  ❌ BOT_TOKEN 為空\n")
    except Exception as e:
        f.write(f"  ❌ 讀取失敗: {e}\n")
        import traceback
        f.write(traceback.format_exc())
    
    f.write("\n")
    f.write("=" * 60 + "\n")

print(f"診斷完成！結果已保存到: {result_file}")

