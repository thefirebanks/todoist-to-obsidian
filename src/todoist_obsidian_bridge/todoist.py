from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_ROOT = "https://api.todoist.com/api/v1"


class TodoistError(RuntimeError):
    pass


class TodoistClient:
    def __init__(self, token: str, api_root: str = API_ROOT) -> None:
        self.token = token
        self.api_root = api_root.rstrip("/")

    def request_json(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.api_root}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        data = None
        headers = {"Authorization": f"Bearer {self.token}"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise TodoistError(f"{method} {url} failed: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise TodoistError(f"{method} {url} failed: {exc.reason}") from exc

        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))

    def paginated_get(self, path: str, query: dict[str, str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            page_query = dict(query)
            page_query["limit"] = "200"
            if cursor:
                page_query["cursor"] = cursor
            payload = self.request_json("GET", path, query=page_query)
            results.extend(payload.get("results", []))
            cursor = payload.get("next_cursor")
            if not cursor:
                return results

    def find_project_id(self, project_name: str) -> str | None:
        for project in self.paginated_get("/projects", {}):
            if project.get("name", "").casefold() == project_name.casefold():
                return str(project["id"])
        return None

    def get_capture_tasks(self, project_name: str, label_name: str, filter_query: str) -> list[dict[str, Any]]:
        if filter_query:
            return self.paginated_get("/tasks/filter", {"query": filter_query})

        query: dict[str, str] = {}
        if project_name:
            project_id = self.find_project_id(project_name)
            if not project_id:
                raise TodoistError(f'Todoist project "{project_name}" was not found.')
            query["project_id"] = project_id
        if label_name:
            query["label"] = label_name
        return self.paginated_get("/tasks", query)

    def get_comments(self, task_id: str) -> list[dict[str, Any]]:
        return self.paginated_get("/comments", {"task_id": task_id})

    def close_task(self, task_id: str) -> None:
        self.request_json("POST", f"/tasks/{urllib.parse.quote(task_id)}/close")
