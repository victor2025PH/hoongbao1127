"""
LuckyRed Admin Dashboard
管理後台 API
"""
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database.connection import SyncSessionLocal
from shared.database.models import User, RedPacket, Transaction, CheckinRecord
from sqlalchemy import func, desc, String
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="LuckyRed Admin",
    description="紅包管理後台",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模板
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


def get_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """管理後台首頁"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/stats")
def get_stats(db=Depends(get_db)):
    """獲取統計數據"""
    try:
        # 用戶統計
        total_users = db.query(func.count(User.id)).scalar() or 0
        
        # 今日新用戶
        today = datetime.utcnow().date()
        new_users_today = db.query(func.count(User.id)).filter(
            func.date(User.created_at) == today
        ).scalar() or 0
        
        # 紅包統計
        total_packets = db.query(func.count(RedPacket.id)).scalar() or 0
        active_packets = db.query(func.count(RedPacket.id)).filter(
            RedPacket.status == 'active'
        ).scalar() or 0
        
        # 交易統計
        total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
        total_volume = db.query(func.sum(Transaction.amount)).scalar() or 0
        
        return {
            "success": True,
            "data": {
                "users": {
                    "total": total_users,
                    "new_today": new_users_today
                },
                "red_packets": {
                    "total": total_packets,
                    "active": active_packets
                },
                "transactions": {
                    "total": total_transactions,
                    "volume": float(total_volume) if total_volume else 0
                }
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/users")
def get_users(page: int = 1, limit: int = 20, search: Optional[str] = None, db=Depends(get_db)):
    """獲取用戶列表（支持搜索）"""
    try:
        offset = (page - 1) * limit
        query = db.query(User)
        
        # 搜索功能
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.username.like(search_term)) |
                (User.tg_id.cast(String).like(search_term)) |
                (User.first_name.like(search_term)) |
                (User.last_name.like(search_term))
            )
        
        users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
        total = query.count()
        
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "id": u.id,
                        "telegram_id": u.tg_id,
                        "username": u.username,
                        "first_name": u.first_name,
                        "last_name": u.last_name,
                        "balance_usdt": float(u.balance_usdt) if u.balance_usdt else 0,
                        "balance_ton": float(u.balance_ton) if u.balance_ton else 0,
                        "balance_stars": u.balance_stars or 0,
                        "balance_points": u.balance_points or 0,
                        "energy": u.xp,
                        "level": u.level,
                        "is_banned": u.is_banned,
                        "is_admin": u.is_admin,
                        "created_at": u.created_at.isoformat() if u.created_at else None
                    }
                    for u in users
                ],
                "total": total,
                "page": page,
                "limit": limit
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/red-packets")
def get_red_packets(page: int = 1, limit: int = 20, db=Depends(get_db)):
    """獲取紅包列表"""
    try:
        offset = (page - 1) * limit
        packets = db.query(RedPacket).order_by(desc(RedPacket.created_at)).offset(offset).limit(limit).all()
        total = db.query(func.count(RedPacket.id)).scalar() or 0
        
        return {
            "success": True,
            "data": {
                "packets": [
                    {
                        "id": p.id,
                        "sender_id": p.sender_id,
                        "total_amount": float(p.total_amount) if p.total_amount else 0,
                        "total_count": p.total_count,
                        "claimed_count": p.claimed_count,
                        "status": p.status,
                        "created_at": p.created_at.isoformat() if p.created_at else None
                    }
                    for p in packets
                ],
                "total": total,
                "page": page,
                "limit": limit
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/transactions")
def get_transactions(page: int = 1, limit: int = 20, db=Depends(get_db)):
    """獲取交易列表"""
    try:
        offset = (page - 1) * limit
        transactions = db.query(Transaction).order_by(desc(Transaction.created_at)).offset(offset).limit(limit).all()
        total = db.query(func.count(Transaction.id)).scalar() or 0
        
        return {
            "success": True,
            "data": {
                "transactions": [
                    {
                        "id": t.id,
                        "user_id": t.user_id,
                        "type": t.type,
                        "amount": float(t.amount) if t.amount else 0,
                        "currency": t.currency.value if t.currency else "usdt",
                        "note": t.note or "",
                        "created_at": t.created_at.isoformat() if t.created_at else None
                    }
                    for t in transactions
                ],
                "total": total,
                "page": page,
                "limit": limit
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 充值請求模型
class AdjustBalanceRequest(BaseModel):
    user_id: int
    amount: float
    currency: str = "usdt"  # usdt, ton, stars, points
    reason: Optional[str] = None


@app.post("/api/adjust-balance")
def adjust_balance(request: AdjustBalanceRequest, db=Depends(get_db)):
    """調整用戶餘額（充值/扣款）"""
    try:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            return {"success": False, "error": "用戶不存在"}
        
        # 獲取當前餘額
        balance_field = f"balance_{request.currency}"
        if not hasattr(user, balance_field):
            return {"success": False, "error": f"不支持的貨幣類型: {request.currency}"}
        
        old_balance = getattr(user, balance_field) or Decimal(0)
        amount_decimal = Decimal(str(request.amount))
        new_balance = old_balance + amount_decimal
        
        # 更新餘額
        setattr(user, balance_field, new_balance)
        
        # 創建交易記錄
        from shared.database.models import CurrencyType
        currency_enum = CurrencyType.USDT
        if request.currency.lower() == "usdt":
            currency_enum = CurrencyType.USDT
        elif request.currency.lower() == "ton":
            currency_enum = CurrencyType.TON
        elif request.currency.lower() == "stars":
            currency_enum = CurrencyType.STARS
        elif request.currency.lower() == "points":
            currency_enum = CurrencyType.POINTS
        
        transaction = Transaction(
            user_id=user.id,
            type="admin_adjust" if amount_decimal >= 0 else "admin_deduct",
            amount=amount_decimal,
            currency=currency_enum,
            balance_before=old_balance,
            balance_after=new_balance,
            note=request.reason or f"管理員{'充值' if amount_decimal >= 0 else '扣款'}: {amount_decimal} {request.currency.upper()}"
        )
        db.add(transaction)
        db.commit()
        
        return {
            "success": True,
            "data": {
                "user_id": user.id,
                "username": user.username,
                "telegram_id": user.tg_id,
                "currency": request.currency,
                "old_balance": float(old_balance),
                "amount": float(amount_decimal),
                "new_balance": float(new_balance),
                "transaction_id": transaction.id
            }
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


@app.get("/api/user/{user_id}")
def get_user(user_id: int, db=Depends(get_db)):
    """獲取單個用戶詳情"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "用戶不存在"}
        
        return {
            "success": True,
            "data": {
                "id": user.id,
                "telegram_id": user.tg_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "balance_usdt": float(user.balance_usdt) if user.balance_usdt else 0,
                "balance_ton": float(user.balance_ton) if user.balance_ton else 0,
                "balance_stars": user.balance_stars or 0,
                "balance_points": user.balance_points or 0,
                "level": user.level,
                "xp": user.xp,
                "is_banned": user.is_banned,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 机器人绑定请求模型
class BindBotRequest(BaseModel):
    user_id: int
    bot_username: Optional[str] = None
    bot_id: Optional[int] = None


@app.post("/api/bind-bot")
def bind_bot(request: BindBotRequest, db=Depends(get_db)):
    """绑定机器人到用户（如果数据库有相关字段）"""
    try:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            return {"success": False, "error": "用戶不存在"}
        
        # 注意：如果 User 模型中没有 bot_id 或 bot_username 字段，需要先添加
        # 这里先返回成功，实际绑定逻辑需要根据数据库模型调整
        # 如果需要在 User 表中添加 bot_id 字段，需要数据库迁移
        
        return {
            "success": True,
            "data": {
                "user_id": user.id,
                "message": "机器人绑定功能需要先在数据库模型中添加 bot_id 字段"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/search-users")
def search_users(q: str, limit: int = 20, db=Depends(get_db)):
    """搜索用户（通过 Telegram ID、用户名等）"""
    try:
        if not q:
            return {"success": False, "error": "搜索关键词不能为空"}
        
        search_term = f"%{q}%"
        users = db.query(User).filter(
            (User.username.like(search_term)) |
            (User.tg_id.cast(String).like(search_term)) |
            (User.first_name.like(search_term)) |
            (User.last_name.like(search_term))
        ).limit(limit).all()
        
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "id": u.id,
                        "telegram_id": u.tg_id,
                        "username": u.username,
                        "first_name": u.first_name,
                        "last_name": u.last_name,
                        "balance_usdt": float(u.balance_usdt) if u.balance_usdt else 0,
                        "balance_ton": float(u.balance_ton) if u.balance_ton else 0,
                        "balance_stars": u.balance_stars or 0,
                        "balance_points": u.balance_points or 0,
                        "level": u.level,
                        "is_banned": u.is_banned,
                        "is_admin": u.is_admin
                    }
                    for u in users
                ],
                "count": len(users)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/health")
def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "admin"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)

