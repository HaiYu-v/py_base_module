
import inspect
import os
from base_module.result.result_enum import BaseResultEnum,ResultEnum

'''
自定义的业务异常
1.强制使用BaseResultEnum，保证有统一规范的错误信息（self.code.message），也能保留下自定义的信息
2.继承堆栈，和异常嵌套信息（多异常嵌套时，只嵌套message，而不嵌套堆栈）

异常消息的示例：
common.Business_exception.BusinessException:
-> [doudian_order.py] [_get_order_list_with_author] IPSA茵芙莎官方旗舰店_48438640_查询一下数据量失败
-> [doudian_order.py] [_get_order_list] BusinessException:IPSA茵芙莎官方旗舰店_48438640_通过API获取订单列表失败:code=40004, msg=非法的参数, sub_msg=订单查询只支持查询最近90天内的数据
'''

class BusinessException(Exception):

    def __init__(self, message: str = None, code: BaseResultEnum = None, cause: Exception = None, stack: list[inspect.FrameInfo] = None):
        """
        :param code: BaseResultEnum 返回结果枚举
        :param message: 可选，覆盖 code 的默认消息
        :param cause: 可选，原始异常
        :param Bcause: 可选，BusinessException异常, 继承code,保留最初异常的code
        """

        # 没有提供code，就使用默认code
        self.code = cause.code if (cause and isinstance(cause, BusinessException)) else (
            code if code else ResultEnum.ERROR)

        # 如果提供了 message，用 message，否则用code的消息
        msg = message if message else code.message

        # 获取创建此异常的函数和文件名
        stack = inspect.stack() if not stack else stack
        if len(stack) > 1:
            caller_method = stack[1].function
            caller_file_name = os.path.basename(stack[1].filename)
        else:
            caller_method = "unknown"
            caller_file_name = "unknown"

        prefix = f"\n-> [{caller_file_name}] [{caller_method}]"

        if cause:
            # 拼接原始异常信息
            msg = f"{prefix} [{type(cause).__name__}] {msg}:{cause}"
            super().__init__(msg)

            # 在 Python 3 中可以使用 __cause__ 保留原始异常栈
            self.__cause__ = cause
        else:
            msg = f"{prefix} [{type(self).__name__}] {msg}"
            super().__init__(msg)