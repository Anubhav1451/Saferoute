# app/api/responses.py
from typing import Any, Dict, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    message: str
    timestamp: str = None

    class Config:
        json_encoders = {
            # Custom encoders if needed
        }


def success_response(data: Any = None, message: str = "Success") -> dict:
    """
    Create a successful API response

    Args:
        data: The data to return
        message: Optional message

    Returns:
        Dictionary representing the API response
    """
    from datetime import datetime
    return {
        "success": True,
        "data": data,
        "error": None,
        "error_code": None,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }


def error_response(
    error: str,
    error_code: str = "ERROR",
    message: str = "An error occurred",
    status_code: int = 400
) -> dict:
    """
    Create an error API response

    Args:
        error: Error details
        error_code: Error code for categorization
        message: User-friendly message
        status_code: HTTP status code (for reference, not included in response)

    Returns:
        Dictionary representing the API response
    """
    from datetime import datetime
    return {
        "success": False,
        "data": None,
        "error": error,
        "error_code": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }


# HTTP exception handler for FastAPI
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions and return standardized response"""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            error=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            message="An error occurred"
        )
    )


# General exception handler
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions and return standardized response"""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    # Log the exception (in production, use proper logging)
    print(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500,
        content=error_response(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred"
        )
    )