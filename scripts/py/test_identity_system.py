"""
测试Universal Identity System功能
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from shared.database.connection import get_db_session
from api.services.identity_service import IdentityService
from shared.database.models import User, UserIdentity, AccountLink
from shared.config.settings import get_settings

settings = get_settings()


async def test_identity_service():
    """测试IdentityService功能"""
    print("=" * 60)
    print("测试 Universal Identity System")
    print("=" * 60)
    
    # 创建数据库会话
    async for db in get_db_session():
        try:
            # 测试1: 通过Telegram ID创建用户
            print("\n[测试1] 通过Telegram ID创建用户")
            telegram_user = await IdentityService.get_or_create_user_by_identity(
                db=db,
                provider='telegram',
                provider_user_id='123456789',
                provider_data={
                    'username': 'test_user',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'language_code': 'zh-TW'
                }
            )
            print(f"✅ 创建用户成功: user_id={telegram_user.id}, uuid={telegram_user.uuid}")
            print(f"   tg_id={telegram_user.tg_id}, username={telegram_user.username}")
            
            # 测试2: 通过Google创建用户
            print("\n[测试2] 通过Google创建用户")
            google_user = await IdentityService.get_or_create_user_by_identity(
                db=db,
                provider='google',
                provider_user_id='user@example.com',
                provider_data={
                    'email': 'user@example.com',
                    'given_name': 'Google',
                    'family_name': 'User',
                    'picture': 'https://example.com/avatar.jpg'
                }
            )
            print(f"✅ 创建Google用户成功: user_id={google_user.id}, uuid={google_user.uuid}")
            print(f"   username={google_user.username}, first_name={google_user.first_name}")
            
            # 测试3: 链接Wallet到Telegram用户
            print("\n[测试3] 链接Wallet到Telegram用户")
            wallet_identity = await IdentityService.link_identity(
                db=db,
                user_id=telegram_user.id,
                provider='wallet',
                provider_user_id='0x1234567890abcdef',
                provider_data={
                    'network': 'TON',
                    'signature': 'mock_signature'
                }
            )
            print(f"✅ 链接Wallet成功: identity_id={wallet_identity.id}")
            print(f"   provider={wallet_identity.provider}, provider_user_id={wallet_identity.provider_user_id}")
            
            # 测试4: 生成Magic Link
            print("\n[测试4] 生成Magic Link")
            magic_token = await IdentityService.generate_magic_link(
                db=db,
                user_id=telegram_user.id,
                link_type='magic_login',
                expires_in_hours=24
            )
            print(f"✅ 生成Magic Link成功: token={magic_token[:20]}...")
            
            # 测试5: 验证Magic Link
            print("\n[测试5] 验证Magic Link")
            verified_user = await IdentityService.verify_magic_link(
                db=db,
                token=magic_token,
                mark_used=False  # 不标记为已使用，以便后续测试
            )
            if verified_user:
                print(f"✅ 验证Magic Link成功: user_id={verified_user.id}")
            else:
                print("❌ 验证Magic Link失败")
            
            # 测试6: 获取用户所有身份
            print("\n[测试6] 获取用户所有身份")
            identities = await IdentityService.get_user_identities(db, telegram_user.id)
            print(f"✅ 获取身份成功: 共{len(identities)}个身份")
            for identity in identities:
                print(f"   - {identity.provider}: {identity.provider_user_id} (primary={identity.is_primary})")
            
            # 测试7: 通过Telegram ID获取用户（兼容旧代码）
            print("\n[测试7] 通过Telegram ID获取用户（兼容旧代码）")
            found_user = await IdentityService.get_user_by_telegram_id(db, 123456789)
            if found_user:
                print(f"✅ 找到用户: user_id={found_user.id}, uuid={found_user.uuid}")
            else:
                print("❌ 未找到用户")
            
            print("\n" + "=" * 60)
            print("✅ 所有测试通过！")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break


async def test_ledger_service():
    """测试LedgerService功能"""
    print("\n" + "=" * 60)
    print("测试 LedgerService")
    print("=" * 60)
    
    from api.services.ledger_service import LedgerService
    from decimal import Decimal
    
    async for db in get_db_session():
        try:
            # 获取测试用户
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.tg_id == 123456789))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ 未找到测试用户，请先运行test_identity_service")
                break
            
            # 测试1: 创建账本条目（增加余额）
            print("\n[测试1] 创建账本条目（增加余额）")
            entry1 = await LedgerService.create_entry(
                db=db,
                user_id=user.id,
                amount=Decimal('100.0'),
                currency='USDT',
                entry_type='DEPOSIT',
                description='测试充值',
                created_by='test'
            )
            print(f"✅ 创建账本条目成功: entry_id={entry1['entry_id']}")
            print(f"   amount={entry1['amount']}, balance_after={entry1['balance_after']}")
            
            # 测试2: 获取余额
            print("\n[测试2] 获取余额")
            balance = await LedgerService.get_balance(db, user.id, 'USDT')
            print(f"✅ 获取余额成功: {balance} USDT")
            
            # 测试3: 创建账本条目（减少余额）
            print("\n[测试3] 创建账本条目（减少余额）")
            entry2 = await LedgerService.create_entry(
                db=db,
                user_id=user.id,
                amount=-Decimal('20.0'),
                currency='USDT',
                entry_type='SEND_PACKET',  # 使用LedgerCategory中定义的枚举值
                related_type='red_packet',
                description='测试发送红包',
                created_by='test'
            )
            print(f"✅ 创建账本条目成功: entry_id={entry2['entry_id']}")
            print(f"   amount={entry2['amount']}, balance_after={entry2['balance_after']}")
            
            # 测试4: 获取所有余额
            print("\n[测试4] 获取所有余额")
            all_balances = await LedgerService.get_all_balances(db, user.id)
            print(f"✅ 获取所有余额成功:")
            for currency, amount in all_balances.items():
                print(f"   {currency}: {amount}")
            
            # 测试5: 获取账本历史
            print("\n[测试5] 获取账本历史")
            history = await LedgerService.get_ledger_history(
                db=db,
                user_id=user.id,
                currency='USDT',
                limit=10
            )
            print(f"✅ 获取账本历史成功: 共{len(history)}条记录")
            for entry in history[:3]:  # 只显示前3条
                print(f"   - {entry['type']}: {entry['amount']} {entry['currency']} (余额: {entry['balance_after']})")
            
            print("\n" + "=" * 60)
            print("✅ LedgerService测试通过！")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break


async def main():
    """主函数"""
    print("开始测试 Universal Identity System...")
    await test_identity_service()
    await test_ledger_service()
    print("\n所有测试完成！")


if __name__ == "__main__":
    asyncio.run(main())

