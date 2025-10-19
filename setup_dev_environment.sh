#!/bin/bash

# إعداد بيئة التطوير للنظام المحاسبي المتطور
# Advanced Accounting System Development Environment Setup

echo "🚀 بدء إعداد بيئة التطوير..."

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
sudo -u postgres psql -c "CREATE DATABASE accounting_dev;"
sudo -u postgres psql -c "CREATE USER accounting_user WITH PASSWORD 'accounting_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE accounting_dev TO accounting_user;"
sudo -u postgres psql -c "ALTER USER accounting_user CREATEDB;"

# تثبيت Redis
echo "🔴 تثبيت Redis..."
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# تثبيت Docker
echo "🐳 تثبيت Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# إضافة المستخدم لمجموعة Docker
sudo usermod -aG docker $USER

# تثبيت Docker Compose
echo "🐙 تثبيت Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

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
npm install -g @angular/cli @vue/cli create-react-app
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

# إنشاء ملف docker-compose.dev.yml
echo "🐳 إنشاء ملف Docker Compose للتطوير..."
cat > docker-compose.dev.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: accounting_postgres_dev
    environment:
      POSTGRES_DB: accounting_dev
      POSTGRES_USER: accounting_user
      POSTGRES_PASSWORD: accounting_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
    networks:
      - accounting_network

  redis:
    image: redis:7-alpine
    container_name: accounting_redis_dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data_dev:/data
    networks:
      - accounting_network

  app:
    build: .
    container_name: accounting_app_dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://accounting_user:accounting_password@postgres:5432/accounting_dev
      - REDIS_URL=redis://redis:6379
      - DEBUG=True
    volumes:
      - .:/app
    depends_on:
      - postgres
      - redis
    networks:
      - accounting_network

volumes:
  postgres_data_dev:
  redis_data_dev:

networks:
  accounting_network:
    driver: bridge
EOF

# إنشاء ملف Makefile
echo "⚙️ إنشاء ملف Makefile..."
cat > Makefile << EOF
.PHONY: help install dev test clean docker-up docker-down

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

docker-up: ## تشغيل الحاويات
	docker-compose -f docker-compose.dev.yml up -d

docker-down: ## إيقاف الحاويات
	docker-compose -f docker-compose.dev.yml down

clean: ## تنظيف الملفات المؤقتة
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage

db-migrate: ## تشغيل ترحيل قاعدة البيانات
	alembic upgrade head

db-reset: ## إعادة تعيين قاعدة البيانات
	alembic downgrade base
	alembic upgrade head

setup-db: ## إعداد قاعدة البيانات
	createdb accounting_dev
	alembic upgrade head

logs: ## عرض سجلات التطبيق
	docker-compose -f docker-compose.dev.yml logs -f app
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

# Docker
.dockerignore

# Uploads
uploads/
media/

# Temporary files
tmp/
temp/
EOF

# إنشاء ملف README للتطوير
echo "📚 إنشاء ملف README للتطوير..."
cat > README_DEV.md << EOF
# دليل التطوير - النظام المحاسبي المتطور
## Development Guide - Advanced Accounting System

## 🚀 البدء السريع

### 1. إعداد البيئة
\`\`\`bash
# تشغيل سكريبت الإعداد
chmod +x setup_dev_environment.sh
./setup_dev_environment.sh

# تفعيل البيئة الافتراضية
source venv/bin/activate
\`\`\`

### 2. تشغيل قاعدة البيانات
\`\`\`bash
# تشغيل الحاويات
make docker-up

# إعداد قاعدة البيانات
make setup-db
\`\`\`

### 3. تشغيل التطبيق
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
├── deployments/            # ملفات النشر
├── requirements.txt        # متطلبات Python
├── docker-compose.dev.yml  # Docker للتطوير
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

## 📊 مراقبة الأداء

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

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
chmod +x setup_dev_environment.sh

echo "✅ تم إعداد بيئة التطوير بنجاح!"
echo "📁 المشروع في: ~/accounting-system"
echo "🚀 لتشغيل التطبيق: cd ~/accounting-system && make dev"
echo "📚 للدليل الكامل: cat README_DEV.md"