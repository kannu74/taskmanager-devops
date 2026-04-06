import httpx
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.auth import create_access_token, get_current_user, require_employee, require_manager
from app.config import settings
from app.schemas import (
    AuthUser,
    EmployeeCreate,
    EmployeeResponse,
    LoginRequest,
    NotificationResponse,
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
    TokenResponse,
)
from app.supabase_client import get_supabase_client

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    supabase = get_supabase_client()

    if payload.role == "manager":
        if (
            payload.username != settings.manager_username
            or payload.password != settings.manager_password
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user = AuthUser(role="manager", username=payload.username, user_id=None)
    else:
        try:
            employee = supabase.find_employee_by_credentials(payload.username, payload.password)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Supabase error: {exc.response.text}",
            ) from exc

        if employee is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user = AuthUser(role="employee", username=employee["name"], user_id=employee["id"])

    token = create_access_token(user)
    return TokenResponse(
        access_token=token,
        role=user.role,
        username=user.username,
        user_id=user.user_id,
    )


@app.get("/me", response_model=TokenResponse)
def get_me(current_user: AuthUser = Depends(get_current_user)) -> TokenResponse:
    return TokenResponse(
        access_token="",
        role=current_user.role,
        username=current_user.username,
        user_id=current_user.user_id,
    )


def _parse_deadline(raw_deadline: str | None) -> datetime:
    if raw_deadline is None:
        return datetime.now(timezone.utc)
    deadline = datetime.fromisoformat(raw_deadline.replace("Z", "+00:00"))
    if deadline.tzinfo is None:
        return deadline.replace(tzinfo=timezone.utc)
    return deadline


def _is_overdue(task: dict) -> bool:
    if task.get("status") == "completed":
        return False
    deadline = _parse_deadline(task.get("deadline"))
    return deadline < datetime.now(timezone.utc)


def _normalize_task(task: dict, employee_map: dict[int, str]) -> dict:
    return {
        **task,
        "assigned_employee_name": employee_map.get(task.get("assigned_employee_id")),
        "is_overdue": _is_overdue(task),
    }


@app.get("/employees", response_model=list[EmployeeResponse])
def list_employees(_: AuthUser = Depends(require_manager)) -> list[EmployeeResponse]:
    try:
        supabase = get_supabase_client()
        return supabase.list_employees()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase error: {exc.response.text}",
        ) from exc


@app.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    _: AuthUser = Depends(require_manager),
) -> EmployeeResponse:
    try:
        supabase = get_supabase_client()
        return supabase.create_employee(payload.name, payload.password)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase error: {exc.response.text}",
        ) from exc


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    current_user: AuthUser = Depends(get_current_user),
) -> list[TaskResponse]:
    try:
        supabase = get_supabase_client()
        employees = supabase.list_employees()
        employee_map = {item["id"]: item["name"] for item in employees}

        if current_user.role == "manager":
            tasks = supabase.list_tasks()
        else:
            if current_user.user_id is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            tasks = supabase.list_tasks_for_employee(current_user.user_id)

        return [_normalize_task(task, employee_map) for task in tasks]
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase error: {exc.response.text}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tasks",
        ) from exc


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    _: AuthUser = Depends(require_manager),
) -> TaskResponse:
    try:
        supabase = get_supabase_client()
        employees = supabase.list_employees()
        employee_map = {item["id"]: item["name"] for item in employees}
        created = supabase.create_task(
            payload.title,
            payload.description,
            payload.deadline.isoformat(),
            payload.assigned_employee_id,
        )
        if created is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Task was not created",
            )
        return _normalize_task(created, employee_map)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase error: {exc.response.text}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        ) from exc


@app.put("/tasks/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    current_user: AuthUser = Depends(require_employee),
) -> TaskResponse:
    if payload.status == "not_completed" and not payload.not_completed_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason is required for not_completed status",
        )

    try:
        supabase = get_supabase_client()
        employees = supabase.list_employees()
        employee_map = {item["id"]: item["name"] for item in employees}
        if current_user.user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        updated = supabase.update_task_status(
            task_id,
            current_user.user_id,
            payload.status,
            payload.not_completed_reason,
        )
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return _normalize_task(updated, employee_map)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase error: {exc.response.text}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task",
        ) from exc


@app.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(
    task_id: int,
    _: AuthUser = Depends(require_manager),
) -> dict[str, str]:
    try:
        supabase = get_supabase_client()
        deleted = supabase.delete_task(task_id)
        if len(deleted) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return {"message": "Task deleted"}
    except httpx.HTTPStatusError as exc:
        message = exc.response.text
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase error: {message}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task",
        ) from exc


@app.get("/notifications", response_model=NotificationResponse)
def get_notifications(current_user: AuthUser = Depends(get_current_user)) -> NotificationResponse:
    try:
        supabase = get_supabase_client()
        employees = supabase.list_employees()
        employee_map = {item["id"]: item["name"] for item in employees}

        if current_user.role == "manager":
            tasks = supabase.list_tasks()
        else:
            if current_user.user_id is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            tasks = supabase.list_tasks_for_employee(current_user.user_id)

        normalized = [_normalize_task(task, employee_map) for task in tasks]
        overdue = [task for task in normalized if task["is_overdue"]]
        return NotificationResponse(overdue_count=len(overdue), overdue_tasks=overdue)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase error: {exc.response.text}",
        ) from exc
