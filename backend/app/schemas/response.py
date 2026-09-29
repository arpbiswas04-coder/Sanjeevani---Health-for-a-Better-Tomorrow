from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class StandardErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
