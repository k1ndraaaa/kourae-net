from typing import BinaryIO, Protocol, Any, Optional, Mapping
from dataclasses import dataclass

class UserForm(Protocol):
    #id lo produce db, así que ni lo pongo
    username: str
    password: str | bytes

class UserUpdateForm(Protocol):
    user_id: int
    username: str | None
    password: str | bytes | None

class FileForm(Protocol):
    user_id: int #inmutable

    filename: str 
    ext: str #inmutable
    
    mime_type: str #inmutable
    size: int #inmutable
    
    bucket: str #inmutable
    object_key: str #inmutable

class FileUpdateForm(Protocol):
    user_id: int #Sólo se pasa como referencia al archivo guardado
    filename: str

@dataclass(frozen=True)
class StorageObject:
    bucket: str
    object_key: str
    data: BinaryIO
    length: int
    mime_type: str

@dataclass(frozen=True)
class StoragePointer:
    bucket: str
    object_key: str
