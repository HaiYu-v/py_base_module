"""data_pipeline：数据流水线的实体与表结构。

其他项目直接：

```python
from data_pipeline import BaseTask, TaskState
```

⚠ **`BaseTask` 是基类、不是一张表**（用户口径：任务表在本地 sqlite，**一种任务一张表**）：
用它的项目各自建表，列从这儿继承 —— **载荷三列（`input_data` / `output_data` / `extra_dict`）
基类上已经声明好了、都可空，子类不用再写**：

```python
from data_pipeline import BaseTask

class MaterialSaveTask(BaseTask, table=True):
    __tablename__ = "material_save_task"
    # input_data / output_data / extra_dict 继承自 BaseTask，不用声明

    # 想让载荷类型写实（可选，老写法也仍然兼容，记得 import payload_column）：
    # input_data: Optional[MaterialSave] = Field(default=None, sa_column=payload_column("启动数据"))
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
