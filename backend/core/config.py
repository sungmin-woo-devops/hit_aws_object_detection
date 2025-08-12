import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # JWT 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-256-bit-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:Sungmin3391!@db.wqgeljfdsovdfjynrkfl.supabase.co:5432/postgres"
    )
    
    # 외부 서비스 설정
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_SECRET_KEY: Optional[str] = os.getenv("SUPABASE_SECRET_KEY")
    MONGO_URI: Optional[str] = os.getenv("MONGO_URI", "your-mongodb-atlas-uri")
    
    # CORS 설정
    ALLOWED_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"


# 전역 설정 인스턴스
settings = Settings()
