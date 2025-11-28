#!/bin/bash
# 在服務器上直接修復編譯錯誤

cd /opt/luckyred/frontend

echo "修復 SendRedPacket.tsx 的類型錯誤..."
sed -i "s/bomb_number: packetType === 'fixed' ? bombNumber : undefined,/bomb_number: packetType === 'fixed' \&\& bombNumber !== null ? bombNumber : undefined,/g" src/pages/SendRedPacket.tsx

echo "修復 I18nProvider.tsx 的重複鍵..."
# 刪除第117行的重複 view_rules（繁體中文）
sed -i '/^    view_rules: .查看規則.,$/d' src/providers/I18nProvider.tsx
# 刪除第297行的重複 view_rules（簡體中文）  
sed -i '/^    view_rules: .查看规则.,$/d' src/providers/I18nProvider.tsx
# 刪除第476行的重複 view_rules（英文）
sed -i '/^    view_rules: .View Rules.,$/d' src/providers/I18nProvider.tsx

# 但保留第43、223、403行的 view_rules（在任務部分）
# 需要更精確的刪除：只刪除在 bomb_rules 之後的 view_rules

echo "重新構建..."
npm run build

echo "完成！"

