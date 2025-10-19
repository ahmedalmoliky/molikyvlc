"""
نماذج النظام المحاسبي المتطور
Advanced Accounting System Models
"""

from decimal import Decimal
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID, uuid4


class AccountType(Enum):
    """أنواع الحسابات المحاسبية"""
    ASSET = "asset"  # أصل
    LIABILITY = "liability"  # خصم
    EQUITY = "equity"  # حقوق ملكية
    REVENUE = "revenue"  # إيراد
    EXPENSE = "expense"  # مصروف


class EntryStatus(Enum):
    """حالات القيود المحاسبية"""
    DRAFT = "draft"  # مسودة
    POSTED = "posted"  # مرتكز
    REVERSED = "reversed"  # معكوس


class InvoiceStatus(Enum):
    """حالات الفواتير"""
    DRAFT = "draft"  # مسودة
    SENT = "sent"  # مرسلة
    PAID = "paid"  # مدفوعة
    OVERDUE = "overdue"  # متأخرة
    CANCELLED = "cancelled"  # ملغاة


@dataclass
class Account:
    """نموذج الحساب المحاسبي"""
    id: UUID
    code: str
    name: str
    name_ar: str
    type: AccountType
    parent_id: Optional[UUID] = None
    balance: Decimal = Decimal('0.00')
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class JournalEntryLine:
    """سطر في القيد المحاسبي"""
    id: UUID
    account_id: UUID
    debit: Decimal
    credit: Decimal
    description: str
    reference: Optional[str] = None


@dataclass
class JournalEntry:
    """القيد المحاسبي"""
    id: UUID
    date: date
    reference: str
    description: str
    entries: List[JournalEntryLine]
    status: EntryStatus
    created_by: UUID
    created_at: datetime = None
    posted_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def is_balanced(self) -> bool:
        """التحقق من توازن القيد (مبدأ القيد المزدوج)"""
        total_debit = sum(entry.debit for entry in self.entries)
        total_credit = sum(entry.credit for entry in self.entries)
        return total_debit == total_credit


@dataclass
class Customer:
    """نموذج العميل"""
    id: UUID
    name: str
    name_ar: str
    email: str
    phone: str
    address: str
    tax_number: Optional[str] = None
    credit_limit: Decimal = Decimal('0.00')
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Supplier:
    """نموذج المورد"""
    id: UUID
    name: str
    name_ar: str
    email: str
    phone: str
    address: str
    tax_number: Optional[str] = None
    payment_terms: int = 30  # أيام الدفع
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class InvoiceItem:
    """عنصر الفاتورة"""
    id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    tax_rate: Decimal = Decimal('0.15')  # 15% ضريبة القيمة المضافة
    tax_amount: Decimal = Decimal('0.00')
    
    def __post_init__(self):
        self.total = self.quantity * self.unit_price
        self.tax_amount = self.total * self.tax_rate


@dataclass
class Invoice:
    """نموذج الفاتورة"""
    id: UUID
    number: str
    date: date
    due_date: date
    customer_id: UUID
    items: List[InvoiceItem]
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    status: InvoiceStatus
    notes: Optional[str] = None
    created_by: UUID = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.subtotal = sum(item.total for item in self.items)
        self.tax_amount = sum(item.tax_amount for item in self.items)
        self.total = self.subtotal + self.tax_amount


@dataclass
class InventoryItem:
    """عنصر المخزون"""
    id: UUID
    code: str
    name: str
    name_ar: str
    description: str
    unit: str  # وحدة القياس
    cost_price: Decimal
    selling_price: Decimal
    quantity_on_hand: Decimal
    minimum_quantity: Decimal
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Employee:
    """نموذج الموظف"""
    id: UUID
    employee_number: str
    name: str
    name_ar: str
    email: str
    phone: str
    position: str
    department: str
    hire_date: date
    salary: Decimal
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class PayrollEntry:
    """قيد الرواتب"""
    id: UUID
    employee_id: UUID
    period_start: date
    period_end: date
    basic_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    net_salary: Decimal
    status: EntryStatus
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.net_salary = self.basic_salary + self.allowances - self.deductions


@dataclass
class AuditLog:
    """سجل المراجعة"""
    id: UUID
    user_id: UUID
    action: str
    table_name: str
    record_id: UUID
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    timestamp: datetime
    ip_address: str
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class FinancialReport:
    """التقرير المالي"""
    id: UUID
    name: str
    name_ar: str
    report_type: str
    period_start: date
    period_end: date
    data: Dict[str, Any]
    generated_by: UUID
    generated_at: datetime = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()


# فئات مساعدة للعمليات المحاسبية
class AccountingValidator:
    """فئة التحقق من العمليات المحاسبية"""
    
    @staticmethod
    def validate_journal_entry(entry: JournalEntry) -> List[str]:
        """التحقق من صحة القيد المحاسبي"""
        errors = []
        
        if not entry.is_balanced():
            errors.append("القيد غير متوازن - مجموع المدين لا يساوي مجموع الدائن")
        
        if not entry.entries:
            errors.append("القيد يجب أن يحتوي على سطر واحد على الأقل")
        
        for line in entry.entries:
            if line.debit < 0 or line.credit < 0:
                errors.append("المبالغ المدينة والدائنة يجب أن تكون موجبة")
            
            if line.debit > 0 and line.credit > 0:
                errors.append("السطر يجب أن يكون إما مدين أو دائن وليس كلاهما")
        
        return errors
    
    @staticmethod
    def validate_invoice(invoice: Invoice) -> List[str]:
        """التحقق من صحة الفاتورة"""
        errors = []
        
        if not invoice.items:
            errors.append("الفاتورة يجب أن تحتوي على عنصر واحد على الأقل")
        
        if invoice.due_date < invoice.date:
            errors.append("تاريخ الاستحقاق يجب أن يكون بعد تاريخ الفاتورة")
        
        for item in invoice.items:
            if item.quantity <= 0:
                errors.append("الكمية يجب أن تكون أكبر من صفر")
            
            if item.unit_price < 0:
                errors.append("سعر الوحدة يجب أن يكون موجب")
        
        return errors


class AccountingCalculator:
    """فئة الحسابات المحاسبية"""
    
    @staticmethod
    def calculate_account_balance(account_id: UUID, entries: List[JournalEntry]) -> Decimal:
        """حساب رصيد الحساب"""
        balance = Decimal('0.00')
        
        for entry in entries:
            if entry.status == EntryStatus.POSTED:
                for line in entry.entries:
                    if line.account_id == account_id:
                        balance += line.debit - line.credit
        
        return balance
    
    @staticmethod
    def calculate_inventory_value(items: List[InventoryItem]) -> Decimal:
        """حساب قيمة المخزون"""
        total_value = Decimal('0.00')
        
        for item in items:
            if item.is_active:
                total_value += item.quantity_on_hand * item.cost_price
        
        return total_value