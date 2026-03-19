import functools
import inspect
import time
from base_module.exception.Business_exception import BusinessException
from base_module.info.log import Log
from base_module.result.result_enum import ResultEnum
from base_module.info.info_cache import InfoCache
from datetime import datetime

def Business(message: str , code: "ResultEnum" = ResultEnum.ERROR, rethrow: bool = True):
    """
    装饰器：捕获异常并使用 InfoCache 或 BusinessException
    :param code: 编码
    :param message: 异常提示信息
    :param rethrow: 是否抛出异常
    """
    def decorator(func):
        func.desc = message
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func.desc = message
                ts_s = int(time.time() * 1000)
                try:
                    Log.log(f"====== [{message}] [{func.__name__}]")
                    return func(*args, **kwargs)
                finally:
                    ts_e = int(time.time() * 1000)
                    Log.log(f"****** [{message}] [{func.__name__}] [{ts_e-ts_s}ms]")

            except Exception as e:
                # 获取被装饰函数调用堆栈，跳过 wrapper 自身
                trace = inspect.trace()
                # 构建异常
                exception = BusinessException(message,code, e, trace)
                if rethrow:
                    # 使用 from e 保留原始异常链
                    raise exception from e
                return None
        return wrapper
    return decorator