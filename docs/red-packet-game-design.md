# 红包游戏规则与数据库设计文档

## 一、游戏玩法规则

### 1.1 最佳手气（Best MVP）玩法

#### 规则定义
- **玩法类型**：随机金额分配，但会标记"手气最佳"获得者
- **分配机制**：使用二倍均值算法，确保随机性和公平性
- **最佳手气判定**：红包被全部领取后，获得金额最大的用户被标记为"最佳手气"
- **奖励机制**：最佳手气获得者可在红包详情中显示特殊标识

#### 算法流程
1. 发送红包时，总金额按随机算法分配给多个红包
2. 每个用户领取时，系统随机分配一个金额（保证最后一人能拿到剩余）
3. 所有红包领取完成后，系统自动计算最大金额获得者
4. 将最大金额获得者的 `is_luckiest` 字段标记为 `true`

#### 金额分配算法
```python
# 二倍均值算法
def calculate_random_amount(remaining_amount, remaining_count):
    if remaining_count == 1:
        return remaining_amount
    
    # 最大金额不超过剩余均值的2倍
    max_amount = remaining_amount * 0.9 / remaining_count * 2
    min_amount = 0.01
    
    amount = random.uniform(min_amount, max_amount)
    # 确保剩余金额足够分配给其他人
    amount = min(amount, remaining_amount - 0.01 * (remaining_count - 1))
    
    return round(amount, 8)
```

### 1.2 红包炸弹（Red Packet Bomb）玩法

#### 规则定义
- **玩法类型**：固定金额分配，但包含"炸弹"机制
- **炸弹设置**：发送者选择0-9范围内的一个数字作为炸弹数字
- **触发条件**：用户领取红包时，如果领取金额的小数点后最后一位数字与炸弹数字相同，则触发炸弹
- **炸弹后果**：
  - 用户失去本次领取的金额（金额退回红包池）
  - 用户失去继续领取该红包的资格
  - 红包继续开放，其他用户仍可领取
  - 炸弹金额重新分配给剩余红包

#### 游戏流程
1. **发送阶段**：
   - 发送者选择"红包炸弹"类型
   - 设置炸弹数字（0-9）
   - 设置总金额和红包数量
   - 系统扣除发送者余额

2. **领取阶段**：
   - 用户点击领取红包
   - 系统计算固定金额：`amount = total_amount / total_count`
   - 检查金额尾数：`last_digit = int(str(amount).split('.')[-1][-1])`
   - 如果 `last_digit == bomb_number`：
     - 标记为炸弹触发
     - 金额退回红包池
     - 用户失去继续领取资格
   - 否则：
     - 正常发放金额
     - 更新领取记录

3. **炸弹金额处理**：
   - 炸弹触发的金额累加到 `bomb_amount` 字段
   - 红包领取完成后，炸弹金额平均分配给所有成功领取的用户
   - 或作为额外奖励给最后一个成功领取的用户

#### 炸弹判定示例
```
炸弹数字：5
领取金额：10.25 USDT
尾数检查：5 (最后一位)
结果：触发炸弹，金额退回
```

## 二、数据库结构设计

### 2.1 扩展 RedPacket 表

```python
class RedPacketType(str, enum.Enum):
    """红包类型"""
    RANDOM = "random"          # 最佳手气（随机金额）
    FIXED = "fixed"            # 红包炸弹（固定金额）
    EQUAL = "equal"            # 平分（保留）
    EXCLUSIVE = "exclusive"    # 专属（保留）

class RedPacket(Base):
    """红包表"""
    __tablename__ = "red_packets"
    
    # 现有字段...
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"))
    chat_id = Column(BigInteger, nullable=True)
    currency = Column(Enum(CurrencyType))
    packet_type = Column(Enum(RedPacketType))
    total_amount = Column(Numeric(20, 8))
    total_count = Column(Integer)
    claimed_amount = Column(Numeric(20, 8), default=0)
    claimed_count = Column(Integer, default=0)
    message = Column(String(256))
    status = Column(Enum(RedPacketStatus))
    expires_at = Column(DateTime)
    created_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 新增字段 - 红包炸弹
    bomb_number = Column(Integer, nullable=True)  # 炸弹数字 0-9
    bomb_amount = Column(Numeric(20, 8), default=0)  # 炸弹触发的总金额
    bomb_trigger_count = Column(Integer, default=0)  # 炸弹触发次数
    
    # 新增字段 - 最佳手气
    luckiest_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 最佳手气用户ID
    luckiest_amount = Column(Numeric(20, 8), nullable=True)  # 最佳手气金额
```

### 2.2 扩展 RedPacketClaim 表

```python
class RedPacketClaim(Base):
    """红包领取记录"""
    __tablename__ = "red_packet_claims"
    
    # 现有字段...
    id = Column(Integer, primary_key=True)
    red_packet_id = Column(Integer, ForeignKey("red_packets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Numeric(20, 8))
    is_luckiest = Column(Boolean, default=False)
    claimed_at = Column(DateTime)
    
    # 新增字段 - 红包炸弹
    is_bomb_triggered = Column(Boolean, default=False)  # 是否触发炸弹
    original_amount = Column(Numeric(20, 8), nullable=True)  # 原始金额（炸弹触发时记录）
```

### 2.3 数据库迁移脚本

```python
# migrations/add_bomb_fields.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 添加红包炸弹字段
    op.add_column('red_packets', 
        sa.Column('bomb_number', sa.Integer(), nullable=True))
    op.add_column('red_packets', 
        sa.Column('bomb_amount', sa.Numeric(20, 8), default=0))
    op.add_column('red_packets', 
        sa.Column('bomb_trigger_count', sa.Integer(), default=0))
    
    # 添加最佳手气字段
    op.add_column('red_packets', 
        sa.Column('luckiest_user_id', sa.Integer(), nullable=True))
    op.add_column('red_packets', 
        sa.Column('luckiest_amount', sa.Numeric(20, 8), nullable=True))
    op.create_foreign_key('fk_red_packets_luckiest_user', 
        'red_packets', 'users', ['luckiest_user_id'], ['id'])
    
    # 添加领取记录炸弹字段
    op.add_column('red_packet_claims', 
        sa.Column('is_bomb_triggered', sa.Boolean(), default=False))
    op.add_column('red_packet_claims', 
        sa.Column('original_amount', sa.Numeric(20, 8), nullable=True))

def downgrade():
    op.drop_column('red_packet_claims', 'original_amount')
    op.drop_column('red_packet_claims', 'is_bomb_triggered')
    op.drop_constraint('fk_red_packets_luckiest_user', 'red_packets')
    op.drop_column('red_packets', 'luckiest_amount')
    op.drop_column('red_packets', 'luckiest_user_id')
    op.drop_column('red_packets', 'bomb_trigger_count')
    op.drop_column('red_packets', 'bomb_amount')
    op.drop_column('red_packets', 'bomb_number')
```

## 三、API 接口设计

### 3.1 创建红包接口（扩展）

```python
class CreateRedPacketRequest(BaseModel):
    chat_id: Optional[int] = None
    chat_title: Optional[str] = None
    currency: CurrencyType
    packet_type: RedPacketType
    total_amount: float
    total_count: int
    message: str = "恭喜發財！🧧"
    bomb_number: Optional[int] = None  # 红包炸弹：0-9，仅当 packet_type=FIXED 时有效
    
    @validator('bomb_number')
    def validate_bomb_number(cls, v, values):
        if values.get('packet_type') == RedPacketType.FIXED and v is None:
            raise ValueError('Bomb number is required for fixed packet type')
        if v is not None and (v < 0 or v > 9):
            raise ValueError('Bomb number must be between 0 and 9')
        return v

@router.post("/create", response_model=RedPacketResponse)
async def create_red_packet(
    request: CreateRedPacketRequest,
    sender_tg_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """创建红包"""
    
    # 1. 验证发送者
    sender = await get_user_by_tg_id(db, sender_tg_id)
    if not sender:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. 余额验证
    balance_field = f"balance_{request.currency.value}"
    current_balance = getattr(sender, balance_field, 0) or Decimal(0)
    required_amount = Decimal(str(request.total_amount))
    
    if current_balance < required_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance. Required: {required_amount}, Available: {current_balance}"
        )
    
    # 3. 事务处理：扣除余额
    async with db.begin():
        # 扣除余额
        new_balance = current_balance - required_amount
        setattr(sender, balance_field, new_balance)
        
        # 创建交易记录
        transaction = Transaction(
            user_id=sender.id,
            type="send_red_packet",
            currency=request.currency,
            amount=-required_amount,
            balance_before=current_balance,
            balance_after=new_balance,
            ref_id=f"packet_{uuid.uuid4()}",
            note=f"发送红包: {request.total_count}份, {request.total_amount} {request.currency.value}"
        )
        db.add(transaction)
        
        # 创建红包
        packet = RedPacket(
            uuid=str(uuid.uuid4()),
            sender_id=sender.id,
            currency=request.currency,
            packet_type=request.packet_type,
            total_amount=required_amount,
            total_count=request.total_count,
            message=request.message,
            chat_id=request.chat_id,
            chat_title=request.chat_title,
            bomb_number=request.bomb_number if request.packet_type == RedPacketType.FIXED else None,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(packet)
        await db.flush()
        
        transaction.ref_id = f"packet_{packet.uuid}"
        await db.commit()
    
    return packet
```

### 3.2 领取红包接口（扩展）

```python
@router.post("/{packet_uuid}/claim", response_model=ClaimResult)
async def claim_red_packet(
    packet_uuid: str,
    claimer_tg_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """领取红包"""
    
    # 1. 查找红包
    packet = await get_red_packet_by_uuid(db, packet_uuid)
    if not packet:
        raise HTTPException(status_code=404, detail="Red packet not found")
    
    if packet.status != RedPacketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Red packet is not active")
    
    if packet.expires_at and packet.expires_at < datetime.utcnow():
        packet.status = RedPacketStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Red packet expired")
    
    # 2. 查找领取者
    claimer = await get_user_by_tg_id(db, claimer_tg_id)
    if not claimer:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 3. 检查是否已领取
    existing_claim = await check_existing_claim(db, packet.id, claimer.id)
    if existing_claim:
        if existing_claim.is_bomb_triggered:
            raise HTTPException(status_code=400, detail="You triggered the bomb and cannot claim again")
        raise HTTPException(status_code=400, detail="Already claimed")
    
    # 4. 计算领取金额
    remaining_amount = packet.total_amount - packet.claimed_amount
    remaining_count = packet.total_count - packet.claimed_count
    
    if remaining_count <= 0:
        packet.status = RedPacketStatus.COMPLETED
        await db.commit()
        raise HTTPException(status_code=400, detail="Red packet is empty")
    
    # 5. 根据红包类型计算金额
    is_bomb_triggered = False
    original_amount = None
    
    if packet.packet_type == RedPacketType.FIXED:
        # 红包炸弹：固定金额
        amount = remaining_amount / remaining_count
        amount = round(amount, 8)
        original_amount = amount
        
        # 检查炸弹
        if packet.bomb_number is not None:
            last_digit = int(str(amount).split('.')[-1][-1]) if '.' in str(amount) else 0
            if last_digit == packet.bomb_number:
                is_bomb_triggered = True
                # 金额退回红包池
                amount = Decimal(0)
    
    elif packet.packet_type == RedPacketType.RANDOM:
        # 最佳手气：随机金额
        if remaining_count == 1:
            amount = remaining_amount
        else:
            max_amount = remaining_amount * Decimal("0.9") / remaining_count * 2
            amount = Decimal(str(random.uniform(0.01, float(max_amount))))
            amount = min(amount, remaining_amount - Decimal("0.01") * (remaining_count - 1))
        amount = round(amount, 8)
    
    else:  # EQUAL
        amount = remaining_amount / remaining_count
        amount = round(amount, 8)
    
    # 6. 事务处理：创建领取记录
    async with db.begin():
        claim = RedPacketClaim(
            red_packet_id=packet.id,
            user_id=claimer.id,
            amount=amount,
            is_bomb_triggered=is_bomb_triggered,
            original_amount=original_amount if is_bomb_triggered else None,
        )
        db.add(claim)
        
        # 更新红包状态
        if is_bomb_triggered:
            # 炸弹触发：金额退回
            packet.bomb_amount += original_amount
            packet.bomb_trigger_count += 1
        else:
            # 正常领取：更新金额和数量
            packet.claimed_amount += amount
            packet.claimed_count += 1
            
            # 更新用户余额
            balance_field = f"balance_{packet.currency.value}"
            current_balance = getattr(claimer, balance_field, 0) or Decimal(0)
            new_balance = current_balance + amount
            setattr(claimer, balance_field, new_balance)
            
            # 创建交易记录
            transaction = Transaction(
                user_id=claimer.id,
                type="claim_red_packet",
                currency=packet.currency,
                amount=amount,
                balance_before=current_balance,
                balance_after=new_balance,
                ref_id=f"packet_{packet.uuid}",
                note=f"领取红包: {amount} {packet.currency.value}"
            )
            db.add(transaction)
        
        # 检查红包是否完成
        if packet.claimed_count >= packet.total_count:
            packet.status = RedPacketStatus.COMPLETED
            packet.completed_at = datetime.utcnow()
            
            # 处理炸弹金额分配
            if packet.packet_type == RedPacketType.FIXED and packet.bomb_amount > 0:
                await distribute_bomb_amount(db, packet)
            
            # 计算最佳手气
            if packet.packet_type == RedPacketType.RANDOM:
                await calculate_luckiest(db, packet)
        
        await db.commit()
    
    # 7. 返回结果
    message = "💣 触发炸弹！金额已退回红包池" if is_bomb_triggered else f"恭喜获得 {amount} {packet.currency.value.upper()}！"
    
    return ClaimResult(
        success=not is_bomb_triggered,
        amount=float(amount),
        is_luckiest=False,  # 将在红包完成后更新
        is_bomb_triggered=is_bomb_triggered,
        message=message
    )
```

### 3.3 辅助函数

```python
async def calculate_luckiest(db: AsyncSession, packet: RedPacket):
    """计算最佳手气"""
    result = await db.execute(
        select(RedPacketClaim)
        .where(RedPacketClaim.red_packet_id == packet.id)
        .where(RedPacketClaim.is_bomb_triggered == False)
        .order_by(RedPacketClaim.amount.desc())
        .limit(1)
    )
    luckiest_claim = result.scalar_one_or_none()
    
    if luckiest_claim:
        packet.luckiest_user_id = luckiest_claim.user_id
        packet.luckiest_amount = luckiest_claim.amount
        
        # 更新领取记录的 is_luckiest 标记
        luckiest_claim.is_luckiest = True
        await db.commit()

async def distribute_bomb_amount(db: AsyncSession, packet: RedPacket):
    """分配炸弹金额"""
    if packet.bomb_amount <= 0:
        return
    
    # 获取所有成功领取的用户（未触发炸弹）
    result = await db.execute(
        select(RedPacketClaim)
        .where(RedPacketClaim.red_packet_id == packet.id)
        .where(RedPacketClaim.is_bomb_triggered == False)
    )
    successful_claims = result.scalars().all()
    
    if not successful_claims:
        # 如果没有成功领取，退回给发送者
        sender = await db.get(User, packet.sender_id)
        balance_field = f"balance_{packet.currency.value}"
        current_balance = getattr(sender, balance_field, 0) or Decimal(0)
        setattr(sender, balance_field, current_balance + packet.bomb_amount)
        
        transaction = Transaction(
            user_id=sender.id,
            type="bomb_refund",
            currency=packet.currency,
            amount=packet.bomb_amount,
            balance_before=current_balance,
            balance_after=current_balance + packet.bomb_amount,
            ref_id=f"packet_{packet.uuid}",
            note="炸弹金额退回"
        )
        db.add(transaction)
        return
    
    # 平均分配给成功领取的用户
    bonus_per_user = packet.bomb_amount / len(successful_claims)
    bonus_per_user = round(bonus_per_user, 8)
    
    for claim in successful_claims:
        user = await db.get(User, claim.user_id)
        balance_field = f"balance_{packet.currency.value}"
        current_balance = getattr(user, balance_field, 0) or Decimal(0)
        new_balance = current_balance + bonus_per_user
        setattr(user, balance_field, new_balance)
        
        # 更新领取金额
        claim.amount += bonus_per_user
        
        # 创建交易记录
        transaction = Transaction(
            user_id=user.id,
            type="bomb_bonus",
            currency=packet.currency,
            amount=bonus_per_user,
            balance_before=current_balance,
            balance_after=new_balance,
            ref_id=f"packet_{packet.uuid}",
            note="炸弹金额奖励"
        )
        db.add(transaction)
```

## 四、余额验证机制

### 4.1 发送红包时的余额验证

```python
def validate_balance_for_send(
    user: User,
    currency: CurrencyType,
    amount: Decimal
) -> tuple[bool, str, Decimal]:
    """
    验证发送红包的余额
    
    Returns:
        (is_valid, error_message, current_balance)
    """
    balance_field = f"balance_{currency.value}"
    current_balance = getattr(user, balance_field, 0) or Decimal(0)
    
    if current_balance < amount:
        return (
            False,
            f"Insufficient balance. Required: {amount}, Available: {current_balance}",
            current_balance
        )
    
    return (True, "", current_balance)
```

### 4.2 事务处理流程

```python
async def send_red_packet_with_transaction(
    db: AsyncSession,
    sender: User,
    request: CreateRedPacketRequest
) -> RedPacket:
    """使用事务发送红包，确保余额一致性"""
    
    async with db.begin():
        # 1. 锁定用户行（SELECT FOR UPDATE）
        result = await db.execute(
            select(User)
            .where(User.id == sender.id)
            .with_for_update()
        )
        locked_user = result.scalar_one()
        
        # 2. 再次验证余额
        is_valid, error_msg, current_balance = validate_balance_for_send(
            locked_user,
            request.currency,
            Decimal(str(request.total_amount))
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 3. 扣除余额
        balance_field = f"balance_{request.currency.value}"
        new_balance = current_balance - Decimal(str(request.total_amount))
        setattr(locked_user, balance_field, new_balance)
        
        # 4. 创建交易记录
        transaction = Transaction(
            user_id=locked_user.id,
            type="send_red_packet",
            currency=request.currency,
            amount=-Decimal(str(request.total_amount)),
            balance_before=current_balance,
            balance_after=new_balance,
            note=f"发送红包: {request.total_count}份"
        )
        db.add(transaction)
        
        # 5. 创建红包
        packet = RedPacket(
            uuid=str(uuid.uuid4()),
            sender_id=locked_user.id,
            currency=request.currency,
            packet_type=request.packet_type,
            total_amount=Decimal(str(request.total_amount)),
            total_count=request.total_count,
            message=request.message,
            bomb_number=request.bomb_number,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(packet)
        
        transaction.ref_id = f"packet_{packet.uuid}"
        
        await db.commit()
        await db.refresh(packet)
        
        return packet
```

### 4.3 异常处理

```python
class InsufficientBalanceError(Exception):
    """余额不足异常"""
    pass

class RedPacketError(Exception):
    """红包操作异常"""
    pass

async def handle_red_packet_error(error: Exception):
    """统一处理红包相关错误"""
    if isinstance(error, InsufficientBalanceError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(error), "error_code": "INSUFFICIENT_BALANCE"}
        )
    elif isinstance(error, RedPacketError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(error), "error_code": "RED_PACKET_ERROR"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"}
        )
```

## 五、测试用例

### 5.1 最佳手气测试

```python
async def test_best_mvp_flow(db: AsyncSession):
    """测试最佳手气流程"""
    # 1. 创建用户
    sender = create_test_user(db, balance_usdt=100)
    claimer1 = create_test_user(db, balance_usdt=0)
    claimer2 = create_test_user(db, balance_usdt=0)
    claimer3 = create_test_user(db, balance_usdt=0)
    
    # 2. 发送最佳手气红包
    packet = await create_red_packet(
        db=db,
        sender_id=sender.id,
        currency=CurrencyType.USDT,
        packet_type=RedPacketType.RANDOM,
        total_amount=10.0,
        total_count=3
    )
    
    # 3. 领取红包
    claim1 = await claim_red_packet(db, packet.uuid, claimer1.tg_id)
    claim2 = await claim_red_packet(db, packet.uuid, claimer2.tg_id)
    claim3 = await claim_red_packet(db, packet.uuid, claimer3.tg_id)
    
    # 4. 验证最佳手气
    await db.refresh(packet)
    assert packet.luckiest_user_id is not None
    assert packet.luckiest_amount is not None
    
    # 5. 验证金额总和
    total_claimed = claim1.amount + claim2.amount + claim3.amount
    assert abs(total_claimed - 10.0) < 0.01
```

### 5.2 红包炸弹测试

```python
async def test_red_packet_bomb_flow(db: AsyncSession):
    """测试红包炸弹流程"""
    # 1. 创建用户
    sender = create_test_user(db, balance_usdt=100)
    claimer1 = create_test_user(db, balance_usdt=0)
    claimer2 = create_test_user(db, balance_usdt=0)
    
    # 2. 发送红包炸弹（炸弹数字5）
    packet = await create_red_packet(
        db=db,
        sender_id=sender.id,
        currency=CurrencyType.USDT,
        packet_type=RedPacketType.FIXED,
        total_amount=10.0,
        total_count=2,
        bomb_number=5
    )
    
    # 3. 领取红包（假设金额为 5.05，尾数为5）
    claim1 = await claim_red_packet(db, packet.uuid, claimer1.tg_id)
    assert claim1.is_bomb_triggered == True
    assert claim1.amount == 0
    
    # 4. 验证用户无法再次领取
    with pytest.raises(HTTPException):
        await claim_red_packet(db, packet.uuid, claimer1.tg_id)
    
    # 5. 其他用户正常领取
    claim2 = await claim_red_packet(db, packet.uuid, claimer2.tg_id)
    assert claim2.is_bomb_triggered == False
    assert claim2.amount > 0
    
    # 6. 验证炸弹金额分配
    await db.refresh(packet)
    # 炸弹金额应该分配给成功领取的用户
```

## 六、API 响应模型

### 6.1 扩展响应模型

```python
class ClaimResult(BaseModel):
    success: bool
    amount: float
    is_luckiest: bool = False
    is_bomb_triggered: bool = False
    message: str

class RedPacketDetailResponse(BaseModel):
    id: int
    uuid: str
    sender_id: int
    sender_name: str
    currency: CurrencyType
    packet_type: RedPacketType
    total_amount: float
    total_count: int
    claimed_amount: float
    claimed_count: int
    message: str
    status: RedPacketStatus
    bomb_number: Optional[int] = None
    bomb_amount: float = 0
    bomb_trigger_count: int = 0
    luckiest_user_id: Optional[int] = None
    luckiest_user_name: Optional[str] = None
    luckiest_amount: Optional[float] = None
    claims: List[ClaimDetailResponse]
    created_at: datetime
    expires_at: Optional[datetime]

class ClaimDetailResponse(BaseModel):
    user_id: int
    user_name: str
    amount: float
    is_luckiest: bool
    is_bomb_triggered: bool
    claimed_at: datetime
```

## 七、前端集成

### 7.1 发送红包表单扩展

```typescript
interface SendRedPacketParams {
  chat_id?: number;
  currency: 'usdt' | 'ton' | 'stars';
  packet_type: 'random' | 'fixed';
  total_amount: number;
  total_count: number;
  message?: string;
  bomb_number?: number; // 0-9, 仅当 packet_type='fixed' 时有效
}

// 表单验证
function validateBombNumber(packetType: string, bombNumber?: number): string | null {
  if (packetType === 'fixed') {
    if (bombNumber === undefined || bombNumber === null) {
      return '请选择炸弹数字';
    }
    if (bombNumber < 0 || bombNumber > 9) {
      return '炸弹数字必须在0-9之间';
    }
  }
  return null;
}
```

### 7.2 红包详情显示

```typescript
interface RedPacketDetail {
  // ... 其他字段
  packet_type: 'random' | 'fixed';
  bomb_number?: number;
  bomb_amount: number;
  bomb_trigger_count: number;
  luckiest_user_id?: number;
  luckiest_user_name?: string;
  luckiest_amount?: number;
  claims: Array<{
    user_name: string;
    amount: number;
    is_luckiest: boolean;
    is_bomb_triggered: boolean;
    claimed_at: string;
  }>;
}

// 显示逻辑
function renderPacketType(packet: RedPacketDetail) {
  if (packet.packet_type === 'random') {
    return '最佳手气';
  } else if (packet.packet_type === 'fixed') {
    return `红包炸弹 (炸弹数字: ${packet.bomb_number})`;
  }
}

function renderClaimStatus(claim: Claim) {
  if (claim.is_bomb_triggered) {
    return '💣 触发炸弹';
  }
  if (claim.is_luckiest) {
    return '⭐ 最佳手气';
  }
  return `获得 ${claim.amount}`;
}
```

## 八、性能优化建议

### 8.1 数据库索引

```sql
-- 优化查询性能
CREATE INDEX idx_red_packets_type_status ON red_packets(packet_type, status);
CREATE INDEX idx_red_packets_luckiest ON red_packets(luckiest_user_id) WHERE luckiest_user_id IS NOT NULL;
CREATE INDEX idx_claims_bomb ON red_packet_claims(is_bomb_triggered) WHERE is_bomb_triggered = true;
```

### 8.2 缓存策略

```python
# 使用 Redis 缓存热门红包信息
async def get_red_packet_cached(packet_uuid: str):
    cache_key = f"red_packet:{packet_uuid}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    packet = await get_red_packet_by_uuid(db, packet_uuid)
    await redis.setex(cache_key, 300, json.dumps(packet))  # 5分钟缓存
    return packet
```

## 九、安全考虑

### 9.1 防刷机制

```python
# 限制用户发送频率
async def check_send_rate_limit(user_id: int):
    key = f"send_rate_limit:{user_id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)  # 1分钟窗口
    if count > 10:  # 每分钟最多10个红包
        raise HTTPException(status_code=429, detail="Send rate limit exceeded")
```

### 9.2 金额验证

```python
# 验证金额范围
MIN_AMOUNT = Decimal("0.01")
MAX_AMOUNT = Decimal("10000")
MIN_COUNT = 1
MAX_COUNT = 100

def validate_red_packet_params(amount: Decimal, count: int):
    if amount < MIN_AMOUNT or amount > MAX_AMOUNT:
        raise ValueError(f"Amount must be between {MIN_AMOUNT} and {MAX_AMOUNT}")
    if count < MIN_COUNT or count > MAX_COUNT:
        raise ValueError(f"Count must be between {MIN_COUNT} and {MAX_COUNT}")
```

## 十、部署检查清单

- [ ] 数据库迁移脚本已执行
- [ ] API 接口已更新并测试
- [ ] 前端表单已添加炸弹数字选择
- [ ] 余额验证机制已实现
- [ ] 事务处理已测试
- [ ] 异常处理已完善
- [ ] 性能优化已实施
- [ ] 安全机制已部署
- [ ] 单元测试已通过
- [ ] 集成测试已通过

