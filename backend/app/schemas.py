from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    role: str = Field(..., pattern="^(manager|employee)$")
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)


class AuthUser(BaseModel):
    role: str
    user_id: int | None = None
    username: str


class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)


class EmployeeResponse(BaseModel):
    id: int
    name: str
    created_at: datetime | None = None


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=2000)
    deadline: datetime
    assigned_employee_id: int


class TaskStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(completed|not_completed)$")
    not_completed_reason: str | None = Field(default=None, max_length=2000)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    deadline: datetime
    assigned_employee_id: int
    assigned_employee_name: str | None = None
    status: str
    not_completed_reason: str | None = None
    is_overdue: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    user_id: int | None = None


class NotificationResponse(BaseModel):
    overdue_count: int
    overdue_tasks: list[TaskResponse]
