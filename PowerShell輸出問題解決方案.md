# PowerShell 輸出被抑制問題 - 解決方案

## 問題描述

在 Cursor 中使用 `run_terminal_cmd` 工具執行 PowerShell 命令時，輸出被抑制，無法看到命令執行結果。

## 根本原因

這是 Cursor 工具調用的系統限制，可能是由於：
1. **輸出流重定向問題**：工具調用可能沒有正確處理 PowerShell 的輸出流
2. **編碼問題**：UTF-8 編碼可能沒有正確設置
3. **緩衝問題**：輸出可能被緩衝，沒有立即顯示
4. **工具限制**：Cursor 的終端工具可能有輸出限制

## 解決方案

### 方案 1: 使用批處理文件（.bat）- 推薦 ⭐

批處理文件通常能更好地顯示輸出：

**使用步驟：**
1. 雙擊運行 `顯示輸出.bat`
2. 所有輸出會同時顯示在屏幕上並保存到文件
3. 查看 `命令輸出_YYYYMMDD_HHMMSS.txt` 文件獲取完整輸出

**優點：**
- 輸出直接顯示在終端
- 同時保存到文件，便於查看
- 不依賴 PowerShell 配置

### 方案 2: 使用 Python 腳本執行命令

創建 Python 腳本，使用 `subprocess` 執行命令並捕獲輸出：

```python
import subprocess
import sys

process = subprocess.run(
    'python --version',
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8'
)
print(process.stdout)
```

**使用步驟：**
1. 運行 `python 執行並顯示輸出.py`
2. 輸出會顯示在終端

### 方案 3: 將輸出寫入文件

將命令輸出重定向到文件，然後讀取文件：

```batch
python test_config.py > output.txt 2>&1
type output.txt
```

### 方案 4: 使用 PowerShell 腳本並設置編碼

在 PowerShell 腳本開頭設置編碼：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
```

然後執行：
```powershell
powershell -ExecutionPolicy Bypass -File "腳本.ps1"
```

### 方案 5: 直接在終端中運行

**最簡單的方法**：直接在 Cursor 的終端中運行命令，而不是通過工具調用：

1. 打開 Cursor 的終端（Terminal）
2. 直接執行命令
3. 輸出會正常顯示

## 推薦工作流程

### 對於配置測試：

1. **雙擊運行** `顯示輸出.bat`
   - 會測試配置讀取
   - 輸出會顯示並保存到文件

2. **或手動執行**：
   ```batch
   cd C:\hbgm001\api
   python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')"
   ```

### 對於服務器啟動：

1. **使用批處理文件**：
   ```batch
   完整測試和啟動.bat
   ```

2. **或手動執行**：
   ```batch
   cd C:\hbgm001\api
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

## 已創建的腳本

1. **`顯示輸出.bat`** - 測試輸出並保存到文件
2. **`執行並顯示輸出.py`** - Python 版本的輸出測試工具
3. **`解決輸出問題.py`** - 將輸出保存到文件的工具
4. **`快速測試.bat`** - 快速測試配置讀取
5. **`完整測試和啟動.bat`** - 完整測試並啟動服務器

## 注意事項

1. **批處理文件編碼**：確保批處理文件使用 UTF-8 編碼保存
2. **Python 腳本編碼**：確保 Python 腳本使用 UTF-8 編碼
3. **終端編碼**：在批處理文件中使用 `chcp 65001` 設置 UTF-8 編碼
4. **文件路徑**：使用絕對路徑或相對路徑時要小心

## 如果仍然無法看到輸出

1. **檢查終端設置**：
   - 確保終端支持 UTF-8
   - 檢查終端的字體設置

2. **使用文件輸出**：
   - 將所有輸出重定向到文件
   - 然後讀取文件查看結果

3. **直接在系統終端運行**：
   - 打開 Windows 命令提示符或 PowerShell
   - 直接執行命令
   - 這樣可以確保看到所有輸出

## 總結

**最佳實踐**：
- 使用批處理文件（.bat）進行測試和執行
- 將重要輸出保存到文件
- 直接在 Cursor 終端中運行命令（而不是通過工具調用）

這樣可以確保您能看到所有輸出，並解決 PowerShell 輸出被抑制的問題。
