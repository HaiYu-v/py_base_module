from typing import Union, List, Tuple
from base_module.utils.time_util import TimeUtil

class SqlUtil:
    # is_number: True表示日期是 20251101 这种格式，False为 2025-11-01

    """ -------------------------------------------------------------------
     * 判断日期是否存在范围内
    """
    @staticmethod
    def date_between(field:str,date_s,date_e,is_number:bool = False,is_houe:bool = False)->str:
        date_e = TimeUtil.get_next_day_str(date_e)
        if is_number:
            date_s = date_s.replace("-", "")
            date_e = date_e.replace("-", "")

        if is_houe:
            date_s += ('00' if is_number else ' 00')
            date_e += ('00' if is_number else ' 00')
        return f"and {field} >= '{date_s}' and {field} < '{date_e}'"

    """ -------------------------------------------------------------------
     * 判断日期是否存在交集
    """
    @staticmethod
    def date_hasIntersection(field_date_start:str,field_date_end:str,date_s,date_e,is_number:bool = False)->str:
        if is_number:
            date_s = date_s.replace("-", "")
            date_e = date_e.replace("-", "")
        return f"AND ({field_date_start} <= '{date_e}' AND {field_date_end} >= '{date_s}')"

    @staticmethod
    def fields(fields: List[Union[str, Tuple[str, str]]]) -> str:
        parts = []
        for f in fields:
            if isinstance(f, tuple):
                parts.append(f"{f[0]} AS {f[1]}")
            else:
                parts.append(f)
        return  ", ".join(parts)

    @staticmethod
    def create_fields(fields: list[tuple[str, str]]) -> str:
        parts = []
        for f in fields:
            parts.append(f"{f[0]} {f[1]}")
        return  f"( {', '.join(parts)} )"

    @staticmethod
    def get_placeholders(fields: List[Union[str, Tuple[str, str]]]) -> str:
        """生成SQL占位符，例如: %s, %s, %s"""
        count = len(fields)
        return ", ".join(["%s"] * count)

    @staticmethod
    def in_sql(field:str, fields:list[Union[str,int]],is_not:bool = False,is_number:bool = False) -> str:
        if(not fields or len(fields) == 0): return ''

        if is_number:
            values = ", ".join(f'{x}' for x in fields)
        else:
            values = ", ".join(f"'{x}'" for x in fields)
        return f"AND {field} {'not in' if is_not else 'in'} ({values})"

    @staticmethod
    def eq_sql(field:str, value:Union[str,int],is_not:bool = False,is_number:bool = False) -> str:
        if not value: return ''

        if is_number:
            value_sql = value
        else:
            value_sql = f"'{value}'"
        return f"AND {field} {'<>' if is_not else '='} {value_sql}"