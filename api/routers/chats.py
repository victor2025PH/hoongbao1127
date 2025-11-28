"""
Lucky Red - 群組和用戶搜索路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import re

from shared.database.connection import get_db_session
from shared.database.models import User, RedPacket
from shared.config.settings import get_settings
from telegram import Bot
from telegram.error import TelegramError
from loguru import logger
from api.utils.telegram_auth import get_tg_id_from_header

settings = get_settings()
router = APIRouter()

bot = Bot(token=settings.BOT_TOKEN)

# 獲取 Bot 自己的 ID（用於檢查 Bot 是否在群組中）
_bot_info = None
async def get_bot_id():
    """獲取 Bot 自己的 ID"""
    global _bot_info
    if _bot_info is None:
        _bot_info = await bot.get_me()
    return _bot_info.id


class ChatInfo(BaseModel):
    """群組/用戶信息"""
    id: int
    title: str
    type: str  # 'group', 'supergroup', 'channel', 'private'
    link: Optional[str] = None  # 群組鏈接（用於基於鏈接的群組）
    user_in_group: Optional[bool] = None  # 用戶是否在群組中
    bot_in_group: Optional[bool] = None  # Bot 是否在群組中
    status_message: Optional[str] = None  # 狀態提示信息
    
    class Config:
        from_attributes = True


class CheckResult(BaseModel):
    """檢查結果"""
    in_group: bool
    message: Optional[str] = None


@router.get("", response_model=List[ChatInfo])
async def get_user_chats(
    tg_id: Optional[int] = Depends(get_tg_id_from_header),  # 從 Telegram initData 獲取
    db: AsyncSession = Depends(get_db_session)
):
    """獲取用戶的群組列表"""
    try:
        # 獲取用戶加入的群組（從紅包記錄中提取）
        result = await db.execute(
            select(RedPacket.chat_id, RedPacket.chat_title)
            .where(RedPacket.sender_id == tg_id)
            .distinct()
        )
        packets = result.all()
        
        chats = []
        seen_chat_ids = set()
        
        for packet in packets:
            if packet.chat_id and packet.chat_id not in seen_chat_ids:
                seen_chat_ids.add(packet.chat_id)
                chats.append(ChatInfo(
                    id=packet.chat_id,
                    title=packet.chat_title or f"Chat {packet.chat_id}",
                    type="group"
                ))
        
        # 也可以通過 Bot API 獲取用戶的群組列表
        # 但這需要 Bot 在群組中，且用戶已授權
        # 這裡先返回從紅包記錄中提取的群組
        
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chats: {str(e)}")


@router.get("/search", response_model=List[ChatInfo])
async def search_chats(
    q: str = Query(..., min_length=1, description="搜索關鍵詞（群組名稱或群鏈接）"),
    tg_id_param: Optional[int] = Query(None, alias="tg_id", description="Telegram 用戶 ID（可選，用於本地測試）"),
    tg_id_header: Optional[int] = Depends(get_tg_id_from_header),  # 從 Telegram initData 獲取
    db: AsyncSession = Depends(get_db_session)
):
    """搜索群組（支持群組名稱和群鏈接）
    
    注意：即使 Bot 不在群組中，也可以通過群組鏈接（t.me/xxx）返回群組信息。
    用戶選擇後，會驗證用戶是否在群組中。
    """
    # 優先使用查詢參數（用於本地測試），否則使用請求頭中的 ID
    tg_id = tg_id_param or tg_id_header
    try:
        chats = []
        seen_chat_ids = set()
        
        # 處理群鏈接格式（t.me/xxx 或 https://t.me/xxx）和 @ 開頭的格式
        search_query = q.strip()
        username_from_link = None
        
        # 處理 @ 開頭的格式（移除 @ 符號）
        if search_query.startswith('@'):
            username_from_link = search_query[1:]
            search_query = username_from_link
        # 處理 t.me/ 鏈接格式
        elif 't.me/' in search_query:
            match = re.search(r't\.me/([^/?]+)', search_query)
            if match:
                username_from_link = match.group(1)
                search_query = username_from_link
        # 如果搜索查詢看起來像 username（只包含字母、數字、下劃線），也嘗試作為群組 username
        elif re.match(r'^[a-zA-Z0-9_]+$', search_query):
            username_from_link = search_query
        
        is_tme_link = username_from_link is not None
        
        # 首先嘗試通過 Bot API 獲取群組信息（對於 t.me 鏈接）
        if username_from_link:
            tg_chat = None
            try:
                # 嘗試使用 @username 格式獲取群組信息
                # 注意：這只適用於有公開 username 的群組，且 Bot 需要在群組中
                tg_chat = await bot.get_chat(f"@{username_from_link}")
                if tg_chat:
                    chat_type = "group"
                    if tg_chat.type == "supergroup":
                        chat_type = "supergroup"
                    elif tg_chat.type == "channel":
                        chat_type = "channel"
                    elif tg_chat.type == "private":
                        # 如果是私人聊天，不應該在群組搜索中返回
                        logger.info(f"@{username_from_link} is a private chat, not a group")
                        tg_chat = None
                    
                    if tg_chat:
                        # 獲取群組標題（優先使用 title，如果沒有則使用 username）
                        chat_title = tg_chat.title or tg_chat.username or f"@{username_from_link}"
                        
                        # 檢查 Bot 是否真的在群組中（使用 get_chat_member）
                        # 注意：對於公開群組，get_chat_member 可能成功但返回 "left" 狀態
                        bot_in_group = False
                        try:
                            bot_id = await get_bot_id()
                            bot_member = await bot.get_chat_member(chat_id=tg_chat.id, user_id=bot_id)
                            # 記錄實際的成員狀態
                            member_status = str(bot_member.status)
                            logger.info(f"Bot member status for {username_from_link} (id: {tg_chat.id}): {member_status}")
                            
                            # 檢查成員狀態：只有 "member", "administrator", "creator" 才算在群組中
                            # "left", "kicked", "restricted" 都不算在群組中
                            if member_status in ["member", "administrator", "creator"]:
                                bot_in_group = True
                                logger.info(f"Bot is in group {username_from_link}, id: {tg_chat.id}, status: {member_status}")
                            else:
                                bot_in_group = False
                                logger.warning(f"Bot is not in group {username_from_link}, id: {tg_chat.id}, status: {member_status}")
                        except TelegramError as e:
                            bot_in_group = False
                            error_msg = str(e).lower()
                            logger.warning(f"Bot is not in group {username_from_link}, id: {tg_chat.id}, error: {str(e)}")
                        
                        chat_info = ChatInfo(
                            id=tg_chat.id,
                            title=chat_title,
                            type=chat_type,
                            link=f"https://t.me/{username_from_link}",  # 保存鏈接以便後續使用
                            bot_in_group=bot_in_group
                        )
                        chats.append(chat_info)
                        seen_chat_ids.add(tg_chat.id)
                        logger.info(f"Successfully found group via Bot API: {username_from_link}, id: {tg_chat.id}, bot_in_group: {bot_in_group}")
            except TelegramError as e:
                # 如果 Bot 不在群組中或沒有權限，嘗試檢查是否是群組
                # 注意：如果是用戶（private chat），不應該創建 placeholder
                error_msg = str(e).lower()
                logger.warning(f"Cannot access via Bot API: {username_from_link}, error: {error_msg}")
                
                # 嘗試再次獲取，確認是否是群組（而不是用戶）
                try:
                    # 使用 get_chat 檢查類型（即使 Bot 不在群組中，對於公開群組也能獲取基本信息）
                    tg_chat_check = await bot.get_chat(f"@{username_from_link}")
                    # 如果是 private chat，不創建 placeholder（這是用戶，不是群組）
                    if tg_chat_check.type == "private":
                        logger.info(f"@{username_from_link} is a private chat (user), not creating placeholder")
                        # 不創建 placeholder，繼續搜索其他結果
                    elif tg_chat_check.type in ["group", "supergroup", "channel"]:
                        # 確認是群組，創建 placeholder
                        link = f"https://t.me/{username_from_link}"
                        placeholder_id = -hash(username_from_link) % (10**9)  # 使用負數 ID 標記
                        
                        chat_info = ChatInfo(
                            id=placeholder_id,
                            title=tg_chat_check.title or f"@{username_from_link}",  # 顯示標題或 username
                            type="group" if tg_chat_check.type in ["group", "supergroup"] else tg_chat_check.type,
                            link=link,  # 保存鏈接
                            bot_in_group=False,  # Bot 不在群組中
                            status_message="機器人不在群組中"
                        )
                        chats.append(chat_info)
                        seen_chat_ids.add(placeholder_id)
                        logger.info(f"Created placeholder group for link: {link}, id: {placeholder_id}")
                except TelegramError as check_error:
                    # 如果再次檢查也失敗，可能是用戶或無法訪問
                    # 為了安全起見，不創建 placeholder（避免將用戶誤認為群組）
                    logger.info(f"Cannot verify @{username_from_link}, might be a user or inaccessible: {str(check_error)}")
                    # 不創建 placeholder，繼續搜索其他結果
        
        # 從數據庫中搜索用戶已發送過紅包的群組
        result = await db.execute(
            select(RedPacket.chat_id, RedPacket.chat_title)
            .where(RedPacket.chat_title.ilike(f"%{search_query}%"))
            .distinct()
        )
        packets = result.all()
        
        for packet in packets:
            if packet.chat_id and packet.chat_id not in seen_chat_ids:
                seen_chat_ids.add(packet.chat_id)
                chats.append(ChatInfo(
                    id=packet.chat_id,
                    title=packet.chat_title or f"Chat {packet.chat_id}",
                    type="group"
                ))
        
        # 如果搜索結果為空且是 t.me 鏈接，嘗試檢查是否是群組
        # 注意：如果是用戶（private chat），不應該創建 placeholder
        if len(chats) == 0 and username_from_link:
            try:
                # 再次嘗試獲取，確認是否是群組
                tg_chat = await bot.get_chat(f"@{username_from_link}")
                # 如果是 private chat，不創建 placeholder（這是用戶，不是群組）
                if tg_chat and tg_chat.type == "private":
                    logger.info(f"@{username_from_link} is a private chat (user), not returning in group search")
                    return []  # 返回空列表，因為這是用戶，應該在用戶搜索中處理
                
                # 如果是群組但 Bot 不在群組中，創建 placeholder
                if tg_chat and tg_chat.type != "private":
                    link = f"https://t.me/{username_from_link}"
                    placeholder_id = -hash(username_from_link) % (10**9)
                    chats.append(ChatInfo(
                        id=placeholder_id,
                        title=tg_chat.title or f"@{username_from_link}",
                        type="group" if tg_chat.type in ["group", "supergroup"] else tg_chat.type,
                        link=link,
                        bot_in_group=False,  # Bot 不在群組中（因為無法訪問）
                        status_message="機器人不在群組中"
                    ))
                    logger.info(f"Created placeholder for group: {link}")
            except TelegramError as e:
                # 如果無法獲取，可能是用戶或 Bot 沒有權限
                # 為了安全起見，不創建 placeholder（避免將用戶誤認為群組）
                error_msg = str(e).lower()
                if "chat not found" in error_msg or "not found" in error_msg:
                    logger.info(f"Cannot find @{username_from_link}, might be a user or inaccessible group")
                    return []  # 返回空列表，不創建 placeholder
                else:
                    # 其他錯誤，也不創建 placeholder
                    logger.warning(f"Error checking @{username_from_link}: {str(e)}")
                    return []
        
        # 檢查每個群組的狀態（Bot 和用戶是否在群組中）
        for chat in chats:
            # 檢查 Bot 是否在群組中
            # 注意：bot.get_chat 成功不代表 Bot 在群組中，需要使用 get_chat_member 檢查
            bot_id = await get_bot_id()
            
            if chat.id > 0:  # 真實群組 ID（不是負數占位符）
                try:
                    # 嘗試獲取 Bot 自己在群組中的成員信息
                    # 這是最準確的方法來判斷 Bot 是否在群組中
                    bot_member = await bot.get_chat_member(chat_id=chat.id, user_id=bot_id)
                    # 檢查成員狀態：只有 "member", "administrator", "creator" 才算在群組中
                    if bot_member.status in ["member", "administrator", "creator"]:
                        chat.bot_in_group = True
                    else:
                        chat.bot_in_group = False
                        chat.status_message = "機器人不在群組中"
                except TelegramError as e:
                    chat.bot_in_group = False
                    error_msg = str(e).lower()
                    if "chat not found" in error_msg or "not found" in error_msg or "user not found" in error_msg:
                        chat.status_message = "機器人不在群組中"
                    elif "not enough rights" in error_msg or "forbidden" in error_msg:
                        chat.status_message = "機器人不在群組中或沒有權限"
                    else:
                        chat.status_message = "無法驗證機器人狀態"
            else:
                # 對於負數 ID（基於鏈接的群組），嘗試檢查 Bot 是否在群組中
                if chat.link:
                    try:
                        match = re.search(r't\.me/([^/?]+)', chat.link)
                        if match:
                            username = match.group(1)
                            # 先獲取群組信息
                            tg_chat = await bot.get_chat(f"@{username}")
                            if tg_chat:
                                # 嘗試獲取 Bot 的成員信息
                                bot_member = await bot.get_chat_member(chat_id=tg_chat.id, user_id=bot_id)
                                # 檢查成員狀態：只有 "member", "administrator", "creator" 才算在群組中
                                if bot_member.status in ["member", "administrator", "creator"]:
                                    chat.bot_in_group = True
                                else:
                                    chat.bot_in_group = False
                                    chat.status_message = "機器人不在群組中"
                                # 更新為真實的群組 ID
                                chat.id = tg_chat.id
                    except TelegramError as e:
                        chat.bot_in_group = False
                        error_msg = str(e).lower()
                        if "chat not found" in error_msg or "user not found" in error_msg:
                            chat.status_message = "機器人不在群組中"
                        else:
                            chat.status_message = "機器人不在群組中或無法訪問"
            
            # 檢查用戶是否在群組中（如果提供了 tg_id）
            if tg_id and chat.id > 0:
                try:
                    await bot.get_chat_member(chat_id=chat.id, user_id=tg_id)
                    chat.user_in_group = True
                except TelegramError:
                    chat.user_in_group = False
            elif tg_id and chat.id < 0 and chat.link:
                # 對於基於鏈接的群組，嘗試獲取真實 ID 後檢查
                try:
                    match = re.search(r't\.me/([^/?]+)', chat.link)
                    if match:
                        username = match.group(1)
                        tg_chat = await bot.get_chat(f"@{username}")
                        if tg_chat:
                            await bot.get_chat_member(chat_id=tg_chat.id, user_id=tg_id)
                            chat.user_in_group = True
                except TelegramError:
                    chat.user_in_group = False
        
        logger.info(f"Search completed for '{q}', found {len(chats)} results")
        return chats
    except Exception as e:
        logger.error(f"Error searching chats: {str(e)}", exc_info=True)
        # 即使出錯，如果是 t.me 鏈接，也嘗試返回一個基於鏈接的群組
        if 't.me/' in q:
            try:
                match = re.search(r't\.me/([^/?]+)', q)
                if match:
                    username = match.group(1)
                    link = f"https://t.me/{username}"
                    placeholder_id = -hash(username) % (10**9)
                    return [ChatInfo(
                        id=placeholder_id,
                        title=f"@{username}",
                        type="group",
                        link=link,
                        bot_in_group=False,  # Bot 不在群組中
                        status_message="機器人不在群組中"
                    )]
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to search chats: {str(e)}")


@router.get("/users/search", response_model=List[ChatInfo])
async def search_users(
    q: str = Query(..., min_length=1, description="搜索關鍵詞（用戶名或用戶ID）"),
    tg_id: Optional[int] = Depends(get_tg_id_from_header),  # 從 Telegram initData 獲取
    db: AsyncSession = Depends(get_db_session)
):
    """搜索用戶（支持用戶名、用戶ID和 t.me 鏈接）
    
    注意：對於 t.me 鏈接，如果識別為群組，則不返回用戶結果。
    """
    try:
        users_found = []
        seen_user_ids = set()
        
        # 處理搜索查詢
        search_query = q.strip()
        is_tme_link = 't.me/' in search_query
        username_from_link = None
        
        # 處理用戶名格式（移除 @ 符號）
        if search_query.startswith('@'):
            search_query = search_query[1:]
        
        # 處理 t.me 鏈接格式
        if is_tme_link:
            match = re.search(r't\.me/([^/?]+)', search_query)
            if match:
                username_from_link = match.group(1)
                search_query = username_from_link
                
                # 對於 t.me 鏈接，先檢查是否是群組
                # 如果是群組，則不返回用戶結果（避免混淆）
                try:
                    tg_chat = await bot.get_chat(f"@{username_from_link}")
                    # 如果成功獲取且不是 private 類型，說明是群組/頻道，不應該在用戶搜索中返回
                    if tg_chat and tg_chat.type != "private":
                        logger.info(f"t.me/{username_from_link} is a {tg_chat.type}, skipping user search")
                        return []  # 返回空列表，因為這是群組，應該在群組搜索中處理
                except TelegramError:
                    # 如果無法獲取，可能是用戶或 Bot 不在群組中
                    # 繼續嘗試作為用戶搜索
                    pass
        
        # 首先嘗試通過 Bot API 獲取用戶信息（優先級最高）
        if search_query and (username_from_link or not is_tme_link):
            try:
                # 嘗試通過用戶名獲取用戶信息
                # 注意：這需要用戶名是公開的
                tg_user = await bot.get_chat(f"@{search_query}")
                if tg_user:
                    # 確保是私人聊天（用戶），不是群組
                    if tg_user.type == "private":
                        user_title = tg_user.username or tg_user.first_name or f"User {tg_user.id}"
                        users_found.append(ChatInfo(
                            id=tg_user.id,
                            title=user_title,
                            type="private"
                        ))
                        seen_user_ids.add(tg_user.id)
                    else:
                        # 如果是群組類型，不應該在用戶搜索中返回
                        logger.info(f"@{search_query} is a {tg_user.type}, not a user")
            except TelegramError as e:
                # 如果獲取失敗，可能是用戶名不存在或不是公開的
                logger.warning(f"Failed to get user via Bot API: {str(e)}")
        
        # 從數據庫中搜索
        result = await db.execute(
            select(User)
            .where(
                (User.username.ilike(f"%{search_query}%")) |
                (User.first_name.ilike(f"%{search_query}%")) |
                (User.last_name.ilike(f"%{search_query}%"))
            )
            .limit(20)
        )
        db_users = result.scalars().all()
        
        for user in db_users:
            if user.tg_id not in seen_user_ids:
                seen_user_ids.add(user.tg_id)
                title = user.username or f"{user.first_name or ''} {user.last_name or ''}".strip() or f"User {user.tg_id}"
                users_found.append(ChatInfo(
                    id=user.tg_id,
                    title=title,
                    type="private"
                ))
        
        return users_found
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")


@router.get("/{chat_id}/check", response_model=CheckResult)
async def check_user_in_chat(
    chat_id: int,
    link: str = Query(None, description="群組鏈接（用於驗證基於鏈接的群組）"),
    tg_id: Optional[int] = Depends(get_tg_id_from_header),  # 從 Telegram initData 獲取
    db: AsyncSession = Depends(get_db_session)
):
    """檢查用戶是否在群組中
    
    如果 chat_id 是負數（基於鏈接的群組），需要提供 link 參數。
    會嘗試通過 Bot API 獲取群組信息，然後檢查用戶是否在群組中。
    """
    try:
        # 如果是基於鏈接的群組（負數 ID），嘗試通過鏈接獲取真實的群組 ID
        if chat_id < 0 and link:
            try:
                # 從鏈接中提取 username
                match = re.search(r't\.me/([^/?]+)', link)
                if match:
                    username = match.group(1)
                    # 嘗試獲取群組信息
                    tg_chat = await bot.get_chat(f"@{username}")
                    if tg_chat:
                        chat_id = tg_chat.id
            except TelegramError as e:
                logger.warning(f"Cannot get chat from link {link}: {str(e)}")
                return CheckResult(
                    in_group=False,
                    message="無法驗證群組，請確保 Bot 在群組中或使用正確的群組鏈接"
                )
        
        # 通過 Bot API 檢查用戶是否在群組中
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=tg_id)
            # 如果成功獲取成員信息，說明用戶在群組中
            return CheckResult(
                in_group=True,
                message="User is in the group"
            )
        except TelegramError as e:
            # 如果獲取失敗，可能是用戶不在群組中或沒有權限
            error_msg = str(e).lower()
            if "user not found" in error_msg or "chat not found" in error_msg:
                return CheckResult(
                    in_group=False,
                    message="用戶不在群組中，請先加入群組"
                )
            elif "not enough rights" in error_msg or "forbidden" in error_msg:
                return CheckResult(
                    in_group=False,
                    message="Bot 沒有權限檢查群組成員，請確保 Bot 在群組中"
                )
            else:
                # 其他錯誤也視為不在群組中
                return CheckResult(
                    in_group=False,
                    message="無法驗證用戶是否在群組中"
                )
    except Exception as e:
        logger.error(f"Error checking user membership: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check user membership: {str(e)}")

