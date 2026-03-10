from typing import BinaryIO, Protocol
from dataclasses import dataclass
from native.PayloadValidator.MainClass import PayloadValidator 
from native.CrossFramework.translators import Request as StandarRequest

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

@dataclass
class Field:
    key: str
    min_length: int | None = None
    max_length: int | None = None
    datatype: type | tuple[type, ...] | None = None
    scanner: tuple | PayloadValidator | None = None

class ExpectedData:
    def __init__(self, request: StandarRequest):
        self.fields: dict[str, Field] = {}
        self.standar_request = request
        self._captured = {}
        self._errors = {}
    def __iter__(self):
        return iter(self.fields.values())
    def add(self, field: Field):
        if field.key in self.fields:
            raise ValueError(f"Field '{field.key}' duplicado")
        self.fields[field.key] = field
        return self
    def read(self):
        data = self.standar_request.get_data()
        if not isinstance(data, dict):
            self._errors["body"] = "INVALID_BODY"
            return {}
        captured = {}
        errors = {}
        for field in self:
            value = data.get(field.key)
            if value is None:
                errors[field.key] = "MISSING"
                continue
            if field.datatype and not isinstance(value, field.datatype):
                errors[field.key] = "INVALID_DATATYPE"
                continue
            if field.min_length and len(value) < field.min_length:
                errors[field.key] = "MIN_LENGTH"
                continue
            if field.max_length and len(value) > field.max_length:
                errors[field.key] = "MAX_LENGTH"
                continue
            if field.scanner:
                if isinstance(field.scanner, (list, tuple, set)):
                    if value not in field.scanner:
                        errors[field.key] = "INVALID_OPTION"
                        continue
                elif not field.scanner.validate_string(value).valido:
                    errors[field.key] = "INVALID_VALUE"
                    continue
            captured[field.key] = value
        self._captured = captured
        self._errors = errors
        return captured
    def missing_fields(self):
        return self._errors
    def is_body_full(self):
        return not bool(self._errors)
    def data(self):
        return self._captured
