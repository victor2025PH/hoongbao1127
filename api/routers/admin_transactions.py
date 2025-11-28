"""
交易管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
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

