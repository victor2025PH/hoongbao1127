#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修復 .env 文件（移除 BOM）
"""
from pathlib import Path

env_file = Path('.env')

if not env_file.exists():
    print("❌ .env 文件不存在")
    exit(1)

# 讀取文件內容
with open(env_file, 'rb') as f:
    content = f.read()

# 檢查並移除 BOM
if content.startswith(b'\xef\xbb\xbf'):
    print("發現 UTF-8 BOM，正在移除...")
    content = content[3:]
    
    # 備份原文件
    backup_file = env_file.with_suffix('.env.bak')
    with open(backup_file, 'wb') as f:
        f.write(content)
    print(f"✅ 已創建備份: {backup_file}")
    
    # 寫回文件（無 BOM）
    with open(env_file, 'wb') as f:
        f.write(content)
    print("✅ 已修復 .env 文件（移除 BOM）")
else:
    print("✅ 文件沒有 BOM，無需修復")

# 驗證修復
print("\n驗證修復:")
from dotenv import load_dotenv
import os
load_dotenv(env_file, override=True)
token = os.getenv('BOT_TOKEN', '')
if token:
    print(f"✅ BOT_TOKEN 讀取成功，長度: {len(token)}")
    print(f"   BOT_TOKEN 前30字符: {token[:30]}")
else:
    print("❌ BOT_TOKEN 仍為空")

