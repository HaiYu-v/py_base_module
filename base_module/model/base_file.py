"""文件基类：所有"文件类"实体的公共字段与派生属性。

继承 BaseModel，已自带 id / creator_id / create_time / update_time / dr，
本类只补充"文件"本身的信息，不描述文件归属（业务表用自己的外键指向文件表）。

约定：
- path 是相对存储根目录的目录，统一 '/' 分隔、不带首尾斜杠，'' 表示根目录
- extension 小写且不含点，如 mp4
- 子类自己声明表名，写法：class VideoFile(BaseFile, table=True): __tablename__ = "video_file"
"""
from pydantic import field_validator
from sqlalchemy import BigInteger, Column
from sqlmodel import Field

from .base_model import BaseModel


class BaseFile(BaseModel):
    """文件基类：不单独建表，由子类继承"""

    # ---------- 文件基本信息 ----------
    name: str = Field(max_length=255, description="文件名(不含后缀)")
    extension: str = Field(default="", max_length=32, description="后缀，小写，不含点，如 mp4")
    original_name: str = Field(default=None, max_length=255, description="用户上传时的原始文件名")
    # 文件可能超过 2G，int 默认映射成 INT，这里显式用 BIGINT
    size: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False, default=0, comment="文件大小，单位字节"),
    )
    duration: float = Field(default=None, description="时长，单位秒；非音视频为空")

    # ---------- 存储信息 ----------
    path: str = Field(default="", max_length=1024, description="所在目录(相对存储根目录)")
    storage: str = Field(default="local", max_length=32, description="存储类型：local / s3 / oss ...")
    sha256: str = Field(default=None, index=True, max_length=64, description="内容哈希，可用于去重")

    mime_type: str = Field(default=None, max_length=128, description="MIME 类型")

    # ---------- 写入归一化 ----------
    # 注意：pydantic 默认只在实例化时校验，直接赋值不会触发；
    # 所以下面的派生属性也做了兜底清洗，不能只靠这两个校验器
    @field_validator("extension")
    @classmethod
    def _normalize_extension(cls, v: str) -> str:
        return (v or "").strip().lstrip(".").lower()

    @field_validator("path")
    @classmethod
    def _normalize_path(cls, v: str) -> str:
        return "/".join(p for p in (v or "").replace("\\", "/").split("/") if p)

    # ---------- 派生属性 ----------
    @property
    def full_name(self) -> str:
        """带后缀的完整文件名"""
        ext = (self.extension or "").strip().lstrip(".").lower()
        return f"{self.name}.{ext}" if ext else self.name

    @property
    def full_path(self) -> str:
        """目录 + 完整文件名(相对存储根目录)"""
        dir_path = (self.path or "").strip("/")
        return f"{dir_path}/{self.full_name}" if dir_path else self.full_name

    @property
    def is_deleted(self) -> bool:
        """软删除判断（复用 BaseModel 的 dr 标记）"""
        return (self.dr or "N").upper() == "Y"
