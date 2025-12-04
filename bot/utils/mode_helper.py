"""
Lucky Red - 交互模式辅助函数
"""
from shared.database.connection import get_db
from shared.database.models import User
from loguru import logger


def get_effective_mode(user: User, chat_type: str) -> str:
    """
    根据用户偏好和上下文智能选择交互模式
    
    Args:
        user: 用户对象
        chat_type: 聊天类型 ("private", "group", "supergroup")
    
    Returns:
        有效的交互模式
    """
    # 安全地获取 interaction_mode（字段可能不存在）
    try:
        mode = getattr(user, 'interaction_mode', None) or "auto"
    except Exception:
        mode = "auto"
    
    # 如果是 auto 模式，根据上下文智能选择
    if mode == "auto":
        if chat_type in ["group", "supergroup"]:
            # 群组中优先使用 inline
            try:
                last_mode = getattr(user, 'last_interaction_mode', None)
                return last_mode if last_mode in ["inline", "keyboard"] else "inline"
            except Exception:
                return "inline"
        else:
            # 私聊中使用上次的模式，默认 keyboard
            try:
                return getattr(user, 'last_interaction_mode', None) or "keyboard"
            except Exception:
                return "keyboard"
    
    # 如果用户选择了 miniapp 但在群组中，回退到 inline
    if mode == "miniapp" and chat_type in ["group", "supergroup"]:
        logger.info(f"User {user.tg_id} selected miniapp but in group, falling back to inline")
        return "inline"
    
    return mode


async def update_user_mode(user_id: int, mode: str, update_last: bool = True):
    """
    更新用户的交互模式
    
    Args:
        user_id: Telegram 用户 ID
        mode: 交互模式
        update_last: 是否同时更新 last_interaction_mode
    """
    try:
        with get_db() as db:
            user = db.query(User).filter(User.tg_id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            # 检查字段是否存在，如果不存在则使用 SQL 直接添加
            try:
                # 尝试访问字段，如果不存在会抛出 AttributeError
                _ = user.interaction_mode
            except AttributeError:
                # 字段不存在，使用 SQL 直接添加
                logger.warning(f"User {user_id} missing interaction_mode field, adding via SQL")
                from sqlalchemy import text
                try:
                    db.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN interaction_mode VARCHAR(20) DEFAULT 'auto'
                    """))
                    db.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN last_interaction_mode VARCHAR(20) DEFAULT 'keyboard'
                    """))
                    db.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN seamless_switch_enabled INTEGER DEFAULT 1
                    """))
                    db.commit()
                    # 重新查询用户
                    db.refresh(user)
                    logger.info(f"Added interaction_mode fields for user {user_id}")
                except Exception as sql_e:
                    logger.error(f"Failed to add fields via SQL: {sql_e}")
                    # 如果添加字段失败，尝试使用 setattr（可能字段已存在但模型未更新）
                    pass
            
            # 使用 setattr 确保即使字段不存在也能设置
            try:
                setattr(user, 'interaction_mode', mode)
                if update_last and mode != "auto":
                    setattr(user, 'last_interaction_mode', mode)
            except Exception as attr_e:
                logger.error(f"Error setting attributes: {attr_e}")
                # 如果 setattr 也失败，使用 SQL 直接更新
                from sqlalchemy import text
                db.execute(text("""
                    UPDATE users 
                    SET interaction_mode = :mode
                    WHERE tg_id = :user_id
                """), {"mode": mode, "user_id": user_id})
                if update_last and mode != "auto":
                    db.execute(text("""
                        UPDATE users 
                        SET last_interaction_mode = :mode
                        WHERE tg_id = :user_id
                    """), {"mode": mode, "user_id": user_id})
            
            db.commit()
            
            # 清除缓存
            from bot.utils.cache import UserCache
            UserCache.invalidate(user_id)
            
            logger.info(f"Updated user {user_id} mode to {mode}")
            return True
    except Exception as e:
        logger.error(f"Error updating user mode: {e}", exc_info=True)
        return False


def get_mode_name(mode: str) -> str:
    """获取模式的显示名称"""
    names = {
        "keyboard": "⌨️ 底部键盘模式",
        "inline": "🔘 内联按钮模式",
        "miniapp": "📱 MiniApp 模式",
        "auto": "🔄 自动模式"
    }
    return names.get(mode, "⌨️ 底部键盘模式")


def get_mode_description(mode: str) -> str:
    """获取模式的描述"""
    descriptions = {
        "keyboard": "传统 bot 体验，在群组中也能使用",
        "inline": "流畅交互，点击消息中的按钮",
        "miniapp": "最丰富的功能，最佳体验（仅私聊）",
        "auto": "根据上下文自动选择最佳模式"
    }
    return descriptions.get(mode, "传统 bot 体验")
