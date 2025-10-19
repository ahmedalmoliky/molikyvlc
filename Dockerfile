# Dockerfile للنظام المحاسبي المتطور
FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# تحديث النظام وتثبيت المتطلبات الأساسية
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد التطبيق
WORKDIR /app

# نسخ ملفات المتطلبات
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ الكود المصدري
COPY . .

# إنشاء مستخدم غير root
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# فتح المنفذ
EXPOSE 8000

# أمر التشغيل
CMD ["uvicorn", "accounting_api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]