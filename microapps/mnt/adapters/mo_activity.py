#PRE-REVISADO

from adapters.Minio.MainClass import *
from adapters.Minio.Errors import *
from typing import BinaryIO
from dataclasses import dataclass

@dataclass(frozen=True)
class StorageObject:
    bucket: str
    object_key: str
    data: BinaryIO
    length: int
    mime_type: str | None = None

@dataclass(frozen=True)
class StoragePointer:
    bucket: str
    object_key: str

class MOActivity:
    def __init__(
        self,
        host:str,
        port:int,
        user:str,
        password:str    
    ):
        self.MinioClient = MinioClient(
            host=host,
            port=port,
            user=user,
            password=password
        )
    def put_object(self, obj: StorageObject) -> None:
        try:
            self.MinioClient.ensure_bucket(obj.bucket)
            self.MinioClient.client.put_object(
                bucket_name=obj.bucket,
                object_name=obj.object_key,
                data=obj.data,
                length=obj.length,
                content_type=obj.mime_type,
            )
        except S3Error as e:
            raise MinioError(f"Error subiendo objeto: {e}")
    def remove_object(self, obj: StoragePointer) -> None:
        try:
            self.MinioClient.client.remove_object(
                bucket_name=obj.bucket,
                object_name=obj.object_key
            )
        except S3Error as e:
            raise MinioError(f"Error eliminando objeto: {e}")
    def get_object(self, pointer: StoragePointer):
        try:
            return self.MinioClient.client.get_object(
                bucket_name=pointer.bucket,
                object_name=pointer.object_key
            )
        except S3Error as e:
            raise MinioError(f"Error obteniendo objeto: {e}")
    def delete_all_from_user(self, user_id: int) -> int:
        try:
            objects = self.MinioClient.client.list_objects(
                bucket_name="users",
                prefix=f"{user_id}/",
                recursive=True
            )
            to_delete = [
                obj.object_name
                for obj in objects
            ]
            if not to_delete:
                return 0
            errors = self.MinioClient.client.remove_objects(
                bucket_name="users",
                delete_object_list=to_delete
            )
            for err in errors:
                raise MinioError(f"Error eliminando objeto {err.object_name}: {err}")
            return len(to_delete)
        except S3Error as e:
            if e.code == "NoSuchBucket":
                return 0
            raise MinioError(e)