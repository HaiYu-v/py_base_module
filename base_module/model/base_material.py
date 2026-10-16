from datetime import date

from base_module import BaseModel
from pydantic import Field
class BaseMaterial(BaseModel):
    platform: str = Field(default="", description="平台")
    site: str = Field(default="", description="站点")
    projectId: int = Field(default=0, description="挂到哪个项目（0 = 不挂）")
    projectName: str = Field(default="", description="项目名")
    author: str = Field(default="", description="作者")
    url: str = Field(default="", description="来源地址")
    kind: str = Field(default="pending", description="素材类型")
    publishDate: date = Field(default=None, description="发布时间")
    title: str = Field(default="", description="素材名")
    title_cn: str = Field(default="", description="素材中文名")
    text: str = Field(default="", description="正文")
    text_cn: str = Field(default="", description="正文中文译文")
    desc: str = Field(default="", description="描述")
    desc_cn: str = Field(default="", description="描述中文译文")
    materialPath: str = Field(default="", description="素材本体（视频 / 音频 / 文本，相对仓库根）")
    coverImagePath: str = Field(default="", description="素材自带的封面底图（相对仓库根）")