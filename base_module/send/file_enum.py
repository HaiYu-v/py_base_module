from enum import Enum

'''
文件的枚举

'''
class FileEnum(Enum):
    # 基础失败
    XLSM = ('xlsm',"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    XLSX = ('xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    XLS  = ('xls',  'application/vnd.ms-excel')

    # Word
    DOC  = ('doc',  'application/msword')
    DOCX = ('docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    # PDF
    PDF  = ('pdf',  'application/pdf')

    # 图片
    JPG  = ('jpg',  'image/jpeg')
    JPEG = ('jpeg', 'image/jpeg')
    PNG  = ('png',  'image/png')
    GIF  = ('gif',  'image/gif')
    BMP  = ('bmp',  'image/bmp')
    WEBP = ('webp', 'image/webp')
    def __init__(self, ext: str, mime: str):
        self._ext = ext
        self._mime = mime

    @property
    def ext(self) -> str:
        return self._ext

    @property
    def mime(self) -> str:
        return self._mime

    def __str__(self):
        return f"[{self._ext}] {self._mime}"