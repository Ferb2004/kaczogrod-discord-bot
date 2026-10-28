import asyncio
from dataclasses import dataclass, field


@dataclass
class Request:
    url: str
    params: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)

@dataclass
class Response:
    status_code: int
    json: dict | list = field(default_factory=dict)
    text: str = field(default_factory=str)
    headers: dict = field(default_factory=dict)
    success: bool = field(default=False)

async def get_request(session, request: Request):
    async with session.get(request.url, params=request.params, headers=request.headers) as r:
        text = await r.text()
        try:
            json_data = await r.json(content_type=None)
        except ValueError:
            json_data = {}

        return Response(
            status_code=r.status,
            json=json_data,
            text=text,
            headers=dict(r.headers),
            success=r.ok,
        )

async def get_all_requests(session, requests_list, return_exceptions=False):
    return await asyncio.gather(
        *(get_request(session, request) for request in requests_list),
        return_exceptions=return_exceptions,
    )