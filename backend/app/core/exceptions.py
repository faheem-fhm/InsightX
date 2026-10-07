from typing import Any, Optional, Dict
from fastapi import HTTPException, status

class InsightXException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class DatasetNotFoundError(InsightXException):
    def __init__(self, dataset_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' was not found."
        )

class InvalidFileFormatError(InsightXException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or unsupported file format: {message}"
        )

class FileSizeExceededError(InsightXException):
    def __init__(self, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds allowed limit of {max_mb}MB."
        )

class PreprocessingError(InsightXException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data preprocessing failed: {message}"
        )

class UnsafeSQLError(InsightXException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Security policy violation: Generated query contains prohibited operations. {message}"
        )

class MLWorkflowError(InsightXException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Machine learning computation error: {message}"
        )
