# app/api/exceptions.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.api.responses import error_response
import logging

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized response format"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            error=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            message="An error occurred"
        )
    )


async def validation_exception_handler(request: Request, exc: Exception):
    """Handle validation exceptions with standardized response format"""
    return JSONResponse(
        status_code=422,
        content=error_response(
            error=str(exc),
            error_code="VALIDATION_ERROR",
            message="Validation error"
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with standardized response format"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=error_response(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred"
        )
    )