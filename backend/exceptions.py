"""
Custom exceptions and error handlers for TimeOpti
"""
from fastapi import HTTPException, status

class TimeOptiException(Exception):
    """Base exception for TimeOpti"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(TimeOptiException):
    """Raised when input validation fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class CalendarError(TimeOptiException):
    """Raised when calendar operations fail"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class OptimizationError(TimeOptiException):
    """Raised when optimization fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class AuthenticationError(TimeOptiException):
    """Raised when authentication fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)

def raise_http_exception(e: TimeOptiException):
    """Convert TimeOptiException to HTTPException"""
    raise HTTPException(status_code=e.status_code, detail=e.message)
