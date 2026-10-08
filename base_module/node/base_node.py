"""节点与图的公共基类。

每个 Protocol 的实现（adapter）以及每张图都继承 BaseNode：
- ``name`` / ``name_cn``：中英名字，图上的节点 key 用 ``name_cn``
- ``desc``：描述这个实现是干嘛的（工作台页头那句说明也从图的 ``desc`` 读）
- **节点日志**：子类只要定义 ``__call__``（节点），就自动挂一层 ``trace_log``
  （见 ``__init_subclass__``），一次调用一条 span，名字取 ``name_cn``
"""

from __future__ import annotations

import functools

from base_module import trace_log


class BaseNode:
    """节点基类：提供描述性属性，并给节点的 ``__call__`` 自动挂节点日志。"""

    #: 英文名（图节点 key / 工作台菜单右侧）
    name: str = ""
    #: 中文名（图节点 key / 工作台菜单左侧）
    name_cn: str = ""
    #: 说明：这个实现是干嘛的
    desc: str = ""

    def __init_subclass__(cls, **kwargs) -> None:
        """子类定义 ``__call__`` 时自动挂上节点日志（``trace_log``）。

        - 名字取 ``name_cn``（图上那个中文节点名），英文名进 tags —— 一次调用一条 span，落 ``log/trace.log``；
        - 只在子类**自己**定义 ``__call__`` 时挂（``cls.__dict__``），继承来的不重复挂；
        - 挂完用 ``functools.update_wrapper`` 保回原签名：LangGraph 靠 ``inspect.signature``
          认节点入参（state 还是 (state, config)），签名被装饰器吃掉会装配失败；
        - 适配器（没有 ``__call__``，只有 ``invoke`` / ``parse`` 这类端口方法）不受影响，
          它们要留痕就自己调 ``Log.log``。
        """
        super().__init_subclass__(**kwargs)
        raw = cls.__dict__.get("__call__")
        if raw is None or getattr(raw, "__traced__", False):
            return
        traced = trace_log(cls.name_cn or cls.name or cls.__name__, tags={"node": cls.name})(raw)
        functools.update_wrapper(traced, raw)  # 保签名 / __name__ / __doc__
        traced.__traced__ = True
        cls.__call__ = traced

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"<{type(self).__name__} {self.name_cn or self.name}>"
