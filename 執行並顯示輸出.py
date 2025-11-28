#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""執行命令並顯示輸出"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """執行命令並顯示輸出"""
    print("=" * 60)
    if description:
        print(f"  {description}")
    else:
        print(f"  執行命令: {cmd}")
    print("=" * 60)
    print()
    
    try:
        # 使用 subprocess 執行命令，實時顯示輸出
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1,  # 行緩衝
            universal_newlines=True
        )
        
        # 實時讀取並顯示輸出
        for line in process.stdout:
            print(line, end='')
            sys.stdout.flush()
        
        # 等待進程結束
        process.wait()
        
        print()
        print(f"退出代碼: {process.returncode}")
        return process.returncode
        
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  PowerShell 輸出測試工具")
    print("=" * 60)
    print()
    
    # 測試 1: 基本 PowerShell 命令
    run_command('powershell -Command "Write-Host \'測試輸出\' -ForegroundColor Green; Get-Location"', "測試 1: 基本 PowerShell 輸出")
    
    # 測試 2: Python 命令
    run_command('python --version', "測試 2: Python 版本")
    
    # 測試 3: 配置讀取
    print()
    print("=" * 60)
    print("  測試 3: 配置讀取")
    print("=" * 60)
    print()
    
    os.chdir(Path(__file__).parent / "api")
    cmd = '''python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')"'''
    exit_code = run_command(cmd, "配置讀取測試")
    
    print()
    print("=" * 60)
    if exit_code == 0:
        print("  ✅ 所有測試完成")
    else:
        print("  ❌ 測試失敗")
    print("=" * 60)


