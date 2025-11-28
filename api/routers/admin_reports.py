"""
管理后台 - 报表路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from shared.database.connection import get_db_session
from shared.database.models import User, RedPacket, Transaction, TelegramGroup
from api.services.report_service import ReportService
from api.utils.auth import get_current_active_admin, AdminUser
from sqlalchemy import select, func

router = APIRouter(prefix="/api/v1/admin/reports", tags=["管理后台-报表"])


class GenerateReportRequest(BaseModel):
    report_type: str  # user, transaction, red_packet, group
    name: str
    format: str  # xlsx, csv, pdf, json
    filters: Optional[Dict[str, Any]] = None
    columns: Optional[List[Dict[str, str]]] = None


@router.post("/generate")
async def generate_report(
    request: GenerateReportRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """生成報表"""
    service = ReportService(db)
    
    # 根據報表類型獲取數據
    if request.report_type == "user":
        data = await _get_user_report_data(db, request.filters or {})
        default_columns = [
            {"key": "id", "title": "ID"},
            {"key": "tg_id", "title": "Telegram ID"},
            {"key": "username", "title": "用戶名"},
            {"key": "first_name", "title": "姓名"},
            {"key": "balance_usdt", "title": "USDT 餘額"},
            {"key": "balance_ton", "title": "TON 餘額"},
            {"key": "level", "title": "等級"},
            {"key": "created_at", "title": "註冊時間"},
        ]
    elif request.report_type == "transaction":
        data = await _get_transaction_report_data(db, request.filters or {})
        default_columns = [
            {"key": "id", "title": "ID"},
            {"key": "user_id", "title": "用戶ID"},
            {"key": "tg_id", "title": "Telegram ID"},
            {"key": "type", "title": "類型"},
            {"key": "currency", "title": "幣種"},
            {"key": "amount", "title": "金額"},
            {"key": "created_at", "title": "時間"},
        ]
    elif request.report_type == "red_packet":
        data = await _get_redpacket_report_data(db, request.filters or {})
        default_columns = [
            {"key": "id", "title": "ID"},
            {"key": "uuid", "title": "UUID"},
            {"key": "sender_id", "title": "發送者ID"},
            {"key": "sender_tg_id", "title": "發送者 Telegram ID"},
            {"key": "chat_id", "title": "群組 ID"},
            {"key": "total_amount", "title": "總金額"},
            {"key": "claimed_count", "title": "已領取"},
            {"key": "status", "title": "狀態"},
            {"key": "created_at", "title": "創建時間"},
        ]
    elif request.report_type == "group":
        data = await _get_group_report_data(db, request.filters or {})
        default_columns = [
            {"key": "id", "title": "ID"},
            {"key": "chat_id", "title": "群組 Telegram ID"},
            {"key": "title", "title": "群組名稱"},
            {"key": "username", "title": "用戶名"},
            {"key": "member_count", "title": "成員數"},
            {"key": "bot_status", "title": "Bot 狀態"},
            {"key": "updated_at", "title": "更新時間"},
        ]
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported report type: {request.report_type}")
    
    columns = request.columns or default_columns
    
    # 生成報表文件
    if request.format == "xlsx":
        file_content = await service.generate_excel(data, columns, request.name)
    elif request.format == "csv":
        file_content = await service.generate_csv(data, columns)
    elif request.format == "json":
        file_content = await service.generate_json(data)
    elif request.format == "pdf":
        file_content = await service.generate_pdf(data, columns, request.name)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
    
    # 創建報表記錄
    report = await service.create_report_record(
        report_type=request.report_type,
        name=request.name,
        config={"filters": request.filters, "columns": columns},
        file_format=request.format,
        generated_by=admin.id
    )
    
    # 保存文件
    file_path = await service.save_report_file(report, file_content)
    
    return {
        "success": True,
        "data": {
            "report_id": report.id,
            "file_path": file_path,
            "download_url": f"/api/v1/admin/reports/{report.id}/download"
        }
    }


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """下載報表文件"""
    service = ReportService(db)
    report = await service.get_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "completed":
        raise HTTPException(status_code=400, detail="Report not ready")
    
    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file not found")
    
    from pathlib import Path
    file_path = Path(report.file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    def iterfile():
        with open(file_path, "rb") as f:
            yield from f
    
    media_type_map = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "pdf": "application/pdf",
        "json": "application/json"
    }
    
    return StreamingResponse(
        iterfile(),
        media_type=media_type_map.get(report.file_format, "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{report.name}.{report.file_format}"'
        }
    )


@router.get("")
async def list_reports(
    report_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取報表列表"""
    service = ReportService(db)
    offset = (page - 1) * limit
    reports = await service.list_reports(report_type, limit, offset)
    
    return {
        "success": True,
        "data": {
            "reports": [
                {
                    "id": r.id,
                    "report_type": r.report_type,
                    "name": r.name,
                    "file_format": r.file_format,
                    "status": r.status,
                    "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                    "download_url": f"/api/v1/admin/reports/{r.id}/download" if r.status == "completed" else None
                }
                for r in reports
            ],
            "page": page,
            "limit": limit
        }
    }


# 輔助函數：獲取報表數據
async def _get_user_report_data(db: AsyncSession, filters: Dict[str, Any]) -> List[Dict]:
    query = select(User)
    
    if filters.get("is_banned") is not None:
        query = query.where(User.is_banned == filters["is_banned"])
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "tg_id": u.tg_id,
            "username": u.username or "",
            "first_name": u.first_name or "",
            "last_name": u.last_name or "",
            "balance_usdt": float(u.balance_usdt or 0),
            "balance_ton": float(u.balance_ton or 0),
            "balance_stars": u.balance_stars or 0,
            "balance_points": u.balance_points or 0,
            "level": u.level,
            "xp": u.xp,
            "is_banned": u.is_banned,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


async def _get_transaction_report_data(db: AsyncSession, filters: Dict[str, Any]) -> List[Dict]:
    query = select(Transaction, User.tg_id).join(User, Transaction.user_id == User.id)
    
    if filters.get("currency"):
        from shared.database.models import CurrencyType
        query = query.where(Transaction.currency == CurrencyType(filters["currency"]))
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "id": t.id,
            "user_id": t.user_id,
            "tg_id": tg_id,
            "type": t.type,
            "currency": t.currency.value if t.currency else "",
            "amount": float(t.amount or 0),
            "balance_before": float(t.balance_before or 0) if t.balance_before else None,
            "balance_after": float(t.balance_after or 0) if t.balance_after else None,
            "note": t.note or "",
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t, tg_id in rows
    ]


async def _get_redpacket_report_data(db: AsyncSession, filters: Dict[str, Any]) -> List[Dict]:
    query = select(RedPacket, User.tg_id).join(User, RedPacket.sender_id == User.id)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "id": p.id,
            "uuid": p.uuid,
            "sender_id": p.sender_id,
            "sender_tg_id": tg_id,
            "chat_id": p.chat_id,
            "chat_title": p.chat_title or "",
            "currency": p.currency.value if p.currency else "",
            "total_amount": float(p.total_amount or 0),
            "total_count": p.total_count,
            "claimed_amount": float(p.claimed_amount or 0),
            "claimed_count": p.claimed_count,
            "status": p.status.value if p.status else "",
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p, tg_id in rows
    ]


async def _get_group_report_data(db: AsyncSession, filters: Dict[str, Any]) -> List[Dict]:
    query = select(TelegramGroup)
    
    result = await db.execute(query)
    groups = result.scalars().all()
    
    return [
        {
            "id": g.id,
            "chat_id": g.chat_id,
            "title": g.title or "",
            "type": g.type or "",
            "username": g.username or "",
            "member_count": g.member_count,
            "bot_status": g.bot_status or "",
            "is_active": g.is_active,
            "updated_at": g.updated_at.isoformat() if g.updated_at else None
        }
        for g in groups
    ]

