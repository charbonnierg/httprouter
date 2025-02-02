from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from litestar import Litestar, Request, WebSocket
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.datastructures import ResponseSpec
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.testing import TestClient

from httprouter.litestar import (
    DELETE,
    GET,
    PATCH,
    POST,
    PUT,
    ROUTER,
    WEBSOCKET,
    mount_router,
)


@dataclass
class UnauthorizedResponse:
    msg: str = "Unauthorized"


auth_responses = {401: ResponseSpec(UnauthorizedResponse, description="Unauthorized")}


@ROUTER(prefix="/api", tags=["Test"], responses=auth_responses)
class FakeRouter:
    """A router for testing purpose."""

    msg: str

    @GET("/get")
    async def fake_get_handler(self) -> dict[str, str]:
        """A GET endpoint for testing purpose."""
        return {"msg": self.msg}

    @POST("/post", status_code=202)
    async def fake_post_handler(self) -> list[int]:
        """A POST endpoint for testing purpose."""
        return [0]

    @PUT("/put", status_code=203)
    async def fake_put_handler(self) -> list[int]:
        """A PUT endpoint for testing purpose."""
        return [0]

    @PATCH("/patch", status_code=203)
    async def fake_patch_handler(self) -> list[int]:
        """A PATCH endpoint for testing purpose."""
        return [0]

    @DELETE("/delete", status_code=204)
    async def fake_delete_handler(self) -> None:
        """A DELETE endpoint for testing purpose."""
        return None

    @WEBSOCKET("/ws")
    async def notify(self, socket: WebSocket[Any, Any, Any]) -> None:
        """A WEBSOCKET endpoint for testing purpose."""
        await socket.accept()
        await socket.send_json({})
        await socket.close()


@ROUTER(tags=["OpenAPI"])
class OpenAPIRouter:
    @GET("/openapi.json", tags=["OpenAPI"])
    async def my_route_handler(self, request: Request) -> dict:
        schema = request.app.openapi_schema
        return schema.to_schema()


def create_app() -> Litestar:
    # Create the app as usual
    app = Litestar(
        openapi_config=OpenAPIConfig(
            title="Fake app",
            version="1.0",
            render_plugins=[SwaggerRenderPlugin()],
        )
    )
    # Mount router instance
    mount_router(app, FakeRouter("OK"))
    mount_router(app, OpenAPIRouter())
    # Return the app
    return app


@pytest.fixture
def client() -> Iterator[TestClient[Litestar]]:
    with TestClient(create_app()) as client:
        yield client


def test_router_minimal() -> None:
    @ROUTER
    class SomeRouter:
        msg: str

        @GET("/")
        async def get(self) -> dict[str, str]:
            return {"msg": self.msg}

    app = Litestar()
    mount_router(app, SomeRouter("OK"))
    with TestClient(app) as client:
        assert client.get("/").json() == {"msg": "OK"}


def test_router_endpoint_get_decorator(client: TestClient[Litestar]) -> None:
    response = client.get("/api/get")
    assert response.json() == {"msg": "OK"}
    assert response.status_code == 200


def test_router_endpoint_post_decorator(client: TestClient[Litestar]) -> None:
    response = client.post("/api/post")
    assert response.json() == [0]
    assert response.status_code == 202


def test_router_endpoint_put_decorator(client: TestClient[Litestar]) -> None:
    response = client.put("/api/put")
    assert response.json() == [0]
    assert response.status_code == 203


def test_router_endpoint_patch_decorator(client: TestClient[Litestar]) -> None:
    response = client.patch("/api/patch")
    assert response.json() == [0]
    assert response.status_code == 203


def test_router_endpoint_delete_decorator(client: TestClient[Litestar]) -> None:
    response = client.delete("/api/delete")
    assert response.text == ""
    assert response.status_code == 204


def test_router_websocket(client: TestClient[Litestar]) -> None:
    with client.websocket_connect("/api/ws") as websocket:
        assert websocket.receive_json() == {}


def test_router_openapi(client: TestClient[Litestar]) -> None:
    response = client.get("/openapi.json")
    assert response.json() == {
        "info": {"title": "Fake app", "version": "1.0"},
        "openapi": "3.1.0",
        "servers": [{"url": "/"}],
        "paths": {
            "/api/delete": {
                "delete": {
                    "tags": ["Test"],
                    "summary": "FakeDeleteHandler",
                    "operationId": "ApiDeleteFakeDeleteHandler",
                    "responses": {
                        "204": {
                            "description": "Request fulfilled, nothing follows",
                            "headers": {},
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/UnauthorizedResponse"
                                    }
                                }
                            },
                        },
                    },
                    "deprecated": False,
                }
            },
            "/api/get": {
                "get": {
                    "tags": ["Test"],
                    "summary": "FakeGetHandler",
                    "operationId": "ApiGetFakeGetHandler",
                    "responses": {
                        "200": {
                            "description": "Request fulfilled, document follows",
                            "headers": {},
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "additionalProperties": {"type": "string"},
                                        "type": "object",
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/UnauthorizedResponse"
                                    }
                                }
                            },
                        },
                    },
                    "deprecated": False,
                }
            },
            "/api/patch": {
                "patch": {
                    "tags": ["Test"],
                    "summary": "FakePatchHandler",
                    "operationId": "ApiPatchFakePatchHandler",
                    "responses": {
                        "203": {
                            "description": "Request fulfilled from cache",
                            "headers": {},
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "items": {"type": "integer"},
                                        "type": "array",
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/UnauthorizedResponse"
                                    }
                                }
                            },
                        },
                    },
                    "deprecated": False,
                }
            },
            "/api/post": {
                "post": {
                    "tags": ["Test"],
                    "summary": "FakePostHandler",
                    "operationId": "ApiPostFakePostHandler",
                    "responses": {
                        "202": {
                            "description": "Request accepted, processing continues off-line",
                            "headers": {},
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "items": {"type": "integer"},
                                        "type": "array",
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/UnauthorizedResponse"
                                    }
                                }
                            },
                        },
                    },
                    "deprecated": False,
                }
            },
            "/api/put": {
                "put": {
                    "tags": ["Test"],
                    "summary": "FakePutHandler",
                    "operationId": "ApiPutFakePutHandler",
                    "responses": {
                        "203": {
                            "description": "Request fulfilled from cache",
                            "headers": {},
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "items": {"type": "integer"},
                                        "type": "array",
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/UnauthorizedResponse"
                                    }
                                }
                            },
                        },
                    },
                    "deprecated": False,
                }
            },
            "/openapi.json": {
                "get": {
                    "tags": ["OpenAPI"],
                    "summary": "MyRouteHandler",
                    "operationId": "OpenapiJsonMyRouteHandler",
                    "responses": {
                        "200": {
                            "description": "Request fulfilled, document follows",
                            "headers": {},
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                        }
                    },
                    "deprecated": False,
                }
            },
        },
        "components": {
            "schemas": {
                "UnauthorizedResponse": {
                    "properties": {
                        "msg": {
                            "type": "string",
                            "default": "Unauthorized",
                            "examples": ["DwEkQQHiBrmXZcSFtoJx"],
                        }
                    },
                    "type": "object",
                    "required": [],
                    "title": "UnauthorizedResponse",
                    "examples": [{"msg": "JIgNZYFcagWptUqCwdER"}],
                }
            }
        },
    }
