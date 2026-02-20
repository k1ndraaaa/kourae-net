#PRE-REVISADO

from adapters.PostgreSQL.MainClass import PostgresClient
from adapters.PostgreSQL.Errors import *
import bcrypt #type:ignore
from dataclasses import dataclass, fields

@dataclass(frozen=True)
class NewUser:
    username: str
    password_hash: str
    registered_ip: str

@dataclass(frozen=True)
class UserPreview:
    id: int
    username: str


class PGErrorBaseError(Exception):pass
class PGActivityError(PGErrorBaseError): pass

DUMMY_HASH = b"$2b$12$C6UzMDM.H6dfI/f/IKcEeO9p9jv6vFVLtZL1NVr7DiIP9N6byN1Ga"

class PGActivity:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
    ):
        self.PostgresClient = PostgresClient(
            host=host,
            port=port,
            user=user,
            password=password,
        )
    def user_exists(self, username: str) -> bool:
        try:
            result = self.PostgresClient.query(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM users
                    WHERE username = %s
                )
                """,
                (username,),
                fetch=True
            )
            return result[0][0]
        except Exception as e:
            raise PGActivityError(e)
    def is_ip_totally_used(
        self,
        ip: str,
        max_users: int = 3
    ) -> bool:
        try:
            result = self.PostgresClient.query(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM users
                    WHERE registered_ip = %s
                    OFFSET %s
                    LIMIT 1
                )
                """,
                (ip, max_users - 1),
                fetch=True,
            )
            return result[0][0]
        except Exception as e:
            raise PGActivityError(e)
    def is_password_correct(
        self,
        username: str,
        password: str
    ) -> bool:
        try:
            result = self.PostgresClient.query(
                "SELECT password_hash FROM users WHERE username = %s LIMIT 1",
                (username,),
                fetch=True
            )
            if result:
                hashed = result[0][0].encode("utf-8")
            else:
                hashed = DUMMY_HASH  # evita enumeración
            return bcrypt.checkpw(password.encode("utf-8"), hashed)
        except Exception as e:
            raise PGActivityError(f"Error verificando password: {e}")
    def is_username_banned(self, username: str) -> bool:
        try:
            result = self.PostgresClient.query(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM banned_usernames
                    WHERE username = %s
                )
                """,
                (username,),
                fetch=True,
            )
            return result[0][0]
        except Exception as e:
            raise PGActivityError(e)
    def new_user(self, user: NewUser) -> None:
        try:
            cols = [f.name for f in fields(user)]
            placeholders = ["%s"] * len(cols)
            values = [getattr(user, c) for c in cols]
            query = f"""
                INSERT INTO users ({', '.join(cols)})
                VALUES ({', '.join(placeholders)})
            """
            self.PostgresClient.query(query, tuple(values))
        except Exception as e:
            raise PGActivityError(
                f"Error registrando usuario en db: {e}"
            )
    def delete_user(self, user_id: int) -> bool:
        try:
            result = self.PostgresClient.query(
                """
                DELETE FROM users
                WHERE id = %s
                RETURNING 1
                """,
                (user_id,),
                fetch=True,
            )
            return bool(result)
        except Exception as e:
            raise PGActivityError(e)
    def get_user_id(self, username: str) -> int | None:
        try:
            row = self.PostgresClient.query(
                "SELECT id FROM users WHERE username = %s",
                (username,),
                fetch=True
            )
            return row[0][0] if row else None
        except Exception as e:
            raise PGActivityError(e)
    def search(
        self,
        search: str,
        offset: int,
        limit: int,
    ) -> list[UserPreview]:
        try:
            rows = self.PostgresClient.query(
                """
                SELECT id, username
                FROM users
                WHERE username ILIKE '%' || %s || '%'
                ORDER BY id
                OFFSET %s
                LIMIT %s
                """,
                (search, offset, limit),
                fetch=True,
            )
            return [UserPreview(id=r[0], username=r[1]) for r in rows]
        except Exception as e:
            raise PGActivityError(e)