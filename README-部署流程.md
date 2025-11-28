# 完整部署流程指南

## 🚀 快速開始

### 方法 1：一鍵完整部署（推薦）

**雙擊運行**：`一鍵完整部署.bat`

這會自動執行：
1. ✅ 本地構建測試
2. ✅ 提交所有更改
3. ✅ 推送到 GitHub
4. ✅ 部署到服務器

---

### 方法 2：分步執行

#### 步驟 1：本地操作

**雙擊運行**：`完整部署流程.bat`

或手動執行：
```bash
# 1. 本地構建測試
cd frontend
npm run build
cd ..

# 2. 提交並推送
git add -A
git commit -m "fix: 修復所有錯誤"
git push origin master
```

#### 步驟 2：服務器部署

**選項 A：使用腳本**
```bash
ssh ubuntu@165.154.254.99 "bash -s" < 服務器部署.sh
```

**選項 B：手動執行**
```bash
ssh ubuntu@165.154.254.99
cd /opt/luckyred
git fetch origin
git reset --hard origin/master
cd frontend
sudo rm -rf dist node_modules/.vite
npm run build
sudo systemctl reload nginx
```

---

## 📋 完整命令列表

### 本地操作（一次性執行）

```powershell
# PowerShell
cd C:\hbgm001
.\完整部署流程.ps1
```

```bash
# CMD
cd C:\hbgm001
完整部署流程.bat
```

### 服務器操作（一次性執行）

```bash
# 從本地執行（需要 SSH 配置）
ssh ubuntu@165.154.254.99 "cd /opt/luckyred && git fetch origin && git reset --hard origin/master && cd frontend && sudo rm -rf dist node_modules/.vite && npm run build && sudo systemctl reload nginx"
```

或複製 `服務器部署.sh` 到服務器後執行：
```bash
chmod +x 服務器部署.sh
./服務器部署.sh
```

---

## 🔍 檢查清單

### 提交前檢查

- [ ] 本地構建成功：`npm run build`
- [ ] 沒有 TypeScript 錯誤
- [ ] 所有相關文件都已修改
- [ ] 檢查 `git status` 確認所有文件

### 部署後檢查

- [ ] 服務器代碼已更新：`git log -1`
- [ ] 前端構建成功
- [ ] 服務運行正常：`systemctl status`
- [ ] 網站可以訪問

---

## ⚠️ 常見問題

### 1. 本地構建失敗

**解決方案**：
```bash
# 檢查錯誤
cd frontend
npm run build

# 修復錯誤後重新執行
```

### 2. 推送失敗（認證問題）

**解決方案**：
1. 訪問：https://github.com/settings/tokens
2. 生成新的 Personal Access Token
3. 推送時使用 token 作為密碼

### 3. 服務器代碼未更新

**解決方案**：
```bash
# 強制重置
ssh ubuntu@165.154.254.99
cd /opt/luckyred
git fetch origin
git reset --hard origin/master
```

### 4. 構建權限錯誤

**解決方案**：
```bash
# 清理並重建
sudo rm -rf dist node_modules/.vite
npm run build
```

---

## 📝 最佳實踐

### ✅ 應該做的

1. **本地完整測試**
   ```bash
   npm run build  # 確保沒有錯誤
   ```

2. **一次性提交相關文件**
   ```bash
   git add -A  # 添加所有修改
   git commit -m "描述性提交信息"
   ```

3. **檢查服務器同步**
   ```bash
   git reset --hard origin/master  # 強制同步
   ```

### ❌ 不應該做的

1. ❌ 不測試就提交
2. ❌ 分開提交相關文件
3. ❌ 忽略構建錯誤
4. ❌ 不檢查服務器代碼版本

---

## 🎯 改進建議

### 立即改進

1. **使用提供的腳本**
   - `一鍵完整部署.bat` - 最簡單
   - `完整部署流程.bat` - 分步執行
   - `服務器部署.sh` - 服務器部署

2. **建立檢查清單**
   - 提交前檢查
   - 部署後驗證

### 長期改進

1. **設置 CI/CD**
   - GitHub Actions 自動測試
   - 自動部署到服務器

2. **使用 Git Hooks**
   - pre-commit：構建測試
   - pre-push：完整檢查

3. **代碼審查流程**
   - Pull Request 審查
   - 自動化測試

---

## 📞 需要幫助？

如果遇到問題，請提供：
1. 錯誤信息
2. 執行的命令
3. 相關文件內容

