"""字段工具类"""
class FieldUtil:
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
    * 取出部分组成字符串
    * @Params list: 值
    * @Params part: 保留多少元素
    * @Params separator: 分隔符
    * @Params has_elide: 是否有省略号
    """
    @staticmethod
    def to_part_str(list:list, part:int = 0, separator:str = ',', has_elide:bool = True) -> str:
        if not list:
            return ""
        # 取前 part 个元素，如果 part <=0 或超出长度就取全部
        sub_list = list[:part] if 0 < part <= len(list) else list
        # 转字符串并用指定分隔符拼接
        result = separator.join(str(x) for x in sub_list)
        # 如果需要省略号且有被省略的元素，添加省略号
        if has_elide and len(list) > part:
            result += separator + "..."
        return result
