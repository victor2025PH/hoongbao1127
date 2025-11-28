# 安裝 sshpass 工具（用於自動輸入密碼）

## Windows 安裝方法

### 方法 1: 使用 WSL（推薦）

如果你有 WSL（Windows Subsystem for Linux）：

```bash
# 在 WSL 中執行
sudo apt-get update
sudo apt-get install sshpass
```

然後在 WSL 中使用腳本。

### 方法 2: 使用 Git Bash

1. 下載 sshpass for Windows: https://github.com/keimpx/sshpass-windows/releases
2. 解壓到某個目錄（如 `C:\tools\sshpass`）
3. 將該目錄添加到系統 PATH

### 方法 3: 使用 Chocolatey

```powershell
choco install sshpass
```

### 方法 4: 手動下載

1. 訪問: https://github.com/keimpx/sshpass-windows
2. 下載最新版本
3. 解壓並添加到 PATH

## 驗證安裝

```bash
sshpass -V
```

如果顯示版本號，說明安裝成功。

## 使用

腳本 `auto-deploy-with-sshpass.bat` 會自動使用 sshpass 輸入密碼。

