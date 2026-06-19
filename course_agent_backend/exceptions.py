"""全局异常处理"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return Response({
            "code": response.status_code,
            "msg": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            "data": None,
        }, status=response.status_code)
    logger.exception(f"Unhandled exception: {exc}")
    return Response({
        "code": 500,
        "msg": "服务器内部错误",
        "data": None,
    }, status=500)
