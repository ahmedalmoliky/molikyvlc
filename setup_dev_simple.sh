#!/bin/bash

# إعداد بيئة التطوير البسيطة (بدون Docker)
# Simple Development Environment Setup (Without Docker)

echo "🚀 بدء إعداد بيئة التطوير البسيطة..."

# تحديث النظام
echo "📦 تحديث النظام..."
sudo apt update && sudo apt upgrade -y

# تثبيت المتطلبات الأساسية
echo "🔧 تثبيت المتطلبات الأساسية..."
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# تثبيت Python 3.11
echo "🐍 تثبيت Python 3.11..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# تثبيت Node.js 18
echo "📦 تثبيت Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# تثبيت PostgreSQL 15
echo "🐘 تثبيت PostgreSQL 15..."
sudo apt install -y postgresql-15 postgresql-client-15 postgresql-contrib-15

# إعداد PostgreSQL
echo "⚙️ إعداد PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres psql -c "CREATE DATABASE accounting_dev;"
sudo -u postgres psql -c "CREATE USER accounting_user WITH PASSWORD 'accounting_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE accounting_dev TO accounting_user;"
sudo -u postgres psql -c "ALTER USER accounting_user CREATEDB;"

# تثبيت Redis
echo "🔴 تثبيت Redis..."
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# إنشاء مجلدات المشروع
echo "📁 إنشاء مجلدات المشروع..."
mkdir -p ~/accounting-system/{backend,frontend,docs,scripts,deployments}
cd ~/accounting-system

# إنشاء البيئة الافتراضية لـ Python
echo "🐍 إنشاء البيئة الافتراضية..."
python3.11 -m venv venv
source venv/bin/activate

# تثبيت متطلبات Python
echo "📦 تثبيت متطلبات Python..."
pip install --upgrade pip
pip install -r requirements.txt

# تثبيت أدوات التطوير
echo "🛠️ تثبيت أدوات التطوير..."
pip install black isort flake8 mypy pytest pytest-cov

# تثبيت أدوات Frontend
echo "⚛️ تثبيت أدوات Frontend..."
cd frontend
npm init -y
npm install -g typescript @types/node

# إعداد Git
echo "📝 إعداد Git..."
git config --global user.name "Accounting System Developer"
git config --global user.email "dev@accounting-system.com"
git config --global init.defaultBranch main

# إنشاء ملف .env
echo "🔐 إنشاء ملف البيئة..."
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://accounting_user:accounting_password@localhost:5432/accounting_dev
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# External Services
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# File Storage
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=txt,pdf,png,jpg,jpeg,gif

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
EOF

# إنشاء ملف Makefile مبسط
echo "⚙️ إنشاء ملف Makefile مبسط..."
cat > Makefile << EOF
.PHONY: help install dev test clean setup-db

help: ## عرض المساعدة
	@echo "الأوامر المتاحة:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## تثبيت المتطلبات
	pip install -r requirements.txt
	npm install

dev: ## تشغيل الخادم للتطوير
	uvicorn accounting_api:app --reload --host 0.0.0.0 --port 8000

test: ## تشغيل الاختبارات
	pytest tests/ -v --cov=accounting_api

test-watch: ## تشغيل الاختبارات مع المراقبة
	pytest-watch tests/

lint: ## فحص الكود
	black accounting_api/
	isort accounting_api/
	flake8 accounting_api/
	mypy accounting_api/

format: ## تنسيق الكود
	black accounting_api/
	isort accounting_api/

clean: ## تنظيف الملفات المؤقتة
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage

setup-db: ## إعداد قاعدة البيانات
	psql -h localhost -U accounting_user -d accounting_dev -f init.sql

start-services: ## تشغيل الخدمات
	sudo systemctl start postgresql
	sudo systemctl start redis-server

stop-services: ## إيقاف الخدمات
	sudo systemctl stop postgresql
	sudo systemctl stop redis-server

status: ## حالة الخدمات
	sudo systemctl status postgresql
	sudo systemctl status redis-server

logs: ## عرض سجلات التطبيق
	tail -f logs/accounting_system.log
EOF

# إنشاء ملف .gitignore
echo "📝 إنشاء ملف .gitignore..."
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.local
.env.development
.env.test
.env.production

# Database
*.db
*.sqlite3

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Coverage
.coverage
htmlcov/
.pytest_cache/

# Uploads
uploads/
media/

# Temporary files
tmp/
temp/
EOF

# إنشاء ملف README للتطوير البسيط
echo "📚 إنشاء ملف README للتطوير البسيط..."
cat > README_SIMPLE.md << EOF
# دليل التطوير البسيط - النظام المحاسبي المتطور
## Simple Development Guide - Advanced Accounting System

## 🚀 البدء السريع

### 1. إعداد البيئة
\`\`\`bash
# تشغيل سكريبت الإعداد
chmod +x setup_dev_simple.sh
./setup_dev_simple.sh

# تفعيل البيئة الافتراضية
source venv/bin/activate
\`\`\`

### 2. تشغيل الخدمات
\`\`\`bash
# تشغيل PostgreSQL و Redis
make start-services

# التحقق من حالة الخدمات
make status
\`\`\`

### 3. إعداد قاعدة البيانات
\`\`\`bash
# إعداد قاعدة البيانات
make setup-db
\`\`\`

### 4. تشغيل التطبيق
\`\`\`bash
# تشغيل الخادم
make dev

# أو مباشرة
uvicorn accounting_api:app --reload
\`\`\`

## 🛠️ الأوامر المفيدة

\`\`\`bash
# عرض جميع الأوامر
make help

# تشغيل الاختبارات
make test

# فحص الكود
make lint

# تنسيق الكود
make format

# عرض السجلات
make logs
\`\`\`

## 📁 هيكل المشروع

\`\`\`
accounting-system/
├── backend/                 # كود Backend
│   ├── accounting_api.py    # API الرئيسي
│   ├── accounting_models.py # النماذج
│   ├── accounting_database.py # قاعدة البيانات
│   └── tests/              # الاختبارات
├── frontend/               # كود Frontend
├── docs/                   # الوثائق
├── scripts/                # السكريبتات
├── requirements.txt        # متطلبات Python
└── Makefile               # أوامر التطوير
\`\`\`

## 🔧 إعدادات التطوير

- **قاعدة البيانات**: PostgreSQL على المنفذ 5432
- **Redis**: على المنفذ 6379
- **API**: على المنفذ 8000
- **البيئة الافتراضية**: venv/

## 📝 معايير التطوير

- **Python**: 3.11+
- **Node.js**: 18+
- **PostgreSQL**: 15+
- **Redis**: 7+

## 🧪 الاختبارات

\`\`\`bash
# تشغيل جميع الاختبارات
pytest

# تشغيل اختبارات مع التغطية
pytest --cov=accounting_api

# تشغيل اختبارات مع المراقبة
pytest-watch
\`\`\`

## 🐛 حل المشاكل

### مشكلة الاتصال بقاعدة البيانات
\`\`\`bash
# التحقق من حالة PostgreSQL
sudo systemctl status postgresql

# إعادة تشغيل PostgreSQL
sudo systemctl restart postgresql
\`\`\`

### مشكلة Redis
\`\`\`bash
# التحقق من حالة Redis
sudo systemctl status redis-server

# إعادة تشغيل Redis
sudo systemctl restart redis-server
\`\`\`

## 📞 الدعم

للحصول على المساعدة، يرجى التواصل مع فريق التطوير.
EOF

# إعطاء صلاحيات التنفيذ
chmod +x setup_dev_simple.sh

echo "✅ تم إعداد بيئة التطوير البسيطة بنجاح!"
echo "📁 المشروع في: ~/accounting-system"
echo "🚀 لتشغيل التطبيق: cd ~/accounting-system && make dev"
echo "📚 للدليل الكامل: cat README_SIMPLE.md"