from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, ConfigDict
from base_module.result.result_enum import BaseResultEnum,ResultEnum

T = TypeVar('T')


class Result(BaseModel, Generic[T]):
    """统一返回体"""
    code: int
    message: str
    data: Optional[T] = None

    def __init__(self, code: int, message: str, data: Optional[T] = None, **kwargs):
        super().__init__(code=code, message=message, data=data, **kwargs)

    @staticmethod
    def success(message:str = None) -> "Result":
        """成功返回"""
        return Result._enum(ResultEnum.SUCCESS, message)

    @staticmethod
    def error(message:str = None) -> "Result":
        """失败返回"""
        return Result._enum(ResultEnum.ERROR, message)
    
    @staticmethod
    def success_data(message:str = None, data: Any = None) -> "Result":
        """成功返回"""
        return Result._enum(ResultEnum.SUCCESS, message, data)

    @staticmethod
    def error_data(message:str = None, data: Any = None) -> "Result":
        """失败返回"""
        return Result._enum(ResultEnum.ERROR, message, data)

    @staticmethod
    def from_enum(result_enum: BaseResultEnum,  data: Any = None) -> "Result":
        """从枚举创建返回体"""
        return Result._enum(ResultEnum.ERROR, None, data)
    
    def _enum(result_enum: BaseResultEnum, message:str = None, data: Any = None) -> "Result":
        """从枚举创建返回体"""
        return Result(
            code=result_enum.code,
            message=result_enum.message if message is None else message,
            data=data
        )
    
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": {}
            }
        }
    )
