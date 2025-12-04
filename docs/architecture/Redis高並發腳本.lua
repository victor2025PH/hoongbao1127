--[[
    高並發紅包領取腳本
    
    文件路徑：c:\hbgm001\docs\architecture\Redis高並發腳本.lua
    
    此 Lua 腳本在 Redis 中原子執行，用於：
    1. 檢查用戶是否已領取
    2. 檢查紅包是否還有剩餘
    3. 計算領取金額
    4. 原子更新計數器
    
    即使在 10k+ QPS 下也能防止超發
--]]

-- ============================================================
-- 腳本 1：領取紅包（核心腳本）
-- ============================================================

-- KEYS:
-- KEYS[1] = packet:{packet_id}:remaining_count  -- 剩餘份數
-- KEYS[2] = packet:{packet_id}:remaining_amount -- 剩餘金額
-- KEYS[3] = packet:{packet_id}:claimed_users    -- 已領取用戶集合 (SET)
-- KEYS[4] = packet:{packet_id}:claims           -- 領取記錄隊列 (LIST)

-- ARGV:
-- ARGV[1] = user_id       -- 用戶ID
-- ARGV[2] = packet_type   -- 紅包類型 (random, equal)
-- ARGV[3] = min_amount    -- 最小金額（用於隨機分配）
-- ARGV[4] = timestamp     -- 時間戳

local remaining_count_key = KEYS[1]
local remaining_amount_key = KEYS[2]
local claimed_users_key = KEYS[3]
local claims_queue_key = KEYS[4]

local user_id = ARGV[1]
local packet_type = ARGV[2]
local min_amount = tonumber(ARGV[3]) or 0.01
local timestamp = ARGV[4]

-- 檢查用戶是否已領取
local already_claimed = redis.call('SISMEMBER', claimed_users_key, user_id)
if already_claimed == 1 then
    return cjson.encode({
        success = false,
        error = 'ALREADY_CLAIMED',
        message = '您已經領取過此紅包'
    })
end

-- 獲取剩餘份數和金額
local remaining_count = tonumber(redis.call('GET', remaining_count_key) or '0')
local remaining_amount = tonumber(redis.call('GET', remaining_amount_key) or '0')

-- 檢查紅包是否已領完
if remaining_count <= 0 or remaining_amount <= 0 then
    return cjson.encode({
        success = false,
        error = 'PACKET_EXHAUSTED',
        message = '紅包已被搶完'
    })
end

-- 計算領取金額
local claim_amount = 0

if packet_type == 'equal' then
    -- 平分模式：每人相同金額
    claim_amount = remaining_amount / remaining_count
    
elseif packet_type == 'random' then
    -- 隨機模式：二倍均值算法
    if remaining_count == 1 then
        -- 最後一個人拿剩餘全部
        claim_amount = remaining_amount
    else
        -- 隨機金額介於 min_amount 和 2 * (剩餘/人數) 之間
        local max_amount = (remaining_amount / remaining_count) * 2
        
        -- 使用時間戳和用戶ID作為隨機種子
        local seed = tonumber(timestamp) + tonumber(user_id)
        math.randomseed(seed)
        claim_amount = min_amount + (max_amount - min_amount) * math.random()
        
        -- 確保剩餘用戶有最低金額可領
        local after_claim = remaining_amount - claim_amount
        local after_count = remaining_count - 1
        if after_count > 0 and after_claim < (min_amount * after_count) then
            claim_amount = remaining_amount - (min_amount * after_count)
        end
    end
end

-- 四捨五入到 8 位小數
claim_amount = math.floor(claim_amount * 100000000) / 100000000

-- 確保領取金額有效
if claim_amount <= 0 then
    claim_amount = min_amount
end
if claim_amount > remaining_amount then
    claim_amount = remaining_amount
end

-- 原子更新
redis.call('DECR', remaining_count_key)
redis.call('INCRBYFLOAT', remaining_amount_key, -claim_amount)
redis.call('SADD', claimed_users_key, user_id)

-- 將領取記錄加入隊列，供異步處理同步到 PostgreSQL
local claim_data = cjson.encode({
    user_id = user_id,
    amount = claim_amount,
    timestamp = timestamp,
    remaining_count = remaining_count - 1,
    remaining_amount = remaining_amount - claim_amount
})
redis.call('RPUSH', claims_queue_key, claim_data)

-- 設定所有鍵的過期時間（24小時）
redis.call('EXPIRE', remaining_count_key, 86400)
redis.call('EXPIRE', remaining_amount_key, 86400)
redis.call('EXPIRE', claimed_users_key, 86400)
redis.call('EXPIRE', claims_queue_key, 86400)

return cjson.encode({
    success = true,
    data = {
        amount = claim_amount,
        remaining_count = remaining_count - 1,
        remaining_amount = remaining_amount - claim_amount,
        is_last = (remaining_count - 1) == 0
    }
})


-- ============================================================
-- 腳本 2：初始化紅包
-- 當新紅包創建時調用
-- ============================================================

--[[
-- KEYS:
-- KEYS[1] = packet:{packet_id}:remaining_count
-- KEYS[2] = packet:{packet_id}:remaining_amount
-- KEYS[3] = packet:{packet_id}:claimed_users

-- ARGV:
-- ARGV[1] = total_count      -- 總份數
-- ARGV[2] = total_amount     -- 總金額
-- ARGV[3] = expire_seconds   -- 過期秒數

local remaining_count_key = KEYS[1]
local remaining_amount_key = KEYS[2]
local claimed_users_key = KEYS[3]

local total_count = ARGV[1]
local total_amount = ARGV[2]
local expire_seconds = tonumber(ARGV[3]) or 86400

redis.call('SET', remaining_count_key, total_count, 'EX', expire_seconds)
redis.call('SET', remaining_amount_key, total_amount, 'EX', expire_seconds)
redis.call('DEL', claimed_users_key)
redis.call('EXPIRE', claimed_users_key, expire_seconds)

return cjson.encode({
    success = true,
    message = '紅包初始化成功'
})
--]]


-- ============================================================
-- 腳本 3：查詢手氣最佳
-- 紅包領完後執行
-- ============================================================

--[[
-- KEYS:
-- KEYS[1] = packet:{packet_id}:claims (LIST)

local claims_key = KEYS[1]

local claims = redis.call('LRANGE', claims_key, 0, -1)
local max_amount = 0
local luckiest_user = nil

for i, claim_json in ipairs(claims) do
    local claim = cjson.decode(claim_json)
    if claim.amount > max_amount then
        max_amount = claim.amount
        luckiest_user = claim.user_id
    end
end

return cjson.encode({
    success = true,
    luckiest_user_id = luckiest_user,
    amount = max_amount
})
--]]


-- ============================================================
-- 腳本 4：檢查紅包狀態
-- ============================================================

--[[
-- KEYS:
-- KEYS[1] = packet:{packet_id}:remaining_count
-- KEYS[2] = packet:{packet_id}:remaining_amount
-- KEYS[3] = packet:{packet_id}:claimed_users

local remaining_count_key = KEYS[1]
local remaining_amount_key = KEYS[2]
local claimed_users_key = KEYS[3]

local remaining_count = tonumber(redis.call('GET', remaining_count_key) or '0')
local remaining_amount = tonumber(redis.call('GET', remaining_amount_key) or '0')
local claimed_count = redis.call('SCARD', claimed_users_key)

return cjson.encode({
    success = true,
    data = {
        remaining_count = remaining_count,
        remaining_amount = remaining_amount,
        claimed_count = claimed_count
    }
})
--]]


-- ============================================================
-- 腳本 5：撤銷領取（管理員使用）
-- ============================================================

--[[
-- KEYS:
-- KEYS[1] = packet:{packet_id}:remaining_count
-- KEYS[2] = packet:{packet_id}:remaining_amount
-- KEYS[3] = packet:{packet_id}:claimed_users

-- ARGV:
-- ARGV[1] = user_id           -- 要撤銷的用戶ID
-- ARGV[2] = refund_amount     -- 退回金額

local remaining_count_key = KEYS[1]
local remaining_amount_key = KEYS[2]
local claimed_users_key = KEYS[3]

local user_id = ARGV[1]
local refund_amount = tonumber(ARGV[2])

-- 檢查用戶是否真的領取過
local was_claimed = redis.call('SISMEMBER', claimed_users_key, user_id)
if was_claimed == 0 then
    return cjson.encode({
        success = false,
        error = 'NOT_CLAIMED',
        message = '該用戶未領取此紅包'
    })
end

-- 撤銷：移除用戶、恢復計數
redis.call('SREM', claimed_users_key, user_id)
redis.call('INCR', remaining_count_key)
redis.call('INCRBYFLOAT', remaining_amount_key, refund_amount)

return cjson.encode({
    success = true,
    message = '撤銷成功'
})
--]]
