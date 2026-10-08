import os
import threading
from datetime import datetime
from typing import Optional
from uuid import uuid4

from snowflake import SnowflakeGenerator
from sqlalchemy import text
from sqlmodel import Field, SQLModel

# 雪花ID机器号（0-1023）。多进程/多机部署时各实例必须填不同的值，
# 通过环境变量 SNOWFLAKE_WORKER_ID 指定，未设置时默认 0
SNOWFLAKE_WORKER_ID = int(os.getenv("SNOWFLAKE_WORKER_ID", "0"))

_generator = SnowflakeGenerator(SNOWFLAKE_WORKER_ID)
_generator_lock = threading.Lock()


def generate_id() -> int:
    """生成雪花ID（64位趋势递增整数）"""
    with _generator_lock:
        return next(_generator)


def generate_uuid() -> str:
    """生成32位UUID（去除连字符）"""
    return uuid4().hex


class BaseModel(SQLModel):
    """实体基类：包含所有表的公共字段"""

    id: Optional[int] = Field(default_factory=generate_id, primary_key=True, description="唯一ID")
    creator_id: Optional[int] = Field(default=0, description="创建者用户ID")
    # DDL: `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
    create_time: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        description="创建时间（数据库生成）",
    )
    # DDL: `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
    update_time: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        description="更新时间（数据库生成，记录被修改时自动刷新）",
    )
    dr: str = Field(default='N', index=True, max_length=1, description="删除标记(Y/N)")

    def desc() -> str:
        return ''
