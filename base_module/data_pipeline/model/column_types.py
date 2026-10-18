"""自定义列类型：JSON 列的读写口径。

| 类型 | 落点 | 用在哪 |
|------|------|--------|
| `PayloadJSON` | SQLite 落 TEXT / MySQL 落 JSON | 任务的 `input_data` / `output_data` / `extra_dict` |
|  |  | （`BaseTask` 上以 `sa_type=PayloadJSON` 声明，三列都可空） |

`PayloadJSON` 只做「写」这一侧的兜底：pydantic 对象自动 dump 成 JSON，
dict / list / None 原样放行。读这一侧不在这里还原成对象 —— 表模型不知道 `T` 是谁
（原因见 `base_task.py` 顶部关于泛型的说明），还原交给 `BaseTask.input_payload()`
/ `output_payload()`，由调用方把模型类传进来。
"""

from typing import Any

from pydantic import BaseModel as PydanticModel
from sqlalchemy import JSON, TypeDecorator


class PayloadJSON(TypeDecorator):
    """JSON 列：吃 pydantic 对象也吃裸 dict。"""

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        """写库前：pydantic 模型 dump 成 JSON 原生结构，其余原样交给 JSON 列。"""
        if isinstance(value, PydanticModel):
            return value.model_dump(mode="json")
        return value

    # 读库不重写：JSON 列反序列化出来就是 dict / list，保持「库里是什么就是什么」。

    # ⚠ 别改用 pydantic 的 `field_serializer` 做这件事：SQLAlchemy 的 JSON 列走的是
    #   `json.dumps`，不经 pydantic 的序列化钩子，实测写了不生效（塞对象仍然抛
    #   `Object of type X is not JSON serializable`）。
