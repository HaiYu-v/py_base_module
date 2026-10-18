r"""验收：`BaseTask` 上的载荷三列（input_data / output_data / extra_dict）。

验的是**真 `BaseTask`**（不是探针里手搓的仿制品）：

1. `BaseTask` 自己**不是一张表**（没有 `__table__` / `__tablename__`）；
2. 两张（及以上）子表都能建出来，三列都在、**都可空**，且**不是同一个 Column 对象**
   （这正是「不能挂 `sa_column`、只能挂 `sa_type`」的验收点）；
3. 走一遍生命周期：建任务 → `set_input_data(pydantic)` → `ensure_deadline()` → 入库 →
   `start(run_id)` → `finish(pydantic)` → 出库 → `input_payload()` / `output_payload()` 还原；
4. `extra_dict` 不给值默认 `{}`，能给 dict；
5. 老写法（子类用 `sa_column=payload_column(...)` 覆盖）**仍然能建表能跑**（向后兼容）；
6. SQLite / MySQL 两个方言都编译得出建表 DDL。

跑法：`.venv\Scripts\python.exe tmp\check_base_task_payloads.py`
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel as PydanticModel
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import create_engine, text
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable
from sqlmodel import Field, Session, SQLModel, select

from base_module import BaseTask, TaskState, payload_column

PAYLOAD_COLUMNS = ("input_data", "output_data", "extra_dict")
checks: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    checks.append(f"{'PASS' if ok else 'FAIL'}  {label}{(' —— ' + detail) if detail else ''}")
    print(checks[-1])


class MaterialSave(PydanticModel):
    """某张流水线的载荷：input 和 output 同型。"""

    title: str
    blocks: list[dict[str, Any]] = []


class MaterialSaveTask(BaseTask, table=True):
    """新写法：载荷三列一个字不写，全继承。"""

    __tablename__ = "check_material_save_task"


class CoverTask(BaseTask, table=True):
    """老写法：子类自己覆盖载荷列（写实类型 + payload_column），必须照样能建表。"""

    __tablename__ = "check_cover_task"
    input_data: Optional[MaterialSave] = Field(
        default=None, sa_column=payload_column("启动数据（子类覆盖）")
    )


def main() -> None:
    check("BaseTask 不是一张表", not hasattr(BaseTask, "__table__"))

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    for model in (MaterialSaveTask, CoverTask):
        cols = {c.name: c for c in sa_inspect(model).columns}
        check(f"{model.__name__} 三列都在", all(n in cols for n in PAYLOAD_COLUMNS))
        check(
            f"{model.__name__} 三列都可空",
            all(cols[n].nullable for n in PAYLOAD_COLUMNS),
            ", ".join(f"{n}={cols[n].nullable}" for n in PAYLOAD_COLUMNS),
        )
        check(
            f"{model.__name__} 三列是 JSON 列（PayloadJSON）",
            all(type(cols[n].type).__name__ == "PayloadJSON" for n in PAYLOAD_COLUMNS),
        )

    check(
        "两张表的 input_data 不是同一个 Column 对象",
        MaterialSaveTask.__table__.c.input_data is not CoverTask.__table__.c.input_data,
    )
    check(
        "CoverTask.input_data 用的是子类覆盖的那一列",
        CoverTask.__table__.c.input_data.comment == "启动数据（子类覆盖）",
        f"comment={CoverTask.__table__.c.input_data.comment!r}",
    )

    # ——— 生命周期 ———
    with Session(engine) as s:
        task = MaterialSaveTask(e_id=1, task_name="material_save", uni_key="k-1")
        task.set_input_data(MaterialSave(title="入参"))
        task.ensure_deadline()
        s.add(task)
        s.commit()
        s.refresh(task)
        task_id = task.id

        check("建任务后 state=pending", task.state == TaskState.PENDING.value)
        check("input_data 落库能还原", task.input_payload(MaterialSave) == MaterialSave(title="入参"))
        check("output_data 空着是 None", task.output_data is None)
        check("extra_dict 不给值时是 {}", task.extra_dict == {})

        task.start("run-1")
        task.finish(MaterialSave(title="产出", blocks=[{"type": "p"}]))
        s.add(task)
        s.commit()

    # ⚠ SQLAlchemy 的 JSON 列**不跟踪就地修改**：下面这次 `["inplace"] = ...` 提交后是丢的
    #   （这是 JSON 列的老脾气，不是这三列的新毛病；要改就整个赋值）
    with Session(engine) as s:
        got = s.exec(select(MaterialSaveTask).where(MaterialSaveTask.id == task_id)).one()
        got.extra_dict["inplace"] = "丢了"
        s.add(got)
        s.commit()

    with Session(engine) as s:
        got = s.exec(select(MaterialSaveTask).where(MaterialSaveTask.id == task_id)).one()
        check("出库后 state=success", got.state == TaskState.SUCCESS.value, got.state)
        check("出库后 run_id", got.run_id == "run-1", repr(got.run_id))
        check(
            "output_data 能还原成同型对象",
            got.output_payload(MaterialSave) == MaterialSave(title="产出", blocks=[{"type": "p"}]),
        )
        check(
            "extra_dict 就地改不落库（JSON 列本来的脾气）",
            got.extra_dict == {},
            repr(got.extra_dict),
        )
        got.extra_dict = {**got.extra_dict, "retry": 2}  # 整个赋值
        s.add(got)
        s.commit()

    with Session(engine) as s:
        got = s.exec(select(MaterialSaveTask).where(MaterialSaveTask.id == task_id)).one()
        check("extra_dict 整个赋值能落库", got.extra_dict == {"retry": 2}, repr(got.extra_dict))
        check(
            "凭空取回 input_data 仍是原对象（同一 T）",
            got.input_payload(MaterialSave) == MaterialSave(title="入参"),
        )
        raw = s.exec(
            text("select input_data, output_data, extra_dict from check_material_save_task")
        ).one()
        check(
            "库里落的是 JSON 原文（没有 pydantic 对象漏出去）",
            raw[0] == '{"title": "\\u5165\\u53c2", "blocks": []}' or "title" in raw[0],
            repr(raw),
        )

    # ——— 方言 ———
    for dialect in (engine.dialect, mysql.dialect()):
        ddl = str(CreateTable(MaterialSaveTask.__table__).compile(dialect=dialect))
        check(f"{dialect.name} 建表 DDL 编得出来", "input_data" in ddl and "extra_dict" in ddl)

    failed = [c for c in checks if c.startswith("FAIL")]
    print(f"\n{'=' * 60}\n{len(checks) - len(failed)}/{len(checks)} 通过")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
