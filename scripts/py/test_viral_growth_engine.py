"""
测试Viral Growth Engine功能
包括Deep Linking和推荐系统
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from shared.config.settings import get_settings
from shared.database.models import User
from api.services.deep_link_service import DeepLinkService
from api.services.referral_service import ReferralService
from api.services.ledger_service import LedgerService
from sqlalchemy import select
from decimal import Decimal

settings = get_settings()


async def test_deep_linking():
    """测试Deep Linking功能"""
    print("\n" + "="*50)
    print("测试1: Deep Linking系统")
    print("="*50)
    
    # 测试红包链接生成
    packet_links = DeepLinkService.generate_packet_link("test-packet-123")
    print(f"\n✅ 红包链接生成成功:")
    print(f"  Telegram: {packet_links['telegram']}")
    print(f"  Web: {packet_links['web']}")
    print(f"  Universal: {packet_links['universal']}")
    
    # 测试邀请链接生成
    invite_links = DeepLinkService.generate_invite_link("REF123")
    print(f"\n✅ 邀请链接生成成功:")
    print(f"  Telegram: {invite_links['telegram']}")
    print(f"  Web: {invite_links['web']}")
    print(f"  Universal: {invite_links['universal']}")
    
    # 测试平台检测
    test_user_agents = [
        "Mozilla/5.0 (compatible; TelegramBot/1.0)",
        "WhatsApp/2.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    ]
    
    print(f"\n✅ 平台检测测试:")
    for ua in test_user_agents:
        platform = DeepLinkService.detect_platform_from_user_agent(ua)
        print(f"  {ua[:50]}... -> {platform}")
    
    # 测试智能重定向
    print(f"\n✅ 智能重定向测试:")
    redirect_url = DeepLinkService.get_redirect_url('packet', 'test-packet-123', 'Mozilla/5.0 (compatible; TelegramBot/1.0)')
    print(f"  Telegram User-Agent -> {redirect_url}")
    
    redirect_url = DeepLinkService.get_redirect_url('packet', 'test-packet-123', 'Mozilla/5.0 (Windows NT 10.0)')
    print(f"  Web User-Agent -> {redirect_url}")


async def test_referral_system():
    """测试推荐系统"""
    print("\n" + "="*50)
    print("测试2: 推荐系统（Tier 1 & Tier 2）")
    print("="*50)
    
    # 创建数据库连接（SQLite需要使用aiosqlite）
    database_url = settings.DATABASE_URL
    if database_url.startswith('sqlite'):
        # 将sqlite://替换为sqlite+aiosqlite://
        if database_url.startswith('sqlite:///'):
            database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///', 1)
        elif database_url.startswith('sqlite://'):
            database_url = database_url.replace('sqlite://', 'sqlite+aiosqlite://', 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # 创建测试用户（推荐关系：User A -> User B -> User C）
        print("\n📝 创建测试用户...")
        
        # User A（推荐人）
        result = await db.execute(select(User).where(User.tg_id == 100001))
        user_a = result.scalar_one_or_none()
        if not user_a:
            user_a = User(
                tg_id=100001,
                username="user_a",
                first_name="User",
                last_name="A",
                referral_code="REF001"
            )
            db.add(user_a)
            await db.commit()
            await db.refresh(user_a)
            print(f"  ✅ 创建User A: id={user_a.id}, referral_code={user_a.referral_code}")
        else:
            print(f"  ✅ User A已存在: id={user_a.id}")
        
        # User B（被User A推荐）
        result = await db.execute(select(User).where(User.tg_id == 100002))
        user_b = result.scalar_one_or_none()
        if not user_b:
            user_b = User(
                tg_id=100002,
                username="user_b",
                first_name="User",
                last_name="B",
                referrer_id=user_a.id,
                referral_code="REF002"
            )
            db.add(user_b)
            await db.commit()
            await db.refresh(user_b)
            print(f"  ✅ 创建User B: id={user_b.id}, referrer_id={user_b.referrer_id}")
        else:
            # 确保推荐关系存在
            if not user_b.referrer_id:
                user_b.referrer_id = user_a.id
                await db.commit()
            print(f"  ✅ User B已存在: id={user_b.id}, referrer_id={user_b.referrer_id}")
        
        # User C（被User B推荐，User A的Tier 2）
        result = await db.execute(select(User).where(User.tg_id == 100003))
        user_c = result.scalar_one_or_none()
        if not user_c:
            user_c = User(
                tg_id=100003,
                username="user_c",
                first_name="User",
                last_name="C",
                referrer_id=user_b.id,
                referral_code="REF003"
            )
            db.add(user_c)
            await db.commit()
            await db.refresh(user_c)
            print(f"  ✅ 创建User C: id={user_c.id}, referrer_id={user_c.referrer_id}")
        else:
            # 确保推荐关系存在
            if not user_c.referrer_id:
                user_c.referrer_id = user_b.id
                await db.commit()
            print(f"  ✅ User C已存在: id={user_c.id}, referrer_id={user_c.referrer_id}")
        
        # 测试推荐奖励处理
        print("\n💰 测试推荐奖励处理...")
        print("  场景: User C 领取了 100 USDT 红包")
        
        # 先给User C充值，确保有余额
        await LedgerService.create_entry(
            db=db,
            user_id=user_c.id,
            amount=Decimal('100'),
            currency='USDT',
            entry_type='DEPOSIT',
            related_type='test',
            description='测试充值',
            created_by='test'
        )
        
        # 处理推荐奖励
        reward_result = await ReferralService.process_referral_reward(
            db=db,
            user_id=user_c.id,
            amount=Decimal('100'),
            currency='USDT',
            reward_type='redpacket',
            metadata={'test': True}
        )
        
        print(f"  ✅ 推荐奖励处理结果:")
        print(f"    Tier 1奖励数量: {len(reward_result['tier1_rewards'])}")
        print(f"    Tier 2奖励数量: {len(reward_result['tier2_rewards'])}")
        print(f"    Tier 1总金额: {reward_result['total_tier1']} USDT")
        print(f"    Tier 2总金额: {reward_result['total_tier2']} USDT")
        
        if reward_result['tier1_rewards']:
            tier1 = reward_result['tier1_rewards'][0]
            print(f"    User B (Tier 1) 获得: {tier1['amount']} USDT")
        
        if reward_result['tier2_rewards']:
            tier2 = reward_result['tier2_rewards'][0]
            print(f"    User A (Tier 2) 获得: {tier2['amount']} USDT")
        
        # 测试推荐统计
        print("\n📊 测试推荐统计...")
        stats_a = await ReferralService.get_referral_stats(db, user_a.id)
        print(f"  User A 推荐统计:")
        print(f"    Tier 1推荐人数: {stats_a['tier1_count']}")
        print(f"    Tier 2推荐人数: {stats_a['tier2_count']}")
        print(f"    总推荐人数: {stats_a['total_referrals']}")
        print(f"    总奖励: {stats_a['total_reward']} USDT")
        
        stats_b = await ReferralService.get_referral_stats(db, user_b.id)
        print(f"  User B 推荐统计:")
        print(f"    Tier 1推荐人数: {stats_b['tier1_count']}")
        print(f"    总推荐人数: {stats_b['total_referrals']}")
        
        # 测试推荐树
        print("\n🌳 测试推荐树...")
        tree = await ReferralService.get_referral_tree(db, user_a.id, max_depth=2)
        print(f"  User A 推荐树:")
        print(f"    用户ID: {tree['user_id']}")
        print(f"    推荐码: {tree['referral_code']}")
        print(f"    直接推荐人数: {len(tree['referrals'])}")
        if tree['referrals']:
            for ref in tree['referrals']:
                print(f"      - User {ref['user_id']} ({ref['username']})")
                if ref['referrals']:
                    for sub_ref in ref['referrals']:
                        print(f"        - User {sub_ref['user_id']} ({sub_ref['username']}) - Tier 2")


async def test_payment_referral():
    """测试支付时的推荐奖励"""
    print("\n" + "="*50)
    print("测试3: 支付时的推荐奖励")
    print("="*50)
    
    # 创建数据库连接（SQLite需要使用aiosqlite）
    database_url = settings.DATABASE_URL
    if database_url.startswith('sqlite'):
        # 将sqlite://替换为sqlite+aiosqlite://
        if database_url.startswith('sqlite:///'):
            database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///', 1)
        elif database_url.startswith('sqlite://'):
            database_url = database_url.replace('sqlite://', 'sqlite+aiosqlite://', 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # 查找测试用户
        result = await db.execute(select(User).where(User.tg_id == 100003))
        user_c = result.scalar_one_or_none()
        
        if not user_c:
            print("  ⚠️ 测试用户不存在，跳过此测试")
            return
        
        print("\n💰 测试场景: User C 充值 200 USDT")
        
        # 模拟充值
        await LedgerService.create_entry(
            db=db,
            user_id=user_c.id,
            amount=Decimal('200'),
            currency='USDT',
            entry_type='FIAT_DEPOSIT',
            related_type='payment',
            description='测试充值',
            created_by='test'
        )
        
        # 处理推荐奖励
        reward_result = await ReferralService.process_referral_reward(
            db=db,
            user_id=user_c.id,
            amount=Decimal('200'),
            currency='USDT',
            reward_type='deposit',
            metadata={'test': True, 'transaction_id': 'TEST_TX_001'}
        )
        
        print(f"  ✅ 推荐奖励处理结果:")
        print(f"    Tier 1总金额: {reward_result['total_tier1']} USDT (应该是 20 USDT)")
        print(f"    Tier 2总金额: {reward_result['total_tier2']} USDT (应该是 10 USDT)")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🚀 Viral Growth Engine 功能测试")
    print("="*60)
    
    try:
        # 测试Deep Linking
        await test_deep_linking()
        
        # 测试推荐系统
        await test_referral_system()
        
        # 测试支付时的推荐奖励
        await test_payment_referral()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

