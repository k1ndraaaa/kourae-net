from __future__ import annotations
import base64, importlib, json
from typing import Any, Optional, Mapping, BinaryIO, Union, Dict, List, Tuple, Callable
from dataclasses import dataclass, field
from io import BytesIO, IOBase, BufferedIOBase, RawIOBase
from types import MappingProxyType
from cgi import parse_header

#helpers propios
def _freeze_mapping(data: Optional[Mapping]) -> Mapping:
    if not data:
        return MappingProxyType({})
    return MappingProxyType(dict(data))
def _normalize_headers(headers: Optional[Mapping[str, str]]) -> Mapping[str, str]:
    if not headers:
        return MappingProxyType({})
    return MappingProxyType({k.lower(): v for k, v in headers.items()})
def _is_instance_of(obj, module_name, class_name):
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        return isinstance(obj, cls)
    except ImportError:
        return False
def _check(obj, module_name, class_name):
    return _is_instance_of(obj, module_name, class_name)
def to_binary_io(file_obj: Union[bytes, bytearray, BinaryIO, object]) -> BinaryIO:
    """
        Normaliza diferentes tipos de entrada a un BinaryIO válido.
        Soporta:
            - bytes o bytearray
            - IOBase (archivos abiertos en modo binario)
            - Wrappers comunes que exponen `.file` o `.stream`
            - Objetos con método `.read()` que retornen bytes
        No depende de ningún framework específico.
    """
    if isinstance(file_obj, (bytes, bytearray)):
        return BytesIO(file_obj)
    if isinstance(file_obj, (BufferedIOBase, RawIOBase)):
        return file_obj
    if isinstance(file_obj, IOBase):
        if getattr(file_obj, "encoding", None) is not None:
            raise TypeError("Se recibió un stream de texto, pedí binario!!")
        return file_obj
    for attr in ("file", "stream"):
        candidate = getattr(file_obj, attr, None)
        if isinstance(candidate, (BufferedIOBase, RawIOBase)):
            return candidate
    read_method = getattr(file_obj, "read", None)
    if callable(read_method):
        try:
            probe = read_method(0)
            if isinstance(probe, bytes):
                return file_obj
        except Exception:
            pass
    raise TypeError(
        f"Tipo de archivo no soportado: {type(file_obj).__name__}"
    )

#objetos de la solicitud
@dataclass(frozen=True, slots=True)
class Client:
    ip: Optional[str] = None
    port: Optional[int] = None
    user_agent: Optional[str] = None
@dataclass(frozen=True, slots=True)
class Auth:
    type: Optional[str] = None
    credentials: Any = None
@dataclass(frozen=True, slots=True)
class Request:
    method: str
    url: str
    path: str
    headers: Mapping[str, str] = field(default_factory=dict)
    query_params: Mapping[str, Any] = field(default_factory=dict)
    path_params: Mapping[str, Any] = field(default_factory=dict)
    body: Any = None
    form: Mapping[str, Any] = field(default_factory=dict)
    files: Mapping[str, Any] = field(default_factory=dict)
    cookies: Mapping[str, str] = field(default_factory=dict)
    client: Client = field(default_factory=Client)
    auth: Auth = field(default_factory=Auth)
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "method", self.method.upper())
        object.__setattr__(self, "headers", _normalize_headers(self.headers))
        object.__setattr__(self, "query_params", _freeze_mapping(self.query_params))
        object.__setattr__(self, "path_params", _freeze_mapping(self.path_params))
        object.__setattr__(self, "form", _freeze_mapping(self.form))
        object.__setattr__(self, "files", _freeze_mapping(self.files))
        object.__setattr__(self, "cookies", _freeze_mapping(self.cookies))
        object.__setattr__(self, "meta", _freeze_mapping(self.meta))

    def header(self, name: str, default: Any = None) -> Any:
        return self.headers.get(name.lower(), default)
    def query(self, name: str, default: Any = None) -> Any:
        return self.query_params.get(name, default)
    def json(self, default: Any = None, *, silent: bool = False) -> Any:
        if self.body is None:
            return default
        if isinstance(self.body, (dict, list)):
            return self.body
        if isinstance(self.body, (str, bytes)):
            try:
                return json.loads(self.body)
            except json.JSONDecodeError:
                if silent:
                    return default
                raise
        return default
    def is_json(self) -> bool:
        content_type = self.header("content-type", "")
        mime_type, _ = parse_header(content_type)
        mime_type = mime_type.lower()
        return mime_type == "application/json" or mime_type.endswith("+json")
    def is_multipart_formdata(self) -> bool:
        content_type = self.header("content-type", "")
        mime_type, params = parse_header(content_type)
        return (
            mime_type.lower() == "multipart/form-data"
            and "boundary" in params
        )

#traductores
def translate_flask_request(flask_req: Any) -> Request:
    headers: Dict[str, str] = dict(flask_req.headers)
    query_params: Dict[str, List[str]] = {
        key: flask_req.args.getlist(key)
        for key in flask_req.args
    }
    form: Dict[str, List[str]] = {
        key: flask_req.form.getlist(key)
        for key in flask_req.form
    }
    body = flask_req.get_data(cache=True)
    files = {}
    for key, storage in flask_req.files.items():
        files[key] = {
            "filename": storage.filename,
            "content_type": storage.content_type,
            "stream": to_binary_io(storage),
        }
    cookies = dict(flask_req.cookies)
    headers_lower = {k.lower(): v for k, v in headers.items()}
    client_ip = (
        headers_lower.get("x-forwarded-for", "").split(",")[0].strip()
        or flask_req.remote_addr
    )
    client = Client(
        ip=client_ip,
        user_agent=headers_lower.get("user-agent"),
    )
    auth_obj = Auth()
    if flask_req.authorization:
        auth_obj = Auth(
            type=flask_req.authorization.type,
            credentials={
                "username": getattr(flask_req.authorization, "username", None),
                "password": getattr(flask_req.authorization, "password", None),
                "token": getattr(flask_req.authorization, "token", None),
            },
        )
    meta = {
        "scheme": flask_req.scheme,
        "host": flask_req.host,
        "content_length": flask_req.content_length,
        "is_secure": flask_req.is_secure,
    }
    return Request(
        method=flask_req.method,
        url=flask_req.url,
        path=flask_req.path,
        headers=headers,
        query_params=query_params,
        path_params={},  # el router debería setear esto luego
        body=body,
        form=form,
        files=files,
        cookies=cookies,
        client=client,
        auth=auth_obj,
        meta=meta,
    )
def translate_django_request(django_req: Any) -> Request:
    headers: Dict[str, str] = dict(django_req.headers)
    query_params: Dict[str, List[str]] = {
        key: django_req.GET.getlist(key)
        for key in django_req.GET
    }
    form: Dict[str, List[str]] = {
        key: django_req.POST.getlist(key)
        for key in django_req.POST
    }
    body = django_req.body
    files = {}
    for key, uploaded in django_req.FILES.items():
        files[key] = {
            "filename": uploaded.name,
            "content_type": uploaded.content_type,
            "stream": to_binary_io(uploaded.file),
        }
    cookies = dict(django_req.COOKIES)
    headers_lower = {k.lower(): v for k, v in headers.items()}
    xff = headers_lower.get("x-forwarded-for", "")
    client_ip = xff.split(",")[0].strip() if xff else django_req.META.get("REMOTE_ADDR")
    client = Client(
        ip=client_ip,
        user_agent=headers_lower.get("user-agent"),
    )
    auth_obj = Auth()
    auth_header = headers_lower.get("authorization")
    if auth_header:
        if auth_header.startswith("Bearer "):
            auth_obj = Auth(
                type="bearer",
                credentials={"token": auth_header[7:]},
            )
        elif auth_header.startswith("Basic "):
            import base64
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = decoded.split(":", 1)
                auth_obj = Auth(
                    type="basic",
                    credentials={
                        "username": username,
                        "password": password,
                    },
                )
            except Exception:
                pass
    meta = {
        "scheme": django_req.scheme,
        "host": django_req.get_host(),
        "content_length": django_req.META.get("CONTENT_LENGTH"),
        "is_secure": django_req.is_secure(),
    }
    return Request(
        method=django_req.method,
        url=django_req.build_absolute_uri(),
        path=django_req.path,
        headers=headers,
        query_params=query_params,
        path_params={},  # lo debería setear igual solo
        body=body,
        form=form,
        files=files,
        cookies=cookies,
        client=client,
        auth=auth_obj,
        meta=meta,
    )
async def translate_fastapi_request(fastapi_req: Any) -> Request:
    headers: Dict[str, str] = dict(fastapi_req.headers)
    query_params: Dict[str, List[str]] = {
        key: fastapi_req.query_params.getlist(key)
        for key in fastapi_req.query_params.keys()
    }
    body = await fastapi_req.body()
    form_data = {}
    files = {}
    content_type = headers.get("content-type", "")
    if content_type.startswith("multipart/") or content_type.startswith(
        "application/x-www-form-urlencoded"
    ):
        form = await fastapi_req.form()
        for key, value in form.multi_items():
            if hasattr(value, "filename"):
                files[key] = {
                    "filename": value.filename,
                    "content_type": value.content_type,
                    "stream": to_binary_io(value.file),
                }
            else:
                form_data.setdefault(key, []).append(value)
    cookies = dict(fastapi_req.cookies)
    headers_lower = {k.lower(): v for k, v in headers.items()}
    xff = headers_lower.get("x-forwarded-for", "")
    client_ip = (
        xff.split(",")[0].strip()
        if xff
        else (fastapi_req.client.host if fastapi_req.client else None)
    )
    client = Client(
        ip=client_ip,
        user_agent=headers_lower.get("user-agent"),
    )
    auth_obj = Auth()
    auth_header = headers_lower.get("authorization")
    if auth_header:
        if auth_header.startswith("Bearer "):
            auth_obj = Auth(
                type="bearer",
                credentials={"token": auth_header[7:]},
            )
        elif auth_header.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = decoded.split(":", 1)
                auth_obj = Auth(
                    type="basic",
                    credentials={
                        "username": username,
                        "password": password,
                    },
                )
            except Exception:
                pass
    meta = {
        "scheme": fastapi_req.url.scheme,
        "host": fastapi_req.url.hostname,
        "content_length": headers_lower.get("content-length"),
        "is_secure": fastapi_req.url.scheme == "https",
    }
    return Request(
        method=fastapi_req.method,
        url=str(fastapi_req.url),
        path=fastapi_req.url.path,
        headers=headers,
        query_params=query_params,
        path_params=fastapi_req.path_params or {},
        body=body,
        form=form_data,
        files=files,
        cookies=cookies,
        client=client,
        auth=auth_obj,
        meta=meta,
    )

TranslatorEntry = Tuple[
    Callable[[Any], bool],# check
    Callable[[Any], Any],# traductor a usar
    bool # async sí o no
]
_TRANSLATORS: List[TranslatorEntry] = []
def register_translator(
    check_fn: Callable[[Any], bool],
    handler_fn: Callable[[Any], Any],
    *,
    is_async: bool = False,
) -> None:
    _TRANSLATORS.append((check_fn, handler_fn, is_async))

#función usable
async def translate(request_obj: Any):
    for check_fn, handler_fn, is_async in _TRANSLATORS:
        if check_fn(request_obj):
            if is_async:
                return await handler_fn(request_obj)
            return handler_fn(request_obj)
    raise TypeError(f"Unsupported request type: {type(request_obj)}")

# Este xframework por el momento soporta 3 tecnologías. Se inyectan al momento de importar este archivo a su proyecto.

def _inject():
    # Flask
    register_translator(
        lambda obj: _check(obj, "flask", "Request"),
        translate_flask_request,
        is_async=False,
    )
    # Django
    register_translator(
        lambda obj: _check(obj, "django.http", "HttpRequest"),
        translate_django_request,
        is_async=False,
    )
    # FastAPI / Starlette
    register_translator(
        lambda obj: _check(obj, "starlette.requests", "Request"),
        translate_fastapi_request,
        is_async=True,
    )
_inject()