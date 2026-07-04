from fastapi import Request
from app.core.runtime import RuntimeGraph


def get_runtime(request: Request) -> RuntimeGraph:
    return request.app.state.runtime
