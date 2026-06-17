from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel
from result.result_enum import BaseResultEnum

T = TypeVar('T')


class Result(BaseModel, Generic[T]):
    """统一返回体"""
    code: int
    message: str
    data: Optional[T] = None

    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> "Result":
        """成功返回"""
        return Result(
            code=200,
            message=message,
            data=data
        )

    @staticmethod
    def error(code: int = 1000, message: str = "操作失败", data: Any = None) -> "Result":
        """失败返回"""
        return Result(
            code=code,
            message=message,
            data=data
        )

    @staticmethod
    def from_enum(result_enum: BaseResultEnum, data: Any = None) -> "Result":
        """从枚举创建返回体"""
        return Result(
            code=result_enum.code,
            message=result_enum.message,
            data=data
        )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": {}
            }
        }
