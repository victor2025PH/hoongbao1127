"""
管理后台 - Telegram 管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from pydantic import BaseModel

from shared.database.connection import get_db_session
from shared.database.models import TelegramGroup, TelegramMessage, User, MessageTemplate
from api.services.telegram_service import TelegramBotService
from api.utils.auth import get_current_active_admin, AdminUser

router = APIRouter(prefix="/api/v1/admin/telegram", tags=["管理后台-Telegram"])


class SendMessageRequest(BaseModel):
    chat_id: int
    text: str
    parse_mode: Optional[str] = "Markdown"
    reply_markup: Optional[dict] = None


class SendBatchMessageRequest(BaseModel):
    chat_ids: List[int]
    text: str
    parse_mode: Optional[str] = "Markdown"


class ResolveIdRequest(BaseModel):
    username: Optional[str] = None
    link: Optional[str] = None


@router.post("/send-message")
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """發送消息到指定聊天"""
    service = TelegramBotService(db)
    result = await service.send_message(
        chat_id=request.chat_id,
        text=request.text,
        parse_mode=request.parse_mode,
        reply_markup=request.reply_markup
    )
    return result


@router.post("/send-batch")
async def send_batch_messages(
    request: SendBatchMessageRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """批量發送消息"""
    service = TelegramBotService(db)
    result = await service.send_batch_messages(
        chat_ids=request.chat_ids,
        text=request.text,
        parse_mode=request.parse_mode
    )
    return result


@router.get("/groups")
async def get_groups(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取群組列表"""
    offset = (page - 1) * limit
    query = select(TelegramGroup)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (TelegramGroup.title.like(search_term)) |
            (TelegramGroup.username.like(search_term))
        )
    
    # 獲取總數
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 獲取數據
    query = query.order_by(desc(TelegramGroup.updated_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    groups = result.scalars().all()
    
    return {
        "success": True,
        "data": {
            "groups": [
                {
                    "id": g.id,
                    "chat_id": g.chat_id,
                    "title": g.title,
                    "type": g.type,
                    "username": g.username,
                    "member_count": g.member_count,
                    "bot_status": g.bot_status,
                    "is_active": g.is_active,
                    "updated_at": g.updated_at.isoformat() if g.updated_at else None
                }
                for g in groups
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    }


@router.get("/groups/{chat_id}")
async def get_group_detail(
    chat_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取群組詳情（增強版）"""
    service = TelegramBotService(db)
    result = await service.get_chat(chat_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Group not found"))
    
    # 從數據庫獲取記錄
    db_result = await db.execute(
        select(TelegramGroup).where(TelegramGroup.chat_id == chat_id)
    )
    group = db_result.scalar_one_or_none()
    
    # 獲取消息統計
    message_stats_result = await db.execute(
        select(
            func.count(TelegramMessage.id).label("total_messages"),
            func.count(TelegramMessage.id).filter(TelegramMessage.status == "sent").label("sent_messages"),
            func.count(TelegramMessage.id).filter(TelegramMessage.status == "failed").label("failed_messages"),
            func.max(TelegramMessage.sent_at).label("last_message_at")
        ).where(TelegramMessage.chat_id == chat_id)
    )
    message_stats = message_stats_result.first()
    
    # 獲取最近的消息（最多10條）
    recent_messages_result = await db.execute(
        select(TelegramMessage)
        .where(TelegramMessage.chat_id == chat_id)
        .order_by(desc(TelegramMessage.created_at))
        .limit(10)
    )
    recent_messages = recent_messages_result.scalars().all()
    
    # 嘗試獲取 Bot 在群組中的狀態
    bot_status_info = None
    try:
        from shared.config.settings import get_settings
        settings = get_settings()
        from telegram import Bot
        bot = Bot(token=settings.BOT_TOKEN)
        bot_info = await bot.get_me()
        bot_member_result = await service.get_chat_member(chat_id, bot_info.id)
        if bot_member_result["success"]:
            bot_status_info = bot_member_result["member"]
    except Exception as e:
        pass  # 如果無法獲取，忽略錯誤
    
    return {
        "success": True,
        "data": {
            "chat": result["chat"],
            "db_record": {
                "id": group.id if group else None,
                "member_count": group.member_count if group else None,
                "bot_status": group.bot_status if group else None,
                "is_active": group.is_active if group else None,
                "invite_link": group.invite_link if group else None,
                "description": group.description if group else None,
                "last_message_at": group.last_message_at.isoformat() if group and group.last_message_at else None,
                "created_at": group.created_at.isoformat() if group and group.created_at else None,
                "updated_at": group.updated_at.isoformat() if group and group.updated_at else None,
            } if group else None,
            "statistics": {
                "total_messages": message_stats.total_messages or 0,
                "sent_messages": message_stats.sent_messages or 0,
                "failed_messages": message_stats.failed_messages or 0,
                "last_message_at": message_stats.last_message_at.isoformat() if message_stats.last_message_at else None,
            },
            "bot_status": bot_status_info,
            "recent_messages": [
                {
                    "id": m.id,
                    "message_id": m.message_id,
                    "content": m.content,
                    "message_type": m.message_type,
                    "status": m.status,
                    "sent_at": m.sent_at.isoformat() if m.sent_at else None,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in recent_messages
            ],
        }
    }


@router.get("/messages")
async def get_messages(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    chat_id: Optional[int] = None,
    to_user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取消息記錄"""
    offset = (page - 1) * limit
    query = select(TelegramMessage)
    
    if chat_id:
        query = query.where(TelegramMessage.chat_id == chat_id)
    if to_user_id:
        query = query.where(TelegramMessage.to_user_id == to_user_id)
    
    # 獲取總數
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 獲取數據
    query = query.order_by(desc(TelegramMessage.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return {
        "success": True,
        "data": {
            "messages": [
                {
                    "id": m.id,
                    "message_id": m.message_id,
                    "chat_id": m.chat_id,
                    "chat_type": m.chat_type,
                    "from_user_id": m.from_user_id,
                    "to_user_id": m.to_user_id,
                    "message_type": m.message_type,
                    "content": m.content,
                    "status": m.status,
                    "sent_at": m.sent_at.isoformat() if m.sent_at else None,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in messages
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    }


@router.post("/resolve-id")
async def resolve_id(
    request: ResolveIdRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """解析 Telegram ID（從用戶名或鏈接）"""
    service = TelegramBotService(db)
    
    if request.username:
        tg_id = await service.resolve_username(request.username)
        if tg_id:
            return {
                "success": True,
                "data": {
                    "username": request.username,
                    "telegram_id": tg_id
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Username not found")
    
    elif request.link:
        result = await service.get_chat_by_link(request.link)
        if result["success"]:
            return {
                "success": True,
                "data": result["chat"]
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "Link not found"))
    
    else:
        raise HTTPException(status_code=400, detail="Either username or link must be provided")


# ========== 消息模板管理 ==========

class CreateTemplateRequest(BaseModel):
    name: str
    category: Optional[str] = None
    content: str
    variables: Optional[dict] = None
    message_type: str = "text"


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[dict] = None
    message_type: Optional[str] = None
    is_active: Optional[bool] = None


class RenderTemplateRequest(BaseModel):
    template_id: int
    variables: dict  # 變量值


@router.get("/templates")
async def get_templates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取消息模板列表"""
    offset = (page - 1) * limit
    query = select(MessageTemplate)
    
    if category:
        query = query.where(MessageTemplate.category == category)
    if is_active is not None:
        query = query.where(MessageTemplate.is_active == is_active)
    if search:
        search_term = f"%{search}%"
        query = query.where(MessageTemplate.name.like(search_term))
    
    # 獲取總數
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 獲取數據
    query = query.order_by(desc(MessageTemplate.updated_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return {
        "success": True,
        "data": {
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "category": t.category,
                    "content": t.content,
                    "variables": t.variables,
                    "message_type": t.message_type,
                    "is_active": t.is_active,
                    "usage_count": t.usage_count or 0,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in templates
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    }


@router.get("/templates/{template_id}")
async def get_template_detail(
    template_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取消息模板詳情"""
    result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {
        "success": True,
        "data": {
            "id": template.id,
            "name": template.name,
            "category": template.category,
            "content": template.content,
            "variables": template.variables,
            "message_type": template.message_type,
            "is_active": template.is_active,
            "usage_count": template.usage_count or 0,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        }
    }


@router.post("/templates")
async def create_template(
    request: CreateTemplateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """創建消息模板"""
    template = MessageTemplate(
        name=request.name,
        category=request.category,
        content=request.content,
        variables=request.variables,
        message_type=request.message_type,
        created_by=admin.id,
        is_active=True
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return {
        "success": True,
        "message": "模板創建成功",
        "data": {
            "id": template.id,
            "name": template.name,
        }
    }


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    request: UpdateTemplateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """更新消息模板"""
    result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if request.name is not None:
        template.name = request.name
    if request.category is not None:
        template.category = request.category
    if request.content is not None:
        template.content = request.content
    if request.variables is not None:
        template.variables = request.variables
    if request.message_type is not None:
        template.message_type = request.message_type
    if request.is_active is not None:
        template.is_active = request.is_active
    
    await db.commit()
    await db.refresh(template)
    
    return {
        "success": True,
        "message": "模板更新成功",
        "data": {
            "id": template.id,
            "name": template.name,
        }
    }


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """刪除消息模板"""
    result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    await db.delete(template)
    await db.commit()
    
    return {
        "success": True,
        "message": "模板刪除成功"
    }


@router.post("/templates/{template_id}/render")
async def render_template(
    template_id: int,
    request: RenderTemplateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """渲染消息模板（替換變量）"""
    result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 替換變量
    rendered_content = template.content
    if request.variables:
        for key, value in request.variables.items():
            rendered_content = rendered_content.replace(f"{{{key}}}", str(value))
    
    # 增加使用次數
    template.usage_count = (template.usage_count or 0) + 1
    await db.commit()
    
    return {
        "success": True,
        "data": {
            "template_id": template.id,
            "template_name": template.name,
            "rendered_content": rendered_content,
            "variables_used": request.variables,
        }
    }

