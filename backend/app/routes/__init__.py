from typing import Any, Optional

def success_envelope(data: Any = None) -> dict:
    return {
        "success": True,
        "data": data,
        "error": None
    }

def error_envelope(message: str, code: int = 400, details: Optional[Any] = None) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {
            "message": message,
            "code": code,
            "details": details
        }
    }
