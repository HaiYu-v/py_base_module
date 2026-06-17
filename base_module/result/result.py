from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel
from result.result_enum import BaseResultEnum,ResultEnum

T = TypeVar('T')


class Result(BaseModel, Generic[T]):
    """统一返回体"""
    code: int
    message: str
    data: Optional[T] = None

    def __init__(self, code: int, message: str, data: Optional[T] = None, **kwargs):
        super().__init__(code=code, message=message, data=data, **kwargs)

    @staticmethod
    def success(data: Any = None) -> "Result":
        """成功返回"""
        return Result.from_enum(ResultEnum.SUCCESS, data)

    @staticmethod
    def error(data: Any = None) -> "Result":
        """失败返回"""
        return Result.from_enum(ResultEnum.ERROR, data)

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
