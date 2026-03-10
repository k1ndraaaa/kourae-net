from native.EnvManager.MainClass import *

#Componentes a usar
from native.JwtManager.Errors import *
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import jwt


class JwtManager:
    ISSUER = "kourae-api"
    def __init__(self):
        self.description = ""
        self.my_relative_path = Path(__file__).resolve().parent.relative_to(root_path)
        self.my_full_path = Path(root_str_path / self.my_relative_path)
        self.env = EnvManager().load_vars_from_env(
            Path(self.my_full_path / ".env")
        )
        self.jwtsecret = self.env.get("jwt_secret_key")
        self.jwtalgorithm = self.env.get("jwt_algorithm")
        self.access_token_minutes = int(self.env.get("access_token_minutes"))
        self.refresh_token_days = int(self.env.get("refresh_token_days"))
        self.utczone = ZoneInfo("UTC")

    def encode(self, payload: dict, expires_delta: timedelta) -> str:
        now = datetime.now(tz=self.utczone)
        data = payload.copy()
        data.update({
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
            "iss": self.ISSUER,
        })
        token = jwt.encode(
            data,
            self.jwtsecret,
            algorithm=self.jwtalgorithm
        )
        return token.decode("utf-8") if isinstance(token, bytes) else token

    def decode(self, token: str, verify_exp: bool = True) -> dict:
        try:
            return jwt.decode(
                token,
                self.jwtsecret,
                algorithms=[self.jwtalgorithm],
                options={"verify_exp": verify_exp},
                leeway=5,
                issuer=self.ISSUER,
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpired("Token expirado")
        except jwt.InvalidTokenError as e:
            raise TokenInvalid(str(e))

    def create_access_token(self, username: str) -> str:
        payload = {
            "sub": str(username),
            "type": "access",
        }
        return self.encode(
            payload,
            timedelta(minutes=self.access_token_minutes)
        )

    def create_refresh_token(self, username: str, jti: str) -> str:
        payload = {
            "sub": str(username),
            "type": "refresh",
            "jti": jti,
        }
        return self.encode(
            payload,
            timedelta(days=self.refresh_token_days)
        )

    def create_token_pair(self, username: str, jti: str) -> dict:
        return {
            "sessionID": self.create_access_token(username),
            "refresh_sessionID": self.create_refresh_token(username, jti),
        }

    def validate_token(self, token: str, expected_type: str) -> dict:
        payload = self.decode(token)
        token_type = payload.get("type")
        if token_type != expected_type:
            raise TokenTypeMismatch(
                f"Se esperaba token '{expected_type}', llegó '{token_type}'"
            )
        sub = payload.get("sub")
        if not sub:
            raise TokenInvalid("Token sin subject")
        return payload

    def is_token_expired(self, token: str) -> bool:
        try:
            self.decode(token, verify_exp=True)
            return False
        except TokenExpired:
            return True

    def whois(self, token: str) -> str:
        payload = self.validate_token(token, expected_type="access")
        return payload["sub"]

    def extract_refresh_payload(self, refresh_token: str) -> dict:
        return self.validate_token(refresh_token, expected_type="refresh")