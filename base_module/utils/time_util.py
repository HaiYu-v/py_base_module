"""
时间工具类 TimeUtil
提供时间格式转换、获取日期边界等常用功能
"""
from datetime import datetime, date, timedelta
from typing import Union
import calendar


class TimeUtil:
    """时间工具类"""
    # 常量：默认dateTime字符串格式
    DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    # 常量：默认date字符串格式
    DEFAULT_DATE_FORMAT = "%Y-%m-%d"

    @staticmethod
    def _parse_to_datetime(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        内部方法：将输入统一转换为datetime对象

        Args:
            time_input: 时间字符串、date对象、datetime对象或None

        Returns:
            datetime对象
        """
        if time_input is None:
            return datetime.now()

        if isinstance(time_input, datetime):
            return time_input

        if isinstance(time_input, date):
            return datetime.combine(time_input, datetime.min.time())

        if isinstance(time_input, str):
            # 尝试多种格式解析
            formats = [
                TimeUtil.DEFAULT_DATETIME_FORMAT,
                TimeUtil.DEFAULT_DATE_FORMAT,
                "%Y-%m-%d %H:%M",
                "%Y-%m",
                "%Y",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(time_input, fmt)
                except ValueError:
                    continue
            raise ValueError(f"无法解析时间字符串: {time_input}")

        raise TypeError(f"不支持的时间类型: {type(time_input)}")

    @staticmethod
    def to_str(time_input: Union[str, date, datetime, None] = None,
               format_str: str = None) -> str:
        """
        转成时间字符串

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前时间）
            format_str: 格式字符串，默认为 DEFAULT_DATETIME_FORMAT

        Returns:
            格式化的时间字符串
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        if format_str is None:
            format_str = TimeUtil.DEFAULT_DATETIME_FORMAT
        return dt.strftime(format_str)

    @staticmethod
    def to_date(time_input: Union[str, date, datetime, None] = None) -> date:
        """
        转成Date对象

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前日期）

        Returns:
            date对象
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt.date()

    @staticmethod
    def to_datetime(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        转成DateTime对象

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前时间）

        Returns:
            datetime对象
        """
        return TimeUtil._parse_to_datetime(time_input)

    @staticmethod
    def to_year_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        转成【yyyy】时间字符串

        Args:
            time_input: 时间字符串、date对象、datetime对象或None

        Returns:
            格式为yyyy的字符串
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt.strftime("%Y")

    @staticmethod
    def to_year_month_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        转成【yyyy-MM】时间字符串

        Args:
            time_input: 时间字符串、date对象、datetime对象或None

        Returns:
            格式为yyyy-MM的字符串
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt.strftime("%Y-%m")

    @staticmethod
    def to_date_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        转成【yyyy-MM-dd】时间字符串

        Args:
            time_input: 时间字符串、date对象、datetime对象或None

        Returns:
            格式为yyyy-MM-dd的字符串
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt.strftime(TimeUtil.DEFAULT_DATE_FORMAT)

    @staticmethod
    def to_datetime_minute_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        转成【yyyy-MM-dd HH:mm】时间字符串

        Args:
            time_input: 时间字符串、date对象、datetime对象或None

        Returns:
            格式为yyyy-MM-dd HH:mm的字符串
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def to_datetime_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        转成【yyyy-MM-dd HH:mm:ss】时间字符串

        Args:
            time_input: 时间字符串、date对象、datetime对象或None

        Returns:
            格式为yyyy-MM-dd HH:mm:ss的字符串
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt.strftime(TimeUtil.DEFAULT_DATETIME_FORMAT)

    @staticmethod
    def get_day_start(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        得到日初的dateTime（00:00:00）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本日）

        Returns:
            当日00:00:00的datetime对象
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return datetime.combine(dt.date(), datetime.min.time())

    

    @staticmethod
    def get_day_end(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        得到日末的dateTime（23:59:59）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本日）

        Returns:
            当日23:59:59的datetime对象
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return datetime.combine(dt.date(), datetime.max.time()).replace(microsecond=0)

    @staticmethod
    def get_month_start(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        得到月初的dateTime（当月第一天00:00:00）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本月）

        Returns:
            当月第一天00:00:00的datetime对象
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return datetime(dt.year, dt.month, 1, 0, 0, 0)

    @staticmethod
    def get_month_end(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        得到月末的dateTime（当月最后一天23:59:59）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本月）

        Returns:
            当月最后一天23:59:59的datetime对象
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        last_day = calendar.monthrange(dt.year, dt.month)[1]
        return datetime(dt.year, dt.month, last_day, 23, 59, 59)

    @staticmethod
    def get_previous_month(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        获取上一个月的月初（上月第一天00:00:00）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前月）

        Returns:
            上一个月第一天00:00:00的datetime对象

        Examples:
            >>> TimeUtil.get_previous_month("2025-03-15")  # 返回 2025-02-01 00:00:00
            >>> TimeUtil.get_previous_month("2025-01-15")  # 返回 2024-12-01 00:00:00
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        # 计算上一个月
        if dt.month == 1:
            # 如果是1月，上一个月是去年12月
            return datetime(dt.year - 1, 12, 1, 0, 0, 0)
        else:
            return datetime(dt.year, dt.month - 1, 1, 0, 0, 0)

    @staticmethod
    def get_previous_month_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        获取上一个月的年月字符串（格式：yyyy-MM）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前月）

        Returns:
            格式为yyyy-MM的字符串

        Examples:
            >>> TimeUtil.get_previous_month_str("2025-03-15")  # 返回 "2025-02"
            >>> TimeUtil.get_previous_month_str("2025-01-15")  # 返回 "2024-12"
        """
        return TimeUtil.to_year_month_str(TimeUtil.get_previous_month(time_input))

    @staticmethod
    def get_previous_month_start(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        获取上一个月的月初（上月第一天00:00:00）

        这是 get_previous_month 的别名方法，使命名更明确

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前月）

        Returns:
            上一个月第一天00:00:00的datetime对象
        """
        return TimeUtil.get_previous_month(time_input)

    @staticmethod
    def get_previous_month_end(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        获取上一个月的月末（上月最后一天23:59:59）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前月）

        Returns:
            上一个月最后一天23:59:59的datetime对象

        Examples:
            >>> TimeUtil.get_previous_month_end("2025-03-15")  # 返回 2025-02-28 23:59:59
            >>> TimeUtil.get_previous_month_end("2025-01-15")  # 返回 2024-12-31 23:59:59
        """
        prev_month = TimeUtil.get_previous_month(time_input)
        return TimeUtil.get_month_end(prev_month)

    @staticmethod
    def get_previous_month_start_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        获取上一个月月初的日期字符串（格式：yyyy-MM-dd）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前月）

        Returns:
            格式为yyyy-MM-dd的字符串（上月第一天）

        Examples:
            >>> TimeUtil.get_previous_month_start_str("2025-03-15")  # 返回 "2025-02-01"
            >>> TimeUtil.get_previous_month_start_str("2025-01-15")  # 返回 "2024-12-01"
            >>> TimeUtil.get_previous_month_start_str()  # 返回当前月的上月第一天
        """
        prev_month = TimeUtil.get_previous_month(time_input)
        return TimeUtil.to_date_str(prev_month)

    @staticmethod
    def get_year_start(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        得到年初的dateTime（当年第一天00:00:00）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本年）

        Returns:
            当年第一天00:00:00的datetime对象
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return datetime(dt.year, 1, 1, 0, 0, 0)

    @staticmethod
    def get_year_end(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        得到年末的dateTime（当年最后一天23:59:59）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本年）

        Returns:
            当年最后一天23:59:59的datetime对象
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return datetime(dt.year, 12, 31, 23, 59, 59)

    @staticmethod
    def get_day_start_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        得到日初的时间字符串（yyyy-MM-dd）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本日）

        Returns:
            格式为yyyy-MM-dd的字符串
        """
        return TimeUtil.to_date_str(TimeUtil.get_day_start(time_input))

    @staticmethod
    def get_day_end_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        得到日末的时间字符串（yyyy-MM-dd）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本日）

        Returns:
            格式为yyyy-MM-dd的字符串
        """
        return TimeUtil.to_date_str(TimeUtil.get_day_end(time_input))

    @staticmethod
    def get_month_start_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        得到月初的时间字符串（yyyy-MM-dd，第一天）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本月）

        Returns:
            格式为yyyy-MM-dd的字符串（月初第一天，如2025-10-01）
        """
        return TimeUtil.to_date_str(TimeUtil.get_month_start(time_input))

    @staticmethod
    def get_month_end_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        得到月末的时间字符串（yyyy-MM-dd，最后一天）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本月）

        Returns:
            格式为yyyy-MM-dd的字符串（月末最后一天，如2025-10-31）
        """
        return TimeUtil.to_date_str(TimeUtil.get_month_end(time_input))

    @staticmethod
    def get_month_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        得到月份的时间字符串（yyyy-MM）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前月）

        Returns:
            格式为yyyy-MM的字符串（如2025-12）
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt.strftime('%Y-%m')

    @staticmethod
    def get_year_start_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        得到年初的时间字符串（yyyy-MM-dd，第一天）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本年）

        Returns:
            格式为yyyy-MM-dd的字符串（年初第一天，如2025-01-01）
        """
        return TimeUtil.to_date_str(TimeUtil.get_year_start(time_input))

    @staticmethod
    def get_year_end_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        得到年末的时间字符串（yyyy-MM-dd，最后一天）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认本年）

        Returns:
            格式为yyyy-MM-dd的字符串（年末最后一天，如2025-12-31）
        """
        return TimeUtil.to_date_str(TimeUtil.get_year_end(time_input))

    @staticmethod
    def get_next_day(time_input: Union[str, date, datetime, None] = None) -> datetime:
        """
        获取下一天的dateTime（同一时间点，+1天）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认今天）

        Returns:
            下一天同一时间点的datetime对象
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt + timedelta(days=1)

    @staticmethod
    def get_next_day_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        获取下一天的日期字符串（yyyy-MM-dd）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认今天）

        Returns:
            格式为yyyy-MM-dd的字符串（下一天）
        """
        return TimeUtil.to_date_str(TimeUtil.get_next_day(time_input))

    @staticmethod
    def get_day_str(time_input: Union[str, date, datetime, None] = None) -> str:
        """
        获取当前日期的字符串（yyyy-MM-dd）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认当前日期）

        Returns:
            格式为yyyy-MM-dd的字符串
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt.strftime('%Y-%m-%d')

    @staticmethod
    def get_previous_day(time_input: Union[str, date, datetime, None] = None,previous:int = 1) -> datetime:
        """
        获取前一天的dateTime（同一时间点，-1天）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认今天）
        
        Returns:
            前一天同一时间点的datetime对象
        """
        dt = TimeUtil._parse_to_datetime(time_input)
        return dt - timedelta(days=previous)

    @staticmethod
    def get_previous_day_str(time_input: Union[str, date, datetime, None] = None,previous:int = 1) -> str:
        """
        获取前一天的日期字符串（yyyy-MM-dd）

        Args:
            time_input: 时间字符串、date对象、datetime对象或None（默认今天）
        
        Returns:
            格式为yyyy-MM-dd的字符串（前一天）
        """
        return TimeUtil.to_date_str(TimeUtil.get_previous_day(time_input,previous))



def main():
    """执行案例，展示TimeUtil的各种用法"""

    print("=" * 80)
    print("TimeUtil 时间工具类使用案例")
    print("=" * 80)

    # 测试数据准备
    test_datetime_str = "2025-10-24 15:30:45"
    test_date_str = "2025-10-24"
    test_datetime_obj = datetime(2025, 10, 24, 15, 30, 45)
    test_date_obj = date(2025, 10, 24)

    print("\n【1. 常量定义】")
    print(f"DEFAULT_DATETIME_FORMAT: {TimeUtil.DEFAULT_DATETIME_FORMAT}")
    print(f"DEFAULT_DATE_FORMAT: {TimeUtil.DEFAULT_DATE_FORMAT}")

    print("\n【2. 转换为时间字符串 - to_str()】")
    print(f"当前时间: {TimeUtil.to_str()}")
    print(f"从datetime字符串: {TimeUtil.to_str(test_datetime_str)}")
    print(f"自定义格式: {TimeUtil.to_str(test_datetime_str, '%Y年%m月%d日 %H时%M分%S秒')}")

    print("\n【3. 转换为Date对象 - to_date()】")
    print(f"从datetime字符串: {TimeUtil.to_date(test_datetime_str)}")
    print(f"从date字符串: {TimeUtil.to_date(test_date_str)}")
    print(f"从datetime对象: {TimeUtil.to_date(test_datetime_obj)}")
    print(f"从date对象: {TimeUtil.to_date(test_date_obj)}")

    print("\n【4. 转换为DateTime对象 - to_datetime()】")
    print(f"从datetime字符串: {TimeUtil.to_datetime(test_datetime_str)}")
    print(f"从date字符串: {TimeUtil.to_datetime(test_date_str)}")
    print(f"从date对象: {TimeUtil.to_datetime(test_date_obj)}")

    print("\n【5. 转换为【yyyy】格式 - to_year_str()】")
    print(f"从datetime字符串: {TimeUtil.to_year_str(test_datetime_str)}")
    print(f"从date对象: {TimeUtil.to_year_str(test_date_obj)}")
    print(f"当前年份: {TimeUtil.to_year_str()}")

    print("\n【6. 转换为【yyyy-MM】格式 - to_year_month_str()】")
    print(f"从datetime字符串: {TimeUtil.to_year_month_str(test_datetime_str)}")
    print(f"从date字符串: {TimeUtil.to_year_month_str(test_date_str)}")
    print(f"当前年月: {TimeUtil.to_year_month_str()}")

    print("\n【7. 转换为【yyyy-MM-dd】格式 - to_date_str()】")
    print(f"从datetime字符串: {TimeUtil.to_date_str(test_datetime_str)}")
    print(f"从datetime对象: {TimeUtil.to_date_str(test_datetime_obj)}")
    print(f"当前日期: {TimeUtil.to_date_str()}")

    print("\n【8. 转换为【yyyy-MM-dd HH:mm】格式 - to_datetime_minute_str()】")
    print(f"从datetime字符串: {TimeUtil.to_datetime_minute_str(test_datetime_str)}")
    print(f"从datetime对象: {TimeUtil.to_datetime_minute_str(test_datetime_obj)}")
    print(f"当前时间（到分钟）: {TimeUtil.to_datetime_minute_str()}")

    print("\n【9. 转换为【yyyy-MM-dd HH:mm:ss】格式 - to_datetime_str()】")
    print(f"从datetime字符串: {TimeUtil.to_datetime_str(test_datetime_str)}")
    print(f"从date对象: {TimeUtil.to_datetime_str(test_date_obj)}")
    print(f"当前时间: {TimeUtil.to_datetime_str()}")

    print("\n【10. 获取日初（00:00:00） - get_day_start()】")
    print(f"指定日期的日初（字符串）: {TimeUtil.get_day_start(test_datetime_str)}")
    print(f"指定日期的日初（date对象）: {TimeUtil.get_day_start(test_date_obj)}")
    print(f"今天的日初: {TimeUtil.get_day_start()}")

    print("\n【11. 获取日末（23:59:59） - get_day_end()】")
    print(f"指定日期的日末（字符串）: {TimeUtil.get_day_end(test_datetime_str)}")
    print(f"指定日期的日末（datetime对象）: {TimeUtil.get_day_end(test_datetime_obj)}")
    print(f"今天的日末: {TimeUtil.get_day_end()}")

    print("\n【12. 获取月初 - get_month_start()】")
    print(f"指定月份的月初（字符串）: {TimeUtil.get_month_start(test_datetime_str)}")
    print(f"指定月份的月初（date对象）: {TimeUtil.get_month_start(test_date_obj)}")
    print(f"本月月初: {TimeUtil.get_month_start()}")
    print(f"指定年月的月初: {TimeUtil.get_month_start('2025-02')}")

    print("\n【13. 获取月末 - get_month_end()】")
    print(f"指定月份的月末（字符串）: {TimeUtil.get_month_end(test_datetime_str)}")
    print(f"指定月份的月末（datetime对象）: {TimeUtil.get_month_end(test_datetime_obj)}")
    print(f"本月月末: {TimeUtil.get_month_end()}")
    print(f"2月的月末（闰年）: {TimeUtil.get_month_end('2024-02')}")
    print(f"2月的月末（平年）: {TimeUtil.get_month_end('2025-02')}")

    print("\n【14. 获取年初 - get_year_start()】")
    print(f"指定年份的年初（字符串）: {TimeUtil.get_year_start(test_datetime_str)}")
    print(f"指定年份的年初（date对象）: {TimeUtil.get_year_start(test_date_obj)}")
    print(f"本年年初: {TimeUtil.get_year_start()}")
    print(f"指定年份的年初: {TimeUtil.get_year_start('2024')}")

    print("\n【15. 获取年末 - get_year_end()】")
    print(f"指定年份的年末（字符串）: {TimeUtil.get_year_end(test_datetime_str)}")
    print(f"指定年份的年末（datetime对象）: {TimeUtil.get_year_end(test_datetime_obj)}")
    print(f"本年年末: {TimeUtil.get_year_end()}")
    print(f"指定年份的年末: {TimeUtil.get_year_end('2024')}")

    print("\n【16. 综合应用案例】")
    print("场景：计算某个月的完整时间范围")
    month_str = "2025-10"
    month_start = TimeUtil.get_month_start(month_str)
    month_end = TimeUtil.get_month_end(month_str)
    print(f"月份: {month_str}")
    print(f"开始时间: {TimeUtil.to_datetime_str(month_start)}")
    print(f"结束时间: {TimeUtil.to_datetime_str(month_end)}")

    print("\n场景：格式转换链")
    original = "2025-10-24 15:30:45"
    print(f"原始时间: {original}")
    date_obj = TimeUtil.to_date(original)
    print(f"转为date对象: {date_obj}")
    datetime_obj = TimeUtil.to_datetime(date_obj)
    print(f"再转为datetime对象: {datetime_obj}")
    final_str = TimeUtil.to_year_month_str(datetime_obj)
    print(f"最终转为年月字符串: {final_str}")

    print("\n【17. 获取日初时间字符串 - get_day_start_str()】（返回yyyy-MM-dd格式）")
    print(f"指定日期的日初（字符串）: {TimeUtil.get_day_start_str(test_datetime_str)}")
    print(f"指定日期的日初（date对象）: {TimeUtil.get_day_start_str(test_date_obj)}")
    print(f"今天的日初: {TimeUtil.get_day_start_str()}")

    print("\n【18. 获取日末时间字符串 - get_day_end_str()】（返回yyyy-MM-dd格式）")
    print(f"指定日期的日末（字符串）: {TimeUtil.get_day_end_str(test_datetime_str)}")
    print(f"指定日期的日末（datetime对象）: {TimeUtil.get_day_end_str(test_datetime_obj)}")
    print(f"今天的日末: {TimeUtil.get_day_end_str()}")

    print("\n【19. 获取月初时间字符串 - get_month_start_str()】（返回yyyy-MM-dd格式，第一天）")
    print(f"指定月份的月初（字符串）: {TimeUtil.get_month_start_str(test_datetime_str)}")
    print(f"指定月份的月初（date对象）: {TimeUtil.get_month_start_str(test_date_obj)}")
    print(f"本月月初: {TimeUtil.get_month_start_str()}")
    print(f"指定年月的月初: {TimeUtil.get_month_start_str('2025-02')}")

    print("\n【20. 获取月末时间字符串 - get_month_end_str()】（返回yyyy-MM-dd格式，最后一天）")
    print(f"指定月份的月末（字符串）: {TimeUtil.get_month_end_str(test_datetime_str)}")
    print(f"指定月份的月末（datetime对象）: {TimeUtil.get_month_end_str(test_datetime_obj)}")
    print(f"本月月末: {TimeUtil.get_month_end_str()}")
    print(f"2月的月末（闰年）: {TimeUtil.get_month_end_str('2024-02')}")
    print(f"2月的月末（平年）: {TimeUtil.get_month_end_str('2025-02')}")

    print("\n【21. 获取年初时间字符串 - get_year_start_str()】（返回yyyy-MM-dd格式，第一天）")
    print(f"指定年份的年初（字符串）: {TimeUtil.get_year_start_str(test_datetime_str)}")
    print(f"指定年份的年初（date对象）: {TimeUtil.get_year_start_str(test_date_obj)}")
    print(f"本年年初: {TimeUtil.get_year_start_str()}")
    print(f"指定年份的年初: {TimeUtil.get_year_start_str('2024')}")

    print("\n【22. 获取年末时间字符串 - get_year_end_str()】（返回yyyy-MM-dd格式，最后一天）")
    print(f"指定年份的年末（字符串）: {TimeUtil.get_year_end_str(test_datetime_str)}")
    print(f"指定年份的年末（datetime对象）: {TimeUtil.get_year_end_str(test_datetime_obj)}")
    print(f"本年年末: {TimeUtil.get_year_end_str()}")
    print(f"指定年份的年末: {TimeUtil.get_year_end_str('2024')}")

    print("\n【23. 字符串方法应用案例】")
    print("场景：快速获取查询时间范围字符串")
    query_date = "2025-10-24"
    print(f"查询日期: {query_date}")
    print(f"日期范围: {TimeUtil.get_day_start_str(query_date)} ~ {TimeUtil.get_day_end_str(query_date)}")

    query_month = "2025-10"
    print(f"\n查询月份: {query_month}")
    print(f"月份范围: {TimeUtil.get_month_start_str(query_month)} ~ {TimeUtil.get_month_end_str(query_month)}")

    query_year = "2025"
    print(f"\n查询年份: {query_year}")
    print(f"年份范围: {TimeUtil.get_year_start_str(query_year)} ~ {TimeUtil.get_year_end_str(query_year)}")

    print("\n" + "=" * 80)
    print("案例演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()

