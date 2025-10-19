-- إعداد قاعدة البيانات للنظام المحاسبي المتطور
-- Database Initialization for Advanced Accounting System

-- إنشاء أنواع البيانات المخصصة
CREATE TYPE account_type_enum AS ENUM ('asset', 'liability', 'equity', 'revenue', 'expense');
CREATE TYPE entry_status_enum AS ENUM ('draft', 'posted', 'reversed');
CREATE TYPE invoice_status_enum AS ENUM ('draft', 'sent', 'paid', 'overdue', 'cancelled');

-- إنشاء جداول النظام الأساسية
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    type account_type_enum NOT NULL,
    parent_id UUID REFERENCES accounts(id),
    balance DECIMAL(15,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    reference VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    status entry_status_enum DEFAULT 'draft',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS journal_entry_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id UUID REFERENCES accounts(id),
    debit DECIMAL(15,2) DEFAULT 0.00,
    credit DECIMAL(15,2) DEFAULT 0.00,
    description TEXT,
    reference VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    tax_number VARCHAR(20),
    credit_limit DECIMAL(15,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    tax_number VARCHAR(20),
    payment_terms INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number VARCHAR(50) UNIQUE NOT NULL,
    date DATE NOT NULL,
    due_date DATE NOT NULL,
    customer_id UUID REFERENCES customers(id),
    subtotal DECIMAL(15,2) NOT NULL,
    tax_amount DECIMAL(15,2) NOT NULL,
    total DECIMAL(15,2) NOT NULL,
    status invoice_status_enum DEFAULT 'draft',
    notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    total DECIMAL(15,2) NOT NULL,
    tax_rate DECIMAL(5,4) DEFAULT 0.15,
    tax_amount DECIMAL(15,2) DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    description TEXT,
    unit VARCHAR(20) NOT NULL,
    cost_price DECIMAL(15,2) NOT NULL,
    selling_price DECIMAL(15,2) NOT NULL,
    quantity_on_hand DECIMAL(10,3) DEFAULT 0.000,
    minimum_quantity DECIMAL(10,3) DEFAULT 0.000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    position VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    salary DECIMAL(15,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payroll_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID REFERENCES employees(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    basic_salary DECIMAL(15,2) NOT NULL,
    allowances DECIMAL(15,2) DEFAULT 0.00,
    deductions DECIMAL(15,2) DEFAULT 0.00,
    net_salary DECIMAL(15,2) NOT NULL,
    status entry_status_enum DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    old_values TEXT,
    new_values TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) NOT NULL
);

CREATE TABLE IF NOT EXISTS financial_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    data TEXT NOT NULL,
    generated_by UUID REFERENCES users(id),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- إنشاء الفهارس لتحسين الأداء
CREATE INDEX IF NOT EXISTS idx_accounts_code ON accounts(code);
CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(type);
CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(date);
CREATE INDEX IF NOT EXISTS idx_journal_entries_status ON journal_entries(status);
CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_account ON journal_entry_lines(account_id);
CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);

-- إنشاء دالة تحديث updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- تطبيق دالة التحديث على الجداول المناسبة
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- إدراج البيانات الأساسية
INSERT INTO roles (name, description, permissions) VALUES
('admin', 'مدير النظام', '{"all": true}'),
('accountant', 'محاسب', '{"accounting": true, "reporting": true}'),
('manager', 'مدير', '{"reporting": true, "view_all": true}'),
('user', 'مستخدم', '{"view_own": true}')
ON CONFLICT (name) DO NOTHING;

-- إدراج الحسابات الأساسية
INSERT INTO accounts (code, name, name_ar, type) VALUES
-- الأصول
('1000', 'Cash', 'النقدية', 'asset'),
('1100', 'Bank Account', 'الحساب البنكي', 'asset'),
('1200', 'Accounts Receivable', 'العملاء', 'asset'),
('1300', 'Inventory', 'المخزون', 'asset'),
('1400', 'Fixed Assets', 'الأصول الثابتة', 'asset'),

-- الخصوم
('2000', 'Accounts Payable', 'الموردين', 'liability'),
('2100', 'Accrued Expenses', 'المصروفات المستحقة', 'liability'),
('2200', 'Long-term Debt', 'الديون طويلة الأجل', 'liability'),

-- حقوق الملكية
('3000', 'Owner Equity', 'حقوق المالك', 'equity'),
('3100', 'Retained Earnings', 'الأرباح المحتجزة', 'equity'),

-- الإيرادات
('4000', 'Sales Revenue', 'إيرادات المبيعات', 'revenue'),
('4100', 'Service Revenue', 'إيرادات الخدمات', 'revenue'),

-- المصروفات
('5000', 'Cost of Goods Sold', 'تكلفة البضائع المباعة', 'expense'),
('5100', 'Operating Expenses', 'المصروفات التشغيلية', 'expense'),
('5200', 'Administrative Expenses', 'المصروفات الإدارية', 'expense')
ON CONFLICT (code) DO NOTHING;

-- إنشاء مستخدم افتراضي
INSERT INTO users (username, email, password_hash, first_name, last_name) VALUES
('admin', 'admin@accounting-system.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeHdJjJjJjJjJjJjJj', 'مدير', 'النظام')
ON CONFLICT (username) DO NOTHING;

-- ربط المستخدم الافتراضي بدور المدير
INSERT INTO user_roles (user_id, role_id) 
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.username = 'admin' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

-- إنشاء دالة حساب رصيد الحساب
CREATE OR REPLACE FUNCTION calculate_account_balance(account_uuid UUID, as_of_date DATE DEFAULT CURRENT_DATE)
RETURNS DECIMAL AS $$
DECLARE
    balance DECIMAL(15,2) := 0.00;
BEGIN
    SELECT COALESCE(SUM(debit - credit), 0.00)
    INTO balance
    FROM journal_entry_lines jel
    JOIN journal_entries je ON jel.journal_entry_id = je.id
    WHERE jel.account_id = account_uuid
    AND je.status = 'posted'
    AND je.date <= as_of_date;
    
    RETURN balance;
END;
$$ LANGUAGE plpgsql;

-- إنشاء دالة التحقق من توازن القيد
CREATE OR REPLACE FUNCTION validate_journal_entry_balance(entry_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    total_debit DECIMAL(15,2);
    total_credit DECIMAL(15,2);
BEGIN
    SELECT COALESCE(SUM(debit), 0.00), COALESCE(SUM(credit), 0.00)
    INTO total_debit, total_credit
    FROM journal_entry_lines
    WHERE journal_entry_id = entry_uuid;
    
    RETURN total_debit = total_credit;
END;
$$ LANGUAGE plpgsql;

-- إنشاء دالة تسجيل عمليات المراجعة
CREATE OR REPLACE FUNCTION log_audit_action()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values, ip_address)
        VALUES (COALESCE(current_setting('app.current_user_id', true)::UUID, '00000000-0000-0000-0000-000000000000'::UUID),
                TG_OP, TG_TABLE_NAME, OLD.id, to_json(OLD)::TEXT, NULL, 
                COALESCE(current_setting('app.client_ip', true), '127.0.0.1'));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values, ip_address)
        VALUES (COALESCE(current_setting('app.current_user_id', true)::UUID, '00000000-0000-0000-0000-000000000000'::UUID),
                TG_OP, TG_TABLE_NAME, NEW.id, to_json(OLD)::TEXT, to_json(NEW)::TEXT,
                COALESCE(current_setting('app.client_ip', true), '127.0.0.1'));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values, ip_address)
        VALUES (COALESCE(current_setting('app.current_user_id', true)::UUID, '00000000-0000-0000-0000-000000000000'::UUID),
                TG_OP, TG_TABLE_NAME, NEW.id, NULL, to_json(NEW)::TEXT,
                COALESCE(current_setting('app.client_ip', true), '127.0.0.1'));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- تطبيق دالة المراجعة على الجداول المهمة
CREATE TRIGGER audit_journal_entries AFTER INSERT OR UPDATE OR DELETE ON journal_entries
    FOR EACH ROW EXECUTE FUNCTION log_audit_action();

CREATE TRIGGER audit_accounts AFTER INSERT OR UPDATE OR DELETE ON accounts
    FOR EACH ROW EXECUTE FUNCTION log_audit_action();

CREATE TRIGGER audit_invoices AFTER INSERT OR UPDATE OR DELETE ON invoices
    FOR EACH ROW EXECUTE FUNCTION log_audit_action();

-- إنشاء عرض ميزان المراجعة
CREATE OR REPLACE VIEW trial_balance AS
SELECT 
    a.code,
    a.name_ar,
    a.type,
    COALESCE(SUM(CASE WHEN jel.debit > 0 THEN jel.debit ELSE 0 END), 0) as total_debit,
    COALESCE(SUM(CASE WHEN jel.credit > 0 THEN jel.credit ELSE 0 END), 0) as total_credit,
    COALESCE(SUM(jel.debit - jel.credit), 0) as balance
FROM accounts a
LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id AND je.status = 'posted'
WHERE a.is_active = true
GROUP BY a.id, a.code, a.name_ar, a.type
HAVING COALESCE(SUM(jel.debit - jel.credit), 0) != 0
ORDER BY a.code;

-- إنشاء عرض قائمة الدخل
CREATE OR REPLACE VIEW profit_loss AS
SELECT 
    a.code,
    a.name_ar,
    a.type,
    COALESCE(SUM(jel.debit - jel.credit), 0) as amount
FROM accounts a
LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id AND je.status = 'posted'
WHERE a.is_active = true 
AND a.type IN ('revenue', 'expense')
GROUP BY a.id, a.code, a.name_ar, a.type
ORDER BY a.type, a.code;

-- إنشاء إحصائيات النظام
CREATE OR REPLACE VIEW system_stats AS
SELECT 
    (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
    (SELECT COUNT(*) FROM accounts WHERE is_active = true) as active_accounts,
    (SELECT COUNT(*) FROM journal_entries WHERE status = 'posted') as posted_entries,
    (SELECT COUNT(*) FROM invoices WHERE status = 'paid') as paid_invoices,
    (SELECT COALESCE(SUM(total), 0) FROM invoices WHERE status = 'paid') as total_revenue,
    (SELECT COUNT(*) FROM audit_logs WHERE timestamp >= CURRENT_DATE) as today_audit_entries;

COMMENT ON DATABASE accounting_dev IS 'قاعدة البيانات الرئيسية للنظام المحاسبي المتطور';
COMMENT ON TABLE accounts IS 'جدول الحسابات المحاسبية';
COMMENT ON TABLE journal_entries IS 'جدول القيود المحاسبية';
COMMENT ON TABLE invoices IS 'جدول الفواتير';
COMMENT ON TABLE audit_logs IS 'جدول سجل المراجعة';

-- إنهاء الإعداد
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO accounting_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO accounting_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO accounting_user;

-- رسالة نجاح الإعداد
DO $$
BEGIN
    RAISE NOTICE 'تم إعداد قاعدة البيانات بنجاح!';
    RAISE NOTICE 'المستخدم: accounting_user';
    RAISE NOTICE 'قاعدة البيانات: accounting_dev';
    RAISE NOTICE 'المستخدم الافتراضي: admin / admin@accounting-system.com';
END $$;