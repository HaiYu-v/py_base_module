import threading

class CountryUtil:
    """
    国家代码转中文名称工具类 (静态方法版)。
    无需实例化，直接调用 CountryUtils.get_name(code)。
    """
    
    _code_map = None
    _lock = threading.Lock()

    # --- 数据定义区 ---
    
    _BASE_MAP = {
        # --- 核心大国 ---
        'CN': '中国', 'US': '美国', 'JP': '日本', 'DE': '德国', 'GB': '英国',
        'FR': '法国', 'IN': '印度', 'IT': '意大利', 'BR': '巴西', 'CA': '加拿大',
        'RU': '俄罗斯', 'KR': '韩国', 'AU': '澳大利亚', 'ES': '西班牙',
        'MX': '墨西哥', 'CH': '瑞士', 'NL': '荷兰', 'SE': '瑞典', 'PL': '波兰',
        
        # --- 东南亚 (ASEAN) 全量 ---
        'SG': '新加坡', 'MY': '马来', 'TH': '泰国', 'VN': '越南',
        'PH': '菲律宾', 'ID': '印尼', 
        'MM': '缅甸', 'KH': '柬埔寨', 'LA': '老挝', 'BN': '文莱', 'TL': '东帝汶',

        # --- 中东 & 非洲 & 其他热门 ---
        'AE': '阿联酋', 'SA': '沙特', 'IL': '以色列', 'TR': '土耳其',
        'EG': '埃及', 'ZA': '南非', 'NG': '尼日利亚', 'AR': '阿根廷',
        'CL': '智利', 'NZ': '新西兰', 'NO': '挪威', 'DK': '丹麦', 'FI': '芬兰',
        'IE': '爱尔兰', 'PT': '葡萄牙', 'GR': '希腊', 'UA': '乌克兰',
        'PK': '巴基斯坦', 'IR': '伊朗', 'IQ': '伊拉克', 'KE': '肯尼亚',
        'CO': '哥伦比亚', 'PE': '秘鲁', 'HU': '匈牙利', 'CZ': '捷克',
        'RO': '罗马尼亚', 'BG': '保加利亚', 'BY': '白俄罗斯', 'AT': '奥地利',
        'BE': '比利时'
    }

    _ALPHA2_TO_ALPHA3 = {
        'CN': 'CHN', 'US': 'USA', 'JP': 'JPN', 'DE': 'DEU', 'GB': 'GBR',
        'FR': 'FRA', 'IN': 'IND', 'IT': 'ITA', 'BR': 'BRA', 'CA': 'CAN',
        'RU': 'RUS', 'KR': 'KOR', 'AU': 'AUS', 'ES': 'ESP', 'MX': 'MEX',
        'CH': 'CHE', 'NL': 'NLD', 'SE': 'SWE', 'PL': 'POL', 'SG': 'SGP',
        'MY': 'MYS', 'TH': 'THA', 'VN': 'VNM', 'PH': 'PHL', 'ID': 'IDN',
        'MM': 'MMR', 'KH': 'KHM', 'LA': 'LAO', 'BN': 'BRN', 'TL': 'TLS',
        'AE': 'ARE', 'SA': 'SAU', 'IL': 'ISR', 'TR': 'TUR', 'EG': 'EGY',
        'ZA': 'ZAF', 'NG': 'NGA', 'AR': 'ARG', 'CL': 'CHL', 'NZ': 'NZL',
        'NO': 'NOR', 'DK': 'DNK', 'FI': 'FIN', 'IE': 'IRL', 'PT': 'PRT',
        'GR': 'GRC', 'UA': 'UKR', 'PK': 'PAK', 'IR': 'IRN', 'IQ': 'IRQ',
        'KE': 'KEN', 'CO': 'COL', 'PE': 'PER', 'HU': 'HUN', 'CZ': 'CZE',
        'RO': 'ROU', 'BG': 'BGR', 'BY': 'BLR', 'AT': 'AUT', 'BE': 'BEL'
    }

    _SPECIAL_REGIONS = {
        'HK': '香港',
        'MO': '澳门',
        'TW': '台湾',
        'PS': '巴勒斯坦',
        'VA': '梵蒂冈'
    }

    @classmethod
    def _init_map(cls, use_short_indonesia: bool = False):
        """内部方法：构建查找字典 (懒加载)"""
        if cls._code_map is not None:
            return

        with cls._lock:
            # 双重检查锁定，防止多线程重复初始化
            if cls._code_map is not None:
                return

            temp_map = {}
            
            # 1. 处理基础国家
            for code, name in cls._BASE_MAP.items():
                final_name = name
                if code == 'ID' and use_short_indonesia:
                    final_name = '印尼'
                
                # 写入 2 位
                temp_map[code.upper()] = final_name
                # 写入 3 位
                if code in cls._ALPHA2_TO_ALPHA3:
                    temp_map[cls._ALPHA2_TO_ALPHA3[code].upper()] = final_name

            # 2. 处理特殊地区
            for code, name in cls._SPECIAL_REGIONS.items():
                temp_map[code.upper()] = name
            
            cls._code_map = temp_map

    @classmethod
    def get_name(cls, code: str, use_short_indonesia: bool = False) -> str:
        """
        根据国家代码获取中文名称 (静态方法)。
        
        :param code: 国家/地区代码 (如 'CN', 'usa', ' HK ')
        :param default: 找不到时的默认返回值
        :param use_short_indonesia: 是否将 "印度尼西亚" 显示为 "印尼"。
                                      注意：如果全局希望固定为简称，可在首次调用前设置，
                                      或者每次调用时传入此参数（会导致重新初始化，建议全局统一）。
                                      *优化策略*：为了性能，通常建议在项目启动时确定一次风格。
                                      此处为了灵活性，如果检测到风格变化且已初始化，会简单处理或忽略变化。
                                      **最佳实践**：项目启动时调用一次 reset_map 确定风格，之后直接调用 get_name(code)。
        :return: 中文名称
        """
        # 简单的风格切换处理：如果 map 已存在但风格不匹配，这里为了性能不做动态重建，
        # 除非你调用 reset_map。 
        # 为了简化使用，我们假设 use_short_indonesia 仅在第一次初始化时生效，
        # 或者每次调用都检查（会有轻微性能损耗）。
        # 下面采用：如果 map 为空则初始化；如果不空且风格不一致，为了简单起见，
        # 本静态版本建议：若需切换风格，请先调用 reset_map()。
        
        if cls._code_map is None:
            cls._init_map(use_short_indonesia)
        
        if not code or not isinstance(code, str):
            return code
        
        clean_code = code.strip().upper()
        return cls._code_map.get(clean_code, code)

    @classmethod
    def reset_map(cls, use_short_indonesia: bool = False):
        """
        重置并重新初始化映射表（用于切换“印尼”简称模式等）。
        在项目启动时调用一次即可。
        """
        cls._code_map = None
        cls._init_map(use_short_indonesia)

    @classmethod
    def get_all_codes(cls) -> list:
        """返回所有支持的代码列表"""
        if cls._code_map is None:
            cls._init_map()
        return sorted(list(cls._code_map.keys()))

# ==========================================
# 使用示例
# ==========================================
if __name__ == "__main__":
    # 场景 A: 默认模式 (印度尼西亚 = 印度尼西亚)
    print("--- 默认模式 ---")
    print(f"CN: {CountryUtils.get_name('CN')}")
    print(f"HK: {CountryUtils.get_name('HK')}")
    print(f"ID: {CountryUtils.get_name('ID')}")
    print(f"mmr (缅甸3位码): {CountryUtils.get_name('mmr')}")

    # 场景 B: 简称模式 (印度尼西亚 = 印尼)
    # 需要先重置地图以应用新配置
    print("\n--- 简称模式 (重置后) ---")
    CountryUtils.reset_map(use_short_indonesia=True)
    print(f"ID: {CountryUtils.get_name('ID')}")
    print(f"IDN: {CountryUtils.get_name('IDN')}")
    
    # 场景 C: 未知代码处理
    print("\n--- 异常处理 ---")
    print(f"XX: {CountryUtils.get_name('XX', default='查无此地')}")
    print(f"None: {CountryUtils.get_name(None)}")
    
    # 场景 D: 东南亚检查
    print("\n--- 东南亚快速检查 ---")
    sea_codes = ["SG", "MY", "TH", "VN", "PH", "ID", "MM", "KH", "LA", "BN"]
    for c in sea_codes:
        print(f"{c}: {CountryUtils.get_name(c)}")