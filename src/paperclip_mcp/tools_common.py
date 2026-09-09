from __future__ import annotations

from .client import JsonValue, PaperclipClient, is_error_response, parse_json_object


async def post_json(client: PaperclipClient, path: str, body_json: str = "{}") -> JsonValue:
    body = parse_json_object(body_json)
    if is_error_response(body):
        return body
    return await client.post(path, body)


async def patch_json(client: PaperclipClient, path: str, body_json: str) -> JsonValue:
    body = parse_json_object(body_json)
    if is_error_response(body):
        return body
    return await client.patch(path, body)


async def put_json(client: PaperclipClient, path: str, body_json: str) -> JsonValue:
    body = parse_json_object(body_json)
    if is_error_response(body):
        return body
    return await client.put(path, body)
