#PRE-REVISADO

from native.EnvManager.MainClass import *

#Componentes a usar
from microapps.auth.adapters.pg_activity import PGActivity
from native.PayloadValidator.MainClass import PayloadValidator, SecurityLevel
import bcrypt, uuid #type:ignore
from native.JwtManager.MainClass import JwtManager
from pathlib import Path
from flask import jsonify #type:ignore

#Referencias
from native.WebResponse.MainClass import  WebResponse
from native.LogManager.MainClass import LogManager
from microapps.mnt.MainClass import Mnt
from native.EnvManager.Errors import BaseError

class AuthManagerBaseError(BaseError): pass
class AuthManagerError(AuthManagerBaseError): pass


class AuthManager:
    def __init__(self):
        self.my_relative_path = Path(__file__).resolve().parent.relative_to(root_path)
        self.my_full_path = root_str_path / self.my_relative_path
        self.bucket = "users"
        self.env = EnvManager().load_vars_from_env(self.my_full_path / ".env")
        self.db = None
        self.jwt = None
        self.validator = None
        
    def init_adapters(self):
        self.db = PGActivity(
            host=str(
                self.env.get("server_host")
            ),
            port=int(
                self.env.get("postgres_port")
            ),
            user=str(
                self.env.get("postgres_user")
            ),
            password=str(
                self.env.get("postgres_password")
            )
        )
        self.jwt = JwtManager()
        self.validator = PayloadValidator(SecurityLevel.USERNAME)
    
    def metainf(self):
        meta = {}
        for k, v in self.__dict__.items():
            meta[k] = v
        return meta
    
    def hash_password(self, password: str) -> str:
        if not isinstance(password, str):
            raise AuthManagerError("Password debe ser str")
        try:
            hashed = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt(rounds=12)
            )
            return hashed.decode("utf-8")
        except Exception as e:
            raise AuthManagerError("Error al hashear password") from e

    def is_user_logged(self, sessionID: str) -> bool:
        if not sessionID:
            return False
        payload = self.jwt.validate_token(
            token=sessionID,
            expected_type="access"
        )
        if not payload:
            return False
        username = payload.get("sub")
        if not username:
            return False
        return self.db.user_exists(username=username)
        
    def set_cookies(self, response, tokens: dict):
        if "sessionID" not in tokens or "refresh_sessionID" not in tokens:
            raise ValueError("Tokens incompletos para set_cookies")
        secure_preference = True
        samesite_preference = "Strict"
        response.set_cookie(
            key="sessionID",
            value=tokens["sessionID"],
            httponly=True,
            secure=secure_preference,
            samesite=samesite_preference,
            max_age=int(self.jwt.env.get("access_token_minutes")) * 60, #configuración de ejemplo para el repositorio
            path="/"
        )
        response.set_cookie(
            key="refresh_sessionID",
            value=tokens["refresh_sessionID"],
            httponly=True,
            secure=secure_preference,
            samesite=samesite_preference,
            max_age=int(self.jwt.env.get("refresh_token_days")) * 24 * 60 * 60, #configuración de ejemplo para el repositorio
            path="/auth"
        )
    
    def login(
        self,
        username: str,
        password: str,
        log_manager: LogManager,
        resp: WebResponse
    ):
        if not isinstance(username, str) or not username.strip():
            return log_manager.http_response(
                resp.fail("Usuario inválido", status=400, code="INVALID_USERNAME")
            )
        if not self.db.is_password_correct(username=username, password=password):
            return log_manager.http_response(
                resp.fail("La contraseña es incorrecta", status=401, code="INCORRECT_PASSWORD")
            )
        return self.make_session(username=username, resp=resp)
    
    def register(
        self,
        username: str,
        password: str,
        ip: str,
        log_manager: LogManager,
        resp: WebResponse
    ):
        if not isinstance(username, str) or not username.strip():
            return log_manager.http_response(
                resp.fail("Usuario inválido", status=400, code="INVALID_USERNAME")
            )
        if not isinstance(password, str) or not password.strip():
            return log_manager.http_response(
                resp.fail("Contraseña inválida", status=400, code="INVALID_PASSWORD")
            )
        if self.db.is_ip_totally_used(ip):
            return log_manager.http_response(
                resp.fail(
                    "No puedes registrar una nueva cuenta bajo en esta red. Por favor, cambia de red para continuar.",
                    status=403,
                    code="IP_TOTALLY_USED"
                )
            )
        if self.db.is_username_banned(username=username):
            return log_manager.http_response(
                resp.fail(
                    "El nombre de usuario ingresado no está disponible",
                    status=409,
                    code="USERNAME_BANNED"
                )
            )
        password_hash = self.hash_password(password)
        self.db.new_user(
            meta={
                "username": username,
                "password_hash": password_hash,
                "registered_ip": ip
            }
        )
        log_manager.notify_new_user(username)
        return self.make_session(username=username, resp=resp)

    def delete_user(
        self,
        mnt: Mnt,
        log_manager: LogManager,
        username: str,
        resp: WebResponse
    ):
        if not isinstance(username, str) or not username.strip():
            return log_manager.http_response(
                resp.fail("Usuario inválido", status=400, code="INVALID_USERNAME")
            )
        try:
            user_id = self.db.get_user_id(username=username)
            mnt.delete_storage_from_user(user_id=user_id)
            deleted = self.db.delete_user(user_id=user_id)
            if not deleted:
                return log_manager.http_response(
                    resp.fail("Usuario no encontrado", status=404, code="USER_NOT_FOUND")
                )
            return log_manager.http_response(
                resp.success(data={"message": "Cuenta eliminada correctamente"})
            )
        except Exception as e:
            return log_manager.http_response(
                resp.fail(
                    "Error eliminando usuario",
                    status=500,
                    code="INTERNAL_ERROR",
                    data=str(e)
                )
            )

    def make_session(
        self,
        username: str,
        resp: WebResponse
    ):
        if not isinstance(username, str) or not username.strip():
            raise AuthManagerError("Username inválido para crear sesión")
        jti = str(uuid.uuid4())
        tokens = self.jwt.create_token_pair(username=username, jti=jti)
        resp.success(data={"username": username, "sessionID": tokens["sessionID"]})
        response = jsonify(resp.to_dict())  # type: ignore
        response.status_code = resp.status
        self.set_cookies(response, tokens)
        return response
        