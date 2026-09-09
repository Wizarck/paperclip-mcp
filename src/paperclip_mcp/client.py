from __future__ import annotations

import json
import mimetypes
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import httpx

from .json_types import JsonObject, JsonValue, QueryParameters, QueryParams, UploadFile
from .registry import disabled_tool_names

__all__ = ["JsonObject", "JsonValue", "QueryParameters"]


@dataclass(frozen=True, slots=True)
class Settings:
    base_url: str
    api_key: str
    company_id: str
    run_id: str
    disabled_tools: frozenset[str]

    @classmethod
    def from_env(cls, environment: Mapping[str, str] | None = None) -> Settings:
        source = os.environ if environment is None else environment
        return cls(
            base_url=source.get("PAPERCLIP_BASE_URL", "http://localhost:3100/api").rstrip("/"),
            api_key=source.get("PAPERCLIP_API_KEY", ""),
            company_id=source.get("PAPERCLIP_COMPANY_ID", ""),
            run_id=source.get("PAPERCLIP_RUN_ID", ""),
            disabled_tools=disabled_tool_names(source.get("PAPERCLIP_DISABLED_TOOLS", "")),
        )


def error_response(message: str, status: int | None = None) -> JsonObject:
    payload: JsonObject = {"isError": True, "message": message}
    if status is not None:
        payload["status"] = status
    return payload


def parse_json_object(body_json: str) -> JsonObject:
    try:
        value: JsonValue = json.loads(body_json)
    except json.JSONDecodeError as exc:
        return error_response(f"body_json must be valid JSON: {exc}")
    if not isinstance(value, dict):
        return error_response("body_json must be a JSON object.")
    return value


def is_error_response(value: JsonObject) -> bool:
    return value.get("isError") is True


class PaperclipClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def company_id(self) -> str:
        return self._settings.company_id

    def headers(
        self,
        additional_headers: Mapping[str, str] | None = None,
        *,
        include_json_content_type: bool = True,
    ) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._settings.api_key}"}
        if include_json_content_type:
            headers["Content-Type"] = "application/json"
        if self._settings.run_id:
            headers["X-Paperclip-Run-Id"] = self._settings.run_id
        if additional_headers:
            headers.update(additional_headers)
        return headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | None = None,
        body: Mapping[str, JsonValue] | None = None,
        files: dict[str, UploadFile] | None = None,
        additional_headers: Mapping[str, str] | None = None,
    ) -> JsonValue:
        url = f"{self._settings.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self.headers(
                        additional_headers, include_json_content_type=files is None
                    ),
                    params=params,
                    json=body,
                    files=files,
                )
                if response.status_code == 409:
                    return error_response(
                        "Conflict (409): Paperclip rejected this operation because the resource "
                        "is in a conflicting state. Do not retry without resolving the conflict.",
                        status=409,
                    )
                response.raise_for_status()
                if response.status_code == 204 or not response.content:
                    return {"ok": True}
                response_body: JsonValue = response.json()
                return response_body
        except httpx.HTTPStatusError as exc:
            return error_response(
                f"HTTP {exc.response.status_code} from Paperclip API: {exc.response.text[:400]}",
                status=exc.response.status_code,
            )
        except httpx.RequestError as exc:
            return error_response(
                f"Could not reach Paperclip at {self._settings.base_url}. "
                f"Is the server running? Error: {exc}"
            )

    async def get(self, path: str, params: QueryParams | None = None) -> JsonValue:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, body: Mapping[str, JsonValue] | None = None) -> JsonValue:
        return await self.request("POST", path, body=body)

    async def patch(self, path: str, body: Mapping[str, JsonValue]) -> JsonValue:
        return await self.request("PATCH", path, body=body)

    async def put(self, path: str, body: Mapping[str, JsonValue] | None = None) -> JsonValue:
        return await self.request("PUT", path, body=body)

    async def delete(self, path: str, params: QueryParams | None = None) -> JsonValue:
        return await self.request("DELETE", path, params=params)

    async def upload_file(self, path: str, file_path: str, field_name: str = "file") -> JsonValue:
        source = Path(file_path)
        try:
            contents = source.read_bytes()
        except OSError as exc:
            return error_response(f"Could not read upload file '{file_path}': {exc}")
        content_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        return await self.request(
            "POST",
            path,
            files={field_name: (source.name, contents, content_type)},
        )
