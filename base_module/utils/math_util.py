from decimal import Decimal
import math
from typing import Union
import numpy as np

# 进行数学计算的工具类
class MathUtil:
    """ ----------------------------------------------------------------------------------
    * 求比值
    * @Params val1: 分子
    * @Params val2: 分母
    * @Params decimal: 保留小数位数
    * @Params is_percent: 是否是百分比
    """
    @staticmethod
    def ratio(val1:int , val2:int,decimal:int = 2,is_percent:bool = False) -> Union[int, str]:
        ret = None
        if(val1 == 0 and val2 == 0):
            ret = 1
        elif(val2 == 0):
            return '-'
        else:
            ret = round(val1 / val2,decimal)
        if(is_percent):
            ret = f"{ret * 100}%"
        return ret

    """ ----------------------------------------------------------------------------------
    * 转成int
    * @Params val: 值
    * @Params default: 默认值
    """
    @staticmethod
    def to_int(val, default:int = 0) -> int:
        try:
            return int(val)
        except Exception:
            return default


    """ ----------------------------------------------------------------------------------
    * 获取最小,最大,平均值, 中位数, 众数
    * @Params arr: 数组
    * @Params default: 默认值
    """
    @staticmethod
    def calc_int_stats(arr:list) -> list:
        length = len(arr)
        data = np.array(arr)
        avg = int(round(data.mean()))                 # 平均值 → int
        median = int(round(np.median(data)))          # 中位数 → int
        min_val = int(data.min())                     # 最小值 → int
        max_val = int(data.max())                     # 最大值 → int
        mode = int(stats.mode(data, keepdims=False).mode)  # 众数 → int

        return [min_val, max_val, avg, median, mode,length]

    """ ----------------------------------------------------------------------------------
    * 千分位逗号
    * @Params arr: 数组
    * @Params default: 默认值
    """
    @staticmethod
    def format_cell(x):
        if isinstance(x, int):
            return f"{x:,}"
        if isinstance(x, float):
            return f"{x:,.2f}"
        return str(x)

    """ ----------------------------------------------------------------------------------
    * 得到整数的百分比,四位整数
    * @Params num: 百分比
    * @Params place: 整数位数
    """
    @staticmethod
    def integer_percentage(num,place=4):
            # 处理负数
            negative = num < 0
            num = abs(num)
            
            # 去掉小数点
            s = format(Decimal(str(num)), "f").replace('0.', '').replace('.', '')
            
            # 如果长度 >= 4，取前place位
            if len(s) >= place:
                res = int(s[:place])
            else:
                # 小于4位，补零到place位
                res = int(s.ljust(place, '0'))
            
            # 还原符号
            return -res if negative else res

    """ ----------------------------------------------------------------------------------
    * 保证百分比合计为total, 最后一项等于total - 其它项之和
    * @Params map: 一组百分比 key, value
    * @Params total: 百分比合计值
    * @Params last_total: 最后一项是否等于total - 其它项之和
    """
    @staticmethod
    def balance_to_total(map:dict,total = 10000,last_total = True):
        k, cur = max(map.items(), key=lambda x: x[1])
        digit = MathUtil.diff_digit(cur,total)
        map = {k: int(v * (10 ** digit)) for k, v in map.items()}

        if not last_total:
            return map
        keys = list(map.keys())
        last_key = keys[-1]

        others_sum = sum(map[k] for k in keys[:-1])
        map[last_key] = total - others_sum
        return map

    """ ----------------------------------------------------------------------------------
    * 计算差多少位
    * @Params map: 一组百分比 key, value
    * @Params total: 百分比合计值
    """
    @staticmethod
    def diff_digit(n,num = 10000):
        if n == 0:
                return 0  # 0 和 10000 数量级无限差

        return int(math.log10(abs(num)) - math.log10(abs(n)))

if __name__ == '__main__':
    print('\n')
    print(MathUtil.balance_to_total({'a': 0.0536, 'b': 0.2100,'c': 0.431000,'d': 0.0091000,'e': 0.2900}))
    # print(integer_percentage(536))