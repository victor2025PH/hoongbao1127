#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""解決 PowerShell 輸出問題的工具"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# 輸出文件
OUTPUT_FILE = Path(__file__).parent / "命令輸出.txt"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def execute_and_save(cmd, description):
    """執行命令並保存輸出到文件"""
    print(f"\n執行: {description}")
    print(f"命令: {cmd}")
    
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"時間: {TIMESTAMP}\n")
        f.write(f"描述: {description}\n")
        f.write(f"命令: {cmd}\n")
        f.write(f"{'='*60}\n\n")
        
        try:
            process = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            output = process.stdout
            f.write(output)
            f.write(f"\n退出代碼: {process.returncode}\n")
            f.write(f"{'='*60}\n\n")
            
            # 同時輸出到控制台
            print(output)
            print(f"退出代碼: {process.returncode}")
            
            return process.returncode, output
            
        except Exception as e:
            error_msg = f"執行失敗: {e}\n"
            f.write(error_msg)
            print(error_msg)
            return 1, error_msg

# 清空輸出文件
if OUTPUT_FILE.exists():
    OUTPUT_FILE.write_text("", encoding='utf-8')

print("=" * 60)
print("  PowerShell 輸出問題解決工具")
print("=" * 60)
print(f"\n所有輸出將保存到: {OUTPUT_FILE}")
print()

# 測試 1: PowerShell 基本命令
exit_code, output = execute_and_save(
    'powershell -Command "Write-Host \'測試輸出\' -ForegroundColor Green; Get-Location"',
    "測試 1: PowerShell 基本輸出"
)

# 測試 2: Python 版本
exit_code, output = execute_and_save(
    'python --version',
    "測試 2: Python 版本"
)

# 測試 3: 配置讀取
os.chdir(Path(__file__).parent / "api")
exit_code, output = execute_and_save(
    '''python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')"''',
    "測試 3: 配置讀取"
)

print()
print("=" * 60)
print(f"所有輸出已保存到: {OUTPUT_FILE}")
print("=" * 60)


