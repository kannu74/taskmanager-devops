import httpx

from app.config import settings


class SupabaseRestClient:
    def __init__(self, url: str, secret_key: str) -> None:
        base_url = url.rstrip("/")
        self.rest_url = f"{base_url}/rest/v1"
        self.headers = {
            "apikey": secret_key,
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        }

    def list_employees(self) -> list[dict]:
        response = httpx.get(
            f"{self.rest_url}/employees",
            params={"select": "id,name,created_at", "order": "created_at.desc"},
            headers=self.headers,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def create_employee(self, name: str, password: str) -> dict:
        response = httpx.post(
            f"{self.rest_url}/employees",
            params={"select": "id,name,created_at"},
            headers={**self.headers, "Prefer": "return=representation"},
            json={"name": name, "password": password},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if data else {}

    def find_employee_by_credentials(self, name: str, password: str) -> dict | None:
        response = httpx.get(
            f"{self.rest_url}/employees",
            params={
                "select": "id,name",
                "name": f"eq.{name}",
                "password": f"eq.{password}",
                "limit": "1",
            },
            headers=self.headers,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None

    def list_tasks(self) -> list[dict]:
        response = httpx.get(
            f"{self.rest_url}/tasks",
            params={
                "select": "id,title,description,deadline,assigned_employee_id,status,not_completed_reason,created_at,updated_at",
                "order": "created_at.desc",
            },
            headers=self.headers,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def list_tasks_for_employee(self, employee_id: int) -> list[dict]:
        response = httpx.get(
            f"{self.rest_url}/tasks",
            params={
                "select": "id,title,description,deadline,assigned_employee_id,status,not_completed_reason,created_at,updated_at",
                "assigned_employee_id": f"eq.{employee_id}",
                "order": "created_at.desc",
            },
            headers=self.headers,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def create_task(
        self,
        title: str,
        description: str,
        deadline_iso: str,
        assigned_employee_id: int,
    ) -> dict:
        response = httpx.post(
            f"{self.rest_url}/tasks",
            params={
                "select": "id,title,description,deadline,assigned_employee_id,status,not_completed_reason,created_at,updated_at"
            },
            headers={**self.headers, "Prefer": "return=representation"},
            json={
                "title": title,
                "description": description,
                "deadline": deadline_iso,
                "assigned_employee_id": assigned_employee_id,
                "status": "pending",
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if data else {}

    def update_task_status(
        self,
        task_id: int,
        employee_id: int,
        status_value: str,
        not_completed_reason: str | None,
    ) -> dict:
        response = httpx.patch(
            f"{self.rest_url}/tasks",
            params={
                "id": f"eq.{task_id}",
                "assigned_employee_id": f"eq.{employee_id}",
                "select": "id,title,description,deadline,assigned_employee_id,status,not_completed_reason,created_at,updated_at",
            },
            headers={**self.headers, "Prefer": "return=representation"},
            json={
                "status": status_value,
                "not_completed_reason": not_completed_reason,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if data else {}

    def delete_task(self, task_id: int) -> list[dict]:
        response = httpx.delete(
            f"{self.rest_url}/tasks",
            params={"id": f"eq.{task_id}", "select": "id"},
            headers={**self.headers, "Prefer": "return=representation"},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()


_supabase_client: SupabaseRestClient | None = None


def get_supabase_client() -> SupabaseRestClient:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseRestClient(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _supabase_client
