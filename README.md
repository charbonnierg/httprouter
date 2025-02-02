# `httprouter`

Write router for ASGI apps using dataclasses-like classes:

- Example using FastAPI:

```python
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI
from starlette.websockets import WebSocket

from httprouter.fastapi import (
    DELETE,
    GET,
    LIFESPAN,
    PATCH,
    POST,
    PUT,
    ROUTER,
    WEBSOCKET,
    mount_router,
)

auth_responses: dict[int | str, Any] = {
    401: {
        "description": "Unauthorized",
        "content": {"application/json": {}},
    }
}


@ROUTER(prefix="/api", tags=["test"], responses=auth_responses)
class FakeRouter:
    """A router for testing purpose."""

    msg: str
    lifespan_started = False
    lifespan_stopped = False

    @GET("/get")
    async def fake_get_handler(self) -> str:
        """A GET endpoint for testing purpose."""
        return self.msg

    @POST("/post", 202)
    async def fake_post_handler(self) -> list[int]:
        """A POST endpoint for testing purpose."""
        return [0]

    @PUT("/put", 203)
    async def fake_put_handler(self) -> list[int]:
        """A PUT endpoint for testing purpose."""
        return [0]

    @PATCH("/patch", 203)
    async def fake_patch_handler(self) -> list[int]:
        """A PATCH endpoint for testing purpose."""
        return [0]

    @DELETE("/delete", 204)
    async def fake_delete_handler(self) -> None:
        """A DELETE endpoint for testing purpose."""
        return None

    @WEBSOCKET("/ws")
    async def notify(self, websocket: WebSocket) -> None:
        """A WEBSOCKET endpoint for testing purpose."""
        await websocket.accept()
        await websocket.send_json({})
        await websocket.close()

    @LIFESPAN
    async def lifespan(self) -> AsyncIterator[None]:
        """Router lifespan."""
        self.lifespan_started = True
        try:
            yield None
        finally:
            self.lifespan_stopped = True


def create_app() -> FastAPI:
    # Create the app as usual
    app = FastAPI(debug=True)
    # Mount router instance
    mount_router(app, FakeRouter("OK"))
    # Return the app
    return app
```
