#!/bin/bash
# 在服務器上直接修復編譯錯誤

cd /opt/luckyred/frontend

echo "正在修復 SendRedPacket.tsx..."
# 修復第72行的類型錯誤
sed -i "s/bomb_number: packetType === 'fixed' ? bombNumber : undefined,/bomb_number: packetType === 'fixed' \&\& bombNumber !== null ? bombNumber : undefined,/g" src/pages/SendRedPacket.tsx

echo "正在修復 I18nProvider.tsx..."
# 刪除重複的 view_rules（在 bomb_rules 之後的）
# 繁體中文：刪除第117行
sed -i '117d' src/providers/I18nProvider.tsx

# 簡體中文：刪除第297行（刪除後行號會變，需要重新計算）
# 先找到 bomb_rules 之後的第一個 view_rules
sed -i '/bomb_rules:.*紅包炸彈.*/,/^    view_rules: .查看规则.*/{
    /^    view_rules: .查看规则.*/d
}' src/providers/I18nProvider.tsx

# 英文：刪除 bomb_rules 之後的第一個 view_rules
sed -i '/bomb_rules:.*Red Packet Bomb.*/,/^    view_rules: .View Rules.*/{
    /^    view_rules: .View Rules.*/d
}' src/providers/I18nProvider.tsx

echo "修復完成，開始構建..."
npm run build

echo "完成！"

