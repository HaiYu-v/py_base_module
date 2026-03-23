"""
链路追踪使用示例
"""
import asyncio
import time
from tracer import trace, ManualSpan


# ─── 示例 1: 最简用法，直接加装饰器 ──────────────────────────
@trace
def get_user(user_id: int):
    time.sleep(5)
    return {"id": user_id, "name": "Alice"}


@trace
def get_orders(user_id: int):
    time.sleep(5)
    return [{"order_id": 1001}, {"order_id": 1002}]


@trace
def build_response(user, orders):
    return {**user, "orders": orders}


@trace
def handle_request(user_id: int):
    """根 Span：整个请求链路"""
    user = get_user(user_id)
    orders = get_orders(user_id)
    return build_response(user, orders)


# ─── 示例 2: 带自定义名称和标签 ───────────────────────────────
@trace("db.query", tags={"db": "postgres", "table": "products"})
def fetch_products():
    time.sleep(0.015)
    return ["prod_a", "prod_b"]


@trace("api.list_products", tags={"service": "catalog"})
def list_products():
    return fetch_products()


# ─── 示例 3: 异步函数 ─────────────────────────────────────────
@trace
async def fetch_remote(url: str):
    await asyncio.sleep(0.01)
    return {"status": 200, "url": url}


@trace("api.dashboard", tags={"version": "v2"})
async def get_dashboard():
    results = await asyncio.gather(
        fetch_remote("https://api.example.com/users"),
        fetch_remote("https://api.example.com/stats"),
    )
    return results


# # ─── 示例 4: 手动 Span（细粒度控制） ──────────────────────────
# @trace
# def process_batch(items: list):
#     for item in items:
#         with ManualSpan("func","process.item", tags={"item_id": item}):
#             time.sleep(0.005)


# ─── 示例 5: 异常捕获 ─────────────────────────────────────────
@trace
def risky_operation():
    time.sleep(0.01)
    raise ValueError("something went wrong")


@trace
def handle_with_error():
    try:
        risky_operation()
    except ValueError:
        pass  # 异常已被记录在 risky_operation 的 Span 中


if __name__ == "__main__":
    print("=" * 60)
    print("示例 1: 同步调用链")
    print("=" * 60)
    handle_request(42)

    print("\n" + "=" * 60)
    print("示例 2: 带标签")
    print("=" * 60)
    list_products()

    print("\n" + "=" * 60)
    print("示例 3: 异步")
    print("=" * 60)
    asyncio.run(get_dashboard())

    # print("\n" + "=" * 60)
    # print("示例 4: 手动 Span")
    # print("=" * 60)
    # process_batch([1, 2, 3])

    print("\n" + "=" * 60)
    print("示例 5: 错误追踪")
    print("=" * 60)
    handle_with_error()