# 上傳文件到 GitHub 倉庫指南

## 方法 1：使用 Git 命令行（推薦）

### 步驟：

1. **打開 PowerShell 或 CMD，進入項目目錄**
   ```powershell
   cd C:\hbgm001
   ```

2. **檢查文件狀態**
   ```powershell
   git status
   ```

3. **添加要上傳的文件**
   ```powershell
   git add frontend/src/pages/SendRedPacket.tsx
   git add frontend/src/providers/I18nProvider.tsx
   ```
   或者添加所有修改的文件：
   ```powershell
   git add .
   ```

4. **提交更改**
   ```powershell
   git commit -m "fix: 修復 TypeScript 編譯錯誤 - bomb_number 類型和 view_rules 重複問題"
   ```

5. **推送到 GitHub**
   ```powershell
   git push origin master
   ```
   或者如果主分支是 `main`：
   ```powershell
   git push origin main
   ```

### 如果遇到認證問題：

**使用 Personal Access Token (推薦)：**
1. 訪問：https://github.com/settings/tokens
2. 生成新的 token（選擇 `repo` 權限）
3. 推送時使用 token 作為密碼

**或者配置 SSH：**
```powershell
# 檢查是否已有 SSH key
ls ~/.ssh

# 如果沒有，生成新的 SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 將公鑰添加到 GitHub
# 複製 ~/.ssh/id_ed25519.pub 的內容
# 到 GitHub Settings > SSH and GPG keys > New SSH key
```

---

## 方法 2：使用 GitHub Desktop（圖形界面，簡單）

### 安裝：
1. 下載：https://desktop.github.com/
2. 安裝並登錄 GitHub 賬號

### 步驟：
1. **打開 GitHub Desktop**
2. **選擇倉庫** `C:\hbgm001`
3. **在左側看到修改的文件**
4. **勾選要提交的文件**：
   - `frontend/src/pages/SendRedPacket.tsx`
   - `frontend/src/providers/I18nProvider.tsx`
5. **填寫提交信息**：
   ```
   fix: 修復 TypeScript 編譯錯誤
   ```
6. **點擊 "Commit to master"**
7. **點擊 "Push origin"** 推送到 GitHub

---

## 方法 3：直接在 GitHub 網頁上傳（最簡單）

### 步驟：
1. **訪問你的 GitHub 倉庫**
2. **點擊要上傳文件所在的文件夾**（例如：`frontend/src/pages/`）
3. **點擊 "Add file" > "Upload files"**
4. **拖拽或選擇文件**：
   - `SendRedPacket.tsx`
   - `I18nProvider.tsx`
5. **填寫提交信息**：
   ```
   fix: 修復 TypeScript 編譯錯誤
   ```
6. **點擊 "Commit changes"**

---

## 快速命令（複製粘貼）

```powershell
# 進入項目目錄
cd C:\hbgm001

# 添加文件
git add frontend/src/pages/SendRedPacket.tsx frontend/src/providers/I18nProvider.tsx

# 提交
git commit -m "fix: 修復 TypeScript 編譯錯誤"

# 推送
git push origin master
```

---

## 檢查是否成功

推送成功後，訪問你的 GitHub 倉庫，應該能看到：
- 最新的提交記錄
- 文件已更新

## 常見問題

### 1. 提示需要認證
解決：使用 Personal Access Token 或配置 SSH

### 2. 提示 "remote: Permission denied"
解決：檢查是否有倉庫的寫入權限

### 3. 提示 "branch is ahead"
解決：執行 `git push origin master` 推送更改

