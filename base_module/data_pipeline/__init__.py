"""data_pipeline：数据流水线的实体与表结构。

其他项目直接：

```python
from data_pipeline import BaseTask, TaskState
```

⚠ **`BaseTask` 是基类、不是一张表**（用户口径：任务表在本地 sqlite，**一种任务一张表**）：
用它的项目各自建表，列从这儿继承，载荷两列用 `payload_column()` 每张表各造一个：

```python
from data_pipeline import BaseTask, payload_column

class MaterialSaveTask(BaseTask, table=True):
    __tablename__ = "material_save_task"
    input_data: Optional[MaterialSave] = Field(default=None, sa_column=payload_column("启动数据"))
```

公共列（`id` / `version` / `creator_id` / `create_time` / `update_time` / `dr` / `prompt`）
在 `base_module` 的 `base_model.BaseModel` 上，本包的表继承它、只写自己的列。

⚠ 表模型在**包导入时**就加载，别改成惰性导入：
`SQLModel.metadata.create_all` 只建已注册的表，少导一个模型模块就少建一张表。
"""

from .model import (
    DEFAULT_DEADLINE_HOURS,
    OPEN_STATES,
    BaseTask,
    PayloadJSON,
    PayloadT,
    TaskState,
    payload_column,
)

__all__ = [
    "BaseTask",
    "TaskState",
    "PayloadT",
    "PayloadJSON",
    "DEFAULT_DEADLINE_HOURS",
    "OPEN_STATES",
    "payload_column",
]
