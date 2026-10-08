from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, ConfigDict
from base_module.result.result_enum import BaseResultEnum,ResultEnum

T = TypeVar('T')


class Result(BaseModel, Generic[T]):
    """统一返回体"""
    code: int
    msg: str
    data: Optional[T] = None

    def __init__(self, code: int, msg: str, data: Optional[T] = None, **kwargs):
        super().__init__(code=code, msg=msg, data=data, **kwargs)

    @staticmethod
    def success(msg:str = None) -> "Result":
        """成功返回"""
        return Result._enum(ResultEnum.SUCCESS, msg)

    @staticmethod
    def error(msg:str = None) -> "Result":
        """失败返回"""
        return Result._enum(ResultEnum.ERROR, msg)
    
    @staticmethod
    def success_data(msg:str = None, data: Any = None) -> "Result":
        """成功返回"""
        return Result._enum(ResultEnum.SUCCESS, msg, data)

    @staticmethod
    def error_data(msg:str = None, data: Any = None) -> "Result":
        """失败返回"""
        return Result._enum(ResultEnum.ERROR, msg, data)

    @staticmethod
    def from_enum(result_enum: BaseResultEnum,  data: Any = None) -> "Result":
        """从枚举创建返回体"""
        return Result._enum(ResultEnum.ERROR, None, data)
    
    def _enum(result_enum: BaseResultEnum, msg:str = None, data: Any = None) -> "Result":
        """从枚举创建返回体"""
        return Result(
            code=result_enum.code,
            msg=result_enum.msg if msg is None else msg,
            data=data
        )
    
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 200,
                "msg": "操作成功",
                "data": {}
            }
        }
    )
