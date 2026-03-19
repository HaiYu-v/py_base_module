from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel
from result.result_enum import ResultEnum

T = TypeVar('T')


class ResultResponse(BaseModel, Generic[T]):
    """统一返回体"""
    code: int
    message: str
    data: Optional[T] = None

    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> "ResultResponse":
        """成功返回"""
        return ResultResponse(
            code=200,
            message=message,
            data=data
        )

    @staticmethod
    def error(code: int = 1000, message: str = "操作失败", data: Any = None) -> "ResultResponse":
        """失败返回"""
        return ResultResponse(
            code=code,
            message=message,
            data=data
        )

    @staticmethod
    def from_enum(result_enum: ResultEnum, data: Any = None) -> "ResultResponse":
        """从枚举创建返回体"""
        return ResultResponse(
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
