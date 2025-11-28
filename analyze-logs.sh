#!/bin/bash
# 分析服務日誌腳本

echo "=========================================="
echo "  Lucky Red 服務日誌分析"
echo "=========================================="
echo ""

# 1. Bot 服務狀態
echo "[1] Bot 服務狀態"
echo "----------------------------------------"
sudo systemctl status luckyred-bot --no-pager -l | head -20
echo ""

# 2. Bot 最近日誌
echo "[2] Bot 最近 30 條日誌"
echo "----------------------------------------"
sudo journalctl -u luckyred-bot -n 30 --no-pager
echo ""

# 3. API 服務狀態
echo "[3] API 服務狀態"
echo "----------------------------------------"
sudo systemctl status luckyred-api --no-pager -l | head -20
echo ""

# 4. API 最近日誌
echo "[4] API 最近 30 條日誌"
echo "----------------------------------------"
sudo journalctl -u luckyred-api -n 30 --no-pager
echo ""

# 5. 檢查錯誤
echo "[5] 檢查錯誤日誌"
echo "----------------------------------------"
echo "Bot 錯誤:"
sudo journalctl -u luckyred-bot --since "5 minutes ago" --no-pager | grep -i "error\|exception\|failed\|traceback" | tail -10
echo ""
echo "API 錯誤:"
sudo journalctl -u luckyred-api --since "5 minutes ago" --no-pager | grep -i "error\|exception\|failed\|traceback" | tail -10
echo ""

# 6. 檢查 Bot Token 配置
echo "[6] Bot Token 配置檢查"
echo "----------------------------------------"
if [ -f /opt/luckyred/.env ]; then
    echo "BOT_TOKEN 配置:"
    grep "BOT_TOKEN" /opt/luckyred/.env | sed 's/BOT_TOKEN=\(.*\)/BOT_TOKEN=***/' 
    echo ""
    echo "BOT_TOKEN 長度: $(grep 'BOT_TOKEN=' /opt/luckyred/.env | cut -d'=' -f2 | wc -c) 字符"
else
    echo "❌ .env 文件不存在"
fi
echo ""

# 7. 檢查服務運行時間
echo "[7] 服務運行時間"
echo "----------------------------------------"
echo "Bot 運行時間:"
sudo systemctl show luckyred-bot --property=ActiveEnterTimestamp --value
echo ""
echo "API 運行時間:"
sudo systemctl show luckyred-api --property=ActiveEnterTimestamp --value
echo ""

echo "=========================================="
echo "  日誌分析完成"
echo "=========================================="

