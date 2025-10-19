"""
إدارة قاعدة البيانات للنظام المحاسبي المتطور
Database management for Advanced Accounting System
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

# إعدادات قاعدة البيانات
settings = get_settings()

# إنشاء محرك قاعدة البيانات
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

# إنشاء مصنع الجلسات
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# قاعدة البيانات
Base = declarative_base()

# إعدادات البيانات الوصفية
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    الحصول على جلسة قاعدة البيانات
    Dependency injection للجلسات
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    مدير السياق لجلسة قاعدة البيانات
    Context manager for database sessions
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """إنشاء الجداول في قاعدة البيانات"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def drop_tables():
    """حذف الجداول من قاعدة البيانات"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


def check_database_connection() -> bool:
    """التحقق من اتصال قاعدة البيانات"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_database_info() -> dict:
    """الحصول على معلومات قاعدة البيانات"""
    try:
        with engine.connect() as connection:
            # معلومات الإصدار
            version_result = connection.execute("SELECT version()")
            version = version_result.fetchone()[0]
            
            # عدد الجداول
            tables_result = connection.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = tables_result.fetchone()[0]
            
            # حجم قاعدة البيانات
            size_result = connection.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            db_size = size_result.fetchone()[0]
            
            return {
                "version": version,
                "table_count": table_count,
                "size": db_size,
                "status": "connected"
            }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {
            "version": "unknown",
            "table_count": 0,
            "size": "unknown",
            "status": "error",
            "error": str(e)
        }


class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = SessionLocal
    
    def get_session(self) -> Session:
        """الحصول على جلسة جديدة"""
        return self.session_factory()
    
    @contextmanager
    def get_session_context(self):
        """مدير السياق للجلسة"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: dict = None):
        """تنفيذ استعلام"""
        with self.get_session_context() as session:
            result = session.execute(query, params or {})
            return result.fetchall()
    
    def execute_scalar(self, query: str, params: dict = None):
        """تنفيذ استعلام وإرجاع قيمة واحدة"""
        with self.get_session_context() as session:
            result = session.execute(query, params or {})
            return result.scalar()
    
    def backup_database(self, backup_path: str):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        import subprocess
        import os
        
        try:
            # استخراج معلومات الاتصال من URL
            db_url = settings.DATABASE_URL
            # تنفيذ pg_dump
            cmd = [
                "pg_dump",
                db_url,
                "-f", backup_path,
                "--verbose",
                "--no-password"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Database backup created successfully: {backup_path}")
                return True
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return False
    
    def restore_database(self, backup_path: str):
        """استعادة قاعدة البيانات من النسخة الاحتياطية"""
        import subprocess
        
        try:
            db_url = settings.DATABASE_URL
            cmd = [
                "psql",
                db_url,
                "-f", backup_path,
                "--verbose"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Database restored successfully from: {backup_path}")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False
    
    def optimize_database(self):
        """تحسين قاعدة البيانات"""
        try:
            with self.get_session_context() as session:
                # تحليل الجداول
                session.execute("ANALYZE")
                
                # إعادة بناء الفهارس
                session.execute("REINDEX DATABASE")
                
                # تنظيف قاعدة البيانات
                session.execute("VACUUM")
                
            logger.info("Database optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            return False
    
    def get_table_stats(self) -> dict:
        """الحصول على إحصائيات الجداول"""
        try:
            with self.get_session_context() as session:
                query = """
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                ORDER BY tablename, attname
                """
                
                result = session.execute(query)
                stats = {}
                
                for row in result:
                    table_name = row.tablename
                    if table_name not in stats:
                        stats[table_name] = []
                    
                    stats[table_name].append({
                        "column": row.attname,
                        "distinct_values": row.n_distinct,
                        "correlation": row.correlation
                    })
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {}
    
    def get_query_performance(self) -> list:
        """الحصول على أداء الاستعلامات"""
        try:
            with self.get_session_context() as session:
                query = """
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                ORDER BY total_time DESC 
                LIMIT 10
                """
                
                result = session.execute(query)
                performance = []
                
                for row in result:
                    performance.append({
                        "query": row.query[:100] + "..." if len(row.query) > 100 else row.query,
                        "calls": row.calls,
                        "total_time": row.total_time,
                        "mean_time": row.mean_time,
                        "rows": row.rows
                    })
                
                return performance
                
        except Exception as e:
            logger.error(f"Error getting query performance: {e}")
            return []


# إنشاء مدير قاعدة البيانات
db_manager = DatabaseManager()


# دوال مساعدة للاستعلامات
def execute_raw_query(query: str, params: dict = None):
    """تنفيذ استعلام خام"""
    return db_manager.execute_query(query, params)


def get_single_value(query: str, params: dict = None):
    """الحصول على قيمة واحدة من الاستعلام"""
    return db_manager.execute_scalar(query, params)


def get_multiple_values(query: str, params: dict = None):
    """الحصول على قيم متعددة من الاستعلام"""
    return db_manager.execute_query(query, params)


# دوال للتحقق من صحة البيانات
def validate_database_integrity() -> dict:
    """التحقق من سلامة قاعدة البيانات"""
    try:
        with get_db_context() as db:
            # التحقق من الجداول المطلوبة
            required_tables = [
                'users', 'roles', 'accounts', 'journal_entries',
                'journal_entry_lines', 'customers', 'suppliers',
                'invoices', 'invoice_items', 'inventory_items',
                'employees', 'payroll_entries', 'audit_logs'
            ]
            
            missing_tables = []
            for table in required_tables:
                result = db.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    )
                """)
                if not result.scalar():
                    missing_tables.append(table)
            
            # التحقق من الفهارس
            missing_indexes = []
            required_indexes = [
                'idx_accounts_code', 'idx_journal_entries_date',
                'idx_invoices_customer', 'idx_audit_logs_timestamp'
            ]
            
            for index in required_indexes:
                result = db.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes 
                        WHERE indexname = '{index}'
                    )
                """)
                if not result.scalar():
                    missing_indexes.append(index)
            
            return {
                "status": "healthy" if not missing_tables and not missing_indexes else "issues",
                "missing_tables": missing_tables,
                "missing_indexes": missing_indexes,
                "total_tables": len(required_tables),
                "total_indexes": len(required_indexes)
            }
            
    except Exception as e:
        logger.error(f"Error validating database integrity: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def get_database_health() -> dict:
    """الحصول على صحة قاعدة البيانات"""
    try:
        # التحقق من الاتصال
        connection_ok = check_database_connection()
        
        # التحقق من السلامة
        integrity = validate_database_integrity()
        
        # معلومات قاعدة البيانات
        info = get_database_info()
        
        # إحصائيات الأداء
        stats = db_manager.get_table_stats()
        performance = db_manager.get_query_performance()
        
        return {
            "connection": connection_ok,
            "integrity": integrity,
            "info": info,
            "stats": stats,
            "performance": performance,
            "timestamp": "2024-01-01T00:00:00Z"  # سيتم تحديثها
        }
        
    except Exception as e:
        logger.error(f"Error getting database health: {e}")
        return {
            "connection": False,
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }