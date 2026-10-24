"""Kodi JSON-RPC HTTP adapter."""

from typing import Any

import httpx


class KodiError(RuntimeError):
    """Raised when Kodi rejects or cannot process a command."""


class KodiClient:
    def __init__(self, url: str, timeout: float = 30.0, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._url = url
        self._timeout = timeout
        self._transport = transport

    async def _call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": "smart-control-voice", "method": method}
        if params is not None:
            payload["params"] = params
        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                response = await client.post(self._url, json=payload)
                response.raise_for_status()
                body = response.json()
        except Exception as error:
            raise KodiError(f"Kodi request failed: {method}") from error
        if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
            raise KodiError(f"Kodi returned an invalid response for {method}")
        if "error" in body:
            raise KodiError(f"Kodi rejected {method}: {body['error']}")
        return body.get("result")

    async def open(self, media_url: str) -> Any:
        return await self._call("Player.Open", {"item": {"file": media_url}})

    async def stop(self) -> Any:
        return await self._call("Player.Stop", {"playerid": 1})

    async def set_volume(self, volume: int) -> Any:
        return await self._call("Application.SetVolume", {"volume": volume})