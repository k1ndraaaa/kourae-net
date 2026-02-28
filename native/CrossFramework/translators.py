from standar import *
from typing import Any, Dict, List
import base64

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