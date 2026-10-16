"""任务表的**基类** `BaseTask`（data_pipeline）—— 用户口径：**一种任务一张表**。

⚠ 本类**不是一张表**（没有 `table=True`）：具体任务各自建表，列的真相只有这一份。
表都落在**本机 sqlite**（`task.db`，见 ``reader_common/task_mapper.py``），
业务实体数据在 MySQL —— 两边互不掺和。

一行 = 一条流水线任务。表口径见 `data_pipeline/STACTUCT.md`：

| 列 | 说明 |
|----|------|
| `e_id` | 对应实体的 id（`reader_data.id` 那一类实体主键） |
| `task_name` | 任务名（要跑哪张流水线 / 哪个节点）—— 一张表一种任务，留着方便看库与回显 |
| `date` | 任务日期，`YYYY-MM-dd`（留给「按天重跑」） |
| `opening` | **开始时间**：过了它这条任务才可以执行；**空 = 随时可执行**（默认空） |
| `pre_task_table` | **前置任务的表名**（如 `reading_task`）：配了就表示「它到了 `pre_state` 才轮到自己」；**空 = 没有前置** |
| `pre_id` | 前置任务的 id（在 `pre_task_table` 那张表里的主键） |
| `pre_state` | 前置任务要达到的**状态**（`TaskState`）：到了它，这条任务才可以执行 |
| `input_data` | 启动数据（json）：跑之前输入给它什么 |
| `output_data` | 结束数据（json）：跑完之后产出什么 |
| `extra_dict` | 附加信息（json）：两份数据之外的杂项，默认 `{}` |
| `state` | 任务状态，见 `TaskState` |
| `deadline` | 截止时间：**没有 `opening` 时默认「创建时间 + 24h」；有 `opening` 时默认「`opening` + 24h」** |
| `run_id` | 运行 id：一次执行一个，用来把日志 / 产物串起来 |

生命周期（对应 STACTUCT.md 的「处理流程」）：

1. 建任务：填 `e_id` / `task_name` / `date`（要延后跑就再给 `opening`），
   `set_input_data()` 初始化启动数据 —— 状态 `pending`
2. 定时脚本捞 `state == pending`、未过期、**且已到 `opening`**、**且前置任务已达标**的行
   → `start(run_id)` —— 状态 `running`
3. 执行过程中打印日志（落 `log/trace.log` / `run_log.db`，靠 `run_id` 关联）
4. 产出写进 `output_data` → `finish()` —— 状态 `success`；报错 → `fail()` —— 状态 `failed`

—— 泛型：`input_data` / `output_data` 同一个 T ——————————————————————

STACTUCT.md：「input_data 和 output_data 是同一类型的对象」。所以本类对载荷类型泛型：

```python
class CoverData(BaseModel):        # 某张流水线的载荷
    title: str
    blocks: list[dict]

class CoverTask(BaseTask, table=True):     # 一张表 = 一个类（表名自己给）
    __tablename__ = "cover_task"
    __table_args__ = (
        UniqueConstraint("uni_key", name="uq_cover_task_uni_key"),
        Index("ix_cover_task_state_deadline", "state", "deadline"),
    )

task: "BaseTask[CoverData]" = CoverTask(e_id=1, task_name="cover")
task.set_input_data(CoverData(title="...", blocks=[]))   # 入参被约束成 CoverData
task.finish(CoverData(title="...", blocks=[...]))
data = task.output_payload(CoverData)                     # 取回来校验成 CoverData
```

⚠ 四条 SQLModel 0.0.48 的实测限制（都在 `tmp/probe_*.py` 里跑过），决定了上面这套写法：

1. **`BaseTask[X]` 只能当「注解」用，不能当「值」用**。
   一旦在运行期真去下标（`BaseTask[X](...)`、`isinstance`、`select(BaseTask[X])`），
   就抛 `TypeError: issubclass() arg 1 must be a class`。
   → 所以本文件顶上加了 `from __future__ import annotations`，注解一律是字符串，不求值；
   真要写运行期表达式，写不带参数的 `BaseTask`（或具体的 `XxxTask`）。
2. **不能靠泛型参数「长出」具体子类**：`class CoverTask(BaseTask[CoverData], table=True)`
   会抛 `ValueError: typing.Any has no matching SQLAlchemy type`。
   → 子类写 `class CoverTask(BaseTask, table=True)`，**不要**下标。
3. **`Optional[T]` 不会自己变成 SQLAlchemy 类型**：字段必须显式给 `sa_column`，
   而且裸 `Column(JSON)` 塞 pydantic 对象会 `TypeError: Object of type X is not JSON serializable`
   （pydantic 的 `field_serializer` 也救不了，SQLAlchemy 的 JSON 列不走它）。
   → 走 `column_types.PayloadJSON`，写入时自动 dump。
4. **`table=True` 的表模型 `__init__` 不走 pydantic 校验**：`T(a="xx")` 不报错、不转型，
   `@model_validator(mode="after")` / `@field_validator` **一个都不触发**（只有字段默认值生效）；
   而在 `model_validate()` 里给字段赋值又会撞
   `AttributeError: 'XxxTask' object has no attribute '_sa_instance_state'`（SQLAlchemy 还没插桩）。
   → **「补 deadline」这类默认值不能靠 validator**，得由写入口显式调方法：见 `ensure_deadline()`
   （`task_mapper.enqueue` 里调）—— 那里以前是 model_validator，等于从来没生效过
   （实测老库所有行的 `deadline` 都是 NULL）。

因为 `T` 在运行期无从得知（限制 1/2），**「JSON → 对象」的还原显式挂在方法上**：
`input_payload(model)` / `output_payload(model)`，把模型类传进去即可。

`extra_dict` **不在这个契约内**：泛型管的是「input 和 output 同型」，杂物走它自己的自由 dict，
免得为了记个重试次数去捏一个载荷字段。

继承 `base_module` 的 `BaseModel`（`base_module/model/base_model.py`），所以**基类的公共列不重复声明**：
`id` / `version` / `creator_id` / `create_time` / `update_time` / `dr` / `prompt` 都在基类上。

⚠ 三条继承来的约定（与 reader-ai 的建表经验一致）：

- `BaseModel` 自己不带 `__table_args__`，所以**每张任务表的约束 / 索引都写在自己类里**；
  ⚠ 约束名 / 索引名**各表必须唯一**（同名会撞）—— 那是每张表自己的事，别指望基类带。
- 基类 `dr`（删除标记）查询时一律带 `dr == "N"` 过滤。

库方言：`input_data` / `output_data` 走 `column_types.PayloadJSON`（impl 是 SQLAlchemy 的 `JSON`）——
SQLite 落 TEXT、MySQL 落 JSON，两边都建得出来。
（MySQL 建短文本列必须给长度，所以 `task_name` / `run_id` 都显式写了 `max_length`。）
"""

from __future__ import annotations

from datetime import date as DateType
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from base_module import BaseModel
from sqlalchemy import Column, DateTime, Index, UniqueConstraint
from sqlmodel import Field

from .column_types import PayloadJSON

#: 任务载荷类型：同一条任务的 `input_data` / `output_data` 恒为同一个 `PayloadT`。
#: 不设 bound —— 常规是 pydantic 模型，简单任务直接塞 dict / list 也放行（见 `PayloadJSON`）。
PayloadT = TypeVar("PayloadT")

#: 任务默认存活时长：创建后 24 小时（见 STACTUCT.md「deadline 默认创建时间+24h」）
DEFAULT_DEADLINE_HOURS = 24

#: 还没跑完的状态：定时脚本只捞这些状态的行来做「过期」判定
OPEN_STATES: tuple[str, ...] = ("pending", "running")


def payload_column(comment: str = "") -> Column:
    """造一个**载荷 / 附加信息**用的 JSON 列（底层是 ``column_types.PayloadJSON``）。

    ⚠⚠ **每次调用都新造一个 Column**（不能写成模块级常量、也不能放基类上共用）：
    SQLAlchemy 的列对象**不能同时挂到两张表**上 —— 共用的话第二张表建表时直接报
    ``Column object 'input_data' already assigned to Table 'xxx'``。
    所以「一种任务一张表」下，每张表自己写 ``sa_column=payload_column("启动数据")``。
    """
    return Column(PayloadJSON, nullable=True, comment=comment or None)


class TaskState(str, Enum):
    """任务状态。落库就是这串小写字符，方便直接看库 / 在 SQL 里筛。"""

    PENDING = "pending"  # 已创建，等定时脚本捞
    RUNNING = "running"  # 已开始，run_id 已落
    SUCCESS = "success"  # 正常结束，output_data 已写
    FAILED = "failed"  # 执行报错，原因是 BusinessException 那一类信息
    EXPIRED = "expired"  # 过了 deadline 还没跑完
    CANCELED = "canceled"  # 人工取消


class BaseTask(BaseModel, Generic[PayloadT]):
    """任务表的**基类**（一行 = 一条流水线任务，载荷类型由 `PayloadT` 指定）。

    ⚠⚠ **它不是一张表**（用户口径：「任务表存在本地的 sqlite，**一种任务一张表**」）：
    本类**没有** ``table=True`` / ``__tablename__`` —— 具体任务各自建表（如
    ``youtube_task`` / ``material_save_task`` / ``listening_task``），列（含载荷两列）
    全从这儿继承。

    子类只需给两样：

    ```python
    class MaterialSaveTask(BaseTask, table=True):
        __tablename__ = "material_save_task"
        __table_args__ = (                       # ⚠ 约束/索引名每张表都要唯一，得自己起
            UniqueConstraint("uni_key", name="uq_material_save_task_uni_key"),
            Index("ix_material_save_task_state_deadline", "state", "deadline"),
        )
    ```

    ⚠ `Generic[PayloadT]` 必须写在类名里（子类**不要**再写 ``BaseTask[MaterialSave]`` ——
    运行期下标会真的去建泛型子模型，SQLModel 直接报错，见本文件顶部的取舍）。
    载荷列是显式的 ``Column(PayloadJSON)``，所以不靠 `PayloadT` 定列类型。
    """

    #: 显式重声明主键：与基类一致，只是让各表的列一眼看全
    id: Optional[int] = Field(default=None, primary_key=True)

    #: ⚠ 显式列类型：sqlmodel 0.0.48 对**推断出来的** datetime 要求 tz-aware，
    #: 不给 `sa_type` 时插入 / 更新一律报 `Datetime values must have timezone information`
    #: （症状：创建任务就失败）。值仍是**北京时间**（基类的 `default_factory=datetime.now`），
    #: 不转 UTC；列类型与以前一模一样。
    create_time: Optional[datetime] = Field(default_factory=datetime.now, sa_type=DateTime)
    update_time: Optional[datetime] = Field(default_factory=datetime.now, sa_type=DateTime)

    e_id: Optional[int] = Field(default=None, index=True, description="对应实体的 id")

    #: **唯一键（业务幂等键）**：整个表**只有这一个唯一键**，不能为空。
    #: 同一条业务对象（比如同一条视频）只允许一条任务 —— 再建就会被数据库拦下来
    #: （正确姿势：建之前先按它查一下，查到就把那条回给调用方，不再插入）。
    uni_key: str = Field(default="", max_length=255, index=True, description="唯一键（业务幂等键）")
    task_name: str = Field(
        default="", max_length=255, index=True, description="任务名（哪张流水线 / 哪个节点）"
    )
    date: DateType = Field(
        default_factory=DateType.today, index=True, description="任务日期 YYYY-MM-dd"
    )

    #: **开始时间**：过了这个时间这条任务才可以执行（定时脚本认领时看它）。
    #: **空 = 随时可执行**（默认就是空，老的调用点什么都不用改）。
    #: 判定只有一处：`can_start()` —— 认领方别自己拼 `opening` 的比较。
    #: ⚠ `deadline` 的缺省**跟着它起算**（`opening + 24h`，见 `ensure_deadline()`）。
    opening: Optional[datetime] = Field(
        default=None,
        index=True,
        sa_type=DateTime,
        description="开始时间（过了它才可执行），空 = 随时可执行",
    )

    #: ——— **前置任务**（三件套，要么都给、要么都不给）———
    #:
    #: 配了这三列就表示：**前置任务到达 `pre_state` 之后，这条任务才可以执行**。
    #: 判定与 `opening` 一样**只有一处**：`can_start()`（`pre_ready()` 那一步）。
    #:
    #: ⚠ 为什么要 `pre_task_table`：用户口径「一种任务一张表」⇒ **id 是每张表各自一套**
    #: （`reading_task#5` 与 `cover_task#5` 可以同时存在），光有 id 定位不到是哪条。
    #: 存的是**真表名**（`model.__tablename__`，如 `cover_task`），认领时按它找表模型。
    #:
    #: ⚠ 本类**不查库**（不持 session / 不认识任务表登记表），前置状态由调用方查好喂进
    #: `can_start(pre_task_state=...)`；查前置的口在 `reader_common.task_mapper`。
    pre_task_table: Optional[str] = Field(
        default=None, max_length=255, description="前置任务的表名（如 reading_task），空 = 没有前置"
    )
    pre_id: Optional[int] = Field(default=None, description="前置任务的 id（那张表里的主键）")
    pre_state: Optional[str] = Field(
        default=None, max_length=16, description="前置任务要达到的状态（TaskState）"
    )

    #: ⚠ 别把字段叫 desc：基类有 desc() 方法，同名会遮蔽；说明列叫 description 那一套
    #:
    #: ⚠⚠ **载荷两列与 `extra_dict` 由每张任务表自己声明**（不在基类上）：
    #: SQLAlchemy 的 ``Column`` 对象**不能同时挂到两张表**上（第二张表建表时直接报
    #: ``Column object 'input_data' already assigned to Table 'xxx'``）。
    #: 所以每张表都写：
    #:
    #: ```python
    #:     input_data: Optional[MaterialSave] = Field(default=None, sa_column=payload_column("启动数据"))
    #:     output_data: Optional[MaterialSave] = Field(default=None, sa_column=payload_column("结束数据"))
    #:     extra_dict: dict[str, Any] = Field(default_factory=dict, sa_column=payload_column("附加信息，默认 {}"))
    #: ```
    #: （``payload_column`` 是下面的小工具：每次调用**新造一个** Column，不共用。）
    #: 好处顺带有了：载荷类型能按表写实（``Optional[MaterialSave]``），一眼看得出这张表装什么。

    state: str = Field(
        default=TaskState.PENDING.value,
        max_length=16,
        index=True,
        description="任务状态（TaskState）",
    )

    #: 默认「创建时间 + 24h」；**有 `opening` 时默认「`opening` + 24h」**：由写入口调的
    #: `ensure_deadline()` 统一补（⚠ 不能写成 model_validator，见那个方法的说明）
    deadline: Optional[datetime] = Field(
        default=None,
        index=True,
        sa_type=DateTime,
        description="截止时间，默认创建时间 + 24h（有 opening 则 opening + 24h）",
    )

    run_id: Optional[str] = Field(
        default=None, max_length=64, index=True, description="运行 id（一次执行一个）"
    )

    # ——— 默认值与工具方法 ———

    def ensure_deadline(self) -> BaseTask[PayloadT]:
        """没给 `deadline` 就按「起算点 + 24h」补上，返回自己（可链式调）。

        - **没有 `opening`**（随时可执行）→ **创建时间 + 24h**；
        - **有 `opening`**（要等到某个点才跑）→ **`opening` + 24h** ——
          不然一条排在三天后的任务一建出来就是 `overdue`。

        已经给了 `deadline` 就一个字不动（显式给的优先）。

        ⚠⚠ **为什么是普通方法、不是 `model_validator`**：SQLModel 0.0.48 的 `table=True` 表模型
        `__init__` **不走 pydantic 校验**（见文件顶部限制 4），validator 永远不会被触发
        —— 以前就是 validator，实测老库所有行的 `deadline` 都是 NULL，等于没生效。
        所以这条规则由**写入口显式调用**：`task_mapper.enqueue()` 里调它。
        """
        if self.deadline is None:
            from_at = self.opening or self.create_time or datetime.now()
            self.deadline = from_at + timedelta(hours=DEFAULT_DEADLINE_HOURS)
        return self

    @property
    def is_finished(self) -> bool:
        """是否已经有终态（成功 / 失败 / 过期 / 取消）。"""
        return self.state in (
            TaskState.SUCCESS.value,
            TaskState.FAILED.value,
            TaskState.EXPIRED.value,
            TaskState.CANCELED.value,
        )

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        """是否已过 deadline 且还没跑完 —— 定时脚本据此把行置 `expired`。"""
        if self.state not in OPEN_STATES or self.deadline is None:
            return False
        return (now or datetime.now()) > self.deadline

    @property
    def has_pre(self) -> bool:
        """配了前置任务没有（`pre_task_table` / `pre_id` / `pre_state` **三个都给了**才算配）。"""
        return bool(self.pre_task_table) and self.pre_id is not None and bool(self.pre_state)

    def pre_ready(self, pre_task_state: Optional[str] = None) -> bool:
        """**前置任务达标没有**：没配前置 → `True`；配了 → `pre_task_state == self.pre_state`。

        - `pre_task_state` = 前置任务**现在**的状态，由调用方查好传进来（本类不查库）；
        - 传 `None`（没去查 / 查不到 / 前置那行被删了）**一律算没达标** ——
          宁可多等一轮 tick，也不要让一条前置没做完的任务先跑掉；
        - 判的是「**等于** `pre_state`」：前置要是停在别的终态（比如 `failed`），这条就一直等，
          **不会死等** —— 本任务 `deadline` 到期后由定时脚本置 `expired`，那就是出口。
        """
        if not self.has_pre:
            return True
        return pre_task_state == self.pre_state

    def can_start(self, now: Optional[datetime] = None, pre_task_state: Optional[str] = None) -> bool:
        """**能不能开跑**：没到 `opening`、或**前置任务还没到位**，就先别动它。

        - `opening` 为空（默认）= 随时可执行，返回 `True`；
        - 给了 `opening`：`now >= opening` 才 `True`（相等就算到点了）；
        - 配了前置任务：前置任务现在的状态必须等于 `pre_state`（见 `pre_ready()`）。

        ⚠ 认领方（定时脚本 / worker）一律走这里判，别自己拿 `opening` 比 ——
        与入库时的时区口径（北京时间 `datetime.now()`）保持一致。

        ⚠ `pre_task_state` **得由调用方查好传进来**：本类不持 session、也不认识任务表登记表
        （`TASK_TABLES`），自己查不了 —— 查前置的口在 `reader_common.task_mapper`
        （`pre_state_of()` / `task_mapper.can_start()`，认领时 `open_tasks(ready_only=True)` 已经滤过）。
        不传 = 没查 = 一律算没达标（配了前置的任务因此不会被误放行）。
        """
        if not self.pre_ready(pre_task_state):
            return False
        if self.opening is None:
            return True
        return (now or datetime.now()) >= self.opening

    # ——— 载荷：写 ———

    def set_input_data(self, input_data: Optional[PayloadT] = None) -> BaseTask[PayloadT]:
        """建任务后初始化启动数据（STACTUCT.md 第 2 步）。

        可以给 `PayloadT` 对象（`PayloadJSON` 会在写库时 dump 成 JSON），也可以给裸 dict。
        不给就是空 `{}` —— 「这一步不需要入参」和「还没设过」得能区分开。
        """
        self.input_data = input_data if input_data is not None else {}
        return self

    def finish(self, output_data: Optional[PayloadT] = None) -> BaseTask[PayloadT]:
        """执行完成：产出进 `output_data`，置 `success`。

        同一条任务的 `output_data` 与 `input_data` 是同一个 `PayloadT` —— 这正是泛型要锁的约束
        （STACTUCT.md「审核和应用」要比对这两份）。
        """
        self.output_data = output_data if output_data is not None else {}
        self.state = TaskState.SUCCESS.value
        return self

    def fail(self, output_data: Optional[Any] = None) -> BaseTask[PayloadT]:
        """执行报错：错误信息挂在 `output_data` 上（如 `{"error": ...}`），置 `failed`。

        ⚠ 这里的入参**故意不标 `PayloadT`**：失败时 `output_data` 装的是错误信息，
        形状跟正常产出无关（`{"error": ...}` / traceback 摘要），标成 `PayloadT` 是假契约。
        """
        self.output_data = output_data if output_data is not None else {}
        self.state = TaskState.FAILED.value
        return self

    # ——— 载荷：读 ———

    def input_payload(self, model: type[PayloadT]) -> Optional[PayloadT]:
        """把 `input_data` 的 JSON 校验回 `model` 类型的对象；没设过则 `None`。

        为什么要显式传 `model`：`T` 在运行期无从得知（见文件顶部限制 1 / 2），
        表模型拿到的一律是 dict。
        """
        return model.model_validate(self.input_data) if self.input_data is not None else None

    def output_payload(self, model: type[PayloadT]) -> Optional[PayloadT]:
        """把 `output_data` 的 JSON 校验回 `model` 类型的对象；没有产出则 `None`。"""
        return model.model_validate(self.output_data) if self.output_data is not None else None

    # ——— 状态流转 ———

    def start(self, run_id: str) -> BaseTask[PayloadT]:
        """定时脚本捞到任务、开始执行：落 run_id 并置 `running`。"""
        self.run_id = run_id
        self.state = TaskState.RUNNING.value
        return self

    def expire(self) -> BaseTask[PayloadT]:
        """过了截止时间还没跑完，置 `expired`。"""
        self.state = TaskState.EXPIRED.value
        return self

    def cancel(self) -> BaseTask[PayloadT]:
        """人工取消，置 `canceled`。"""
        self.state = TaskState.CANCELED.value
        return self
