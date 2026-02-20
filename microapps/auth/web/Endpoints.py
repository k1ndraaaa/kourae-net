#PRE-REVISADO

#Componentes a usar
from flask import * #type:ignore 
from microapps.mutual.webclient import WebClient
#Referencias  
from microapps.auth.MainClass import AuthManager
from native.LogManager.MainClass import LogManager
from native.WebResponse.MainClass import WebResponse
from microapps.mnt.MainClass import Mnt


this = "auth"
blueprint = Blueprint(this, __name__) #type:ignore

#incrusted_apps
mnt = None

#incrusted_workers
log_manager = None
auth_manager = None

web_client = None

def register(
    app, 
    logmanager: LogManager,
    authmanager: AuthManager,
    mntmicroapp: Mnt
):
    global log_manager, auth_manager, mnt, web_client
    log_manager = logmanager
    auth_manager = authmanager
    mnt = mntmicroapp
    app.register_blueprint(
        blueprint,
        url_prefix=f"/{this}"
    )
    web_client = WebClient(
        auth_manager=auth_manager,
        log_manager=log_manager
    )


@blueprint.route('/a', methods=["POST"])
def auth():
    ip = "unknown"
    try:
        resp = WebResponse()
        ok, _ = web_client.request_has_valid_auth_cookie(request)  # type: ignore
        if ok:
            return log_manager.http_response(
                resp.fail(
                    message="Ya hay una sesión existente",
                    status=403,
                    code="SESSION_EXISTS"
                )
            )
        ok, error = web_client.request_has_valid_content_type(
            request=request, #type:ignore
            expected_mimetype="application/json"
        )  # type: ignore

        if not ok:
            return log_manager.http_response(
                resp.fail(
                    message=error or "Content-Type inválido",
                    status=415,
                    code="UNSUPPORTED_MEDIA_TYPE"
                )
            )
        ok, missing = web_client.request_has_requested_headers(
            request=request, #type:ignore
            ignore=["cf-connecting-ip"]
        )  # type: ignore

        if not ok:
            return log_manager.http_response(
                resp.fail(
                    message=missing or "Solicitud mal formulada",
                    status=400,
                    code="MISSING_HEADERS"
                )
            )
        ip = request.headers.get( #type:ignore
            "CF-Connecting-IP",
            request.remote_addr #type:ignore
        ).split(',')[0].strip()  # type: ignore
        expected_data = {
            "username": {
                "min-length": int(auth_manager.env.get("min_user_length")),
                "max-length": int(auth_manager.env.get("max_user_length")),
                "scanner": "username"
            },
            "password": {
                "min-length": int(auth_manager.env.get("min_password_length")),
                "max-length": int(auth_manager.env.get("max_password_length")),
                "scanner": "password"
            }
        }
        ok, code, msg, data = web_client.request_has_jsoncontent(
            request=request, #type:ignore
            expected_data=expected_data
        )
        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=400, code=code)
            )
        json_data = data["json"]
        ok, code, msg, jdata = web_client.json_request_safe(
            json_data=json_data,
            expected_data=expected_data
        )
        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=400, code=code)
            )
        json_data = jdata["json"]
        username = json_data["username"]
        password = json_data["password"]
        if auth_manager.db.user_exists(username=username):
            return auth_manager.login(
                username=username,
                password=password,
                log_manager=log_manager,
                resp=resp
            )
        else:
            return auth_manager.register(
                username=username,
                password=password,
                ip=ip,
                log_manager=log_manager,
                resp=resp
            )
    except Exception as e:
        return web_client.failed_request(
            e=e,
            ip=ip
        )

@blueprint.route('/d', methods=["POST"])
def delete():
    ip = "unknown"
    try:
        resp = WebResponse()
        ok, error = web_client.request_has_valid_content_type(
            request=request, #type:ignore
            expected_mimetype="application/json"
        )
        if not ok:
            return log_manager.http_response(
                resp.fail(
                    message=error or "Content-Type inválido",
                    status=415,
                    code="UNSUPPORTED_MEDIA_TYPE"
                )
            )
        ok, missing = web_client.request_has_requested_headers(
            request=request, #type:ignore
            ignore=["cf-connecting-ip"]
        )
        if not ok:
            return log_manager.http_response(
                resp.fail(
                    message=missing or "Solicitud mal formulada",
                    status=400,
                    code="MISSING_HEADERS"
                )
            )
        ip = request.headers.get( #type:ignore
            "CF-Connecting-IP",
            request.remote_addr #type:ignore
        ).split(',')[0].strip()
        ok, reason = web_client.request_has_valid_auth_cookie(request) #type:ignore
        if not ok:
            return log_manager.http_response(
                resp.fail(reason, status=401, code="UNAUTHORIZED_RESOURCE")
            )
        token = request.cookies.get("sessionID") #type:ignore
        payload = auth_manager.jwt.validate_token(token, expected_type="access")
        if not payload:
            return log_manager.http_response(
                resp.fail("Token inválido", status=401, code="INVALID_TOKEN")
            )
        username = payload.get("sub")
        expected_data = {
            "password": {
                "min-length": int(auth_manager.env.get("min_password_length")),
                "max-length": int(auth_manager.env.get("max_password_length")),
                "scanner": "password"
            }
        }
        ok, code, msg, data = web_client.request_has_jsoncontent(
            request=request, #type:ignore
            expected_data=expected_data
        )
        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=400, code=code)
            )
        json_data = data["json"]
        password = json_data["password"]
        if not auth_manager.db.is_password_correct(
            username=username,
            password=password
        ):
            return log_manager.http_response(
                resp.fail("La contraseña es incorrecta", status=401, code="INCORRECT_PASSWORD")
            )
        response = auth_manager.delete_user(
            mnt=mnt,
            log_manager=log_manager,
            username=username,
            resp=resp
        )
        return response
    except Exception as e:
        return web_client.failed_request(
            e=e,
            ip=ip,
        )

@blueprint.route('/logout', methods=["GET"])
def logout():
    response = make_response(redirect(url_for('index')))  #type:ignore
    response.set_cookie('sessionID', '', expires=0)
    response.set_cookie('refresh_sessionID', '', expires=0)
    return response