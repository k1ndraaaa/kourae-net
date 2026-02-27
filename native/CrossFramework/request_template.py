from typing import Any, Optional, Mapping, BinaryIO, Union
from dataclasses import dataclass, field
from __future__ import annotations
import json
from io import BytesIO, IOBase, BufferedIOBase, RawIOBase
from types import MappingProxyType
from cgi import parse_header

def _freeze_mapping(data: Optional[Mapping]) -> Mapping:
    if not data:
        return MappingProxyType({})
    return MappingProxyType(dict(data))

def _normalize_headers(headers: Optional[Mapping[str, str]]) -> Mapping[str, str]:
    if not headers:
        return MappingProxyType({})
    return MappingProxyType({k.lower(): v for k, v in headers.items()})

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
    
#función cross-framework
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