#PRE-REVISADO

#Componentes a usar
from flask import * #type:ignore
from microapps.mnt.web.guards import *
from microapps.mutual.webclient import WebClient

#Referencias
from native.LogManager.MainClass import LogManager
from microapps.auth.MainClass import AuthManager
from microapps.mnt.MainClass import Mnt, InvalidSearchQuery, PostMeta, StorageObject, PostUpdate

this = "mnt"
blueprint = Blueprint(this, __name__) #type:ignore

#incrusted_apps
auth_manager = None

#incrusted_workers
log_manager = None
mnt = None
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

@blueprint.route('/search', methods=["GET"])
def search():
    accept = request.headers.get("Accept", "")  # type: ignore
    wants_json = "application/json" in accept
    query = request.args.get("q", "").strip()  # type: ignore
    if not query:
        if wants_json:
            return jsonify({ #type:ignore
                "query": "",
                "start": 0,
                "page_size": 10,
                "total": 0,
                "results": []
            }), 200
        return redirect(url_for("index"))  # type: ignore
    try:
        start = int(request.args.get("start", 0))  # type: ignore
    except (TypeError, ValueError):
        start = 0
    PAGE_SIZE = 10
    MAX_RESULTS = 1000
    start = max(0, start)
    start = (start // PAGE_SIZE) * PAGE_SIZE
    start = min(start, MAX_RESULTS - PAGE_SIZE)
    try:
        results, total = mnt.search(
            search=query,
            offset=start,
            limit=PAGE_SIZE
        )
    except InvalidSearchQuery:
        if wants_json:
            return jsonify({ #type:ignore
                "error": "INVALID_ENTRY",
                "message": "Búsqueda inválida"
            }), 400
        return redirect(url_for("index"))  # type: ignore
    total = min(total, MAX_RESULTS)
    if wants_json:
        return jsonify({ #type:ignore
            "query": query,
            "start": start,
            "page_size": PAGE_SIZE,
            "total": total,
            "results": results
        }), 200
    return render_template( #type:ignore
        "search.html",
        query=query,
        start=start,
        page_size=PAGE_SIZE,
        total=total,
        results=results
    )

@blueprint.route('/upload', methods=["POST"])
@guarded_endpoint(
    expected_mimetype="multipart/form-data",
    auth=True
)
def upload_file(*args, **kwargs):
    ip = "unknown"

    try:
        headers = kwargs["headers"]
        resp = kwargs["response"]
        ip = headers.get("ip", "unknown")

        expected_data = {
            "title": {
                "min-length": int(mnt.env.get("min_post_title_length")),
                "max-length": int(mnt.env.get("max_post_title_length")),
                "scanner": "title"
            },
            "privacy": {
                "scanner": ("public", "private")
            },
            "description": {
                "min-length": 0,
                "max-length": int(mnt.env.get("max_post_description_length")),
                "scanner": "text"
            }
        }

        expected_files = {
            "file": {
                "size": 0
            }
        }

        ok, code, msg, data = web_client.request_has_formdatacontent(
            request=request,  # type: ignore
            expected_data=expected_data,
            expected_files=expected_files
        )

        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=401, code=code)
            )

        form_data = data["form"]
        files_data = data["files"]

        ok, code, msg, fdata = web_client.formdata_request_safe(
            form_data=form_data,
            files_data=files_data,
            expected_data=expected_data,
            expected_files=expected_files
        )

        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=400, code=code)
            )

        form_data = fdata["form"]
        files_data = fdata["files"]

        file_data = files_data["file"]

        username = auth_manager.jwt.whois(
            token=request.cookies.get("sessionID")  # type: ignore
        )

        if not username:
            return log_manager.http_response(
                resp.fail("Sesión inválida", status=401, code="INVALID_SESSION")
            )

        user_id = auth_manager.db.get_user_id(username=username)

        if user_id is None:
            return log_manager.http_response(
                resp.fail("Usuario no encontrado", status=404, code="USER_NOT_FOUND")
            )

        object_key = f"{username}/{file_data['filename']}"

        post = PostMeta(
            user_id=int(user_id),
            author=username,
            privacy=form_data["privacy"],
            post_title=form_data["title"],
            post_description=form_data.get("description", ""),
            bucket=mnt.bucket,
            object_key=object_key,
            mime_type=file_data["mime-type"],
            size=int(file_data["size"]),
        )

        storage = StorageObject(
            bucket=mnt.bucket,
            object_key=object_key,
            length=int(file_data["size"]),
            mime_type=file_data["mime-type"],
            data=file_data["file-object"].stream  # <- BinaryIO real
        )

        mnt.upload_post(post=post, file=storage)

        return log_manager.http_response(
            resp.success(data={"message": "Post subido correctamente."})
        )

    except Exception as e:
        return web_client.failed_request(
            log_manager=log_manager,
            e=e,
            ip=ip,
            resp=resp
        )

@blueprint.route('/delete', methods=["POST"])
@guarded_endpoint(
    expected_mimetype="application/json",
    auth=True
)
def delete_file(*args, **kwargs):
    ip = "unknown"

    try:
        headers = kwargs["headers"]
        resp = kwargs["response"]
        ip = headers.get("ip", "unknown")

        expected_data = {
            "title": {
                "min-length": int(mnt.env.get("min_post_title_length")),
                "max-length": int(mnt.env.get("max_post_title_length")),
                "scanner": "title"
            }
        }

        ok, code, msg, data = web_client.request_has_jsoncontent(
            request=request,  # type: ignore
            expected_data=expected_data
        )

        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=401, code=code)
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

        title = json_data["title"]

        username = auth_manager.jwt.whois(
            token=request.cookies.get("sessionID")  # type: ignore
        )

        if not username:
            return log_manager.http_response(
                resp.fail("Sesión inválida", status=401, code="INVALID_SESSION")
            )

        deleted = mnt.delete_post(
            user=username,
            post_title=title
        )

        if not deleted:
            return log_manager.http_response(
                resp.fail("Post no encontrado", status=404, code="NOT_FOUND")
            )

        return log_manager.http_response(
            resp.success(data={"message": "Post eliminado correctamente."})
        )

    except Exception as e:
        return web_client.failed_request(
            log_manager=log_manager,
            e=e,
            ip=ip,
            resp=resp
        )

@blueprint.route('/update', methods=["POST"])
@guarded_endpoint(
    expected_mimetype="application/json",
    auth=True
)
def update_file(*args, **kwargs):
    ip = "unknown"

    try:
        headers = kwargs["headers"]
        resp = kwargs["response"]
        ip = headers.get("ip", "unknown")

        expected_data = {
            "old_title": {
                "min-length": int(mnt.env.get("min_post_title_length")),
                "max-length": int(mnt.env.get("max_post_title_length")),
                "scanner": "title"
            },
            "title": {
                "min-length": int(mnt.env.get("min_post_title_length")),
                "max-length": int(mnt.env.get("max_post_title_length")),
                "scanner": "title"
            },
            "privacy": {
                "scanner": ("public", "private")
            },
            "description": {
                "min-length": 0,
                "max-length": int(mnt.env.get("max_post_description_length")),
                "scanner": "text"
            }
        }

        ok, code, msg, data = web_client.request_has_jsoncontent(
            request=request,  # type: ignore
            expected_data=expected_data
        )

        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=401, code=code)
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

        username = auth_manager.jwt.whois(
            token=request.cookies.get("sessionID")  # type: ignore
        )

        if not username:
            return log_manager.http_response(
                resp.fail("Sesión inválida", status=401, code="INVALID_SESSION")
            )

        user_id = auth_manager.db.get_user_id(username=username)

        if user_id is None:
            return log_manager.http_response(
                resp.fail("Usuario no encontrado", status=404, code="USER_NOT_FOUND")
            )

        mnt.update_post(
            update=PostUpdate(
                user_id=int(user_id),
                old_title=json_data["old_title"],
                post_title=json_data["title"],
                privacy=json_data["privacy"],
                post_description=json_data["description"],
            )
        )

        return log_manager.http_response(
            resp.success(data={"message": "Post actualizado correctamente."})
        )

    except Exception as e:
        return web_client.failed_request(
            log_manager=log_manager,
            e=e,
            ip=ip,
            resp=resp
        )