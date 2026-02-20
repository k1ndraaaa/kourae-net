#PRE-REVISADO

from typing import Tuple, List
from enum import Enum
from native.LogManager.MainClass import LogManager, error
from native.WebResponse.MainClass import WebResponse
from native.PayloadValidator.MainClass import *
from microapps.auth.MainClass import AuthManager
from werkzeug.datastructures import Headers  # type: ignore
from werkzeug.http import parse_options_header  # type: ignore
from flask import Request  # type: ignore
from werkzeug.utils import secure_filename #type:ignore
from native.EnvManager.Errors import BaseError

class WebClientBaseError(BaseError): pass
class WebClientError(WebClientBaseError): pass

class AuthStatus(Enum):
    MISSING = "AUTH_COOKIE_MISSING"
    EXPIRED = "AUTH_COOKIE_EXPIRED"
    VALID = "AUTH_COOKIE_VALID"
    ERROR = "AUTH_CHECK_ERROR"


class WebClient:
    AUTH_COOKIE_NAME = "sessionID"

    def __init__(self, auth_manager: AuthManager, log_manager: LogManager):
        self.auth_manager = auth_manager
        self.log_manager = log_manager
        # Normalizamos los headers que vamos a pedir (en minúsculas para eficiencia)
        self.requested_headers_lower: List[str] = ["cf-connecting-ip"]
        self.title_validator = PayloadValidator(SecurityLevel.STRICT)
        self.text_validator = PayloadValidator(SecurityLevel.SAFE_TEXT)
        self.username_validator = PayloadValidator(SecurityLevel.USERNAME)

    #se queda
    def request_has_requested_headers(
        self, 
        request: Request, 
        ignore: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        ignore = [h.lower() for h in (ignore or [])]  # Normaliza a minúsculas
        headers_lower = [h.lower() for h in request.headers.keys()]
        missing = [
            h for h in self.requested_headers_lower
            if h not in headers_lower and h not in ignore
        ]
        return (not missing, missing)

    #se queda
    def request_has_valid_content_type(
        self, request: Request, expected_mimetype: str
    ) -> Tuple[bool, str | None]:
        if not request.mimetype:
            return False, "Content-Type requerido"
        mimetype, _ = parse_options_header(request.mimetype)
        if mimetype.lower() != expected_mimetype.lower():
            return False, f"Content-Type inválido ({request.mimetype})"
        return True, None

    #se queda
    def request_has_valid_auth_cookie(self, request: Request) -> Tuple[bool, AuthStatus]:
        session_id = request.cookies.get(self.AUTH_COOKIE_NAME)
        if not session_id:
            return False, AuthStatus.MISSING
        try:
            is_logged_in = self.auth_manager.is_user_logged(session_id)
            if not is_logged_in:
                return False, AuthStatus.EXPIRED
        except Exception as e:
            raise WebClientError(e)
        return True, AuthStatus.VALID

    #falta checar, pero seguro se queda
    def failed_request(
        self, 
        e: Exception, 
        ip: str
    ) -> WebResponse:
        self.log_manager.log(
            level=error,
            code="UNEXPECTED_ERROR",
            message=f"Ocurrió un error durante la solicitud: {str(e)}.",
            source=str(ip),
            printq=True,
        )
        resp = WebResponse()
        return self.log_manager.http_response(
            resp.fail(
                "Ocurrió un error durante la solicitud.",
                status=500,
                code="INTERNAL_SERVER_ERROR",
            )
        )
    
    #se queda
    def request_has_formdatacontent(
        self,
        request: Request,
        expected_data: dict | None = None,
        expected_files: dict | None = None
    ):
        try:
            form_data = {}
            files_data = {}
            if expected_data:
                form = request.form or {}
                missing_fields = []
                for field in expected_data:
                    value = form.get(field)
                    if value is None:
                        missing_fields.append(field)
                    else:
                        form_data[field] = value
                if missing_fields:
                    return (
                        False,
                        "MISSING_FORM_FIELDS",
                        f"Faltan campos requeridos: {', '.join(missing_fields)}",
                        None
                    )
            if expected_files:
                files = request.files or {}
                missing_files = []
                for field in expected_files:
                    file = files.get(field)
                    if file is None or not file.filename:
                        missing_files.append(field)
                    else:
                        files_data[field] = {
                            "file-object": file
                        }
                if missing_files:
                    return (
                        False,
                        "MISSING_FILES_FIELDS",
                        f"Faltan archivos requeridos: {', '.join(missing_files)}",
                        None
                    )
            return True, None, None, {
                "form": form_data,
                "files": files_data
            }
        except Exception as e:
            raise WebClientError(e)

    #se queda
    def formdata_request_safe(
        self,
        form_data: dict | None = None,
        files_data: dict | None = None,
        expected_data: dict | None = None,
        expected_files: dict | None = None
    ):
        form_data = form_data or {}
        files_data = files_data or {}
        try:
            if expected_data:
                for field, rules in expected_data.items():
                    value = form_data.get(field)
                    if value is None:
                        continue
                    scanner = rules.get("scanner")
                    if scanner:
                        if scanner == "title":
                            if not self.title_validator.validate_string(value).valido:
                                return False, f"INVALID_{field.upper()}", f"{field} inválido", None
                        elif scanner == "text":
                            if not self.text_validator.validate_string(value).valido:
                                return False, f"INVALID_{field.upper()}", f"{field} inválido", None
                        elif isinstance(scanner, (list, tuple, set)):
                            if value not in scanner:
                                return False, f"INVALID_{field.upper()}", f"{field} inválido", None
                        elif scanner == "username":
                            if not self.username_validator.validate_string(value).valido:
                                return False, f"INVALID_{field.upper()}", f"{field} inválido", None
                    max_len = rules.get("max-length")
                    min_len = rules.get("min-length")
                    if max_len:
                        if len(value) > max_len:
                            return False, f"{field.upper()}_TOO_LONG", f"{field} demasiado largo", None
                    if min_len:
                        if len(value) < min_len:
                            return False, f"{field.upper()}_TOO_SHORT", f"{field} demasiado corto", None
                    allowed = rules.get("allowed")
                    if allowed and value not in allowed:
                        return False, f"INVALID_{field.upper()}", f"{field} inválido", None
            if expected_files:
                for field, rules in expected_files.items():
                    meta = files_data.get(field)
                    if not meta:
                        continue 
                    file = meta["file-object"]
                    filename = secure_filename(file.filename)
                    if "." not in filename:
                        return False, "INVALID_FILENAME", "Nombre de archivo inválido", None
                    ext = filename.rsplit(".", 1)[1].lower()
                    ext_meta = ALLOWED_EXTENSIONS.get(ext)
                    if not ext_meta:
                        return False, "INVALID_EXTENSION", "Tipo de archivo no permitido", None
                    file.seek(0, 2)
                    size = file.tell()
                    file.seek(0)
                    max_size = rules.get("size")
                    if max_size and size > max_size:
                        return False, "CONTENT_TOO_LARGE", "Archivo demasiado grande", None
                    base_name = secure_filename(form_data.get("title", "file"))
                    meta.update({
                        "filename": f"{base_name}.{ext}",
                        "mime-type": ext_meta["mime"],
                        "size": size
                    })
            return True, None, None, {
                "form": form_data,
                "files": files_data
            }
        except Exception as e:
            raise WebClientError(e)
    
    #se queda
    def request_has_jsoncontent(
        self,
        request: Request,
        expected_data: dict | None = None
    ):
        try:
            json_data = {}
            try:
                data = request.get_json(force=True, silent=True) or {}
            except Exception as e:
                return False, "INVALID_JSON", f"Error al parsear JSON: {e}", None
            if expected_data:
                missing_fields = []
                for field in expected_data:
                    value = data.get(field)
                    if value is None:
                        missing_fields.append(field)
                    else:
                        json_data[field] = value
                if missing_fields:
                    return (
                        False,
                        "MISSING_JSON_FIELDS",
                        f"Faltan campos requeridos: {', '.join(missing_fields)}",
                        None
                    )
            return True, None, None, {"json": json_data}
        except Exception as e:
            raise WebClientError(e)
    
    #se queda
    def json_request_safe(
        self,
        json_data: dict | None = None,
        expected_data: dict | None = None
    ):
        json_data = json_data or {}
        try:
            if expected_data:
                for field, rules in expected_data.items():
                    value = json_data.get(field)
                    if value is None:
                        continue
                    scanner = rules.get("scanner")
                    if scanner:
                        if scanner == "title":
                            if not self.title_validator.validate_string(value).valido:
                                return False, f"INVALID_{field.upper()}", f"{field} inválido", None
                        elif scanner == "text":
                            if not self.text_validator.validate_string(value).valido:
                                return False, f"INVALID_{field.upper()}", f"{field} inválido", None
                        elif isinstance(scanner, (list, tuple, set)):
                            if value not in scanner:
                                return False, f"INVALID_{field.upper()}", f"{field} inválido", None
                        elif scanner == "username":
                            if not self.username_validator.validate_string(value).valido:
                                return False, f"INVALID_{field.upper()}", f"{field} inválido", None
                    max_len = rules.get("max-length")
                    if max_len and isinstance(value, (str, list, tuple)) and len(value) > max_len:
                        return False, f"{field.upper()}_TOO_LONG", f"{field} demasiado largo", None
                    min_len = rules.get("min-length")
                    if min_len and isinstance(value, (str, list, tuple)) and len(value) < min_len:
                        return False, f"{field.upper()}_TOO_SHORT", f"{field} demasiado corto", None
                    allowed = rules.get("allowed")
                    if allowed and value not in allowed:
                        return False, f"INVALID_{field.upper()}", f"{field} inválido", None
            return True, None, None, {
                "json": json_data
            }
        except Exception as e:
            raise WebClientError(e)