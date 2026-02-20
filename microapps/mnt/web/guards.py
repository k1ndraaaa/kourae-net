#PRE-REVISADO

from flask import Request #type:ignore
from native.WebResponse.MainClass import WebResponse
from native.LogManager.MainClass import LogManager
from microapps.mutual.webclient import WebClient
from functools import wraps

def endpoint_guard(
    *,
    request: Request,
    web_client: WebClient,
    log_manager: LogManager,
    expected_mimetype: str,
    require_auth: bool = True,
    
):
    resp = WebResponse()
    headers: dict[str, str | None] = {}

    ok, error = web_client.request_has_valid_content_type(
        request=request,  # type: ignore
        expected_mimetype=expected_mimetype
    )
    if not ok:
        return False, log_manager.http_response(
            resp.fail(
                message=error or "Content-Type inválido",
                status=415,
                code="UNSUPPORTED_MEDIA_TYPE"
            )
        )

    ok, missing = web_client.request_has_requested_headers(
        request=request  # type: ignore
    )
    if not ok:
        return False, log_manager.http_response(
            resp.fail(
                message=missing or "Solicitud mal formulada",
                status=400,
                code="MISSING_HEADERS"
            )
        )

    # 3. IP (contexto)
    ip = request.headers.get(
        "CF-Connecting-IP",
        request.remote_addr,
    )
    if ip:
        ip = ip.split(",")[0].strip()

    headers["ip"] = ip

    if require_auth:
        ok, reason = web_client.request_has_valid_auth_cookie(
            request=request  # type: ignore
        )
        if not ok:
            return False, log_manager.http_response(
                resp.fail(
                    message="No hay una sesión activa",
                    status=401,
                    code="UNAUTHORIZED_RESOURCE"
                )
            )

    return True, {
        "headers": headers,
        "response": resp,
    }

def guarded_endpoint(
    *, 
    expected_mimetype: str, 
    auth: bool = True
):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                request: Request = kwargs["request"]
                web_client: WebClient = kwargs["web_client"]
                log_manager: LogManager = kwargs["log_manager"]
            except KeyError as e:
                raise RuntimeError(
                    f"Falta dependencia requerida en endpoint: {e}"
                )

            ok, result = endpoint_guard(
                request=request,
                web_client=web_client,
                log_manager=log_manager,
                expected_mimetype=expected_mimetype,
                require_auth=auth,
            )
            if not ok:
                return result
            kwargs.update(result)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
