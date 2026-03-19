from enum import Enum

'''
结果的枚举

10 开头的表示的是失败

100，101 表示不同类型的失败

1001，1002 表示某类型下的不同失败

'''
class ResultEnum(Enum):
    # 基础失败
    ERROR = (1000,"操作失败")
    SUCCESS = (200, "操作成功")


    def __init__(self, code: int, message: str):
        self._code = code
        self._message = message

    @property
    def code(self) -> int:
        return self._code

    @property
    def message(self) -> str:
        return self._message

    def __str__(self):
        return f"[{self._code}] {self._message}"
