from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias

from pydantic import JsonValue as PydanticJsonValue

JsonValue: TypeAlias = PydanticJsonValue
JsonObject: TypeAlias = dict[str, JsonValue]
QueryValue: TypeAlias = str | int | float | bool | None
QueryParams: TypeAlias = Mapping[str, QueryValue]
QueryParameters: TypeAlias = dict[str, QueryValue]
UploadFile: TypeAlias = tuple[str, bytes, str]
