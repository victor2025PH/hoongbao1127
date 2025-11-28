#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全自動測試配置並啟動服務器"""
import sys
import os
import subprocess
from pathlib import Path

# 設置工作目錄
BASE_DIR = Path(__file__).parent
API_DIR = BASE_DIR / "api"
RESULT_FILE = BASE_DIR / "自動測試結果.txt"

# 同時輸出到控制台和文件
class TeeOutput:
    def __init__(self, *files):
        self.files = files
    
    def write(self, text):
        for f in self.files:
            f.write(text)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()

# 打開結果文件
result_file = open(RESULT_FILE, 'w', encoding='utf-8')
tee = TeeOutput(sys.stdout, result_file)
sys.stdout = tee
sys.stderr = tee

print("=" * 60)
print("  全自動測試和啟動服務器")
print("=" * 60)
print()

# 步驟 1: 檢查 .env 文件
print("[步驟 1] 檢查 .env 文件...")
env_file = BASE_DIR / ".env"
print(f"  路徑: {env_file}")
print(f"  存在: {env_file.exists()}")

if not env_file.exists():
    print()
    print("❌ 錯誤: .env 文件不存在！")
    print(f"   請在 {env_file} 創建 .env 文件")
    print("   內容應包含: BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs")
    sys.exit(1)

# 檢查 .env 文件內容
print("  檢查 BOT_TOKEN...")
try:
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'BOT_TOKEN' in content:
            # 提取 BOT_TOKEN 值
            for line in content.split('\n'):
                if line.strip().startswith('BOT_TOKEN='):
                    token_value = line.split('=', 1)[1].strip()
                    if token_value:
                        print(f"  ✅ 找到 BOT_TOKEN: {token_value[:20]}...")
                        break
            else:
                print("  ⚠️  BOT_TOKEN 行存在但值為空")
        else:
            print("  ❌ .env 文件中沒有 BOT_TOKEN")
            sys.exit(1)
except Exception as e:
    print(f"  ❌ 讀取 .env 文件失敗: {e}")
    sys.exit(1)

print()

# 步驟 2: 測試配置讀取
print("[步驟 2] 測試配置讀取...")
sys.path.insert(0, str(BASE_DIR))

try:
    from shared.config.settings import get_settings, ENV_FILE
    
    print(f"  ENV_FILE 路徑: {ENV_FILE}")
    print(f"  文件存在: {ENV_FILE.exists()}")
    
    settings = get_settings()
    print(f"  BOT_TOKEN 長度: {len(settings.BOT_TOKEN)}")
    
    if settings.BOT_TOKEN:
        print(f"  ✅ BOT_TOKEN 讀取成功: {settings.BOT_TOKEN[:20]}...")
    else:
        print("  ❌ BOT_TOKEN 為空！")
        print()
        print("  可能的原因:")
        print("    1. dotenv 未正確加載 .env 文件")
        print("    2. pydantic-settings 未讀取環境變量")
        print("    3. .env 文件格式不正確")
        print()
        print("  診斷信息:")
        import os
        from dotenv import load_dotenv
        load_dotenv(env_file, override=True)
        env_token = os.getenv("BOT_TOKEN")
        print(f"    環境變量 BOT_TOKEN: {env_token[:20] if env_token else '空'}...")
        sys.exit(1)
        
except Exception as e:
    print(f"  ❌ 配置讀取失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# 步驟 3: 檢查依賴
print("[步驟 3] 檢查依賴...")
try:
    import uvicorn
    print("  ✅ uvicorn 已安裝")
except ImportError:
    print("  ❌ uvicorn 未安裝")
    print("    執行: pip install uvicorn")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    print("  ✅ python-dotenv 已安裝")
except ImportError:
    print("  ❌ python-dotenv 未安裝")
    print("    執行: pip install python-dotenv")
    sys.exit(1)

try:
    from pydantic_settings import BaseSettings
    print("  ✅ pydantic-settings 已安裝")
except ImportError:
    print("  ❌ pydantic-settings 未安裝")
    print("    執行: pip install pydantic-settings")
    sys.exit(1)

print()

# 步驟 4: 啟動服務器
print("[步驟 4] 啟動服務器...")
print("  服務器地址: http://127.0.0.1:8000")
print("  API 文檔: http://127.0.0.1:8000/docs")
print("  按 Ctrl+C 停止服務器")
print()
print("=" * 60)
print()

# 切換到 API 目錄
os.chdir(API_DIR)

# 啟動服務器
try:
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--reload",
        "--host", "127.0.0.1",
        "--port", "8000"
    ], check=True)
except KeyboardInterrupt:
    print()
    print("服務器已停止")
except subprocess.CalledProcessError as e:
    print()
    print(f"❌ 服務器啟動失敗，退出代碼: {e.returncode}")
    sys.exit(1)
except Exception as e:
    print()
    print(f"❌ 啟動服務器時發生錯誤: {e}")
    import traceback
    traceback.print_exc()
    result_file.close()
    sys.exit(1)

# 關閉結果文件
result_file.close()

