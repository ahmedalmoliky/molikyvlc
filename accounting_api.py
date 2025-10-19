"""
واجهة برمجة التطبيقات للنظام المحاسبي
Accounting System API
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import uuid
import json

from accounting_models import (
    Account, AccountType, JournalEntry, JournalEntryLine, EntryStatus,
    Invoice, InvoiceItem, InvoiceStatus, Customer, Supplier,
    InventoryItem, Employee, PayrollEntry, AuditLog, FinancialReport,
    AccountingValidator, AccountingCalculator
)
from accounting_database import get_session_factory, create_database_engine

# إعداد التطبيق
app = FastAPI(
    title="النظام المحاسبي المتطور",
    description="نظام محاسبي شامل لإدارة العمليات المالية",
    version="1.0.0"
)

security = HTTPBearer()

# إعداد قاعدة البيانات
DATABASE_URL = "postgresql://username:password@localhost/accounting_db"
engine = create_database_engine(DATABASE_URL)
SessionLocal = get_session_factory(engine)

def get_db():
    """الحصول على جلسة قاعدة البيانات"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """التحقق من المستخدم الحالي"""
    # هنا يجب تنفيذ منطق التحقق من المستخدم
    # للتبسيط، سنعود بمستخدم افتراضي
    return {"user_id": str(uuid.uuid4()), "username": "admin"}

# ==================== واجهات الحسابات ====================

@app.post("/accounts/", response_model=dict)
async def create_account(
    code: str,
    name: str,
    name_ar: str,
    type: AccountType,
    parent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """إنشاء حساب جديد"""
    try:
        account = Account(
            id=uuid.uuid4(),
            code=code,
            name=name,
            name_ar=name_ar,
            type=type,
            parent_id=uuid.UUID(parent_id) if parent_id else None
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return {
            "success": True,
            "message": "تم إنشاء الحساب بنجاح",
            "account_id": str(account.id)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/accounts/", response_model=List[dict])
async def get_accounts(
    type: Optional[AccountType] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """الحصول على قائمة الحسابات"""
    query = db.query(Account)
    
    if type:
        query = query.filter(Account.type == type)
    if is_active is not None:
        query = query.filter(Account.is_active == is_active)
    
    accounts = query.all()
    return [
        {
            "id": str(account.id),
            "code": account.code,
            "name": account.name,
            "name_ar": account.name_ar,
            "type": account.type.value,
            "balance": float(account.balance),
            "is_active": account.is_active
        }
        for account in accounts
    ]

@app.get("/accounts/{account_id}/balance")
async def get_account_balance(
    account_id: str,
    db: Session = Depends(get_db)
):
    """الحصول على رصيد الحساب"""
    account = db.query(Account).filter(Account.id == uuid.UUID(account_id)).first()
    if not account:
        raise HTTPException(status_code=404, detail="الحساب غير موجود")
    
    # حساب الرصيد من القيود المحاسبية
    balance = AccountingCalculator.calculate_account_balance(
        uuid.UUID(account_id), 
        db.query(JournalEntry).filter(JournalEntry.status == EntryStatus.POSTED).all()
    )
    
    return {
        "account_id": account_id,
        "account_name": account.name_ar,
        "balance": float(balance)
    }

# ==================== واجهات القيود المحاسبية ====================

@app.post("/journal-entries/", response_model=dict)
async def create_journal_entry(
    date: date,
    reference: str,
    description: str,
    entries: List[dict],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """إنشاء قيد محاسبي جديد"""
    try:
        # إنشاء أسطر القيد
        journal_lines = []
        for entry_data in entries:
            line = JournalEntryLine(
                id=uuid.uuid4(),
                account_id=uuid.UUID(entry_data["account_id"]),
                debit=Decimal(str(entry_data["debit"])),
                credit=Decimal(str(entry_data["credit"])),
                description=entry_data.get("description", ""),
                reference=entry_data.get("reference")
            )
            journal_lines.append(line)
        
        # إنشاء القيد
        journal_entry = JournalEntry(
            id=uuid.uuid4(),
            date=date,
            reference=reference,
            description=description,
            entries=journal_lines,
            status=EntryStatus.DRAFT,
            created_by=uuid.UUID(current_user["user_id"])
        )
        
        # التحقق من صحة القيد
        errors = AccountingValidator.validate_journal_entry(journal_entry)
        if errors:
            raise HTTPException(status_code=400, detail={"errors": errors})
        
        db.add(journal_entry)
        db.commit()
        db.refresh(journal_entry)
        
        return {
            "success": True,
            "message": "تم إنشاء القيد بنجاح",
            "journal_entry_id": str(journal_entry.id)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/journal-entries/{entry_id}/post")
async def post_journal_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """ترحيل القيد المحاسبي"""
    entry = db.query(JournalEntry).filter(JournalEntry.id == uuid.UUID(entry_id)).first()
    if not entry:
        raise HTTPException(status_code=404, detail="القيد غير موجود")
    
    if entry.status != EntryStatus.DRAFT:
        raise HTTPException(status_code=400, detail="القيد غير قابل للترحيل")
    
    # التحقق من صحة القيد
    errors = AccountingValidator.validate_journal_entry(entry)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    try:
        entry.status = EntryStatus.POSTED
        entry.posted_at = datetime.now()
        db.commit()
        
        return {
            "success": True,
            "message": "تم ترحيل القيد بنجاح"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ==================== واجهات الفواتير ====================

@app.post("/invoices/", response_model=dict)
async def create_invoice(
    number: str,
    date: date,
    due_date: date,
    customer_id: str,
    items: List[dict],
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """إنشاء فاتورة جديدة"""
    try:
        # إنشاء عناصر الفاتورة
        invoice_items = []
        for item_data in items:
            item = InvoiceItem(
                id=uuid.uuid4(),
                description=item_data["description"],
                quantity=Decimal(str(item_data["quantity"])),
                unit_price=Decimal(str(item_data["unit_price"])),
                tax_rate=Decimal(str(item_data.get("tax_rate", 0.15)))
            )
            invoice_items.append(item)
        
        # إنشاء الفاتورة
        invoice = Invoice(
            id=uuid.uuid4(),
            number=number,
            date=date,
            due_date=due_date,
            customer_id=uuid.UUID(customer_id),
            items=invoice_items,
            subtotal=Decimal('0.00'),  # سيتم حسابه تلقائياً
            tax_amount=Decimal('0.00'),  # سيتم حسابه تلقائياً
            total=Decimal('0.00'),  # سيتم حسابه تلقائياً
            status=InvoiceStatus.DRAFT,
            notes=notes,
            created_by=uuid.UUID(current_user["user_id"])
        )
        
        # التحقق من صحة الفاتورة
        errors = AccountingValidator.validate_invoice(invoice)
        if errors:
            raise HTTPException(status_code=400, detail={"errors": errors})
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        return {
            "success": True,
            "message": "تم إنشاء الفاتورة بنجاح",
            "invoice_id": str(invoice.id),
            "total": float(invoice.total)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/invoices/", response_model=List[dict])
async def get_invoices(
    status: Optional[InvoiceStatus] = None,
    customer_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """الحصول على قائمة الفواتير"""
    query = db.query(Invoice)
    
    if status:
        query = query.filter(Invoice.status == status)
    if customer_id:
        query = query.filter(Invoice.customer_id == uuid.UUID(customer_id))
    
    invoices = query.all()
    return [
        {
            "id": str(invoice.id),
            "number": invoice.number,
            "date": invoice.date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "customer_id": str(invoice.customer_id),
            "total": float(invoice.total),
            "status": invoice.status.value
        }
        for invoice in invoices
    ]

# ==================== واجهات التقارير ====================

@app.get("/reports/trial-balance")
async def get_trial_balance(
    as_of_date: date,
    db: Session = Depends(get_db)
):
    """تقرير ميزان المراجعة"""
    accounts = db.query(Account).filter(Account.is_active == True).all()
    trial_balance = []
    
    for account in accounts:
        balance = AccountingCalculator.calculate_account_balance(
            account.id,
            db.query(JournalEntry).filter(
                JournalEntry.status == EntryStatus.POSTED,
                JournalEntry.date <= as_of_date
            ).all()
        )
        
        if balance != 0:  # إظهار الحسابات التي لها رصيد فقط
            trial_balance.append({
                "account_code": account.code,
                "account_name": account.name_ar,
                "debit": float(balance) if balance > 0 else 0,
                "credit": float(-balance) if balance < 0 else 0
            })
    
    return {
        "as_of_date": as_of_date.isoformat(),
        "trial_balance": trial_balance
    }

@app.get("/reports/profit-loss")
async def get_profit_loss(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """تقرير قائمة الدخل"""
    # حساب الإيرادات
    revenue_accounts = db.query(Account).filter(
        Account.type == AccountType.REVENUE,
        Account.is_active == True
    ).all()
    
    total_revenue = Decimal('0.00')
    for account in revenue_accounts:
        balance = AccountingCalculator.calculate_account_balance(
            account.id,
            db.query(JournalEntry).filter(
                JournalEntry.status == EntryStatus.POSTED,
                JournalEntry.date >= start_date,
                JournalEntry.date <= end_date
            ).all()
        )
        total_revenue += balance
    
    # حساب المصروفات
    expense_accounts = db.query(Account).filter(
        Account.type == AccountType.EXPENSE,
        Account.is_active == True
    ).all()
    
    total_expenses = Decimal('0.00')
    for account in expense_accounts:
        balance = AccountingCalculator.calculate_account_balance(
            account.id,
            db.query(JournalEntry).filter(
                JournalEntry.status == EntryStatus.POSTED,
                JournalEntry.date >= start_date,
                JournalEntry.date <= end_date
            ).all()
        )
        total_expenses += balance
    
    net_profit = total_revenue - total_expenses
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "revenue": float(total_revenue),
        "expenses": float(total_expenses),
        "net_profit": float(net_profit)
    }

# ==================== واجهات المراجعة ====================

@app.get("/audit-logs/", response_model=List[dict])
async def get_audit_logs(
    table_name: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """الحصول على سجل المراجعة"""
    query = db.query(AuditLog)
    
    if table_name:
        query = query.filter(AuditLog.table_name == table_name)
    if user_id:
        query = query.filter(AuditLog.user_id == uuid.UUID(user_id))
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id),
            "action": log.action,
            "table_name": log.table_name,
            "record_id": str(log.record_id),
            "timestamp": log.timestamp.isoformat(),
            "ip_address": log.ip_address
        }
        for log in logs
    ]

# ==================== واجهات الصحة ====================

@app.get("/health")
async def health_check():
    """فحص صحة النظام"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)