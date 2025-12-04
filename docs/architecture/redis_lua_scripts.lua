--[[
    High-Concurrency Red Packet Claim Script
    
    This Lua script runs atomically in Redis to:
    1. Check if user already claimed
    2. Check if packet has remaining
    3. Calculate claim amount
    4. Update counters atomically
    
    Prevents overselling even at 10k+ QPS
--]]

-- KEYS:
-- KEYS[1] = packet:{packet_id}:remaining_count
-- KEYS[2] = packet:{packet_id}:remaining_amount
-- KEYS[3] = packet:{packet_id}:claimed_users (SET)
-- KEYS[4] = packet:{packet_id}:claims (LIST) - stores claim results for async processing

-- ARGV:
-- ARGV[1] = user_id
-- ARGV[2] = packet_type (random, equal)
-- ARGV[3] = min_amount (for random distribution)
-- ARGV[4] = timestamp

local remaining_count_key = KEYS[1]
local remaining_amount_key = KEYS[2]
local claimed_users_key = KEYS[3]
local claims_queue_key = KEYS[4]

local user_id = ARGV[1]
local packet_type = ARGV[2]
local min_amount = tonumber(ARGV[3]) or 0.01
local timestamp = ARGV[4]

-- Check if user already claimed
local already_claimed = redis.call('SISMEMBER', claimed_users_key, user_id)
if already_claimed == 1 then
    return cjson.encode({
        success = false,
        error = 'ALREADY_CLAIMED',
        message = 'User has already claimed this packet'
    })
end

-- Get remaining count and amount
local remaining_count = tonumber(redis.call('GET', remaining_count_key) or '0')
local remaining_amount = tonumber(redis.call('GET', remaining_amount_key) or '0')

-- Check if packet is exhausted
if remaining_count <= 0 or remaining_amount <= 0 then
    return cjson.encode({
        success = false,
        error = 'PACKET_EXHAUSTED',
        message = 'Red packet has been fully claimed'
    })
end

-- Calculate claim amount
local claim_amount = 0

if packet_type == 'equal' then
    -- Equal distribution
    claim_amount = remaining_amount / remaining_count
elseif packet_type == 'random' then
    -- Random distribution (二倍均值算法)
    if remaining_count == 1 then
        -- Last claim gets everything
        claim_amount = remaining_amount
    else
        -- Random between min_amount and 2 * (remaining / count)
        local max_amount = (remaining_amount / remaining_count) * 2
        -- Use simple random (Redis doesn't have good random, use timestamp-based)
        local seed = tonumber(timestamp) + tonumber(user_id)
        math.randomseed(seed)
        claim_amount = min_amount + (max_amount - min_amount) * math.random()
        
        -- Ensure minimum for remaining users
        local after_claim = remaining_amount - claim_amount
        local after_count = remaining_count - 1
        if after_count > 0 and after_claim < (min_amount * after_count) then
            claim_amount = remaining_amount - (min_amount * after_count)
        end
    end
end

-- Round to 8 decimal places
claim_amount = math.floor(claim_amount * 100000000) / 100000000

-- Ensure claim amount is valid
if claim_amount <= 0 then
    claim_amount = min_amount
end
if claim_amount > remaining_amount then
    claim_amount = remaining_amount
end

-- Atomic update
redis.call('DECR', remaining_count_key)
redis.call('INCRBYFLOAT', remaining_amount_key, -claim_amount)
redis.call('SADD', claimed_users_key, user_id)

-- Queue the claim for async processing to PostgreSQL
local claim_data = cjson.encode({
    user_id = user_id,
    amount = claim_amount,
    timestamp = timestamp,
    remaining_count = remaining_count - 1,
    remaining_amount = remaining_amount - claim_amount
})
redis.call('RPUSH', claims_queue_key, claim_data)

-- Set expiry on all keys (24 hours)
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


--[[
    Initialize Red Packet in Redis
    Called when a new red packet is created
--]]

-- INIT_PACKET Script
-- KEYS:
-- KEYS[1] = packet:{packet_id}:remaining_count
-- KEYS[2] = packet:{packet_id}:remaining_amount
-- KEYS[3] = packet:{packet_id}:claimed_users

-- ARGV:
-- ARGV[1] = total_count
-- ARGV[2] = total_amount
-- ARGV[3] = expire_seconds

--[[
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
    message = 'Packet initialized'
})
--]]


--[[
    Check Luckiest Winner
    Run after packet is fully claimed
--]]

-- LUCKIEST_CHECK Script
-- KEYS[1] = packet:{packet_id}:claims (LIST)

--[[
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
