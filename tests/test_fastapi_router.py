from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
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


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as client:
        yield client


def test_router_minimal() -> None:
    @ROUTER
    class SomeRouter:
        msg: str

        @GET("/")
        async def get(self) -> str:
            return self.msg

    app = FastAPI()
    mount_router(app, SomeRouter("OK"))
    with TestClient(app) as client:
        assert client.get("/").json() == "OK"


def test_router_endpoint_get_decorator(client: TestClient) -> None:
    response = client.get("/api/get")
    assert response.json() == "OK"
    assert response.status_code == 200


def test_router_endpoint_post_decorator(client: TestClient) -> None:
    response = client.post("/api/post")
    assert response.json() == [0]
    assert response.status_code == 202


def test_router_endpoint_put_decorator(client: TestClient) -> None:
    response = client.put("/api/put")
    assert response.json() == [0]
    assert response.status_code == 203


def test_router_endpoint_patch_decorator(client: TestClient) -> None:
    response = client.patch("/api/patch")
    assert response.json() == [0]
    assert response.status_code == 203


def test_router_endpoint_delete_decorator(client: TestClient) -> None:
    response = client.delete("/api/delete")
    assert response.text == ""
    assert response.status_code == 204


def test_router_websocket(client: TestClient) -> None:
    with client.websocket_connect("/api/ws") as websocket:
        assert websocket.receive_json() == {}


def test_router_lifespan() -> None:
    app = FastAPI(debug=True)
    router = FakeRouter("Hello world")
    mount_router(app, router)
    assert router.lifespan_started is False
    assert router.lifespan_stopped is False
    with TestClient(app):
        assert router.lifespan_started is True
    assert router.lifespan_stopped is True


def test_router_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.json() == {
        "info": {
            "title": "FastAPI",
            "version": "0.1.0",
        },
        "openapi": "3.1.0",
        "paths": {
            "/api/delete": {
                "delete": {
                    "description": "A DELETE endpoint for testing purpose.",
                    "operationId": "fake_delete_handler_api_delete_delete",
                    "responses": {
                        "204": {
                            "description": "Successful Response",
                        },
                        "401": {
                            "content": {
                                "application/json": {},
                            },
                            "description": "Unauthorized",
                        },
                    },
                    "summary": "Fake Delete Handler",
                    "tags": [
                        "test",
                    ],
                },
            },
            "/api/get": {
                "get": {
                    "description": "A GET endpoint for testing purpose.",
                    "operationId": "fake_get_handler_api_get_get",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "title": "Response Fake Get Handler Api Get Get",
                                        "type": "string",
                                    },
                                },
                            },
                            "description": "Successful Response",
                        },
                        "401": {
                            "content": {
                                "application/json": {},
                            },
                            "description": "Unauthorized",
                        },
                    },
                    "summary": "Fake Get Handler",
                    "tags": [
                        "test",
                    ],
                },
            },
            "/api/patch": {
                "patch": {
                    "description": "A PATCH endpoint for testing purpose.",
                    "operationId": "fake_patch_handler_api_patch_patch",
                    "responses": {
                        "203": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "items": {
                                            "type": "integer",
                                        },
                                        "title": "Response Fake Patch Handler Api Patch "
                                        "Patch",
                                        "type": "array",
                                    },
                                },
                            },
                            "description": "Successful Response",
                        },
                        "401": {
                            "content": {
                                "application/json": {},
                            },
                            "description": "Unauthorized",
                        },
                    },
                    "summary": "Fake Patch Handler",
                    "tags": [
                        "test",
                    ],
                },
            },
            "/api/post": {
                "post": {
                    "description": "A POST endpoint for testing purpose.",
                    "operationId": "fake_post_handler_api_post_post",
                    "responses": {
                        "202": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "items": {
                                            "type": "integer",
                                        },
                                        "title": "Response Fake Post Handler Api Post Post",
                                        "type": "array",
                                    },
                                },
                            },
                            "description": "Successful Response",
                        },
                        "401": {
                            "content": {
                                "application/json": {},
                            },
                            "description": "Unauthorized",
                        },
                    },
                    "summary": "Fake Post Handler",
                    "tags": [
                        "test",
                    ],
                },
            },
            "/api/put": {
                "put": {
                    "description": "A PUT endpoint for testing purpose.",
                    "operationId": "fake_put_handler_api_put_put",
                    "responses": {
                        "203": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "items": {
                                            "type": "integer",
                                        },
                                        "title": "Response Fake Put Handler Api Put Put",
                                        "type": "array",
                                    },
                                },
                            },
                            "description": "Successful Response",
                        },
                        "401": {
                            "content": {
                                "application/json": {},
                            },
                            "description": "Unauthorized",
                        },
                    },
                    "summary": "Fake Put Handler",
                    "tags": [
                        "test",
                    ],
                },
            },
        },
    }
