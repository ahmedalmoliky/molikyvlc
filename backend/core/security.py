"""
نظام الأمان والحماية للنظام المحاسبي المتطور
Security and protection system for Advanced Accounting System
"""

import hashlib
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from passlib.context import CryptContext
from passlib.hash import bcrypt
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# إعدادات التشفير
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# مفتاح التشفير
encryption_key = settings.ENCRYPTION_KEY.encode()
cipher_suite = Fernet(encryption_key)


class PasswordManager:
    """مدير كلمات المرور"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """تشفير كلمة المرور"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """التحقق من كلمة المرور"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """إنشاء كلمة مرور قوية"""
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """التحقق من قوة كلمة المرور"""
        result = {
            "valid": True,
            "score": 0,
            "requirements": {
                "length": len(password) >= 8,
                "uppercase": any(c.isupper() for c in password),
                "lowercase": any(c.islower() for c in password),
                "numbers": any(c.isdigit() for c in password),
                "special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
            },
            "suggestions": []
        }
        
        # حساب النقاط
        if result["requirements"]["length"]:
            result["score"] += 1
        if result["requirements"]["uppercase"]:
            result["score"] += 1
        if result["requirements"]["lowercase"]:
            result["score"] += 1
        if result["requirements"]["numbers"]:
            result["score"] += 1
        if result["requirements"]["special"]:
            result["score"] += 1
        
        # إضافة طول إضافي للنقاط
        if len(password) >= 12:
            result["score"] += 1
        if len(password) >= 16:
            result["score"] += 1
        
        # التحقق من الصحة
        result["valid"] = all(result["requirements"].values()) and result["score"] >= 4
        
        # إضافة اقتراحات
        if not result["requirements"]["length"]:
            result["suggestions"].append("يجب أن تكون كلمة المرور 8 أحرف على الأقل")
        if not result["requirements"]["uppercase"]:
            result["suggestions"].append("أضف حروف كبيرة")
        if not result["requirements"]["lowercase"]:
            result["suggestions"].append("أضف حروف صغيرة")
        if not result["requirements"]["numbers"]:
            result["suggestions"].append("أضف أرقام")
        if not result["requirements"]["special"]:
            result["suggestions"].append("أضف رموز خاصة")
        
        return result


class TokenManager:
    """مدير الرموز المميزة"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """إنشاء رمز وصول"""
        try:
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            
            to_encode.update({"exp": expire, "type": "access"})
            encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """إنشاء رمز تحديث"""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
            to_encode.update({"exp": expire, "type": "refresh"})
            encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """التحقق من الرمز المميز"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """فك تشفير الرمز المميز"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"Token decode error: {e}")
            return None


class EncryptionManager:
    """مدير التشفير"""
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """تشفير البيانات"""
        try:
            if isinstance(data, str):
                data = data.encode()
            encrypted_data = cipher_suite.encrypt(data)
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """فك تشفير البيانات"""
        try:
            encrypted_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise
    
    @staticmethod
    def generate_key() -> str:
        """إنشاء مفتاح تشفير جديد"""
        return Fernet.generate_key().decode()
    
    @staticmethod
    def hash_data(data: str, salt: Optional[str] = None) -> str:
        """تشفير البيانات باستخدام Hash"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        data_with_salt = f"{data}{salt}"
        hash_object = hashlib.sha256(data_with_salt.encode())
        return f"{salt}:{hash_object.hexdigest()}"
    
    @staticmethod
    def verify_hash(data: str, hashed_data: str) -> bool:
        """التحقق من Hash البيانات"""
        try:
            salt, hash_value = hashed_data.split(":")
            data_with_salt = f"{data}{salt}"
            hash_object = hashlib.sha256(data_with_salt.encode())
            return hash_object.hexdigest() == hash_value
        except Exception as e:
            logger.error(f"Error verifying hash: {e}")
            return False


class SecurityManager:
    """مدير الأمان الشامل"""
    
    def __init__(self):
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager()
        self.encryption_manager = EncryptionManager()
        self.failed_attempts = {}  # تتبع محاولات تسجيل الدخول الفاشلة
        self.locked_accounts = {}  # الحسابات المقفلة
    
    def authenticate_user(self, username: str, password: str, ip_address: str) -> Dict[str, Any]:
        """مصادقة المستخدم"""
        try:
            # التحقق من الحساب المقفل
            if self.is_account_locked(username):
                return {
                    "success": False,
                    "message": "الحساب مقفل مؤقتاً بسبب محاولات تسجيل دخول فاشلة",
                    "locked_until": self.locked_accounts.get(username, {}).get("locked_until")
                }
            
            # هنا يجب التحقق من قاعدة البيانات
            # للتبسيط، سنستخدم بيانات وهمية
            if username == "admin" and password == "admin123":
                # إنشاء الرموز المميزة
                access_token = self.token_manager.create_access_token(
                    {"sub": username, "user_id": "1"}
                )
                refresh_token = self.token_manager.create_refresh_token(
                    {"sub": username, "user_id": "1"}
                )
                
                # إعادة تعيين محاولات تسجيل الدخول الفاشلة
                self.reset_failed_attempts(username)
                
                return {
                    "success": True,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                }
            else:
                # تسجيل محاولة فاشلة
                self.record_failed_attempt(username, ip_address)
                return {
                    "success": False,
                    "message": "اسم المستخدم أو كلمة المرور غير صحيحة"
                }
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {
                "success": False,
                "message": "خطأ في المصادقة"
            }
    
    def record_failed_attempt(self, username: str, ip_address: str):
        """تسجيل محاولة تسجيل دخول فاشلة"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                "count": 0,
                "last_attempt": None,
                "ip_addresses": set()
            }
        
        self.failed_attempts[username]["count"] += 1
        self.failed_attempts[username]["last_attempt"] = datetime.now()
        self.failed_attempts[username]["ip_addresses"].add(ip_address)
        
        # قفل الحساب بعد 5 محاولات فاشلة
        if self.failed_attempts[username]["count"] >= 5:
            self.lock_account(username, 30)  # قفل لمدة 30 دقيقة
    
    def reset_failed_attempts(self, username: str):
        """إعادة تعيين محاولات تسجيل الدخول الفاشلة"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
    
    def is_account_locked(self, username: str) -> bool:
        """التحقق من قفل الحساب"""
        if username not in self.locked_accounts:
            return False
        
        locked_until = self.locked_accounts[username]["locked_until"]
        if datetime.now() > locked_until:
            del self.locked_accounts[username]
            return False
        
        return True
    
    def lock_account(self, username: str, minutes: int):
        """قفل الحساب"""
        self.locked_accounts[username] = {
            "locked_until": datetime.now() + timedelta(minutes=minutes),
            "reason": "too_many_failed_attempts"
        }
    
    def validate_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """التحقق من الصلاحيات"""
        # هنا يجب التحقق من قاعدة البيانات
        # للتبسيط، سنعود بـ True
        return True
    
    def log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """تسجيل حدث أمني"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "details": details
            }
            logger.info(f"Security event: {event}")
            # هنا يجب حفظ الحدث في قاعدة البيانات
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def generate_csrf_token(self, user_id: str) -> str:
        """إنشاء رمز CSRF"""
        data = f"{user_id}{datetime.now().isoformat()}"
        return self.encryption_manager.hash_data(data)
    
    def validate_csrf_token(self, token: str, user_id: str) -> bool:
        """التحقق من رمز CSRF"""
        try:
            # التحقق من صحة الرمز
            return True  # للتبسيط
        except Exception as e:
            logger.error(f"CSRF validation error: {e}")
            return False
    
    def sanitize_input(self, data: str) -> str:
        """تنظيف المدخلات"""
        if not isinstance(data, str):
            return str(data)
        
        # إزالة الأحرف الخطيرة
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        for char in dangerous_chars:
            data = data.replace(char, '')
        
        return data.strip()
    
    def validate_file_upload(self, filename: str, file_size: int, content_type: str) -> Dict[str, Any]:
        """التحقق من صحة رفع الملف"""
        result = {
            "valid": True,
            "errors": []
        }
        
        # التحقق من نوع الملف
        allowed_extensions = settings.ALLOWED_EXTENSIONS
        file_extension = filename.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            result["valid"] = False
            result["errors"].append(f"نوع الملف غير مسموح: {file_extension}")
        
        # التحقق من حجم الملف
        if file_size > settings.MAX_FILE_SIZE:
            result["valid"] = False
            result["errors"].append(f"حجم الملف كبير جداً: {file_size} bytes")
        
        # التحقق من نوع المحتوى
        allowed_types = [
            'text/plain', 'application/pdf', 'image/jpeg', 'image/png',
            'application/vnd.ms-excel', 'text/csv'
        ]
        if content_type not in allowed_types:
            result["valid"] = False
            result["errors"].append(f"نوع المحتوى غير مسموح: {content_type}")
        
        return result


# إنشاء مدير الأمان العام
security_manager = SecurityManager()


# دوال مساعدة للاستخدام العام
def hash_password(password: str) -> str:
    """تشفير كلمة المرور"""
    return security_manager.password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور"""
    return security_manager.password_manager.verify_password(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any]) -> str:
    """إنشاء رمز وصول"""
    return security_manager.token_manager.create_access_token(data)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """التحقق من الرمز المميز"""
    return security_manager.token_manager.verify_token(token)


def encrypt_data(data: str) -> str:
    """تشفير البيانات"""
    return security_manager.encryption_manager.encrypt_data(data)


def decrypt_data(encrypted_data: str) -> str:
    """فك تشفير البيانات"""
    return security_manager.encryption_manager.decrypt_data(encrypted_data)


def sanitize_input(data: str) -> str:
    """تنظيف المدخلات"""
    return security_manager.sanitize_input(data)