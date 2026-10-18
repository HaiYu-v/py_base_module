r"""演示：JSON 列（extra_dict）的就地修改为什么"丢了"。

跑法：`.venv\Scripts\python.exe tmp\demo_json_inplace.py`
"""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlmodel import Field, Session, SQLModel, select

from base_module import BaseTask


class DemoTask(BaseTask, table=True):
    __tablename__ = "demo_json_inplace_task"


engine = create_engine("sqlite://")
SQLModel.metadata.create_all(engine)


def show(label: str, task_id: int) -> None:
    with Session(engine) as s:
        raw = s.connection().execute(
            text("select extra_dict from demo_json_inplace_task where id = :i"), {"i": task_id}
        ).one()[0]
    print(f"   {label}：库里的 extra_dict = {raw}")


with Session(engine) as s:
    t = DemoTask(task_name="demo", uni_key="demo-1")
    s.add(t)
    s.commit()
    task_id = t.id

print("=== 用一条已经入库的任务试 ===")
show("初始", task_id)

print("\n① 就地改：task.extra_dict['retry'] = 2，然后 commit")
with Session(engine) as s:
    task = s.exec(select(DemoTask).where(DemoTask.id == task_id)).one()
    task.extra_dict["retry"] = 2
    print("   Python 对象里：", task.extra_dict)
    s.add(task)
    s.commit()
show("commit 之后", task_id)
print("   → 丢了：SQLAlchemy 没看出「extra_dict 变过」，压根没生成 UPDATE")

print("\n② 整个赋值：task.extra_dict = {**task.extra_dict, 'retry': 2}，然后 commit")
with Session(engine) as s:
    task = s.exec(select(DemoTask).where(DemoTask.id == task_id)).one()
    task.extra_dict = {**task.extra_dict, "retry": 2}
    print("   Python 对象里：", task.extra_dict)
    s.add(task)
    s.commit()
show("commit 之后", task_id)
print("   → 生效：属性被重新赋值了，SQLAlchemy 记为「改过」→ 生成 UPDATE")

print("\n③ 对照：新建的任务**还没第一次 commit**时，就地改是能进的")
with Session(engine) as s:
    t2 = DemoTask(task_name="demo-2", uni_key="demo-2")
    t2.extra_dict["retry"] = 9  # 同一个对象，之后才 insert
    s.add(t2)
    s.commit()
    show("新任务", t2.id)
print("   → 没丢：这条走的是 INSERT，整行值（含刚改的内容）一起写进去")

print("\n④ 别指望「就地改 + 顺手整个赋值」能救回来")
print("   旧值是同一个 dict 对象时，SQLAlchemy 拿新值跟它比 `==` 会判成「没变」→ 照样不写；")
print("   换成「本次 session 里新建的对象」又会写进去 —— 同一个写法两种结果，纯看运气。")
print("   → 结论：要改 extra_dict，就显式构造一个新 dict 赋给它（按 ② 写）。")
