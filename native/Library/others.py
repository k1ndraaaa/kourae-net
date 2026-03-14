from typing import BinaryIO, Protocol
from dataclasses import dataclass

def human_readable_size(size_bytes: int):
    if size_bytes == 0:
        return "0B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(units)-1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f}{units[i]}"

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
