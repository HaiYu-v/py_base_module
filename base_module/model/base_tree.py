from sqlmodel import Field
from .base_model import BaseModel



class BaseTree(BaseModel):
    """实体基类：包含所有表的公共字段"""

    p_id: int = Field(default=None, index=True, description="父编码")
    name: str = Field(description="名称")
    full_path:str = Field(default='', index=True, max_length=255, description="完整路径")
    level: int = Field(default=1, description="层级")
    sort: str = Field(default=1, description="排序, 使用分数索引")
    lv1: int = Field(default=None, index=True, description="一级编码")
    lv2: int = Field(default=None, index=True, description="二级编码")
    lv3: int = Field(default=None, index=True, description="三级编码")
    lv4: int = Field(default=None, index=True, description="四级编码")

