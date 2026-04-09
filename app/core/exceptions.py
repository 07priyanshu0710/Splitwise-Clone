from fastapi import HTTPException, status

class SplitwiseError(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class BusinessLogicError(SplitwiseError):
    """Exception raised for errors in business logic."""
    pass

class UnauthorizedError(SplitwiseError):
    """Exception raised for unauthorized access."""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)

class NotFoundError(SplitwiseError):
    """Exception raised when a resource is not found."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)

class ForbiddenError(SplitwiseError):
    """Exception raised when a user does not have permission."""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)
