# 🔍 Telegram MiniApp 调试方法

由于Telegram WebView无法直接打开开发者工具，这里提供多种调试方法：

## 方法1: 使用调试面板（推荐）

### 启用方式：
在URL后添加 `#debug=1`

**示例**：
- `https://mini.usdt2026.cc#debug=1`
- `https://mini.usdt2026.cc/tasks#debug=1`
- `https://mini.usdt2026.cc/lucky-wheel#debug=1`

### 功能：
- ✅ 实时显示控制台日志
- ✅ 显示网络请求（URL、状态码、耗时）
- ✅ 显示localStorage内容
- ✅ 显示Telegram WebApp信息（版本、平台、initData等）

### 使用方法：
1. 在Telegram中打开MiniApp
2. 在URL后添加 `#debug=1`
3. 页面底部会出现绿色调试面板
4. 点击面板标题可以展开/收起
5. 切换不同标签查看日志、网络、存储等信息

## 方法2: 使用调试页面（最详细）

### 访问方式：
直接访问 `/debug` 路由

**示例**：
- `https://mini.usdt2026.cc/debug`
- 或者在Telegram Bot中发送链接：`https://mini.usdt2026.cc/debug`

### 功能：
- ✅ 完整的Telegram环境信息
- ✅ 用户信息（ID、用户名等）
- ✅ InitData信息（可复制）
- ✅ API测试功能（可直接测试接口）
- ✅ 完整的控制台日志捕获
- ✅ 环境信息（User Agent、URL等）

### 使用方法：
1. 在Telegram中打开MiniApp
2. 手动修改URL为 `https://mini.usdt2026.cc/debug`
3. 或通过Bot发送调试链接
4. 查看所有调试信息
5. 点击"测试API"按钮测试接口
6. 点击"复制InitData"复制认证信息

## 方法3: 查看服务器日志

### 查看API日志：
```bash
# 实时查看API日志
sudo journalctl -u luckyred-api -f

# 查看最近100条日志
sudo journalctl -u luckyred-api -n 100

# 查看包含"task"的日志
sudo journalctl -u luckyred-api | grep -i task

# 查看错误日志
sudo journalctl -u luckyred-api | grep -i error
```

### 查看Nginx日志：
```bash
# 查看访问日志
sudo tail -f /var/log/nginx/access.log

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 查看特定域名的日志
sudo tail -f /var/log/nginx/access.log | grep mini.usdt2026.cc
```

## 方法4: 在代码中添加日志

### 前端日志：
前端已经添加了详细的日志，包括：
- `[Telegram] WebApp initialized` - Telegram初始化信息
- `[API Request]` - API请求信息（开发环境）
- `[API Error]` - API错误信息

### 查看方式：
1. 使用调试面板（方法1）
2. 使用调试页面（方法2）
3. 在浏览器中打开（如果可能）

## 方法5: 使用URL参数

### 测试不同场景：
- `?test=1` - 测试模式
- `?debug=1` - 调试模式（等同于#debug=1）
- `?tg_id=123456` - 测试用户ID（本地开发）

## 方法6: 在浏览器中测试（仅用于开发）

### 注意：
浏览器中无法获取Telegram `initData`，API会返回401，这是正常的。

### 使用方法：
1. 在浏览器中打开 `https://mini.usdt2026.cc`
2. 打开开发者工具（F12）
3. 查看控制台和网络请求
4. 注意：API会返回401，因为缺少Telegram认证

## 📋 调试检查清单

### 1. 检查Telegram环境
- [ ] 是否在Telegram中打开（不是浏览器）
- [ ] 是否显示 `[Telegram] WebApp initialized`
- [ ] `hasInitData` 是否为 `true`
- [ ] `initDataLength` 是否大于0

### 2. 检查API请求
- [ ] 请求URL是否正确（`/api/v1/tasks/status`）
- [ ] 是否包含 `X-Telegram-Init-Data` header
- [ ] 响应状态码（200/401/404）
- [ ] 响应内容

### 3. 检查用户认证
- [ ] 用户ID是否存在
- [ ] 用户是否在数据库中注册
- [ ] InitData是否正确解析

### 4. 检查服务器
- [ ] API服务是否运行（`sudo systemctl status luckyred-api`）
- [ ] Nginx是否正常（`sudo nginx -t`）
- [ ] 数据库连接是否正常

## 🚀 快速调试步骤

1. **在Telegram中打开MiniApp**
   ```
   https://mini.usdt2026.cc#debug=1
   ```

2. **查看调试面板**
   - 检查"Info"标签中的Telegram信息
   - 检查"Network"标签中的API请求
   - 检查"Console"标签中的错误日志

3. **如果问题仍然存在，访问调试页面**
   ```
   https://mini.usdt2026.cc/debug
   ```
   - 复制InitData
   - 测试API接口
   - 查看完整日志

4. **查看服务器日志**
   ```bash
   sudo journalctl -u luckyred-api -f
   ```

## 💡 常见问题

### Q: 调试面板不显示？
A: 确保URL中包含 `#debug=1`，并且页面已完全加载

### Q: InitData为空？
A: 确保在Telegram中打开，不是在浏览器中

### Q: API返回401？
A: 检查InitData是否正确传递，查看Network标签中的请求头

### Q: 如何复制日志？
A: 在调试页面中点击"复制所有日志"按钮

