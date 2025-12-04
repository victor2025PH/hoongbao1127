"""
交易管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from shared.database.connection import get_db_session
from shared.database.models import Transaction, User, CurrencyType
from sqlalchemy.orm import joinedload
from api.utils.auth import get_current_admin
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/api/v1/admin/transactions", tags=["管理后台-交易管理"])


# Pydantic 模型
class TransactionListItem(BaseModel):
    id: int
    user_id: int
    user_tg_id: Optional[int] = None
    user_username: Optional[str] = None
    user_name: Optional[str] = None
    type: str
    currency: str
    amount: Decimal
    balance_before: Optional[Decimal] = None
    balance_after: Optional[Decimal] = None
    ref_id: Optional[str] = None
    note: Optional[str] = None
    status: str  # pending, completed, rejected, cancelled
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionDetail(TransactionListItem):
    pass


class TransactionStats(BaseModel):
    total_count: int
    total_income: Decimal
    total_expense: Decimal
    net_amount: Decimal
    by_currency: dict
    by_type: dict


@router.get("/list", response_model=dict)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    ref_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """获取交易列表"""
    # Transaction 模型没有直接的 user 关系，需要通过 user_id 查询
    query = select(Transaction)
    
    # 构建筛选条件
    conditions = []
    
    if user_id:
        conditions.append(Transaction.user_id == user_id)
    
    if transaction_type:
        conditions.append(Transaction.type == transaction_type)
    
    if currency:
        try:
            currency_enum = CurrencyType(currency)
            conditions.append(Transaction.currency == currency_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的币种: {currency}")
    
    if ref_id:
        conditions.append(Transaction.ref_id.contains(ref_id))
    
    if start_date:
        conditions.append(Transaction.created_at >= start_date)
    
    if end_date:
        conditions.append(Transaction.created_at <= end_date)
    
    if min_amount:
        conditions.append(Transaction.amount >= min_amount)
    
    if max_amount:
        conditions.append(Transaction.amount <= max_amount)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count()).select_from(Transaction)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    # 分页查询
    query = query.order_by(Transaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # 获取用户信息
    user_ids = list(set(tx.user_id for tx in transactions))
    users_query = select(User).where(User.id.in_(user_ids))
    users_result = await db.execute(users_query)
    users = {user.id: user for user in users_result.scalars().all()}
    
    # 构建响应数据
    items = []
    for tx in transactions:
        user = users.get(tx.user_id)
        items.append(TransactionListItem(
            id=tx.id,
            user_id=tx.user_id,
            user_tg_id=user.tg_id if user else None,
            user_username=user.username if user else None,
            user_name=f"{user.first_name or ''} {user.last_name or ''}".strip() if user else None,
            type=tx.type,
            currency=tx.currency.value,
            amount=tx.amount,
            balance_before=tx.balance_before,
            balance_after=tx.balance_after,
            ref_id=tx.ref_id,
            note=tx.note,
            status=tx.status,
            created_at=tx.created_at,
        ))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{transaction_id}", response_model=TransactionDetail)
async def get_transaction_detail(
    transaction_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """获取交易详情"""
    query = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="交易不存在")
    
    # 获取用户信息
    user_query = select(User).where(User.id == transaction.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    return TransactionDetail(
        id=transaction.id,
        user_id=transaction.user_id,
        user_tg_id=user.tg_id if user else None,
        user_username=user.username if user else None,
        user_name=f"{user.first_name or ''} {user.last_name or ''}".strip() if user else None,
        type=transaction.type,
        currency=transaction.currency.value,
        amount=transaction.amount,
        balance_before=transaction.balance_before,
        balance_after=transaction.balance_after,
        ref_id=transaction.ref_id,
        note=transaction.note,
        status=transaction.status,
        created_at=transaction.created_at,
    )


@router.get("/stats/overview", response_model=TransactionStats)
async def get_transaction_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    currency: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """获取交易统计概览"""
    query = select(Transaction)
    
    conditions = []
    if start_date:
        conditions.append(Transaction.created_at >= start_date)
    if end_date:
        conditions.append(Transaction.created_at <= end_date)
    if currency:
        try:
            currency_enum = CurrencyType(currency)
            conditions.append(Transaction.currency == currency_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的币种: {currency}")
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    total_count = len(transactions)
    total_income = sum(float(tx.amount) for tx in transactions if float(tx.amount) > 0)
    total_expense = sum(abs(float(tx.amount)) for tx in transactions if float(tx.amount) < 0)
    net_amount = total_income - total_expense
    
    # 按币种统计
    by_currency = {}
    for currency_type in CurrencyType:
        currency_txs = [tx for tx in transactions if tx.currency == currency_type]
        by_currency[currency_type.value] = {
            "count": len(currency_txs),
            "income": sum(float(tx.amount) for tx in currency_txs if float(tx.amount) > 0),
            "expense": sum(abs(float(tx.amount)) for tx in currency_txs if float(tx.amount) < 0),
        }
    
    # 按类型统计
    by_type = {}
    type_list = ["deposit", "withdraw", "send", "receive", "checkin", "invite"]
    for tx_type in type_list:
        type_txs = [tx for tx in transactions if tx.type == tx_type]
        if type_txs:
            by_type[tx_type] = {
                "count": len(type_txs),
                "total": sum(float(tx.amount) for tx in type_txs),
            }
    
    return TransactionStats(
        total_count=total_count,
        total_income=Decimal(str(total_income)),
        total_expense=Decimal(str(total_expense)),
        net_amount=Decimal(str(net_amount)),
        by_currency=by_currency,
        by_type=by_type,
    )


@router.get("/stats/trend")
async def get_transaction_trend(
    days: int = Query(30, ge=1, le=365),
    currency: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """获取交易趋势数据"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    query = select(
        func.date(Transaction.created_at).label('date'),
        func.count(Transaction.id).label('count'),
        func.sum(
            func.case(
                (Transaction.amount > 0, Transaction.amount),
                else_=0
            )
        ).label('income'),
        func.sum(
            func.case(
                (Transaction.amount < 0, func.abs(Transaction.amount)),
                else_=0
            )
        ).label('expense'),
    ).where(
        Transaction.created_at >= start_date,
        Transaction.created_at <= end_date,
    )
    
    if currency:
        try:
            currency_enum = CurrencyType(currency)
            query = query.where(Transaction.currency == currency_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的币种: {currency}")
    
    query = query.group_by(
        func.date(Transaction.created_at)
    ).order_by(
        func.date(Transaction.created_at)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    dates = []
    counts = []
    incomes = []
    expenses = []
    
    for row in rows:
        dates.append(row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date))
        counts.append(row.count)
        incomes.append(float(row.income) if row.income else 0)
        expenses.append(float(row.expense) if row.expense else 0)
    
    return {
        "dates": dates,
        "counts": counts,
        "incomes": incomes,
        "expenses": expenses,
    }


class ApproveRequest(BaseModel):
    """審核請求"""
    note: Optional[str] = None  # 審核備註


class RejectRequest(BaseModel):
    """拒絕請求"""
    reason: str  # 拒絕原因


@router.get("/pending", response_model=dict)
async def get_pending_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    transaction_type: Optional[str] = Query(None),  # deposit 或 withdraw
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """獲取待審核的交易列表"""
    query = select(Transaction).where(Transaction.status == "pending")
    
    if transaction_type:
        query = query.where(Transaction.type == transaction_type)
    
    # 只顯示充值或提現
    query = query.where(Transaction.type.in_(["deposit", "withdraw"]))
    
    # 獲取總數
    count_query = select(func.count()).select_from(Transaction).where(
        Transaction.status == "pending",
        Transaction.type.in_(["deposit", "withdraw"])
    )
    if transaction_type:
        count_query = count_query.where(Transaction.type == transaction_type)
    total = await db.scalar(count_query)
    
    # 分頁查詢
    query = query.order_by(Transaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # 獲取用戶信息
    user_ids = list(set(tx.user_id for tx in transactions))
    users_query = select(User).where(User.id.in_(user_ids))
    users_result = await db.execute(users_query)
    users = {user.id: user for user in users_result.scalars().all()}
    
    # 構建響應數據
    items = []
    for tx in transactions:
        user = users.get(tx.user_id)
        items.append(TransactionListItem(
            id=tx.id,
            user_id=tx.user_id,
            user_tg_id=user.tg_id if user else None,
            user_username=user.username if user else None,
            user_name=f"{user.first_name or ''} {user.last_name or ''}".strip() if user else None,
            type=tx.type,
            currency=tx.currency.value,
            amount=tx.amount,
            balance_before=tx.balance_before,
            balance_after=tx.balance_after,
            ref_id=tx.ref_id,
            note=tx.note,
            status=tx.status,
            created_at=tx.created_at,
        ))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/{transaction_id}/approve")
async def approve_transaction(
    transaction_id: int,
    request: Optional[ApproveRequest] = Body(None),
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """批准交易（充值或提現）"""
    if request is None:
        request = ApproveRequest()
    
    # 查找交易
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="交易不存在")
    
    if transaction.status != "pending":
        raise HTTPException(status_code=400, detail=f"交易狀態為 {transaction.status}，無法審核")
    
    # 查找用戶
    result = await db.execute(select(User).where(User.id == transaction.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    balance_field = f"balance_{transaction.currency.value}"
    current_balance = getattr(user, balance_field, 0) or Decimal(0)
    
    if transaction.type == "deposit":
        # 批准充值：增加用戶餘額
        new_balance = current_balance + transaction.amount
        setattr(user, balance_field, new_balance)
        transaction.balance_after = new_balance
        transaction.status = "completed"
        
        if request.note:
            transaction.note = f"{transaction.note or ''} [審核通過: {request.note}]".strip()
        
        logger.info(
            f"Deposit approved: tx_id={transaction_id}, user_id={user.id}, "
            f"amount={transaction.amount}, currency={transaction.currency.value}, "
            f"admin_id={current_admin.get('id')}"
        )
        
    elif transaction.type == "withdraw":
        # 批准提現：餘額已經在申請時凍結，這裡只需要標記為完成
        # 實際轉賬應該由管理員手動執行或通過支付網關自動執行
        transaction.status = "completed"
        
        if request.note:
            transaction.note = f"{transaction.note or ''} [審核通過: {request.note}]".strip()
        
        logger.info(
            f"Withdraw approved: tx_id={transaction_id}, user_id={user.id}, "
            f"amount={transaction.amount}, currency={transaction.currency.value}, "
            f"address={transaction.ref_id}, admin_id={current_admin.get('id')}"
        )
    else:
        raise HTTPException(status_code=400, detail="只能審核充值或提現交易")
    
    await db.commit()
    
    return {
        "success": True,
        "message": "交易已批准",
        "transaction_id": transaction_id,
        "status": transaction.status,
    }


@router.post("/{transaction_id}/reject")
async def reject_transaction(
    transaction_id: int,
    request: RejectRequest,
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """拒絕交易（充值或提現）"""
    # 查找交易
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="交易不存在")
    
    if transaction.status != "pending":
        raise HTTPException(status_code=400, detail=f"交易狀態為 {transaction.status}，無法審核")
    
    # 查找用戶
    result = await db.execute(select(User).where(User.id == transaction.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    balance_field = f"balance_{transaction.currency.value}"
    current_balance = getattr(user, balance_field, 0) or Decimal(0)
    
    if transaction.type == "deposit":
        # 拒絕充值：不更新餘額，只標記為拒絕
        transaction.status = "rejected"
        transaction.note = f"{transaction.note or ''} [審核拒絕: {request.reason}]".strip()
        
        logger.info(
            f"Deposit rejected: tx_id={transaction_id}, user_id={user.id}, "
            f"amount={transaction.amount}, currency={transaction.currency.value}, "
            f"reason={request.reason}, admin_id={current_admin.get('id')}"
        )
        
    elif transaction.type == "withdraw":
        # 拒絕提現：退回凍結的餘額
        new_balance = current_balance + transaction.amount  # 退回凍結的金額
        setattr(user, balance_field, new_balance)
        transaction.balance_after = new_balance
        transaction.status = "rejected"
        transaction.note = f"{transaction.note or ''} [審核拒絕: {request.reason}]".strip()
        
        logger.info(
            f"Withdraw rejected: tx_id={transaction_id}, user_id={user.id}, "
            f"amount={transaction.amount}, currency={transaction.currency.value}, "
            f"reason={request.reason}, admin_id={current_admin.get('id')}"
        )
    else:
        raise HTTPException(status_code=400, detail="只能審核充值或提現交易")
    
    await db.commit()
    
    return {
        "success": True,
        "message": "交易已拒絕",
        "transaction_id": transaction_id,
        "status": transaction.status,
    }


# ========================================
# 審核統計和批量操作
# ========================================

class BatchApproveRequest(BaseModel):
    """批量批准請求"""
    transaction_ids: List[int]
    note: Optional[str] = None


class BatchRejectRequest(BaseModel):
    """批量拒絕請求"""
    transaction_ids: List[int]
    reason: str


@router.get("/pending/stats")
async def get_pending_stats(
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """獲取待審核統計"""
    # 充值統計
    deposit_result = await db.execute(
        select(
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.status == "pending",
            Transaction.type == "deposit"
        )
    )
    deposit_stats = deposit_result.one()
    
    # 提現統計
    withdraw_result = await db.execute(
        select(
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.status == "pending",
            Transaction.type == "withdraw"
        )
    )
    withdraw_stats = withdraw_result.one()
    
    # 按幣種統計
    currency_stats = {}
    for currency in ['usdt', 'ton', 'stars', 'points']:
        try:
            currency_type = CurrencyType(currency)
            result = await db.execute(
                select(
                    func.count(Transaction.id).label('count'),
                    func.sum(Transaction.amount).label('total')
                ).where(
                    Transaction.status == "pending",
                    Transaction.type.in_(["deposit", "withdraw"]),
                    Transaction.currency == currency_type
                )
            )
            stats = result.one()
            currency_stats[currency] = {
                "count": stats.count or 0,
                "total": float(stats.total or 0)
            }
        except:
            currency_stats[currency] = {"count": 0, "total": 0}
    
    return {
        "deposit": {
            "count": deposit_stats.count or 0,
            "total": float(deposit_stats.total or 0)
        },
        "withdraw": {
            "count": withdraw_stats.count or 0,
            "total": float(withdraw_stats.total or 0)
        },
        "by_currency": currency_stats,
        "total_pending": (deposit_stats.count or 0) + (withdraw_stats.count or 0)
    }


@router.post("/batch/approve")
async def batch_approve_transactions(
    request: BatchApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """批量批准交易"""
    if len(request.transaction_ids) > 100:
        raise HTTPException(status_code=400, detail="一次最多批量處理 100 筆交易")
    
    results = {"success": [], "failed": []}
    
    for tx_id in request.transaction_ids:
        try:
            result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                results["failed"].append({"id": tx_id, "reason": "交易不存在"})
                continue
            
            if transaction.status != "pending":
                results["failed"].append({"id": tx_id, "reason": f"狀態為 {transaction.status}"})
                continue
            
            if transaction.type not in ["deposit", "withdraw"]:
                results["failed"].append({"id": tx_id, "reason": "非充值/提現交易"})
                continue
            
            # 獲取用戶
            user_result = await db.execute(select(User).where(User.id == transaction.user_id))
            user = user_result.scalar_one_or_none()
            
            if not user:
                results["failed"].append({"id": tx_id, "reason": "用戶不存在"})
                continue
            
            balance_field = f"balance_{transaction.currency.value}"
            current_balance = getattr(user, balance_field, 0) or Decimal(0)
            
            if transaction.type == "deposit":
                new_balance = current_balance + transaction.amount
                setattr(user, balance_field, new_balance)
                transaction.balance_after = new_balance
            
            transaction.status = "completed"
            if request.note:
                transaction.note = f"{transaction.note or ''} [批量審核通過: {request.note}]".strip()
            
            results["success"].append(tx_id)
            
        except Exception as e:
            results["failed"].append({"id": tx_id, "reason": str(e)})
    
    await db.commit()
    
    logger.info(
        f"Batch approve: success={len(results['success'])}, failed={len(results['failed'])}, "
        f"admin_id={current_admin.get('id')}"
    )
    
    return {
        "success": True,
        "approved_count": len(results["success"]),
        "failed_count": len(results["failed"]),
        "results": results
    }


@router.post("/batch/reject")
async def batch_reject_transactions(
    request: BatchRejectRequest,
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """批量拒絕交易"""
    if len(request.transaction_ids) > 100:
        raise HTTPException(status_code=400, detail="一次最多批量處理 100 筆交易")
    
    results = {"success": [], "failed": []}
    
    for tx_id in request.transaction_ids:
        try:
            result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                results["failed"].append({"id": tx_id, "reason": "交易不存在"})
                continue
            
            if transaction.status != "pending":
                results["failed"].append({"id": tx_id, "reason": f"狀態為 {transaction.status}"})
                continue
            
            if transaction.type not in ["deposit", "withdraw"]:
                results["failed"].append({"id": tx_id, "reason": "非充值/提現交易"})
                continue
            
            # 獲取用戶
            user_result = await db.execute(select(User).where(User.id == transaction.user_id))
            user = user_result.scalar_one_or_none()
            
            if not user:
                results["failed"].append({"id": tx_id, "reason": "用戶不存在"})
                continue
            
            # 提現拒絕需要退款
            if transaction.type == "withdraw":
                balance_field = f"balance_{transaction.currency.value}"
                current_balance = getattr(user, balance_field, 0) or Decimal(0)
                new_balance = current_balance + transaction.amount
                setattr(user, balance_field, new_balance)
                transaction.balance_after = new_balance
            
            transaction.status = "rejected"
            transaction.note = f"{transaction.note or ''} [批量審核拒絕: {request.reason}]".strip()
            
            results["success"].append(tx_id)
            
        except Exception as e:
            results["failed"].append({"id": tx_id, "reason": str(e)})
    
    await db.commit()
    
    logger.info(
        f"Batch reject: success={len(results['success'])}, failed={len(results['failed'])}, "
        f"reason={request.reason}, admin_id={current_admin.get('id')}"
    )
    
    return {
        "success": True,
        "rejected_count": len(results["success"]),
        "failed_count": len(results["failed"]),
        "results": results
    }


@router.get("/audit-log")
async def get_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None, description="approve/reject"),
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """獲取審核日誌"""
    # 查詢已審核的交易（非 pending 狀態的充值/提現）
    conditions = [
        Transaction.type.in_(["deposit", "withdraw"]),
        Transaction.status.in_(["completed", "rejected"])
    ]
    
    if action == "approve":
        conditions.append(Transaction.status == "completed")
    elif action == "reject":
        conditions.append(Transaction.status == "rejected")
    
    # 統計總數
    count_query = select(func.count(Transaction.id)).where(*conditions)
    total = (await db.execute(count_query)).scalar() or 0
    
    # 查詢數據
    query = (
        select(Transaction)
        .where(*conditions)
        .order_by(Transaction.updated_at.desc() if hasattr(Transaction, 'updated_at') else Transaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # 獲取用戶信息
    user_ids = list(set(tx.user_id for tx in transactions))
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {u.id: u for u in users_result.scalars().all()}
    
    items = []
    for tx in transactions:
        user = users.get(tx.user_id)
        items.append({
            "id": tx.id,
            "user_id": tx.user_id,
            "user_tg_id": user.tg_id if user else None,
            "user_name": f"{user.first_name or ''} {user.last_name or ''}".strip() if user else None,
            "type": tx.type,
            "currency": tx.currency.value,
            "amount": float(tx.amount),
            "status": tx.status,
            "note": tx.note,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }

