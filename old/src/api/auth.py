"""
API认证模块
提供JWT Token生成与验证
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

SECRET_KEY = os.getenv('API_SECRET_KEY', 'quantaitrade-secret-key-change-in-production')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        str: JWT令牌字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        Optional[Dict]: 解码后的数据，验证失败返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token验证失败: {e}")
        return None


def get_current_user(token: str) -> Optional[str]:
    """
    从token获取当前用户名

    Args:
        token: JWT令牌字符串

    Returns:
        Optional[str]: 用户名，验证失败返回None
    """
    payload = verify_token(token)
    if payload:
        return payload.get('sub')
    return None