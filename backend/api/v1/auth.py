"""
واجهات المصادقة والأمان
Authentication and Security Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ...core.security import security_manager, verify_token
from ...core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# نماذج البيانات
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime


# دوال المساعدة
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """الحصول على المستخدم الحالي"""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="رمز غير صالح",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="خطأ في المصادقة",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_client_ip(request: Request) -> str:
    """الحصول على عنوان IP للعميل"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host


# واجهات API
@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    تسجيل الدخول
    User Login
    """
    try:
        client_ip = get_client_ip(request)
        
        # تسجيل محاولة تسجيل الدخول
        security_manager.log_security_event(
            "login_attempt",
            login_data.username,
            {"ip_address": client_ip, "timestamp": datetime.now().isoformat()}
        )
        
        # مصادقة المستخدم
        auth_result = security_manager.authenticate_user(
            login_data.username,
            login_data.password,
            client_ip
        )
        
        if auth_result["success"]:
            # تسجيل تسجيل الدخول الناجح
            security_manager.log_security_event(
                "login_success",
                login_data.username,
                {"ip_address": client_ip, "timestamp": datetime.now().isoformat()}
            )
            
            return LoginResponse(
                success=True,
                message="تم تسجيل الدخول بنجاح",
                access_token=auth_result["access_token"],
                refresh_token=auth_result["refresh_token"],
                token_type=auth_result["token_type"],
                expires_in=30 * 60  # 30 دقيقة
            )
        else:
            # تسجيل فشل تسجيل الدخول
            security_manager.log_security_event(
                "login_failed",
                login_data.username,
                {"ip_address": client_ip, "reason": auth_result["message"]}
            )
            
            return LoginResponse(
                success=False,
                message=auth_result["message"]
            )
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في تسجيل الدخول"
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request
):
    """
    تحديث الرمز المميز
    Refresh Access Token
    """
    try:
        client_ip = get_client_ip(request)
        
        # التحقق من رمز التحديث
        payload = verify_token(refresh_data.refresh_token)
        
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="رمز التحديث غير صالح"
            )
        
        # إنشاء رمز وصول جديد
        new_access_token = security_manager.token_manager.create_access_token({
            "sub": payload["sub"],
            "user_id": payload["user_id"]
        })
        
        # تسجيل حدث التحديث
        security_manager.log_security_event(
            "token_refresh",
            payload["sub"],
            {"ip_address": client_ip}
        )
        
        return LoginResponse(
            success=True,
            message="تم تحديث الرمز بنجاح",
            access_token=new_access_token,
            token_type="bearer",
            expires_in=30 * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في تحديث الرمز"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    تسجيل الخروج
    User Logout
    """
    try:
        client_ip = get_client_ip(request)
        
        # تسجيل حدث تسجيل الخروج
        security_manager.log_security_event(
            "logout",
            current_user["sub"],
            {"ip_address": client_ip}
        )
        
        return {
            "success": True,
            "message": "تم تسجيل الخروج بنجاح"
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في تسجيل الخروج"
        )


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على ملف المستخدم
    Get User Profile
    """
    try:
        # هنا يجب جلب بيانات المستخدم من قاعدة البيانات
        # للتبسيط، سنعود ببيانات وهمية
        return UserProfile(
            id=current_user["user_id"],
            username=current_user["sub"],
            email="admin@accounting-system.com",
            first_name="مدير",
            last_name="النظام",
            is_active=True,
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في جلب ملف المستخدم"
        )


@router.put("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    request: Request = None
):
    """
    تغيير كلمة المرور
    Change Password
    """
    try:
        client_ip = get_client_ip(request) if request else "unknown"
        
        # التحقق من كلمة المرور الحالية
        # هنا يجب التحقق من قاعدة البيانات
        # للتبسيط، سنتحقق من كلمة مرور وهمية
        if password_data.current_password != "admin123":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="كلمة المرور الحالية غير صحيحة"
            )
        
        # التحقق من قوة كلمة المرور الجديدة
        strength_check = security_manager.password_manager.validate_password_strength(
            password_data.new_password
        )
        
        if not strength_check["valid"]:
            return {
                "success": False,
                "message": "كلمة المرور ضعيفة",
                "suggestions": strength_check["suggestions"]
            }
        
        # تشفير كلمة المرور الجديدة
        hashed_password = security_manager.password_manager.hash_password(
            password_data.new_password
        )
        
        # هنا يجب حفظ كلمة المرور الجديدة في قاعدة البيانات
        
        # تسجيل حدث تغيير كلمة المرور
        security_manager.log_security_event(
            "password_change",
            current_user["sub"],
            {"ip_address": client_ip}
        )
        
        return {
            "success": True,
            "message": "تم تغيير كلمة المرور بنجاح"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في تغيير كلمة المرور"
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest,
    request: Request
):
    """
    إعادة تعيين كلمة المرور
    Reset Password
    """
    try:
        client_ip = get_client_ip(request)
        
        # التحقق من وجود المستخدم
        # هنا يجب التحقق من قاعدة البيانات
        # للتبسيط، سنتحقق من إيميل وهمي
        if reset_data.email != "admin@accounting-system.com":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="المستخدم غير موجود"
            )
        
        # إنشاء رمز إعادة تعيين
        reset_token = security_manager.encryption_manager.hash_data(
            f"{reset_data.email}{datetime.now().isoformat()}"
        )
        
        # هنا يجب إرسال إيميل إعادة التعيين
        # وإضافة الرمز إلى قاعدة البيانات
        
        # تسجيل حدث طلب إعادة تعيين كلمة المرور
        security_manager.log_security_event(
            "password_reset_request",
            reset_data.email,
            {"ip_address": client_ip, "reset_token": reset_token}
        )
        
        return {
            "success": True,
            "message": "تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في إعادة تعيين كلمة المرور"
        )


@router.get("/security-events")
async def get_security_events(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """
    الحصول على الأحداث الأمنية
    Get Security Events
    """
    try:
        # هنا يجب جلب الأحداث الأمنية من قاعدة البيانات
        # للتبسيط، سنعود بقائمة فارغة
        
        return {
            "success": True,
            "events": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Get security events error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في جلب الأحداث الأمنية"
        )


@router.get("/permissions")
async def get_permissions(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    الحصول على صلاحيات المستخدم
    Get User Permissions
    """
    try:
        # هنا يجب جلب صلاحيات المستخدم من قاعدة البيانات
        # للتبسيط، سنعود بصلاحيات وهمية
        
        permissions = {
            "accounting": {
                "create_journal": True,
                "post_journal": True,
                "view_balances": True,
                "create_invoice": True
            },
            "reporting": {
                "view_reports": True,
                "export_reports": True,
                "create_custom_reports": True
            },
            "administration": {
                "manage_users": True,
                "manage_accounts": True,
                "system_settings": True
            }
        }
        
        return {
            "success": True,
            "permissions": permissions
        }
        
    except Exception as e:
        logger.error(f"Get permissions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطأ في جلب الصلاحيات"
        )