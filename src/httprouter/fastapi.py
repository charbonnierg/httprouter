from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from contextlib import (
    AbstractAsyncContextManager,
    asynccontextmanager,
)
from dataclasses import asdict, dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    Protocol,
    TypeAlias,
    TypeVar,
    dataclass_transform,
    overload,
)

from fastapi import APIRouter, FastAPI, Response, params
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterator, Iterator
    from enum import Enum


__all__ = [
    "DELETE",
    "GET",
    "LIFESPAN",
    "PATCH",
    "POST",
    "PUT",
    "ROUTER",
    "WEBSOCKET",
    "mount_router",
]


class Router(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Any]]


Method: TypeAlias = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
RouterLifespan: TypeAlias = Callable[[], AbstractAsyncContextManager[None]]
IncEx: TypeAlias = set[int] | set[str] | dict[int, Any] | dict[str, Any]

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
RT = TypeVar("RT", bound=Router)


@dataclass
class WEBSOCKET:
    path: str
    name: str | None = None

    def __call__(self, fn: F) -> F:
        _set_ws_route_spec(fn, self)
        return fn


@dataclass
class ROUTE:
    path: str
    status_code: int | None = None
    response_model: Any | None = field(default_factory=lambda: Default(None))
    tags: list[str | Enum] | None = None
    summary: str | None = None
    description: str | None = None
    response_description: str = "Successful Response"
    responses: dict[int | str, dict[str, Any]] | None = None
    dependencies: Sequence[params.Depends] | None = None
    deprecated: bool | None = None
    operation_id: str | None = None
    response_model_include: IncEx | None = None
    response_model_exclude: IncEx | None = None
    response_model_by_alias: bool = True
    response_model_exclude_unset: bool = False
    response_model_exclude_defaults: bool = False
    response_model_exclude_none: bool = False
    include_in_schema: bool = True
    name: str | None = None
    openapi_extra: dict[str, Any] | None = None
    methods: list[Method] = field(default_factory=lambda: ["GET"])

    def __call__(self, fn: F) -> F:
        _set_route_spec(fn, self)
        return fn


@dataclass
class GET(ROUTE):
    """Mark a method as a GET HTTP endpoint."""

    methods: list[Method] = field(default_factory=lambda: ["GET"])


@dataclass
class POST(ROUTE):
    """Mark a method as a POST HTTP endpoint."""

    methods: list[Method] = field(default_factory=lambda: ["POST"])


@dataclass
class PUT(ROUTE):
    """Mark a method as a PUT HTTP endpoint."""

    methods: list[Method] = field(default_factory=lambda: ["PUT"])


@dataclass
class PATCH(ROUTE):
    """Mark a method as a PATCH HTTP endpoint."""

    methods: list[Method] = field(default_factory=lambda: ["PATCH"])


@dataclass
class DELETE(ROUTE):
    """Mark a method as a DELETE HTTP endpoint."""

    methods: list[Method] = field(default_factory=lambda: ["DELETE"])


@dataclass
class RouterSpec:
    prefix: str = ""
    tags: list[str | Enum] | None = None
    responses: dict[Any, dict[str, Any]] | None = None
    deprecated: bool | None = None
    include_in_schema: bool = True
    dependencies: Sequence[params.Depends] | None = None
    default_response_class: type[Response] = field(
        default_factory=lambda: Default(JSONResponse)
    )


@overload
@dataclass_transform()
def ROUTER(cls: type[T]) -> type[T]: ...  # pragma: no cover


@overload
@dataclass_transform()
def ROUTER(
    *,
    prefix: str = "",
    tags: list[str | Enum] | None = None,
    responses: dict[Any, dict[str, Any]] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    dependencies: Sequence[params.Depends] | None = None,
    default_response_class: type[Response] = Default(JSONResponse),
) -> Callable[[type[T]], type[T]]: ...  # pragma: no cover


@dataclass_transform()
def ROUTER(
    cls: type[T] | None = None, **kwargs: Any
) -> type[T] | Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        _set_router_spec(cls, RouterSpec(**kwargs))
        return dataclass(cls)

    if cls is None:
        return decorator
    return decorator(cls)


def LIFESPAN(
    method: Callable[[RT], AsyncIterator[None]],
) -> Callable[[RT], AbstractAsyncContextManager[None]]:
    """Mark a method as a router lifespan."""

    wrapped = asynccontextmanager(method)
    _set_router_lifespan_marker(wrapped)
    return wrapped


################################################
#   Internal API                               #
################################################


ROUTE_SPEC_ATTR = "__route_spec__"
WS_ROUTE_SPEC_ATTR = "__ws_route_spec__"
ROUTER_LIFESPAN_ATTR = "__router_lifespan__"
ROUTER_SPEC_ATTR = "__router_spec__"


def _set_ws_route_spec(fn: Callable[..., Any], spec: WEBSOCKET) -> None:
    setattr(fn, WS_ROUTE_SPEC_ATTR, spec)


def _set_route_spec(fn: Callable[..., Any], spec: ROUTE) -> None:
    setattr(fn, ROUTE_SPEC_ATTR, spec)


def _set_router_spec(router: type[Any], spec: RouterSpec) -> None:
    setattr(router, ROUTER_SPEC_ATTR, spec)


def _set_router_lifespan_marker(
    lifespan: Callable[[RT], AbstractAsyncContextManager[None]],
) -> None:
    setattr(lifespan, ROUTER_LIFESPAN_ATTR, None)


def _find_router_spec(router: Any) -> RouterSpec | None:
    return getattr(router, ROUTER_SPEC_ATTR, None)


def _find_lifespan(router: Router) -> RouterLifespan | None:
    for _, member in inspect.getmembers(router):
        if hasattr(member, ROUTER_LIFESPAN_ATTR):
            return member
    return None


def _find_routes_from_router(
    router: Router,
) -> Iterator[tuple[Callable[..., Any], ROUTE]]:
    for _, member in inspect.getmembers(router):
        if hasattr(member, ROUTE_SPEC_ATTR):
            yield member, getattr(member, ROUTE_SPEC_ATTR)


def _find_websocket_routes_from_router(
    router: Router,
) -> Iterator[tuple[Callable[..., Any], WEBSOCKET]]:
    for _, member in inspect.getmembers(router):
        if hasattr(member, WS_ROUTE_SPEC_ATTR):
            yield member, getattr(member, WS_ROUTE_SPEC_ATTR)


def inspect_router(router: Router) -> RouterMembers:
    spec = _find_router_spec(router)
    if spec is None:
        raise TypeError("router classes must be decorated with @router decorator")
    return RouterMembers(
        spec=spec,
        routes=list(_find_routes_from_router(router)),
        websocket_routes=list(_find_websocket_routes_from_router(router)),
        lifespan=_find_lifespan(router),
    )


@dataclass
class RouterMembers:
    spec: RouterSpec
    routes: list[tuple[Callable[..., Any], ROUTE]]
    websocket_routes: list[tuple[Callable[..., Any], WEBSOCKET]]
    lifespan: RouterLifespan | None


def mount_router(
    app: FastAPI | APIRouter,
    router: Router,
    *,
    prefix: str = "",
    tags: list[str | Enum] | None = None,
    responses: dict[Any, dict[str, Any]] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    dependencies: Sequence[params.Depends] | None = None,
    default_response_class: type[Response] = Default(JSONResponse),
) -> None:
    """Mount a router into a FastAPI application or an API Router."""
    members = inspect_router(router)
    lifespan = _make_lifespan_for_router(members.lifespan)
    api_router = APIRouter(lifespan=lifespan, **asdict(members.spec))
    for fn, route_spec in members.routes:
        api_router.add_api_route(endpoint=fn, **asdict(route_spec))
    for ws_fn, ws_spec in members.websocket_routes:
        api_router.add_api_websocket_route(endpoint=ws_fn, **asdict(ws_spec))
    app.include_router(
        api_router,
        prefix=prefix,
        tags=tags,
        responses=responses,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        dependencies=dependencies,
        default_response_class=default_response_class,
    )


def _make_lifespan_for_router(
    lifespan: RouterLifespan | None,
) -> Callable[[Any], AbstractAsyncContextManager[None]] | None:
    if lifespan is None:
        return None

    @asynccontextmanager
    async def wrapper(_: Any) -> AsyncIterator[None]:
        async with lifespan():
            yield None

    return wrapper
