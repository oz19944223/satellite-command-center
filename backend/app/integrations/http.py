from __future__ import annotations
import asyncio
from typing import Any
import httpx

class UpstreamError(RuntimeError):
    def __init__(self, source: str, message: str, status_code: int | None = None):
        super().__init__(message)
        self.source = source
        self.status_code = status_code
        self.message = message

class SafeHttpClient:
    def __init__(self, source: str, timeout: float = 10.0, transport: httpx.AsyncBaseTransport | None = None):
        self.source = source
        self.timeout = timeout
        self.transport = transport

    async def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        delays = [0.0, 0.5, 1.0, 2.0]
        last: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport, follow_redirects=True) as client:
            for attempt, delay in enumerate(delays):
                if delay:
                    await asyncio.sleep(delay)
                try:
                    response = await client.get(url, params=params)
                    if response.status_code == 429 or response.status_code >= 500:
                        last = UpstreamError(self.source, f"HTTP {response.status_code}", response.status_code)
                        continue
                    response.raise_for_status()
                    return response.json()
                except (httpx.TimeoutException, httpx.ConnectError) as exc:
                    last = exc
                    continue
                except httpx.HTTPStatusError as exc:
                    raise UpstreamError(self.source, str(exc), exc.response.status_code) from exc
                except ValueError as exc:
                    raise UpstreamError(self.source, "Malformed JSON response") from exc
        raise UpstreamError(self.source, str(last or "Upstream request failed"))
