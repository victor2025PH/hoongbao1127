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
from sqlalchemy import func, desc
from datetime import datetime, timedelta

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
def get_users(page: int = 1, limit: int = 20, db=Depends(get_db)):
    """獲取用戶列表"""
    try:
        offset = (page - 1) * limit
        users = db.query(User).order_by(desc(User.created_at)).offset(offset).limit(limit).all()
        total = db.query(func.count(User.id)).scalar() or 0
        
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "id": u.id,
                        "telegram_id": u.tg_id,
                        "username": u.username,
                        "balance": float(u.balance_usdt) if u.balance_usdt else 0,
                        "energy": u.xp,
                        "level": u.level,
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
                        "status": "completed",
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


@app.get("/health")
def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "admin"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)

