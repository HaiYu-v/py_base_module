"""
链路追踪系统 - 无侵入式装饰器实现
用法: @trace 或 @trace(name="custom_name", tags={"key": "val"})
"""
import inspect
import time
import uuid
import json
import logging
import traceback
import functools
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import datetime
import os
from logging.handlers import TimedRotatingFileHandler

from base_module.exception.Business_exception import BusinessException
from base_module.info.log import Log

# ─── 日志配置 ────────────────────────────────────────────────
LOG_FILE = r"log/trace.log"  # 指定日志文件路径
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logger = logging.getLogger("tracer")
if not logger.handlers:
    # 文件 Handler
    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="midnight",    # 每天滚动：midnight / H（每小时）/ D（每天）
        interval=1,
        backupCount=30,      # 保留最近 30 天
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)

    # # 控制台 Handler（可选，不需要就删掉）
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(logging.Formatter("%(message)s"))
    # logger.addHandler(console_handler)

    logger.setLevel(logging.INFO)

# ─── Context（跨异步/线程安全） ────────────────────────────────
_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_span_stack: ContextVar[list] = ContextVar("span_stack", default=None)


def _get_stack() -> list:
    stack = _span_stack.get()
    if stack is None:
        stack = []
        _span_stack.set(stack)
    return stack


# ─── 数据结构 ─────────────────────────────────────────────────
@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    name: str
    func:str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "ok"          # ok | error
    error: Optional[str] = None
    tags: dict = field(default_factory=dict)
    children: list = field(default_factory=list)  # 仅内存聚合用

    def finish(self, error: Optional[Exception] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000)
        if error:
            self.status = "error"
            self.error = traceback.format_exc()

    def to_log(self) -> str:
        name = f"name[{self.name}] " if self.name else ''
        start = datetime.datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S")
        tags_str = ("tags[" + ",".join(f"{k}={v}" for k, v in self.tags.items())+"] ") if self.tags else ""
        parent_str = f"span[{self.parent_id[:8]}-{self.span_id[:8]}]" if self.parent_id else f"span[        -{self.span_id[:8]}]"
        error_str = f"error[{self.error.splitlines()[-1]}] " if self.error else ""
        duration_str = f"duration[{self.duration_ms}ms] " if self.duration_ms else ""
        status_str = f"status[{self.status}] " if self.duration_ms else ""
        return (
            f"trace[{self.trace_id[:8]}] "
            f"{parent_str} "
            f"start[{start}] "
            f"{name}"
            f"func[{self.func}] "
            f"{duration_str}"
            f"{status_str}"
            f"{tags_str}"
            f"{error_str}"
        )


# ─── 采集器 ───────────────────────────────────────────────────
class TraceCollector:
    """收集完整链路，在根 Span 结束时输出整棵树"""

    def __init__(self):
        self._spans: dict[str, Span] = {}
        self._roots: list[Span] = []

    def add(self, span: Span):
        self._spans[span.span_id] = span
        if span.parent_id and span.parent_id in self._spans:
            self._spans[span.parent_id].children.append(span)
        elif not span.parent_id:
            self._roots.append(span)

    def emit(self, root: Span):
        """逐行纯文本输出每个 span，输出后清理当次链路"""
        spans = self._collect(root)
        for span in spans:
            logger.info(span.to_log())
        for span in spans:
            self._spans.pop(span.span_id, None)
        if root in self._roots:
            self._roots.remove(root)

    def _collect(self, span: Span) -> list[Span]:
        result = [span]
        for child in span.children:
            result.extend(self._collect(child))
        return result


_collector = TraceCollector()


# ─── 装饰器 ───────────────────────────────────────────────────
def trace(_func, tags: dict = None):
    """
    无侵入链路追踪装饰器，支持同步和异步函数。

    用法:
        @trace
        def my_func(): ...

        @trace(name="custom", tags={"service": "order"})
        async def my_async_func(): ...
    """
    name = None
    def decorator(func):
        span_func = f"{func.__qualname__}"
        span_name = name
        func.desc = name
        if _is_async(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await _run_async(func, span_func, span_name, tags or {}, args, kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return _run_sync(func, span_func, span_name, tags or {}, args, kwargs)
            return sync_wrapper

    # 支持 @trace 和 @trace(...) 两种用法
    if not isinstance(_func, str):
        return decorator(_func)
    else:
        name = _func
    return decorator


def _make_span(span_func:str, span_name: str, tags: dict) -> tuple[Span, bool]:
    """创建 Span，返回 (span, is_root)"""
    stack = _get_stack()
    is_root = not stack

    if is_root:
        trace_id = _trace_id.get() or uuid.uuid4().hex
        _trace_id.set(trace_id)
        parent_id = None
    else:
        trace_id = _trace_id.get()
        parent_id = stack[-1].span_id

    span = Span(
        trace_id=trace_id,
        span_id=uuid.uuid4().hex[:16],
        parent_id=parent_id,
        func=span_func,
        name=span_name,
        start_time=time.time(),
        tags=tags,
    )
    _collector.add(span)
    stack.append(span)
    return span, is_root


def _finish_span(span: Span, is_root: bool, error: Optional[Exception]):
    stack = _get_stack()
    span.finish(error)
    # 不管在不在栈顶，直接移除自己，防止异常场景下栈错位
    try:
        stack.remove(span)
    except ValueError:
        pass
    if is_root:
        _collector.emit(span)


def _run_sync(func, span_func, span_name, tags, args, kwargs):
    span, is_root = _make_span(span_func, span_name, tags)
    exc = None
    try:
        Log.log(f"====== [{span.name}] [{func.__name__}]")
        result = func(*args, **kwargs)
        return result
    except Exception as e:
        # 获取被装饰函数调用堆栈，跳过 wrapper 自身
        trace = inspect.trace()
        # 构建异常
        exc = BusinessException(span_name,None, e, trace)
        raise exc from e
    finally:
        _finish_span(span, is_root, exc)
        Log.log(f"****** [{span.name}] [{func.__name__}] [{span.duration_ms}ms]")


async def _run_async(func, span_func, span_name, tags, args, kwargs):
    span, is_root = _make_span(span_func, span_name, tags)
    exc = None
    try:
        Log.log(f"====== [{span.name}] [{func.__name__}]")
        result = await func(*args, **kwargs)
        return result
    except Exception as e:
        # 获取被装饰函数调用堆栈，跳过 wrapper 自身
        trace = inspect.trace()
        # 构建异常
        exc = BusinessException(span_name,None, e, trace)
        raise exc from e
    finally:
        _finish_span(span, is_root, exc)
        Log.log(f"****** [{span.name}] [{func.__name__}] [{span.duration_ms}ms]")


def _is_async(func) -> bool:
    import asyncio
    return asyncio.iscoroutinefunction(func)


# ─── 手动 Span（可选，用于更细粒度控制） ───────────────────────
class ManualSpan:
    """上下文管理器，手动创建 Span"""
    def __init__(self, func:str, name: str, tags: dict = None):
        self.func = func
        self.name = name
        self.tags = tags or {}

    def __enter__(self) -> Span:
        self.span, self.is_root = _make_span(self.func, self.name, self.tags)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        _finish_span(self.span, self.is_root, exc_val)
        return False  # 不吞异常