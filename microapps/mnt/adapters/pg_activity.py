#PRE-REVISADO

from adapters.PostgreSQL.MainClass import *
from adapters.PostgreSQL.Errors import *
from dataclasses import dataclass, fields
from datetime import datetime

def human_readable_size(size_bytes: int):
    if size_bytes == 0:
        return "0B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(units)-1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f}{units[i]}"

@dataclass(frozen=True)
class PostMeta:
    user_id: int
    author: str
    privacy: str
    post_title: str
    post_description: str
    bucket: str
    object_key: str
    mime_type: str
    size: int

@dataclass(frozen=True)
class PublicPost:
    author: str
    privacy: str
    post_title: str
    post_description: str
    size: int
    created_at: datetime

@dataclass(frozen=True)
class PostUpdate:
    user_id: int
    old_title: str
    post_title: str
    privacy: str
    post_description: str

class PGErrorBaseError(Exception):pass
class PGActivityError(PGErrorBaseError): pass

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
    def post_exists(
        self,
        post_title: str,
        user_id: int
    ) -> bool:
        try:
            result = self.PostgresClient.query(
                """
                SELECT 1
                FROM posts
                WHERE post_title = %s
                  AND user_id = %s
                LIMIT 1
                """,
                (post_title, user_id),
                fetch=True,
            )
            return bool(result)
        except Exception as e:
            raise PGActivityError(e)
    def is_post_public(
        self,
        post_title: str,
        user_id: int,
    ) -> bool:
        try:
            result = self.PostgresClient.query(
                """
                SELECT privacy
                FROM posts
                WHERE post_title = %s
                  AND user_id = %s
                LIMIT 1
                """,
                (post_title, user_id),
                fetch=True,
            )
            return bool(result and result[0][0] == "public")
        except Exception as e:
            raise PGActivityError(e)
    def new_post(
        self, 
        meta: PostMeta
    ) -> None:
        try:
            cols = [f.name for f in fields(meta)]
            placeholders = ["%s"] * len(cols)
            values = [getattr(meta, c) for c in cols]
            query = f"""
                INSERT INTO posts ({', '.join(cols)})
                VALUES ({', '.join(placeholders)})
            """
            self.PostgresClient.query(query, tuple(values))
        except Exception as e:
            raise PGActivityError(e)
    def delete_post(
        self,
        post_title: str,
        user_id: int,
    ) -> bool:
        try:
            self.PostgresClient.query(
                """
                DELETE FROM posts
                WHERE post_title = %s
                  AND user_id = %s
                """,
                (post_title, user_id),
            )
            return True
        except Exception as e:
            raise PGActivityError(e)
    def update_post(
        self, 
        update: PostUpdate
    ) -> bool:
        try:
            updatable_fields = [
                f.name for f in fields(update)
                if f.name not in ("user_id", "old_title")
            ]
            set_clause = ", ".join(f"{f} = %s" for f in updatable_fields)
            values = [getattr(update, f) for f in updatable_fields]
            query = f"""
                UPDATE posts
                SET {set_clause}
                WHERE post_title = %s
                  AND user_id = %s
            """
            affected = self.PostgresClient.query(
                query,
                tuple(values + [update.old_title, update.user_id]),
                return_rowcount=True
            )
            return affected > 0
        except Exception as e:
            raise PGActivityError(e)
    def delete_all_from_user(
        self, 
        user_id: int
    ) -> int:
        try:
            affected = self.PostgresClient.query(
                """
                DELETE FROM posts
                WHERE user_id = %s
                """,
                (user_id,),
                return_rowcount=True,
            )
            return affected
        except Exception as e:
            raise PGActivityError(e)
    def get_post(
        self,
        post_title: str,
        user_id: int,
    ) -> PostMeta | None:
        try:
            result = self.PostgresClient.query(
                """
                SELECT
                    user_id,
                    author,
                    privacy,
                    post_title,
                    post_description,
                    bucket,
                    object_key,
                    mime_type,
                    size
                FROM posts
                WHERE post_title = %s
                  AND user_id = %s
                LIMIT 1
                """,
                (post_title, user_id),
                fetch=True,
            )
            if not result:
                return None
            row = result[0]
            return PostMeta(
                user_id=row[0],
                author=row[1],
                privacy=row[2],
                post_title=row[3],
                post_description=row[4],
                bucket=row[5],
                object_key=row[6],
                mime_type=row[7],
                size=row[8],
            )
        except Exception as e:
            raise PGActivityError(e)
    def search(
        self,
        search: str,
        offset: int,
        limit: int,
    ) -> list[PublicPost]:
        try:
            rows = self.PostgresClient.query(
                """
                SELECT
                    author,
                    privacy,
                    post_title,
                    post_description,
                    size,
                    created_at
                FROM posts
                WHERE
                    privacy = 'public'
                    AND (
                        post_title ILIKE '%' || %s || '%'
                        OR post_description ILIKE '%' || %s || '%'
                        OR author ILIKE '%' || %s || '%'
                    )
                ORDER BY created_at DESC
                OFFSET %s
                LIMIT %s
                """,
                (search, search, search, offset, limit),
                fetch=True,
            )
            return [
                PublicPost(
                    author=r[0],
                    privacy=r[1],
                    post_title=r[2],
                    post_description=r[3],
                    size=r[4],
                    created_at=r[5],
                )
                for r in rows
            ]
        except Exception as e:
            raise PGActivityError(e)