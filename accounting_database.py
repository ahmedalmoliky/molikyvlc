"""
قاعدة البيانات للنظام المحاسبي
Accounting System Database Schema
"""

from sqlalchemy import create_engine, Column, String, Integer, Decimal, Boolean, DateTime, Date, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

Base = declarative_base()

class AccountType(Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

class EntryStatus(Enum):
    DRAFT = "draft"
    POSTED = "posted"
    REVERSED = "reversed"

class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class Account(Base):
    """جدول الحسابات المحاسبية"""
    __tablename__ = 'accounts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    type = Column(SQLEnum(AccountType), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=True)
    balance = Column(Decimal(15, 2), default=0.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    parent = relationship("Account", remote_side=[id])
    children = relationship("Account", backref="parent_account")
    journal_entry_lines = relationship("JournalEntryLine", back_populates="account")

class JournalEntry(Base):
    """جدول القيود المحاسبية"""
    __tablename__ = 'journal_entries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    reference = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(EntryStatus), default=EntryStatus.DRAFT)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)
    
    # العلاقات
    entries = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")

class JournalEntryLine(Base):
    """جدول أسطر القيود المحاسبية"""
    __tablename__ = 'journal_entry_lines'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey('journal_entries.id'), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=False)
    debit = Column(Decimal(15, 2), default=0.00)
    credit = Column(Decimal(15, 2), default=0.00)
    description = Column(Text, nullable=True)
    reference = Column(String(50), nullable=True)
    
    # العلاقات
    journal_entry = relationship("JournalEntry", back_populates="entries")
    account = relationship("Account", back_populates="journal_entry_lines")

class Customer(Base):
    """جدول العملاء"""
    __tablename__ = 'customers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    tax_number = Column(String(20), nullable=True)
    credit_limit = Column(Decimal(15, 2), default=0.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    invoices = relationship("Invoice", back_populates="customer")

class Supplier(Base):
    """جدول الموردين"""
    __tablename__ = 'suppliers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    tax_number = Column(String(20), nullable=True)
    payment_terms = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Invoice(Base):
    """جدول الفواتير"""
    __tablename__ = 'invoices'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(String(50), unique=True, nullable=False)
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    subtotal = Column(Decimal(15, 2), nullable=False)
    tax_amount = Column(Decimal(15, 2), nullable=False)
    total = Column(Decimal(15, 2), nullable=False)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    """جدول عناصر الفواتير"""
    __tablename__ = 'invoice_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id'), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Decimal(10, 3), nullable=False)
    unit_price = Column(Decimal(15, 2), nullable=False)
    total = Column(Decimal(15, 2), nullable=False)
    tax_rate = Column(Decimal(5, 4), default=0.15)
    tax_amount = Column(Decimal(15, 2), default=0.00)
    
    # العلاقات
    invoice = relationship("Invoice", back_populates="items")

class InventoryItem(Base):
    """جدول عناصر المخزون"""
    __tablename__ = 'inventory_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(20), nullable=False)
    cost_price = Column(Decimal(15, 2), nullable=False)
    selling_price = Column(Decimal(15, 2), nullable=False)
    quantity_on_hand = Column(Decimal(10, 3), default=0.000)
    minimum_quantity = Column(Decimal(10, 3), default=0.000)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Employee(Base):
    """جدول الموظفين"""
    __tablename__ = 'employees'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_number = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    position = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    hire_date = Column(Date, nullable=False)
    salary = Column(Decimal(15, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    payroll_entries = relationship("PayrollEntry", back_populates="employee")

class PayrollEntry(Base):
    """جدول قيود الرواتب"""
    __tablename__ = 'payroll_entries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    basic_salary = Column(Decimal(15, 2), nullable=False)
    allowances = Column(Decimal(15, 2), default=0.00)
    deductions = Column(Decimal(15, 2), default=0.00)
    net_salary = Column(Decimal(15, 2), nullable=False)
    status = Column(SQLEnum(EntryStatus), default=EntryStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    employee = relationship("Employee", back_populates="payroll_entries")

class AuditLog(Base):
    """جدول سجل المراجعة"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False)
    table_name = Column(String(50), nullable=False)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=False)

class FinancialReport(Base):
    """جدول التقارير المالية"""
    __tablename__ = 'financial_reports'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    report_type = Column(String(50), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    data = Column(Text, nullable=False)  # JSON data
    generated_by = Column(UUID(as_uuid=True), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

# إعداد قاعدة البيانات
def create_database_engine(database_url: str):
    """إنشاء محرك قاعدة البيانات"""
    engine = create_engine(database_url, echo=True)
    return engine

def create_tables(engine):
    """إنشاء الجداول في قاعدة البيانات"""
    Base.metadata.create_all(engine)

def get_session_factory(engine):
    """إنشاء مصنع الجلسات"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

# مثال على الاستخدام
if __name__ == "__main__":
    # إعداد قاعدة البيانات
    DATABASE_URL = "postgresql://username:password@localhost/accounting_db"
    engine = create_database_engine(DATABASE_URL)
    create_tables(engine)
    
    print("تم إنشاء قاعدة البيانات بنجاح!")