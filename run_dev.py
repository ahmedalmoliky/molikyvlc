#!/usr/bin/env python3
"""
سكريبت تشغيل التطبيق للتطوير
Development Run Script
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def check_services():
    """التحقق من الخدمات المطلوبة"""
    print("🔍 التحقق من الخدمات...")
    
    # التحقق من PostgreSQL
    try:
        result = subprocess.run(['pg_isready', '-h', 'localhost', '-p', '5432'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL يعمل")
        else:
            print("❌ PostgreSQL غير متاح")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL غير مثبت")
        return False
    
    # التحقق من Redis
    try:
        result = subprocess.run(['redis-cli', 'ping'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis يعمل")
        else:
            print("❌ Redis غير متاح")
            return False
    except FileNotFoundError:
        print("❌ Redis غير مثبت")
        return False
    
    return True

def setup_environment():
    """إعداد البيئة"""
    print("⚙️ إعداد البيئة...")
    
    # إنشاء مجلدات مطلوبة
    os.makedirs('logs', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # التحقق من ملف .env
    if not os.path.exists('.env'):
        print("❌ ملف .env غير موجود")
        print("يرجى تشغيل setup_dev_simple.sh أولاً")
        return False
    
    print("✅ البيئة جاهزة")
    return True

def install_dependencies():
    """تثبيت المتطلبات"""
    print("📦 تثبيت المتطلبات...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ تم تثبيت المتطلبات")
        return True
    except subprocess.CalledProcessError:
        print("❌ فشل في تثبيت المتطلبات")
        return False

def run_database_migration():
    """تشغيل ترحيل قاعدة البيانات"""
    print("🗄️ إعداد قاعدة البيانات...")
    
    try:
        # تشغيل ملف init.sql
        subprocess.run(['psql', '-h', 'localhost', '-U', 'accounting_user', 
                       '-d', 'accounting_dev', '-f', 'init.sql'], 
                      check=True, capture_output=True)
        print("✅ تم إعداد قاعدة البيانات")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل في إعداد قاعدة البيانات: {e}")
        return False

def start_application():
    """تشغيل التطبيق"""
    print("🚀 تشغيل التطبيق...")
    
    try:
        # تشغيل uvicorn
        cmd = [sys.executable, '-m', 'uvicorn', 'accounting_api:app', 
               '--reload', '--host', '0.0.0.0', '--port', '8000']
        
        print(f"تشغيل الأمر: {' '.join(cmd)}")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف التطبيق")
    except Exception as e:
        print(f"❌ خطأ في تشغيل التطبيق: {e}")

def main():
    """الدالة الرئيسية"""
    print("=" * 50)
    print("🚀 بدء تشغيل النظام المحاسبي المتطور")
    print("=" * 50)
    
    # التحقق من الخدمات
    if not check_services():
        print("\n❌ فشل في التحقق من الخدمات")
        print("يرجى تشغيل:")
        print("  make start-services")
        sys.exit(1)
    
    # إعداد البيئة
    if not setup_environment():
        sys.exit(1)
    
    # تثبيت المتطلبات
    if not install_dependencies():
        sys.exit(1)
    
    # إعداد قاعدة البيانات
    if not run_database_migration():
        print("⚠️ تحذير: فشل في إعداد قاعدة البيانات")
        print("يمكنك المتابعة، لكن قد تحتاج لإعداد قاعدة البيانات يدوياً")
    
    print("\n" + "=" * 50)
    print("✅ كل شيء جاهز!")
    print("🌐 التطبيق متاح على: http://localhost:8000")
    print("📚 وثائق API: http://localhost:8000/docs")
    print("🛑 لإيقاف التطبيق: Ctrl+C")
    print("=" * 50)
    
    # تشغيل التطبيق
    start_application()

if __name__ == "__main__":
    main()