"""接口日志：``ApiLogMiddleware`` 中间件 + ``@log_api`` 装饰器（**就写文本文件，不接数据库**）。

一条 ``/api`` 请求 = 一行日志，追加到 ``log/api/YYYY-MM-DD.log``（一天一个文件，直接 grep）。

中间件和装饰器分工，谁也不越界：

| 谁 | 管什么 |
|---|---|
| 中间件（``ApiLogMiddleware``，挂 app） | 请求侧：请求 id / ip / 方法 / url；响应侧：HTTP 状态码 / 耗时；收尾把这一行追加进当天文件 |
| 装饰器（``@log_api("登录")``，打在接口函数上） | 业务侧：接口中文名 + 返回体里的 ``code`` / ``msg`` |

好处：**每个 ``/api`` 请求都有一行日志**（中间件兜底，漏打装饰器也不会没日志），
装饰器只做锦上添花 —— 接口层不用为了日志到处 try/except。

上下文用 ``contextvars`` 传（一次请求一个，不会串到别的请求上），
里面那个对象是**可变的**：中间件造好塞进去，鉴权依赖 / 装饰器就地往上补字段。

用法（FastAPI / Starlette）::

    from base_module import ApiLogMiddleware, log_api

    # 1) 挂中间件（默认写 log/api；log_dir=None 就是不落盘，只发请求 id）
    app.add_middleware(ApiLogMiddleware)
    app.add_middleware(ApiLogMiddleware, log_dir="log/api", keep_days=30)

    # 2) 接口盖中文名，一定打在最外层（@as_result 之上）
    @router.post("/login")
    @log_api("登录")
    @as_result
    def login(...): ...

    # 3) 鉴权依赖里解出用户后补一笔（可选）
    set_current_user(user.id)

日志写失败（磁盘满 / 没权限）**绝不会打断请求**：日志是附属品，见 ``write_api_log``。
"""

import contextlib
import inspect
import time
import uuid
from collections.abc import Callable, Mapping
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from base_module.result.result_enum import ResultEnum

#: 只记接口（``/api/...``）：素材 / 静态文件出口（拖一次进度条就是几十个 Range 请求）记了也没用
LOG_PATH_PREFIX = "/api"

#: msg 写文件前的截断长度（太长会把一行撑爆；宁截断也不报错）
MSG_MAX = 512

#: 北京时间（UTC+8）：日志的时间一律按它算，跨天切文件才不会错开一刀
CN_TZ = timezone(timedelta(hours=8))

#: 默认日志目录（相对进程当前工作目录）
DEFAULT_LOG_DIR = Path("log") / "api"

#: 默认保留天数（<= 0 = 不自动清理）
DEFAULT_KEEP_DAYS = 0

#: 一行的字段顺序（制表符分隔，方便 cut / awk；也便于直接 grep request_id）
LOG_FIELDS = (
    "created_at",
    "request_id",
    "user_id",
    "ip",
    "method",
    "url",
    "http_status",
    "code",
    "cost_ms",
    "label",
    "msg",
)

#: 已经扫过过期文件的「目录 + 日期」（同一天只清理一次，不重复扫目录）
_cleaned: set[tuple[str, str]] = set()


def now_cn() -> datetime:
    """当前北京时间（naive，不带 tzinfo；直接格式化即可）。"""
    return datetime.now(CN_TZ).replace(tzinfo=None)


@dataclass
class ApiLog:
    """接口日志：**一个 ``/api`` 请求一行**（要写出去的那份数据）。"""

    #: 请求 id（一次请求一个；响应头 ``X-Request-Id`` 给的是它）
    request_id: str = ""
    #: 用户 id（没登录 / 没带 token = 0）
    user_id: int = 0
    #: 客户端 ip
    ip: str = ""
    #: HTTP 方法
    method: str = ""
    #: 请求地址（带 query）
    url: str = ""
    #: 接口名：``@log_api("登录")`` 里的中文标签
    label: str = ""
    #: HTTP 状态码
    http_status: int = 200
    #: 业务返回码
    code: int = 0
    #: 业务返回文案
    msg: str = ""
    #: 耗时（毫秒）
    cost_ms: int = 0
    #: 请求时间（北京时间）
    created_at: datetime = field(default_factory=now_cn)


#: 当前请求的日志草稿（那份 ``ApiLog``）：
#: 必须在**同一个请求**里读写，所以用 ContextVar 而不是全局变量
_current: ContextVar[Optional[ApiLog]] = ContextVar("api_request_log", default=None)

#: 请求开始的 ``time.perf_counter`` 起点（算耗时用，不是日志字段、不写出去）
_started: ContextVar[float] = ContextVar("api_request_started", default=0.0)


def current_log() -> Optional[ApiLog]:
    """取当前请求的日志草稿（不在请求里 —— 如后台任务 —— 返回 None）。

    别的日志（业务 trace）可以靠它自动带上 request_id / user_id。
    """
    return _current.get()


def current_request_id() -> str:
    """当前请求 id（不在请求里就是空串）。"""
    entry = _current.get()
    return entry.request_id if entry else ""


def set_current_user(user_id: int) -> None:
    """把当前用户写进这次请求的日志草稿（鉴权依赖解出用户后调一次）。"""
    entry = _current.get()
    if entry is not None:
        entry.user_id = int(user_id or 0)


def record_api_result(code: int, msg: str) -> None:
    """把业务返回记进日志草稿（统一返回体 / as_result 之类的兜底处调它）。

    这样**没打 @log_api 的接口**也能记到 code / msg（日志里不留空白）。
    """
    entry = _current.get()
    if entry is None:
        return
    entry.code = int(code or 0)
    entry.msg = (msg or "")[:MSG_MAX]


def log_api(label: str) -> Callable:
    """接口日志装饰器：给接口盖个中文名字，并把返回体里的 code / msg 记进日志。

    写法 —— **一定打在最外层（@as_result 之上）**，因为要读 as_result 返回的那个 Result：

        @router.post("/login")
        @log_api("登录")
        @as_result
        def login(...): ...

    同步 / 异步接口都能用；打错顺序也不会炸（读不到 dict 就只记接口名）。
    """

    def decorate(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                entry = _current.get()
                if entry is not None:
                    entry.label = label
                result = await fn(*args, **kwargs)
                _fill(entry, result)
                return result

            async_wrapper.__signature__ = inspect.signature(fn).replace(
                return_annotation=inspect.Signature.empty
            )
            return async_wrapper

        @wraps(fn)
        def wrapper(*args, **kwargs):
            entry = _current.get()
            if entry is not None:
                entry.label = label
            result = fn(*args, **kwargs)
            _fill(entry, result)
            return result

        wrapper.__signature__ = inspect.signature(fn).replace(
            return_annotation=inspect.Signature.empty
        )
        return wrapper

    return decorate


def _fill(entry: Optional[ApiLog], result: object) -> None:
    """把 ``{code, msg, data}`` 这种 dict 结果里的 code / msg 抄进日志。"""
    if entry is None or not isinstance(result, Mapping):
        return
    code = result.get("code")
    if isinstance(code, int):
        entry.code = code
    msg = result.get("msg")
    if isinstance(msg, str):
        entry.msg = msg[:MSG_MAX]


def client_ip(request: Request) -> str:
    """客户端 ip：优先取反代头（nginx / vite 代理会补），再退到 TCP 对端。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()[:64]
    return (request.client.host if request.client else "")[:64]


class ApiLogMiddleware(BaseHTTPMiddleware):
    """每个 ``/api`` 请求往文件里追加一行接口日志：什么时候、谁、请求了什么、多久、返回什么。

    - 写日志就是**一次 append**，写完接着返回响应；写失败也**绝不打断请求**（见 ``write_api_log``）；
    - 响应带 ``X-Request-Id``：前端报错时把它一起截下来，就能直接
      ``grep <request_id> log/api/*.log`` 把这条请求捞出来。

    参数：
        log_dir: 日志目录（默认 ``log/api``）；传 None = 不落盘（只加请求 id 上下文与响应头）。
        keep_days: 保留天数（默认 0 = 不清理；> 0 时顺手删掉过期文件，同一天只扫一次目录）。
        prefix: 只记这个前缀下的请求，默认 ``/api``。
        error_code / error_msg: 请求抛异常（HTTP 500）时记进日志的业务码，默认取 ``ResultEnum.ERROR``。
    """

    def __init__(
        self,
        app,
        log_dir: Optional[str | Path] = DEFAULT_LOG_DIR,
        keep_days: int = DEFAULT_KEEP_DAYS,
        prefix: str = LOG_PATH_PREFIX,
        error_code: Optional[int] = None,
        error_msg: str = "",
    ) -> None:
        super().__init__(app)
        #: 落盘目录（None = 不落盘）
        self._log_dir = None if log_dir is None else Path(log_dir)
        self._keep_days = int(keep_days)
        self._prefix = prefix
        self._error_code = ResultEnum.ERROR.code if error_code is None else int(error_code)
        self._error_msg = error_msg or ResultEnum.ERROR.msg

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(self._prefix):
            return await call_next(request)
        # CORS 的预检（OPTIONS）不是真调用，不记：它由中间件直接答，跟前端打个照面而已
        if request.method == "OPTIONS":
            return await call_next(request)

        entry = ApiLog(
            # 上游（网关 / 前端）带了自己的请求 id 就沿用，方便两头对账
            request_id=(request.headers.get("x-request-id") or uuid.uuid4().hex)[:64],
            ip=client_ip(request),
            method=request.method[:16],
            url=str(request.url)[:1024],
            # created_at 交给默认值（北京时间 now_cn）：这里就是请求进来的时刻
        )
        token: Token = _current.set(entry)
        _started.set(time.perf_counter())
        try:
            response = await call_next(request)
            entry.http_status = response.status_code
            if not entry.label:
                # 没打 @log_api 的接口用路由名兜底（就是接口函数名），别让接口名空着
                entry.label = str(getattr(request.scope.get("route"), "name", "") or "")[:128]
            response.headers["X-Request-Id"] = entry.request_id
        except Exception as err:  # noqa: BLE001 - 记完 500 再原样抛给上层（HTTP 还是 500）
            entry.http_status = 500
            entry.code = self._error_code
            entry.msg = (str(err) or self._error_msg)[:MSG_MAX]
            raise
        finally:
            entry.cost_ms = int((time.perf_counter() - _started.get()) * 1000)
            _current.reset(token)
            write_api_log(entry, self._log_dir, self._keep_days)
        return response


# ---------------------------------------------------------------------------
# 落盘：一天一个纯文本文件，追加一行
# ---------------------------------------------------------------------------


def _cell(value: object) -> str:
    """一格内的换行 / 制表符换成空格，保证「一行 = 一条请求」不被撑破。"""
    return str("" if value is None else value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def format_api_log(entry: ApiLog) -> str:
    """把一条接口日志按 ``LOG_FIELDS`` 的顺序格式化成一行（制表符分隔）。"""
    created = entry.created_at or now_cn()
    cells = []
    for name in LOG_FIELDS:
        if name == "created_at":
            cells.append(created.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            cells.append(_cell(getattr(entry, name, "")))
    return "\t".join(cells)


def write_api_log(
    entry: ApiLog,
    log_dir: Optional[str | Path] = DEFAULT_LOG_DIR,
    keep_days: int = DEFAULT_KEEP_DAYS,
) -> None:
    """把一条接口日志追加到 ``<log_dir>/YYYY-MM-DD.log``（一天一个文件，就一次 open + write）。

    磁盘满 / 没权限 / 目录建不出来 —— 一律当没写成，**不抛异常**（日志不许影响接口本身）。
    """
    if log_dir is None:
        return
    with contextlib.suppress(Exception):
        created = entry.created_at or now_cn()
        day = created.strftime("%Y-%m-%d")
        root = Path(log_dir)
        root.mkdir(parents=True, exist_ok=True)
        if keep_days > 0 and (str(root), day) not in _cleaned:
            _cleaned.add((str(root), day))
            _clean_expired(root, keep_days)
        with (root / f"{day}.log").open("a", encoding="utf-8") as fp:
            fp.write(format_api_log(entry) + "\n")


def _clean_expired(root: Path, keep_days: int) -> None:
    """删掉 ``YYYY-MM-DD.log`` 里比保留天数更早的文件（认不出的名字不动）。"""
    deadline = (now_cn() - timedelta(days=keep_days)).date()
    with contextlib.suppress(Exception):
        for item in root.glob("*.log"):
            try:
                day = datetime.strptime(item.stem, "%Y-%m-%d").date()
            except ValueError:
                continue
            if day < deadline:
                with contextlib.suppress(OSError):
                    item.unlink()


__all__ = [
    "ApiLog",
    "ApiLogMiddleware",
    "CN_TZ",
    "DEFAULT_KEEP_DAYS",
    "DEFAULT_LOG_DIR",
    "LOG_FIELDS",
    "LOG_PATH_PREFIX",
    "MSG_MAX",
    "client_ip",
    "current_log",
    "current_request_id",
    "format_api_log",
    "log_api",
    "now_cn",
    "record_api_result",
    "set_current_user",
    "write_api_log",
]
