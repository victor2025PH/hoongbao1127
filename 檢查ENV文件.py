#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
檢查 .env 文件格式
"""
import os
from pathlib import Path

env_file = Path('.env')

print("=" * 50)
print("檢查 .env 文件")
print("=" * 50)
print()

if not env_file.exists():
    print("❌ .env 文件不存在")
    exit(1)

print(f"✅ 文件存在: {env_file.absolute()}")
print(f"   文件大小: {env_file.stat().st_size} bytes")
print()

# 讀取文件內容
with open(env_file, 'rb') as f:
    raw_content = f.read()

print("文件編碼檢查:")
print(f"   前 100 字節: {raw_content[:100]}")
print(f"   是否包含 BOM: {raw_content.startswith(b'\\xef\\xbb\\xbf')}")
print()

# 嘗試不同編碼讀取
encodings = ['utf-8', 'utf-8-sig', 'gbk', 'latin-1']
content = None
used_encoding = None

for encoding in encodings:
    try:
        with open(env_file, 'r', encoding=encoding) as f:
            content = f.read()
            used_encoding = encoding
            print(f"✅ 成功使用 {encoding} 編碼讀取")
            break
    except Exception as e:
        print(f"❌ 使用 {encoding} 編碼失敗: {e}")

print()

if content is None:
    print("❌ 無法讀取文件內容")
    exit(1)

print(f"文件內容（前 500 字符）:")
print("-" * 50)
print(content[:500])
print("-" * 50)
print()

# 檢查 BOT_TOKEN
lines = content.split('\n')
bot_token_line = None
for i, line in enumerate(lines, 1):
    if 'BOT_TOKEN' in line.upper():
        bot_token_line = (i, line)
        break

if bot_token_line:
    line_num, line_content = bot_token_line
    print(f"✅ 找到 BOT_TOKEN 行（第 {line_num} 行）:")
    # 隱藏完整 token，只顯示前後部分
    if '=' in line_content:
        key, value = line_content.split('=', 1)
        value = value.strip()
        if value:
            masked_value = value[:10] + '...' + value[-10:] if len(value) > 20 else value[:10] + '...'
            print(f"   {key}={masked_value}")
            print(f"   實際長度: {len(value)} 字符")
        else:
            print(f"   {line_content}")
            print("   ⚠️  值為空！")
    else:
        print(f"   {line_content}")
        print("   ⚠️  格式不正確（缺少 = 號）")
else:
    print("❌ 未找到 BOT_TOKEN 行")

print()

# 測試 dotenv 加載
print("測試 dotenv 加載:")
try:
    from dotenv import load_dotenv
    load_dotenv(env_file, override=True)
    token = os.getenv('BOT_TOKEN', '')
    if token:
        print(f"✅ dotenv 加載成功，BOT_TOKEN 長度: {len(token)}")
        print(f"   BOT_TOKEN 前30字符: {token[:30]}")
    else:
        print("❌ dotenv 加載後 BOT_TOKEN 仍為空")
        print("   可能原因:")
        print("   1. .env 文件中 BOT_TOKEN 值為空")
        print("   2. 文件格式不正確（例如有多餘空格）")
        print("   3. 編碼問題")
except ImportError:
    print("❌ python-dotenv 未安裝")
except Exception as e:
    print(f"❌ 加載失敗: {e}")

print()
print("=" * 50)

