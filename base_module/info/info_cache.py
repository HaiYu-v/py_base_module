import inspect
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from collections import OrderedDict
from collections.abc import KeysView
import threading
from base_module.exception.Business_exception import BusinessException
from base_module.result.result_enum import ResultEnum
from base_module.info.log import Log


class InfoCache:
    """
    信息缓存

    用于缓存一些基础信息，便于打印和输出日志

    Author: 胡亚北
    Version: 1.0.0
    Date: 2025-10-21
    """

    # 是否打印日志
    IS_PRINT_LOG = True

    # 常量定义
    DESC = "desc"
    START_TIME = "startTime"
    RUNNING = "running"
    ID = "id"
    STATUS = "status"
    NOTHING_STATUS = "nothing"
    EXECUTING_STATUS = "executing"
    FAILED_STATUS = "failed"
    SUCCESS_STATUS = "success"
    EXCEPTIONAL_STATUS = "exceptional"
    DATE_FORMATTER = "%Y-%m-%d %H:%M:%S.%f"

    # 类级别的ID计数器（线程安全）
    _next_id = 0
    _id_lock = threading.Lock()

    def __init__(self, desc: Optional[str] = None, tier: Optional[str] = '', prefix: Optional[str] = ''):
        """
        初始化InfoCache

        Args:
            desc: 描述信息
            date_format: 日期格式，默认为 '%Y-%m-%d %H:%M:%S.%f'
        """
        # 使用OrderedDict保证顺序（类似Java的TreeMap）
        self._info: Dict[str, Any] = OrderedDict()

        # 时间格式
        self._formatter = self.DATE_FORMATTER
        # 层次
        self._tier = tier
        # 前缀
        self._prefix = prefix

        if desc:
            self.put(self.DESC, desc)

    @classmethod
    def build(cls, desc: Optional[str] = None, tier: Optional[str] = '', prefix: Optional[str] = '') -> 'InfoCache':
        """
        构建InfoCache实例

        Args:
            desc: 描述信息
            date_format: 日期格式

        Returns:
            InfoCache实例
        """
        info = cls(desc, tier, prefix)
        info.executing()
        return info

    # -----------------------------------------------------------------------------------------------------------------
    # 打印日志
    def log(self, message: str):
        if self.IS_PRINT_LOG:
            preStr = f"[{self._prefix}{self._tier}] " if self._prefix else ''
            Log.log(f"{preStr}{message}")

    # -----------------------------------------------------------------------------------------------------------------
    # 开始计时

    def start_time(self) -> float:
        """
        开始计时

        Returns:
            开始时间戳（毫秒）
        """
        self.put(self.START_TIME, int(time.time() * 1000))

    # -----------------------------------------------------------------------------------------------------------------
    # 计时结束

    def end_time(self) -> Optional[int]:
        """
        计时结束

        Returns:
            运行时间（毫秒），如果未开始计时则返回None
        """
        self.put(self.RUNNING, int(time.time() * 1000) - self.get(self.START_TIME))

    def start(self, key: str) -> float:
        self.put(key, int(time.time() * 1000))

    def end(self, key: str) -> float:
        end = int(time.time() * 1000)
        if (self.get(key)):
            start = self.get(key)
            if not isinstance(start, int):
                return None
            running = end - start
            if self.IS_PRINT_LOG:
                self.log(f"【执行耗时】{key}：{self.get_timeStr(start)} => {running}ms")
            self.put(key, f"{self.get_timeStr(start)} => {running}ms")
            return
        return None

    # -----------------------------------------------------------------------------------------------------------------
    # ID

    def id(self) -> str:
        """
        生成递增ID

        Returns:
            递增的ID字符串
        """
        with self._id_lock:
            InfoCache._next_id += 1
            id_value = str(InfoCache._next_id)

        self.put(self.ID, id_value)
        return id_value

    # -----------------------------------------------------------------------------------------------------------------
    # ID(UUID)

    def id_uuid(self) -> str:
        """
        生成UUID

        Returns:
            UUID字符串
        """
        id_value = str(uuid.uuid4())
        self.put(self.ID, id_value)
        return id_value

    # -----------------------------------------------------------------------------------------------------------------
    # 计数

    def auto_increment(self, key: str) -> int:
        """
        对指定key进行计数

        Args:
            key: 计数的键名

        Returns:
            当前计数值
        """
        count_value = self.get(key) or 0
        if not isinstance(count_value, int):
            count_value = 0

        count_value += 1
        self.put(key, count_value)
        return count_value

    def count(self, key: str, value: int) -> int:
        if (value is None):
            if self.IS_PRINT_LOG:
                self.log(f"【计数】{key}：value is None")
            return None

        if (self.get(key) and (not isinstance(self.get(key), int))):
            if self.IS_PRINT_LOG:
                self.log(f"【计数】{key}：oldValue is not INT")
            return None

        count_value = (self.get(key) or 0) + value
        self.put(key, count_value)
        if self.IS_PRINT_LOG:
            self.log(f"【计数】{key}：{count_value}")
        return count_value

    # -----------------------------------------------------------------------------------------------------------------
    # 状态方法

    def failed(self, message: str):
        """失败状态"""
        if message is not None:
            self.put(f'{self.FAILED_STATUS}_message', message)
        self.put(self.STATUS, self.FAILED_STATUS)
        self.end_time()

        if self.IS_PRINT_LOG:
            if self.get(f'{self.FAILED_STATUS}_message') is not None:
                self.log(f"【失败原因】{self.get(f'{self.FAILED_STATUS}_message')}")

            self.log(f"===== 【执行失败！！！】{self.get(self.DESC)} =====\n")

        return self

    '''
        1. 创建BusinessException
        2. 修改任务状态为异常
    '''

    def cbe(self, message: str = None, code: ResultEnum = None,  cause: Exception = None,
            stack: list[inspect.FrameInfo] = None) -> BusinessException:
        stack = inspect.stack() if not stack else stack
        be = BusinessException(message, code,  cause, stack)
        self.exceptional(str(be))
        return be

    def exceptional(self, message: str = None):
        """异常状态"""
        if message is not None:
            self.put(f'{self.EXCEPTIONAL_STATUS}_message', message)
        self.put(self.STATUS, self.EXCEPTIONAL_STATUS)
        self.end_time()

        if self.IS_PRINT_LOG:
            if self.get(f'{self.EXCEPTIONAL_STATUS}_message') is not None:
                self.log(f"【异常消息】{self.get(f'{self.EXCEPTIONAL_STATUS}_message')}")

            self.log(f"===== 【执行异常！！！】{self.get(self.DESC)} =====\n")

        return self

    def executing(self, message: str = None):
        """执行中状态"""
        if message is not None:
            self.put(f'{self.EXECUTING_STATUS}_message', message)

        # 有状态后,就不可以再修改成执行状态了
        if (self.get(self.STATUS)):
            return self

        self.put(self.STATUS, self.EXECUTING_STATUS)

        if self.IS_PRINT_LOG:
            self.log(f"===== 【开始执行】{self.get(self.DESC)} =====")

            if self.get(f'{self.EXECUTING_STATUS}_message') is not None:
                self.log(f"【执行消息】{self.get(f'{self.EXECUTING_STATUS}_message')}")

        self.start_time()

    def try_success(self, message: str = None):
        """尝试成功"""

        # 失败或异常后就不能再成功
        if (self.get(self.STATUS) == self.EXCEPTIONAL_STATUS or self.get(self.STATUS) == self.FAILED_STATUS):
            return self

        if message is not None:
            self.put(f'{self.SUCCESS_STATUS}_message', message)
        self.put(self.STATUS, self.SUCCESS_STATUS)
        self.end_time()

        if self.IS_PRINT_LOG:
            if self.get(f'{self.SUCCESS_STATUS}_message') is not None:
                self.log(f"【成功消息】{self.get(f'{self.SUCCESS_STATUS}_message')}")

            self.log(f"===== 【执行成功】{self.get(self.DESC)} =====\n")
        return self

    # -----------------------------------------------------------------------------------------------------------------
    # 设置子信息缓存:put_sub_info

    def psi(self, key: str, value: 'InfoCache'):
        self._info[key] = value.get_info()

    # 创建子info:create_sub_info
    def csi(self, key: str, prefix: Optional[str] = '') -> 'InfoCache':
        sub_info = InfoCache.build(key, tier=f"{self._tier}>", prefix=prefix)
        self.psi(key, sub_info)
        return sub_info


    # -----------------------------------------------------------------------------------------------------------------
    # 设置信息

    def put(self, key: str, value: Any = None) -> Any:
        """
        设置信息
        """
        self._info[key] = value

        # 如果value是数组类型，特殊处理
        if self.IS_PRINT_LOG:
            if isinstance(value, (list, tuple)):
                self.log(f"{key}：{self.print_array(value)}")
            else:
                self.log(f"{key}：{self.print_object(value)}")
        return value

    def print_object(self, value: Any):
        if value is not None and not isinstance(value, (int, float, str, bool, dict)):
            return type(value).__name__
        else:
            return value

    def print_array(self, value: Any):
        if isinstance(value, (list, tuple)):
            if len(value) < 10:
                return f"{value}"
            else:
                return f"共{len(value)}个：{value[:10]} ..."

    # -----------------------------------------------------------------------------------------------------------------
    # 获取信息

    def get(self, key: str) -> Any:
        """
        获取信息

        Args:
            key: 键名

        Returns:
            对应的值
        """
        return self._info.get(key)

    # -----------------------------------------------------------------------------------------------------------------
    # 删除

    def remove(self, key: str) -> Any:
        """
        删除信息

        Args:
            key: 键名

        Returns:
            被删除的值
        """
        return self._info.pop(key, None)

    # -----------------------------------------------------------------------------------------------------------------
    # 包含

    def contains_key(self, key: str) -> bool:
        """
        检查是否包含指定键

        Args:
            key: 键名

        Returns:
            是否包含
        """
        return key in self._info

    # -----------------------------------------------------------------------------------------------------------------
    # JSON格式的信息

    def to_json(self) -> str:
        """
        转换为JSON字符串

        Returns:
            JSON字符串
        """
        info_copy = self._prepare_info_for_json()
        return json.dumps(info_copy, ensure_ascii=False)

    # -----------------------------------------------------------------------------------------------------------------
    # 获取信息（格式化）

    def to_json_pretty(self) -> str:
        """
        转换为格式化的JSON字符串

        Returns:
            格式化的JSON字符串
        """
        info_copy = self._prepare_info_for_json()
        return json.dumps(info_copy, ensure_ascii=False, indent=2)

    def _prepare_info_for_json(self) -> Dict[str, Any]:
        """
        准备用于JSON序列化的信息（转换时间戳和不可序列化类型）
        """
        info_copy = self._info.copy()

        # 递归转换dict_keys为列表（关键修复）
        def convert_dict_keys(obj):
            if isinstance(obj, dict):
                # 处理字典的值
                return {k: convert_dict_keys(v) for k, v in obj.items()}
            elif isinstance(obj, KeysView):
                # 将dict_keys转换为列表
                return list(obj)
            elif isinstance(obj, (list, tuple)):
                # 处理列表/元组中的元素
                return [convert_dict_keys(item) for item in obj]
            else:
                return obj

        # 先转换所有可能的dict_keys为列表
        info_copy = convert_dict_keys(info_copy)

        # 原有时间戳转换逻辑（保持不变）
        if self.START_TIME in info_copy and isinstance(info_copy[self.START_TIME], (int, float)):
            timestamp_ms = info_copy[self.START_TIME]
            info_copy[self.START_TIME] = self.get_timeStr(timestamp_ms)

        return info_copy

    def get_timeStr(self, timestamp) -> str:
        if timestamp is None:
            return None
        dt = datetime.fromtimestamp(timestamp / 1000.0)
        return dt.strftime(self._formatter)[:-3]

    # -----------------------------------------------------------------------------------------------------------------
    # 设置日期格式

    def set_formatter(self, formatter: str) -> None:
        """
        设置日期格式

        Args:
            formatter: 日期格式字符串
        """
        self._formatter = formatter

    # -----------------------------------------------------------------------------------------------------------------
    # 获取一些常见属性

    def get_desc(self) -> Optional[str]:
        """获取描述"""
        obj = self.get(self.DESC)
        return obj if isinstance(obj, str) else None

    def get_start_str(self) -> Optional[str]:
        """获取开始时间（字符串格式）"""
        obj = self.get(self.START_TIME)
        return obj if isinstance(obj, str) else None

    def get_start_datetime(self) -> Optional[datetime]:
        """
         * 获取开始时间（datetime对象）
         *
         * @param  无
         * @return datetime对象，如果时间戳不存在则返回None
        """
        obj = self.get(self.START_TIME)
        if obj and isinstance(obj, (int, float)):
            # 将毫秒级时间戳转换为datetime对象
            return datetime.fromtimestamp(obj / 1000)
        elif obj and isinstance(obj, str):
            # 如果是字符串格式，尝试解析
            try:
                return datetime.strptime(obj, self._formatter)
            except ValueError:
                return None
        elif isinstance(obj, datetime):
            # 如果已经是datetime对象，直接返回
            return obj
        return None

    def get_start_timestamp(self) -> Optional[int]:
        """获取开始时间戳（毫秒）"""
        obj = self.get(self.START_TIME)
        if obj and isinstance(obj, str):
            try:
                dt = datetime.strptime(obj, self._formatter)
                return int(dt.timestamp() * 1000)
            except ValueError:
                return None
        elif isinstance(obj, (int, float)):
            return int(obj)
        return None

    def get_running_time(self) -> Optional[int]:
        """获取运行时间"""
        obj = self.get(self.RUNNING)
        return obj if isinstance(obj, int) else None

    def get_count(self, key: str) -> Optional[int]:
        """获取计数值"""
        obj = self.get(key)
        return obj if isinstance(obj, int) else 0

    def get_str(self, key: str) -> Optional[str]:
        """获取字符串值"""
        obj = self.get(key)
        return obj if isinstance(obj, str) else None

    def get_id(self) -> Optional[str]:
        """获取ID"""
        obj = self.get(self.ID)
        return obj if isinstance(obj, str) else None

    def get_status(self) -> Optional[str]:
        """获取状态"""
        obj = self.get(self.STATUS)
        return obj if isinstance(obj, str) else None

    # -----------------------------------------------------------------------------------------------------------------
    # 状态判断

    def is_success(self) -> bool:
        """是否成功"""
        return self.SUCCESS_STATUS == self.get_status()

    def is_failed(self) -> bool:
        """是否失败"""
        return self.FAILED_STATUS == self.get_status()

    def is_exceptional(self) -> bool:
        """是否异常"""
        return self.EXCEPTIONAL_STATUS == self.get_status()

    def is_executing(self) -> bool:
        """是否执行中"""
        return self.EXECUTING_STATUS == self.get_status()

    # -----------------------------------------------------------------------------------------------------------------
    # Getter和Setter
    def get_info(self) -> Dict[str, Any]:
        """获取所有信息"""
        return self._info

    def set_info(self, info: Dict[str, Any]) -> None:
        """设置所有信息"""
        self._info = info


def main():
    info = InfoCache.build("测试")
    info.executing()
    info.try_success()
    print(info.to_json_pretty())


if __name__ == '__main__':
    main()
