"""领域模型：表结构 / 纯数据对象。

| 文件 | 是什么 |
|------|--------|
| `base_task.py` | 任务表的**基类** `BaseTask`：一行 = 一条流水线任务 —— ⚠ 它**不是一张表** |
| `column_types.py` | 自定义列类型：`PayloadJSON` 负责 `input_data` / `output_data` 的写入 dump |

⚠ **一种任务一张表**（用户口径）：具体任务表（`youtube_task` / `material_save_task` /
`listening_task`）由**用它的项目**各自在 `reader_common/model/` 里定义，继承 `BaseTask`。
所以这里不再有「通用任务表」；`payload_column()` 就是给那些表造载荷列的小工具
（SQLAlchemy 的 Column 对象不能跨表共用，必须每张表各造一个）。

⚠ 表模型**立即导入**（不惰性）：`create_all` 只建已注册的表，漏导一个定义表的模型模块，
库里就会少建表 —— 各项目的 `reader_common/model/__init__.py` 就是干这个的。
"""

from .base_task import (
    DEFAULT_DEADLINE_HOURS,
    OPEN_STATES,
    BaseTask,
    PayloadT,
    TaskState,
    payload_column,
)
from .column_types import PayloadJSON

__all__ = [
    "BaseTask",
    "TaskState",
    "PayloadT",
    "PayloadJSON",
    "DEFAULT_DEADLINE_HOURS",
    "OPEN_STATES",
    "payload_column",
]
