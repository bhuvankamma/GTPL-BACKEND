from typing import Any, Optional

def success_response(
    message: str,
    data: Optional[Any] = None
):
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(
    message: str,
    data: Optional[Any] = None
):
    return {
        "success": False,
        "message": message,
        "data": data
    }
