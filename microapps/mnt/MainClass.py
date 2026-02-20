#PRE-REVISADO

from native.EnvManager.MainClass import *

#Componentes a usar
from microapps.mnt.adapters.pg_activity import PGActivity, PostMeta, PostUpdate
from microapps.mnt.adapters.mo_activity import MOActivity, StorageObject, StoragePointer

from native.PayloadValidator.MainClass import PayloadValidator, SecurityLevel, ALLOWED_EXTENSIONS
from werkzeug.utils import secure_filename #type:ignore
from pathlib import Path


#Referencias
from native.LogManager.MainClass import LogManager
from native.WebResponse.MainClass import WebResponse
from native.EnvManager.Errors import BaseError

class MntBaseError(BaseError): pass
class MntError(MntBaseError): pass

class InvalidSearchQuery(MntError):pass


class Mnt:
    def __init__(self):
        self.my_relative_path = Path(__file__).resolve().parent.relative_to(root_path)
        self.my_full_path = root_str_path / self.my_relative_path
        self.bucket = "users"
        self.env = EnvManager().load_vars_from_env(self.my_full_path / ".env")
        self.minioClient = None
        self.db = None
        self.title_validator = None
        self.text_validator = None
        
    def init_adapters(self):
        self.minioClient = MOActivity(
            host=str(
                self.env.get("server_host")
            ),
            port=int(
                self.env.get("minio_port")
            ),
            user=str(
                self.env.get("minio_user")
            ),
            password=str(
                self.env.get("minio_password")
            )
        )
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
        self.title_validator = PayloadValidator(SecurityLevel.STRICT)
        self.text_validator = PayloadValidator(SecurityLevel.SAFE_TEXT)

    def metainf(self):
        meta = {}
        for k, v in self.__dict__.items():
            meta[k] = v
        return meta
    
    def _generate(self, response):
        try:
            while True:
                chunk = response.read(32 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            try:
                response.close()
            finally:
                if hasattr(response, "release_conn"):
                    response.release_conn()

    def delete_storage_from_user(self, user_id: int) -> None:
        try:
            self.minioClient.delete_all_from_user(user_id)
            self.db.delete_all_from_user(user_id)
        except Exception as e:
            raise MntError(f"Fallo en base de datos: {e}")

    def upload_post(self, post: PostMeta, file: StorageObject) -> None:
        try:
            self.minioClient.put_object(file)
            try:
                self.db.new_post(post)
            except Exception:
                self.minioClient.remove_object(
                    StoragePointer(file.bucket, file.object_key)
                )
                raise
        except Exception as e:
            raise MntError(e)
    
    def delete_post(
        self, 
        user_id: int, 
        post_title: str
    ) -> None:
        try:
            post = self.db.get_post(post_title, user_id)
            self.minioClient.remove_object(
                StoragePointer(post.bucket, post.object_key)
            )
            self.db.delete_post(post_title, user_id)
        except Exception as e:
            raise MntError(e)
        
    def update_post(
        self, 
        update: PostUpdate
    ) -> None:
        try:
            updated = self.db.update_post(update)
        except Exception as e:
            raise MntError(e)
            
    def open(self, user_id: int, post_title: str):
        post = self.db.get_post(post_title, user_id)
        stream = self.minioClient.get_object(
            StoragePointer(post.bucket, post.object_key)
        )
        return {
            "mime_type": post.mime_type,
            "size": post.size,
            "stream": self._generate(stream)
        }

    def search(
        self,
        search: str,
        offset: int,
        limit: int
    ):
        if not self.text_validator.validate_string(s=search).valido:
            raise InvalidSearchQuery("Búsqueda inválida")
        return self.db.search(
            search=search,
            offset=offset,
            limit=limit
        )
