# app/exceptions.py
from fastapi import HTTPException


class APIException(HTTPException):
    """Custom API exception for consistent error handling"""
    def __init__(
        self,
        detail: str,
        status_code: int = 400,
        error_code: str = None,
        headers: dict = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or f"API_ERROR_{status_code}"