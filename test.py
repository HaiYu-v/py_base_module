from enum import Enum
from base_hyb import ByteUtil

class ByteEnum(Enum):
    def __new__(cls, total, bytes):
        obj = object.__new__(cls)
        obj._value_ = total
        obj.total = total
        obj.bytes = bytes
        obj.count = total * bytes
        return obj

    # 达人数量,5w个达人
    kol = (50000, 600)
    # 视频 每个达人多少视频
    aweme = (100, 650)
    # 直播 每个达人多少直播
    live = (100, 850)
    # 达人日记录，每月每个达人30个记录
    kol_daily = (30,25)
    # 直播日记录，每月每个达人20个直播记录
    live_daily = (20, 55)
    # 视频日记录，每月每个达人400个视频记录
    aweme_daily = (400, 40)
    # 视频商品，每个视频记录带2个商品
    item_aweme = (2, 350)
    # 直播商品，每个直播记录带10个商品
    item_live = (10, 350)

# 每次抓取10%的达人
KOL_CARW  = 0.1
# 12个月
MONTH = 12

kol_bytes = ByteEnum.kol.count
aweme_bytes = ByteEnum.kol.total * ByteEnum.aweme.count
live_bytes = ByteEnum.kol.total * ByteEnum.live.count
count1:int = kol_bytes + aweme_bytes + live_bytes
ret1 = ByteUtil.format_bytes(count1)

kol_daily_bytes = ByteEnum.kol.total * KOL_CARW * ByteEnum.kol_daily.count
live_daily_bytes = ByteEnum.kol.total * KOL_CARW * ByteEnum.live_daily.count
aweme_daily_bytes = ByteEnum.kol.total * KOL_CARW * ByteEnum.aweme_daily.count
item_aweme_daily_bytes = ByteEnum.kol.total * KOL_CARW * ByteEnum.item_aweme.total * ByteEnum.item_aweme.count
item_live_daily_bytes = ByteEnum.kol.total * KOL_CARW * ByteEnum.item_live.total * ByteEnum.item_live.count

count2 = MONTH * (kol_daily_bytes + live_daily_bytes + aweme_daily_bytes + item_aweme_daily_bytes +  item_live_daily_bytes)
ret2 = ByteUtil.format_bytes(count2)

ret = ByteUtil.format_bytes(count1 + count2)

print(ret)