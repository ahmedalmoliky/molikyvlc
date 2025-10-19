"""
إعدادات النظام المحاسبي المتطور
Configuration settings for Advanced Accounting System
"""

import os
from typing import Optional
from pydantic import BaseSettings, validator
from functools import lru_cache


class Settings(BaseSettings):
    """إعدادات النظام"""
    
    # إعدادات التطبيق
    APP_NAME: str = "النظام المحاسبي المتطور"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # إعدادات قاعدة البيانات
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # إعدادات Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    
    # إعدادات الأمان
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # إعدادات التشفير
    ENCRYPTION_KEY: str
    PASSWORD_HASH_ROUNDS: int = 12
    
    # إعدادات الملفات
    UPLOAD_FOLDER: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "xlsx", "csv"}
    
    # إعدادات البريد الإلكتروني
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: int = 587
    EMAIL_USER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_USE_TLS: bool = True
    
    # إعدادات SMS
    SMS_PROVIDER: Optional[str] = None
    SMS_API_KEY: Optional[str] = None
    
    # إعدادات المراقبة
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    LOG_LEVEL: str = "INFO"
    
    # إعدادات API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Advanced Accounting System"
    
    # إعدادات CORS
    BACKEND_CORS_ORIGINS: list = []
    
    # إعدادات الجلسة
    SESSION_COOKIE_NAME: str = "accounting_session"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    # إعدادات التخزين المؤقت
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_MAX_SIZE: int = 1000
    
    # إعدادات التقارير
    REPORT_CACHE_TTL: int = 3600  # 1 hour
    MAX_REPORT_ROWS: int = 10000
    
    # إعدادات النسخ الاحتياطي
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    BACKUP_RETENTION_DAYS: int = 30
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """الحصول على إعدادات النظام"""
    return Settings()


# إعدادات البيئة المختلفة
class DevelopmentSettings(Settings):
    """إعدادات بيئة التطوير"""
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    SESSION_COOKIE_SECURE: bool = False


class TestingSettings(Settings):
    """إعدادات بيئة الاختبار"""
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/1"


class ProductionSettings(Settings):
    """إعدادات بيئة الإنتاج"""
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "WARNING"
    SESSION_COOKIE_SECURE: bool = True


def get_settings_by_env(env: str = None) -> Settings:
    """الحصول على الإعدادات حسب البيئة"""
    if env is None:
        env = os.getenv("ENVIRONMENT", "production")
    
    if env == "development":
        return DevelopmentSettings()
    elif env == "testing":
        return TestingSettings()
    elif env == "production":
        return ProductionSettings()
    else:
        return Settings()


# إعدادات قاعدة البيانات
DATABASE_CONFIG = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": False,
}

# إعدادات Redis
REDIS_CONFIG = {
    "decode_responses": True,
    "socket_keepalive": True,
    "socket_keepalive_options": {},
    "health_check_interval": 30,
}

# إعدادات JWT
JWT_CONFIG = {
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7,
}

# إعدادات التشفير
ENCRYPTION_CONFIG = {
    "algorithm": "AES-256-GCM",
    "key_size": 32,
    "iv_size": 12,
    "tag_size": 16,
}

# إعدادات المراقبة
MONITORING_CONFIG = {
    "prometheus_port": 9090,
    "grafana_port": 3000,
    "metrics_path": "/metrics",
    "health_check_path": "/health",
}

# إعدادات التقارير
REPORT_CONFIG = {
    "formats": ["pdf", "excel", "csv"],
    "max_rows": 10000,
    "cache_ttl": 3600,
    "template_path": "templates/reports",
}

# إعدادات الأمان
SECURITY_CONFIG = {
    "password_min_length": 8,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_numbers": True,
    "password_require_special": True,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 30,
    "session_timeout_minutes": 60,
}

# إعدادات التخزين
STORAGE_CONFIG = {
    "local_path": "uploads",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": {
        "images": ["jpg", "jpeg", "png", "gif"],
        "documents": ["pdf", "doc", "docx", "txt"],
        "spreadsheets": ["xlsx", "xls", "csv"],
    },
    "compression": True,
    "encryption": True,
}

# إعدادات الإشعارات
NOTIFICATION_CONFIG = {
    "email_enabled": True,
    "sms_enabled": False,
    "push_enabled": False,
    "webhook_enabled": False,
    "retry_attempts": 3,
    "retry_delay_seconds": 60,
}

# إعدادات التكامل
INTEGRATION_CONFIG = {
    "banking_apis": {
        "enabled": False,
        "providers": ["sab", "alrajhi", "ncb"],
        "timeout_seconds": 30,
    },
    "tax_systems": {
        "enabled": False,
        "providers": ["zakat", "vat"],
        "timeout_seconds": 30,
    },
    "payment_gateways": {
        "enabled": False,
        "providers": ["stripe", "paypal", "mada"],
        "timeout_seconds": 30,
    },
}

# إعدادات النسخ الاحتياطي
BACKUP_CONFIG = {
    "enabled": True,
    "schedule": "0 2 * * *",  # Daily at 2 AM
    "retention_days": 30,
    "compression": True,
    "encryption": True,
    "storage": {
        "local": True,
        "cloud": False,
        "s3_bucket": None,
    },
}

# إعدادات الأداء
PERFORMANCE_CONFIG = {
    "cache_enabled": True,
    "cache_ttl": 300,  # 5 minutes
    "query_timeout": 30,  # seconds
    "max_connections": 100,
    "connection_timeout": 10,  # seconds
    "read_timeout": 30,  # seconds
    "write_timeout": 30,  # seconds
}

# إعدادات السجلات
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/accounting_system.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": False,
        },
    },
}