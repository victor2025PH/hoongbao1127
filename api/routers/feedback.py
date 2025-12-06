"""
用户反馈路由
用于收集用户反馈和建议
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from loguru import logger

from shared.database.connection import get_db_session
from shared.database.models import User
from api.utils.telegram_auth import get_tg_id_from_header

router = APIRouter()


class FeedbackRequest(BaseModel):
    """反馈请求"""
    type: str = Field(..., description="反馈类型: bug, feature, suggestion, other")
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(..., min_length=1, max_length=2000, description="内容")
    contact: Optional[str] = Field(None, max_length=100, description="联系方式（可选）")
    screenshot_url: Optional[str] = Field(None, max_length=500, description="截图URL（可选）")


class FeedbackResponse(BaseModel):
    """反馈响应"""
    success: bool
    feedback_id: int
    message: str


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """提交用户反馈"""
    # 获取用户信息（可选，允许匿名反馈）
    user_id = None
    if tg_id:
        result = await db.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user:
            user_id = user.id
    
    # 保存反馈到数据库（如果有 Feedback 表）
    # 目前先记录到日志
    logger.info(
        f"用户反馈 [{request.type}]: {request.title}\n"
        f"用户ID: {user_id or '匿名'}\n"
        f"内容: {request.content}\n"
        f"联系方式: {request.contact or '无'}\n"
        f"截图: {request.screenshot_url or '无'}"
    )
    
    # TODO: 保存到数据库表
    # feedback = Feedback(
    #     user_id=user_id,
    #     type=request.type,
    #     title=request.title,
    #     content=request.content,
    #     contact=request.contact,
    #     screenshot_url=request.screenshot_url,
    #     created_at=datetime.utcnow()
    # )
    # db.add(feedback)
    # await db.commit()
    
    return FeedbackResponse(
        success=True,
        feedback_id=0,  # TODO: 返回实际ID
        message="反馈已提交，感谢您的反馈！"
    )


@router.get("/types")
async def get_feedback_types():
    """获取反馈类型列表"""
    return {
        "types": [
            {"value": "bug", "label": "Bug 报告"},
            {"value": "feature", "label": "功能建议"},
            {"value": "suggestion", "label": "改进建议"},
            {"value": "other", "label": "其他"},
        ]
    }

