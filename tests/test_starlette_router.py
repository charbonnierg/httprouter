from collections.abc import Iterator

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.schemas import SchemaGenerator
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

from httprouter.starlette import (
    DELETE,
    GET,
    PATCH,
    POST,
    PUT,
    ROUTER,
    WEBSOCKET,
    mount_router,
)


@ROUTER(prefix="/api")
class FakeRouter:
    """A router for testing purpose."""

    msg: str

    @GET("/get")
    async def fake_get_handler(self, request: Request) -> JSONResponse:
        """
        responses:
            200:
                description: A message
                examples:
                    "hello"
        """
        return JSONResponse(self.msg)

    @POST("/post")
    async def fake_post_handler(self, request: Request) -> JSONResponse:
        """A POST endpoint for testing purpose."""
        return JSONResponse([0], status_code=202)

    @PUT("/put")
    async def fake_put_handler(self, request: Request) -> JSONResponse:
        """A PUT endpoint for testing purpose."""
        return JSONResponse([0], status_code=203)

    @PATCH("/patch")
    async def fake_patch_handler(self, request: Request) -> JSONResponse:
        """A PATCH endpoint for testing purpose."""
        return JSONResponse([0], status_code=203)

    @DELETE("/delete")
    async def fake_delete_handler(self, request: Request) -> Response:
        """A DELETE endpoint for testing purpose."""
        return Response(status_code=204)

    @WEBSOCKET("/ws")
    async def notify(self, websocket: WebSocket) -> None:
        """A WEBSOCKET endpoint for testing purpose."""
        await websocket.accept()
        await websocket.send_json({})
        await websocket.close()


@ROUTER
class OpenAPIRouter:
    schema_generator: SchemaGenerator

    @GET("/openapi.json")
    async def openapi(self, request: Request) -> Response:
        return self.schema_generator.OpenAPIResponse(request=request)


def create_app() -> Starlette:
    # Create the app as usual
    app = Starlette(debug=True)
    schemas = SchemaGenerator(
        {"openapi": "3.0.0", "info": {"title": "Fake API", "version": "1.0"}}
    )
    # Mount router instance
    mount_router(app, FakeRouter("OK"))
    mount_router(app, OpenAPIRouter(schemas))
    print(schemas.get_schema(app.routes))
    print(app.routes)
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
        async def get(self, request: Request) -> JSONResponse:
            return JSONResponse(self.msg)

    app = Starlette()
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
