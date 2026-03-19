import platform
import os
import matplotlib.pyplot as plt
import unicodedata
from io import BytesIO
from openpyxl import Workbook
from matplotlib.font_manager import FontProperties
from base_module import MathUtil

def get_system_font():
    system = platform.system()

    # Linux
    if system == 'Linux':
        candidates = [
            '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/arphic/ukai.ttc',
        ]

    # Windows
    elif system == 'Windows':
        candidates = [
            r'C:\Windows\Fonts\msyh.ttc',      # 微软雅黑
            r'C:\Windows\Fonts\simhei.ttf',    # 黑体
            r'C:\Windows\Fonts\simsun.ttc',    # 宋体
        ]

    # macOS
    elif system == 'Darwin':
        candidates = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
        ]

    else:
        candidates = []

    for font_path in candidates:
        if os.path.exists(font_path):
            return FontProperties(fname=font_path)

    return None


"""表格工具类"""
class TableUtil:
    FONT = get_system_font()
    @staticmethod
    def format_cell(x):
        if isinstance(x, int):
            return f"{x:,}"
        if isinstance(x, float):
            return f"{x:,.2f}"
        return str(x)

    """ ----------------------------------------------------------------------------------
    * 计算长度
    * @Params arr: 数组
    * @Params default: 默认值
    """
    @staticmethod
    def text_display_width(text: str) -> float:
        width = 0
        for ch in text:
            # 中文 / 全角字符
            if unicodedata.east_asian_width(ch) in ('W', 'F'):
                width += 1.2
            # 数字
            elif ch.isdigit():
                width += 0.9
            # 大写字母
            elif ch.isupper():
                width += 1.2
            # 其他
            else:
                width += 0.6
        return width

    """ ----------------------------------------------------------------------------------
    * 创建表格图片
    * @Params title: 标题
    * @Params cols: 列
    * @Params rows: 行
    """
    @staticmethod
    def create_table_img(title: str, cols: list[str], rows: list[list]) -> BytesIO:
        cols = [MathUtil.format_cell(col) for col in cols]
        rows = [[MathUtil.format_cell(cell) for cell in row] for row in rows]
        # =========================
        # 4️⃣ 计算每列最大显示宽度
        # =========================
        col_max_widths = []
        num_cols = len(cols)

        for col_idx in range(num_cols):
            texts = [str(cols[col_idx])]
            for row in rows:
                texts.append(str(row[col_idx]))

            max_width = max(TableUtil.text_display_width(t) for t in texts)
            col_max_widths.append(max_width)

        # =========================
        # 5️⃣ 转换为 colWidths（比例）
        # =========================
        CHAR_WIDTH = 0.045  # 中文友好系数
        col_widths = [max(w, 1e-6) * CHAR_WIDTH for w in col_max_widths]

        total_width = sum(col_widths) or 1.0
        col_widths = [w / total_width for w in col_widths]

        min_ratio = 0.03
        max_ratio = 0.25
        col_widths = [min(max(w, min_ratio), max_ratio) for w in col_widths]
        total_width = sum(col_widths) or 1.0
        col_widths = [w / total_width for w in col_widths]


        # =========================
        # 6️⃣ figure 尺寸自适应
        # =========================
        fig_width = max(12, sum(col_max_widths) * 0.20)
        fig_height = max(2.6, 1.2 + 0.30 * len(rows))

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.axis('off')


        # 5️⃣ 添加表格标题
        table_title = title
        ax.set_title(table_title, fontsize=14, fontweight='bold', pad=8,fontproperties=TableUtil.FONT)

        # 6️⃣ 创建表格
        table = ax.table(
            cellText=rows,
            colLabels=cols,
            colWidths=col_widths,
            cellLoc='center',
            loc='upper center',
        )

        # 7️⃣ 调整样式
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 1.5)  # 调整行高
        for (r, c), cell in table.get_celld().items():
            if c == 0 or r == 0:
                cell.set_text_props(ha='center', va='center',fontproperties=TableUtil.FONT)
            else:
                cell.set_text_props(ha='right', va='center',fontproperties=TableUtil.FONT)
                cell.PAD = 0.02  # 可选：左对齐后给一点内边距，视觉更舒服

        # 8️⃣ 保存为图片
        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=300)
        plt.close(fig)
        buf.seek(0)

        return buf


        """ ----------------------------------------------------------------------------------
    
    * 创建表格图片
    * @Params title: 标题
    * @Params cols: 列
    * @Params rows: 行
    """
    @staticmethod
    def create_table_excel(title: str, cols: list[str], rows: list[list]) -> BytesIO:
        # 创建Excel工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = title
        
        # 写入表头
        ws.append(list(cols))
        
        # 写入数据
        for row in list:
            ws.append(row)
        
        # 根据表头设置列宽
        for idx, header in enumerate(cols, start=1):
            column_letter = ws.cell(row=1, column=idx).column_letter
            header_length = len(str(header))
            adjusted_width = header_length + 8
            ws.column_dimensions[column_letter].width = adjusted_width
            
        # 将Excel文件保存到内存
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        return excel_file