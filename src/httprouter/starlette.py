from __future__ import annotations

import inspect
from collections.abc import Callable
from contextlib import (
    AbstractAsyncContextManager,
)
from dataclasses import asdict, dataclass, field, replace
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    ClassVar,
    Literal,
    Protocol,
    Sequence,
    TypeAlias,
    TypeVar,
    dataclass_transform,
    overload,
)

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, WebSocketRoute
from starlette.routing import Router as StarletteRouter
from starlette.websockets import WebSocket

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterator


__all__ = [
    "DELETE",
    "GET",
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
F = TypeVar("F", bound=Callable[[Any, Request], Awaitable[Response]])
WF = TypeVar("WF", bound=Callable[[Any, WebSocket], Awaitable[None]])
RT = TypeVar("RT", bound=Router)


@dataclass
class WEBSOCKET:
    path: str
    name: str | None = None

    def __call__(self, fn: WF) -> WF:
        _set_ws_route_spec(fn, self)
        return fn


@dataclass
class ROUTE:
    path: str
    include_in_schema: bool = True
    name: str | None = None
    middleware: Sequence[Middleware] | None = None
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
    middleware: Sequence[Middleware] | None = None


@overload
@dataclass_transform()
def ROUTER(cls: type[T]) -> type[T]: ...  # pragma: no cover


@overload
@dataclass_transform()
def ROUTER(
    *, prefix: str = "", middleware: Sequence[Middleware] | None = None
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


################################################
#   Internal API                               #
################################################


ROUTE_SPEC_ATTR = "__route_spec__"
WS_ROUTE_SPEC_ATTR = "__ws_route_spec__"
ROUTER_SPEC_ATTR = "__router_spec__"


def _set_ws_route_spec(fn: Callable[..., Any], spec: WEBSOCKET) -> None:
    setattr(fn, WS_ROUTE_SPEC_ATTR, spec)


def _set_route_spec(fn: Callable[..., Any], spec: ROUTE) -> None:
    setattr(fn, ROUTE_SPEC_ATTR, spec)


def _set_router_spec(router: type[Any], spec: RouterSpec) -> None:
    setattr(router, ROUTER_SPEC_ATTR, spec)


def _find_router_spec(router: Any) -> RouterSpec | None:
    return getattr(router, ROUTER_SPEC_ATTR, None)


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
    )


@dataclass
class RouterMembers:
    spec: RouterSpec
    routes: list[tuple[Callable[..., Any], ROUTE]]
    websocket_routes: list[tuple[Callable[..., Any], WEBSOCKET]]


def mount_router(
    app: Starlette | StarletteRouter,
    router: Router,
    *,
    prefix: str = "",
) -> None:
    """Mount a router into a FastAPI application or an API Router."""
    members = inspect_router(router)
    spec = replace(members.spec)
    for fn, route_spec in members.routes:
        route_spec = replace(route_spec)
        route_spec.middleware = concat(spec.middleware, route_spec.middleware)
        route_spec.path = _get_path(prefix, spec, route_spec)
        route = Route(endpoint=fn, **asdict(route_spec))
        app.routes.append(route)
    for ws_fn, ws_spec in members.websocket_routes:
        ws_spec = replace(ws_spec)
        ws_spec.path = _get_path(prefix, spec, ws_spec)
        ws_route = WebSocketRoute(endpoint=ws_fn, **asdict(ws_spec))
        app.routes.append(ws_route)


def concat(a: Sequence[T] | None, b: Sequence[T] | None) -> Sequence[T] | None:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return [*a, *b]


def _get_path(
    mount_prefix: str, router_spec: RouterSpec, spec: ROUTE | WEBSOCKET
) -> str:
    mount_prefix = mount_prefix.rstrip("/")
    router_prefix = router_spec.prefix.rstrip("/").lstrip("/")
    path = spec.path.lstrip("/")
    if not router_prefix:
        return f"{mount_prefix}/{path}"
    else:
        return f"{mount_prefix}/{router_prefix}/{path}"
