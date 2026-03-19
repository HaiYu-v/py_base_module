class ByteUtil:
    """
    将字节转为 KB / MB / GB / TB 自动选择最合适单位
    :param size: 字节数(int)
    :param precision: 保留小数位
    :return: 字符串，例如 "1.23 MB"
    """
    @classmethod
    def format_bytes(cls, size: int, precision: int = 2) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        index = 0
        size = float(size)

        while size >= 1024 and index < len(units) - 1:
            size /= 1024
            index += 1

        return f"{size:.{precision}f} {units[index]}"