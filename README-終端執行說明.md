# 終端執行說明

## 重要提示

由於 Cursor 工具調用的限制，**請直接在 Cursor 的終端中運行以下命令**，而不是通過 AI 工具調用。

## 快速開始

### 方法 1: 雙擊運行（最簡單）⭐

1. **雙擊 `一鍵測試和啟動.bat`**
   - 會自動檢查依賴
   - 測試配置讀取
   - 啟動服務器

2. **或雙擊 `快速檢查.bat`**
   - 只測試配置讀取
   - 不啟動服務器

### 方法 2: 在 Cursor 終端中運行

1. **打開 Cursor 終端**（Terminal 面板，快捷鍵：Ctrl+`）
2. **執行以下命令**：

```batch
cd C:\hbgm001
一鍵測試和啟動.bat
```

## 詳細步驟

### 步驟 1: 檢查 .env 文件

在終端中執行：
```batch
cd C:\hbgm001
type .env
```

確認文件包含：
```
BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs
BOT_USERNAME=sucai2025_bot
```

### 步驟 2: 測試配置讀取

在終端中執行：
```batch
cd C:\hbgm001\api
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')"
```

**預期輸出**：
```
BOT_TOKEN 長度: 46
BOT_TOKEN: 8271541107:AAH1YPO82cRzcwcdY9GE
```

如果顯示 `BOT_TOKEN: 空`，說明配置讀取失敗。

### 步驟 3: 安裝依賴（如果需要）

在終端中執行：
```batch
cd C:\hbgm001\api
python -m pip install python-dotenv pydantic-settings uvicorn
```

### 步驟 4: 啟動服務器

在終端中執行：
```batch
cd C:\hbgm001\api
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**預期輸出**：
```
INFO:     Will watch for changes in these directories: ['C:\\hbgm001\\api']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 可用的腳本

### 1. `一鍵測試和啟動.bat`
- ✅ 自動檢查 .env 文件
- ✅ 自動檢查並安裝依賴
- ✅ 測試配置讀取
- ✅ 啟動服務器

### 2. `快速檢查.bat`
- ✅ 只測試配置讀取
- ✅ 不啟動服務器

### 3. `完整測試和啟動.bat`
- ✅ 完整測試流程
- ✅ 啟動服務器

## 常見問題

### Q: 為什麼看不到輸出？

A: 這是 Cursor 工具調用的限制。請直接在 Cursor 終端中運行命令，或雙擊運行 `.bat` 文件。

### Q: BOT_TOKEN 讀取為空怎麼辦？

A: 檢查以下幾點：
1. `.env` 文件是否在 `C:\hbgm001\.env`
2. 文件格式是否正確（`BOT_TOKEN=...`，沒有引號）
3. 文件編碼是否為 UTF-8
4. `python-dotenv` 是否已安裝

### Q: 服務器啟動失敗怎麼辦？

A: 檢查：
1. 端口 8000 是否被占用
2. 所有依賴是否已安裝
3. 查看錯誤信息

### Q: 如何停止服務器？

A: 在終端中按 `Ctrl+C`

## 驗證服務器運行

服務器啟動後，在瀏覽器中訪問：
- **API 文檔**: http://127.0.0.1:8000/docs
- **API 根路徑**: http://127.0.0.1:8000

## 下一步

1. ✅ 確認服務器已啟動
2. ✅ 訪問 http://127.0.0.1:8000/docs 查看 API 文檔
3. ✅ 測試 API 端點


