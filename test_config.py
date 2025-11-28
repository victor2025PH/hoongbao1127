#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""測試配置讀取"""
import sys
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

from shared.config.settings import get_settings, ENV_FILE

# 輸出文件
output_file = Path(__file__).parent / "config_test_result.txt"

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 50 + "\n")
    f.write("配置讀取測試\n")
    f.write("=" * 50 + "\n")
    f.write(f"\n.env 文件路徑: {ENV_FILE}\n")
    f.write(f".env 文件存在: {ENV_FILE.exists()}\n")

    if ENV_FILE.exists():
        f.write(f"\n.env 文件內容（前200字符）:\n")
        try:
            with open(ENV_FILE, 'r', encoding='utf-8') as env_f:
                content = env_f.read(200)
                f.write(content + "\n")
        except Exception as e:
            f.write(f"讀取失敗: {e}\n")

    f.write("\n" + "=" * 50 + "\n")
    f.write("讀取配置:\n")
    f.write("=" * 50 + "\n")

    try:
        settings = get_settings()
        f.write(f"\nBOT_TOKEN 長度: {len(settings.BOT_TOKEN)}\n")
        if settings.BOT_TOKEN:
            f.write(f"BOT_TOKEN 前20字符: {settings.BOT_TOKEN[:20]}\n")
            f.write(f"BOT_TOKEN 後10字符: {settings.BOT_TOKEN[-10:]}\n")
            f.write("✅ BOT_TOKEN 讀取成功！\n")
        else:
            f.write("❌ BOT_TOKEN: 空\n")
        
        f.write(f"\n其他配置:\n")
        f.write(f"  APP_NAME: {settings.APP_NAME}\n")
        f.write(f"  DATABASE_URL: {settings.DATABASE_URL[:50]}...\n")
        
    except Exception as e:
        f.write(f"\n❌ 讀取配置失敗: {e}\n")
        import traceback
        f.write(traceback.format_exc())

    f.write("\n" + "=" * 50 + "\n")

# 同時輸出到控制台
print(f"測試完成！結果已保存到: {output_file}")
print(f"請查看文件: {output_file}")

