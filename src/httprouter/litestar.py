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
    ClassVar,
    Mapping,
    Protocol,
    Sequence,
    TypeAlias,
    TypeVar,
    dataclass_transform,
    overload,
)

import litestar.types as lt
from litestar import Litestar, Request, Response, WebSocket, route, websocket
from litestar import Router as LitestarRouter
from litestar.background_tasks import BackgroundTask, BackgroundTasks
from litestar.config.response_cache import CACHE_FOREVER
from litestar.datastructures import CacheControlHeader, ETag
from litestar.dto import AbstractDTO
from litestar.enums import HttpMethod, MediaType
from litestar.exceptions import HTTPException
from litestar.openapi.datastructures import ResponseSpec
from litestar.openapi.spec import Operation, SecurityRequirement

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


Method: TypeAlias = HttpMethod | lt.Method | Sequence[HttpMethod | lt.Method]
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
    path: str | Sequence[str]
    after_request: lt.AfterRequestHookHandler | None = None
    after_response: lt.AfterResponseHookHandler | None = None
    background: BackgroundTask | BackgroundTasks | None = None
    before_request: lt.BeforeRequestHookHandler | None = None
    cache: bool | int | type[CACHE_FOREVER] = False
    cache_control: CacheControlHeader | None = None
    cache_key_builder: lt.CacheKeyBuilder | None = None
    dto: type[AbstractDTO[Any]] | None | lt.EmptyType = lt.Empty
    etag: ETag | None = None
    exception_handlers: lt.ExceptionHandlersMap | None = None
    guards: Sequence[lt.Guard] | None = None
    http_method: Method = field(default_factory=lambda: HttpMethod.GET)
    media_type: MediaType | str | None = None
    middleware: Sequence[lt.Middleware] | None = None
    name: str | None = None
    opt: Mapping[str, Any] | None = None
    request_class: type[Request[Any, Any, Any]] | None = None
    request_max_body_size: int | None | lt.EmptyType = lt.Empty
    response_class: type[Response[Any]] | None = None
    response_cookies: lt.ResponseCookies | None = None
    response_headers: lt.ResponseHeaders | None = None
    return_dto: type[AbstractDTO[Any]] | None | lt.EmptyType = lt.Empty
    status_code: int | None = None
    sync_to_thread: bool | None = None
    # OpenAPI related attributes
    content_encoding: str | None = None
    content_media_type: str | None = None
    deprecated: bool = False
    description: str | None = None
    include_in_schema: bool | lt.EmptyType = lt.Empty
    operation_class: type[Operation] = Operation
    operation_id: str | lt.OperationIDCreator | None = None
    raises: Sequence[type[HTTPException]] | None = None
    response_description: str | None = None
    responses: Mapping[int, ResponseSpec] | None = None
    signature_namespace: Mapping[str, Any] | None = None
    security: Sequence[SecurityRequirement] | None = None
    summary: str | None = None
    tags: Sequence[str] | None = None
    type_decoders: lt.TypeDecodersSequence | None = None
    type_encoders: lt.TypeEncodersMap | None = None

    def __call__(self, fn: F) -> F:
        _set_route_spec(fn, self)
        return fn


@dataclass
class GET(ROUTE):
    """Mark a method as a GET HTTP endpoint."""

    http_method: Method = "GET"


@dataclass
class POST(ROUTE):
    """Mark a method as a POST HTTP endpoint."""

    http_method: Method = "POST"


@dataclass
class PUT(ROUTE):
    """Mark a method as a PUT HTTP endpoint."""

    http_method: Method = "PUT"


@dataclass
class PATCH(ROUTE):
    """Mark a method as a PATCH HTTP endpoint."""

    http_method: Method = "PATCH"


@dataclass
class DELETE(ROUTE):
    """Mark a method as a DELETE HTTP endpoint."""

    http_method: Method = "DELETE"


@dataclass
class RouterSpec:
    prefix: str = ""
    after_request: lt.AfterRequestHookHandler | None = None
    after_response: lt.AfterResponseHookHandler | None = None
    before_request: lt.BeforeRequestHookHandler | None = None
    cache_control: CacheControlHeader | None = None
    dependencies: lt.Dependencies | None = None
    dto: type[AbstractDTO[Any]] | None | lt.EmptyType = lt.Empty
    etag: ETag | None = None
    exception_handlers: lt.ExceptionHandlersMap | None = None
    guards: Sequence[lt.Guard] | None = None
    include_in_schema: bool | lt.EmptyType = lt.Empty
    middleware: Sequence[lt.Middleware] | None = None
    opt: Mapping[str, Any] | None = None
    parameters: lt.ParametersMap | None = None
    request_class: type[Request[Any, Any, Any]] | None = None
    response_class: type[Response[Any]] | None = None
    response_cookies: lt.ResponseCookies | None = None
    response_headers: lt.ResponseHeaders | None = None
    return_dto: type[AbstractDTO[Any]] | None | lt.EmptyType = lt.Empty
    security: Sequence[SecurityRequirement] | None = None
    signature_namespace: Mapping[str, Any] | None = None
    signature_types: Sequence[Any] | None = None
    tags: Sequence[str] | None = None
    type_decoders: lt.TypeDecodersSequence | None = None
    type_encoders: lt.TypeEncodersMap | None = None
    websocket_class: type[WebSocket[Any, Any, Any]] | None = None
    request_max_body_size: int | None | lt.EmptyType = lt.Empty
    responses: Mapping[int, ResponseSpec] | None = None


@overload
@dataclass_transform()
def ROUTER(cls: type[T]) -> type[T]: ...  # pragma: no cover


@overload
@dataclass_transform()
def ROUTER(
    *,
    prefix: str = "",
    after_request: lt.AfterRequestHookHandler | None = None,
    after_response: lt.AfterResponseHookHandler | None = None,
    before_request: lt.BeforeRequestHookHandler | None = None,
    cache_control: CacheControlHeader | None = None,
    dependencies: lt.Dependencies | None = None,
    dto: type[AbstractDTO[Any]] | None | lt.EmptyType = lt.Empty,
    etag: ETag | None = None,
    exception_handlers: lt.ExceptionHandlersMap | None = None,
    guards: Sequence[lt.Guard] | None = None,
    include_in_schema: bool | lt.EmptyType = lt.Empty,
    middleware: Sequence[lt.Middleware] | None = None,
    opt: Mapping[str, Any] | None = None,
    parameters: lt.ParametersMap | None = None,
    request_class: type[Request[Any, Any, Any]] | None = None,
    response_class: type[Response[Any]] | None = None,
    response_cookies: lt.ResponseCookies | None = None,
    response_headers: lt.ResponseHeaders | None = None,
    return_dto: type[AbstractDTO[Any]] | None | lt.EmptyType = lt.Empty,
    security: Sequence[SecurityRequirement] | None = None,
    signature_namespace: Mapping[str, Any] | None = None,
    signature_types: Sequence[Any] | None = None,
    tags: Sequence[str] | None = None,
    type_decoders: lt.TypeDecodersSequence | None = None,
    type_encoders: lt.TypeEncodersMap | None = None,
    websocket_class: type[WebSocket[Any, Any, Any]] | None = None,
    request_max_body_size: int | None | lt.EmptyType = lt.Empty,
    responses: dict[int, ResponseSpec] | None = None,
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
    app: Litestar,
    router: Router,
    *,
    prefix: str = "",
    responses: Mapping[int, ResponseSpec] | None = None,
    tags: list[str] | None = None,
    include_in_schema: bool | lt.EmptyType = lt.Empty,
) -> None:
    """Mount a router into a FastAPI application or an API Router."""
    members = inspect_router(router)
    spec = replace(members.spec)
    spec.responses = merge(responses, spec.responses)
    spec.tags = concat_unique(tags, spec.tags)
    if prefix:
        spec.prefix = f"{prefix.rstrip('/')}/{spec.prefix.lstrip('/')}"
    if include_in_schema is not lt.Empty:
        spec.include_in_schema = include_in_schema
    options = asdict(spec)
    del options["responses"]
    del options["prefix"]
    api_router = LitestarRouter(
        path=spec.prefix,
        route_handlers=[],
        **options,
    )
    for fn, route_spec in members.routes:
        route_spec = replace(route_spec)
        route_spec.responses = merge(spec.responses, route_spec.responses)
        options = asdict(route_spec)
        options["responses"] = spec.responses
        controller = route(**options)(fn)
        api_router.register(controller)
    for ws_fn, ws_spec in members.websocket_routes:
        ws_controller = websocket(path=ws_spec.path, name=ws_spec.name)(ws_fn)
        api_router.register(ws_controller)
    app.register(api_router)


K = TypeVar("K")
V = TypeVar("V")


def merge(a: Mapping[K, V] | None, b: Mapping[K, V] | None) -> Mapping[K, V] | None:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return {**a, **b}


def concat_unique(a: Sequence[V] | None, b: Sequence[V] | None) -> Sequence[V] | None:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return list({*a, *b})
