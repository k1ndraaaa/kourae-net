from __future__ import annotations
from collections import Counter, defaultdict
from typing import Any, List
import re, unicodedata
from native.PayloadValidator.Errors import *
from native.Library.commons import SecurityLevel, Issue, ValidationResult, is_forbidden_category, has_combining_marks, has_mixed_scripts, normalize_and_clean, detect_sql_payload, detect_xss_payload, safe_str

ALLOWED_EXTENSIONS = {
    "pdf":  {"mime": "application/pdf", "category": "document"},
    "txt":  {"mime": "text/plain", "category": "document"},
    "md":   {"mime": "text/markdown", "category": "document"},
    "doc":  {"mime": "application/msword", "category": "document"},
    "docx": {"mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "category": "document"},
    "xls":  {"mime": "application/vnd.ms-excel", "category": "document"},
    "xlsx": {"mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "category": "document"},
    "ppt":  {"mime": "application/vnd.ms-powerpoint", "category": "document"},
    "pptx": {"mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation", "category": "document"},
    "odt":  {"mime": "application/vnd.oasis.opendocument.text", "category": "document"},
    "ods":  {"mime": "application/vnd.oasis.opendocument.spreadsheet", "category": "document"},
    "epub": {"mime": "application/epub+zip", "category": "document"},
    "rtf":  {"mime": "application/rtf", "category": "document"},
    "png":  {"mime": "image/png", "category": "image"},
    "jpg":  {"mime": "image/jpeg", "category": "image"},
    "jpeg": {"mime": "image/jpeg", "category": "image"},
    "webp": {"mime": "image/webp", "category": "image"},
    "gif":  {"mime": "image/gif", "category": "image"},
    "bmp":  {"mime": "image/bmp", "category": "image"},
    "tiff": {"mime": "image/tiff", "category": "image"},
    "svg":  {"mime": "image/svg+xml", "category": "image"},
    "ico":  {"mime": "image/x-icon", "category": "image"},
    "mp3":  {"mime": "audio/mpeg", "category": "audio"},
    "wav":  {"mime": "audio/wav", "category": "audio"},
    "ogg":  {"mime": "audio/ogg", "category": "audio"},
    "flac": {"mime": "audio/flac", "category": "audio"},
    "m4a":  {"mime": "audio/mp4", "category": "audio"},
    "aac":  {"mime": "audio/aac", "category": "audio"},
    "mp4":  {"mime": "video/mp4", "category": "video"},
    "webm": {"mime": "video/webm", "category": "video"},
    "mov":  {"mime": "video/quicktime", "category": "video"},
    "avi":  {"mime": "video/x-msvideo", "category": "video"},
    "mkv":  {"mime": "video/x-matroska", "category": "video"},
    "flv":  {"mime": "video/x-flv", "category": "video"},
    "wmv":  {"mime": "video/x-ms-wmv", "category": "video"},
    "html": {"mime": "text/html", "category": "web"},
    "css":  {"mime": "text/css", "category": "web"},
    "js":   {"mime": "application/javascript", "category": "web"},
    "php":  {"mime": "application/x-httpd-php", "category": "web"},
    "xml":  {"mime": "application/xml", "category": "web"},
    "json": {"mime": "application/json", "category": "web"},
    "py":   {"mime": "text/x-python", "category": "code"},
    "java": {"mime": "text/x-java-source", "category": "code"},
    "c":    {"mime": "text/x-csrc", "category": "code"},
    "cpp":  {"mime": "text/x-c++src", "category": "code"},
    "rb":   {"mime": "text/x-ruby", "category": "code"},
    "go":   {"mime": "text/x-go", "category": "code"},
    "sh":   {"mime": "application/x-sh", "category": "code"},
    "ts":   {"mime": "application/typescript", "category": "code"},
    "swift":{"mime": "text/x-swift", "category": "code"},
    "php":  {"mime": "application/x-httpd-php", "category": "code"},
    "rs":   {"mime": "text/rust", "category": "code"},
    "kt":   {"mime": "text/x-kotlin", "category": "code"},
    "zip":  {"mime": "application/zip", "category": "archive"},
    "rar":  {"mime": "application/vnd.rar", "category": "archive"},
    "7z":   {"mime": "application/x-7z-compressed", "category": "archive"},
    "tar":  {"mime": "application/x-tar", "category": "archive"},
    "gz":   {"mime": "application/gzip", "category": "archive"},
    "bz2":  {"mime": "application/x-bzip2", "category": "archive"},
    "xz":   {"mime": "application/x-xz", "category": "archive"},
    "ttf":  {"mime": "font/ttf", "category": "font"},
    "otf":  {"mime": "font/otf", "category": "font"},
    "woff": {"mime": "font/woff", "category": "font"},
    "woff2":{"mime": "font/woff2", "category": "font"},
    "csv":  {"mime": "text/csv", "category": "data"},
    "tsv":  {"mime": "text/tab-separated-values", "category": "data"},
    "ics":  {"mime": "text/calendar", "category": "data"},
    "epub": {"mime": "application/epub+zip", "category": "document"},
    "iso": {"mime": "application/x-iso9660-image", "category": "game"},
    "bin": {"mime": "application/octet-stream", "category": "game"},
    "cue": {"mime": "application/octet-stream", "category": "game"},
    "img": {"mime": "application/octet-stream", "category": "game"},
    "mdf": {"mime": "application/octet-stream", "category": "game"},
    "mds": {"mime": "application/octet-stream", "category": "game"},
    "dll": {"mime": "application/octet-stream", "category": "binary"},
    "asi": {"mime": "application/octet-stream", "category": "binary"},
    "ini": {"mime": "text/plain", "category": "config"},
    "cfg": {"mime": "text/plain", "category": "config"},
    "pak": {"mime": "application/octet-stream", "category": "mod"},
    "vpk": {"mime": "application/octet-stream", "category": "mod"},
    "apk": {"mime": "application/octet-stream", "category": "mod"},
    "wad": {"mime": "application/octet-stream", "category": "mod"},
    "uasset": {"mime": "application/octet-stream", "category": "mod"},
    "unity3d": {"mime": "application/octet-stream", "category": "mod"},
    "nfo": {"mime": "text/plain", "category": "info"},
    "sfv": {"mime": "text/plain", "category": "info"},
    "md5": {"mime": "text/plain", "category": "info"},
    "sha1": {"mime": "text/plain", "category": "info"},
    "sha256": {"mime": "text/plain", "category": "info"}
}

MAX_LEN_PER_FIELD = 500

FORBIDDEN_CHARS_STRICT = set("<>[]{}()'\";\\")
FORBIDDEN_CHARS_PARANOID = set(
    ".,-#<>[]$%*()'`;?¿:\"=~{}@&/|·¬\\"
)

STRICT_REGEX = re.compile(r"^[A-Za-z0-9_]+$")
PARANOID_REGEX = re.compile(r"^[a-z0-9]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._-]{3,32}$")

class PayloadValidator:
    def __init__(self, level: SecurityLevel):
        self.level = level

    def scan_string(self, path: str, s: str) -> List[Issue]:
        issues: List[Issue] = []

        if len(s) > MAX_LEN_PER_FIELD:
            issues.append(Issue(
                path, "length_exceeded",
                severity=2,
                count=len(s),
                extra={"max": MAX_LEN_PER_FIELD}
            ))

        normalized = normalize_and_clean(s)
        if normalized != s:
            issues.append(Issue(
                path,
                "unicode_normalization_changed",
                severity=2
            ))
        s = normalized

        if self.level == SecurityLevel.USERNAME:
            if has_combining_marks(s):
                issues.append(Issue(path, "combining_marks_detected", severity=5))

            if has_mixed_scripts(s):
                issues.append(Issue(path, "mixed_unicode_scripts", severity=5))

            for ch in s:
                if ord(ch) > 127:
                    issues.append(Issue(
                        path,
                        "non_ascii_char",
                        char=repr(ch),
                        codepoint=f"U+{ord(ch):04X}",
                        category=unicodedata.category(ch),
                        severity=5
                    ))
                    break

            if not USERNAME_REGEX.fullmatch(s):
                issues.append(Issue(
                    path,
                    "invalid_username_format",
                    severity=4,
                    extra={"regex": USERNAME_REGEX.pattern}
                ))

            return issues #aquí cierro proceso

        if self.level in {SecurityLevel.OPEN, SecurityLevel.SAFE_TEXT}:
            if detect_sql_payload(s):
                issues.append(Issue(path, "sql_injection_like", severity=3))
            if detect_xss_payload(s):
                issues.append(Issue(path, "xss_like", severity=3))

        if self.level in {SecurityLevel.STRICT, SecurityLevel.PARANOID}:
            if has_combining_marks(s):
                issues.append(Issue(path, "combining_marks_detected", severity=5))

            if has_mixed_scripts(s):
                issues.append(Issue(path, "mixed_unicode_scripts", severity=5))

            for ch in s:
                if ord(ch) > 127:
                    issues.append(Issue(
                        path,
                        "non_ascii_char",
                        char=repr(ch),
                        codepoint=f"U+{ord(ch):04X}",
                        category=unicodedata.category(ch),
                        severity=5
                    ))
                    break

            if self.level == SecurityLevel.STRICT:
                if not STRICT_REGEX.fullmatch(s):
                    issues.append(Issue(path, "regex_violation_strict", severity=4))

            if self.level == SecurityLevel.PARANOID:
                if not PARANOID_REGEX.fullmatch(s):
                    issues.append(Issue(path, "regex_violation_paranoid", severity=5))

        forbidden = (
            FORBIDDEN_CHARS_PARANOID if self.level == SecurityLevel.PARANOID
            else FORBIDDEN_CHARS_STRICT if self.level == SecurityLevel.STRICT
            else set()
        )

        bad_chars = {
            ch: cnt for ch, cnt in Counter(s).items()
            if ch in forbidden or is_forbidden_category(ch)
        }

        if bad_chars:
            issues.append(Issue(
                path,
                "invalid_chars_detected",
                severity=4,
                extra={"chars": bad_chars}
            ))

        return issues

    def walk(self, obj: Any, path: str = "$") -> List[Issue]:
        issues: List[Issue] = []

        if isinstance(obj, dict):
            for k, v in obj.items():
                ks = safe_str(k)
                if ks is None:
                    issues.append(Issue(path, "invalid_key_type", severity=5))
                else:
                    issues.extend(self.scan_string(f'{path}["{ks}"]<key>', ks))
                issues.extend(self.walk(v, f'{path}["{k}"]'))

        elif isinstance(obj, (list, tuple, set)):
            for i, item in enumerate(obj):
                issues.extend(self.walk(item, f"{path}[{i}]"))

        else:
            s = safe_str(obj)
            if s is None:
                issues.append(Issue(path, "invalid_value_type", severity=5))
            else:
                issues.extend(self.scan_string(path, s))

        return issues

    def validate(self, payload: Any) -> ValidationResult:
        issues = self.walk(payload)
        grouped = defaultdict(list)
        for i in issues:
            grouped[i.path].append(i)

        return ValidationResult(
            valido=len(issues) == 0,
            severity_max=max((i.severity for i in issues), default=0),
            errores=sorted(set(i.problem for i in issues)),
            detalles=grouped
        )

    def is_valid(self, payload: Any) -> bool:
        return self.validate(payload).valido

    def validate_string(self, s: str, path: str = "$") -> ValidationResult:
        try:
            issues = self.scan_string(path, s)
            grouped = defaultdict(list)
            for i in issues:
                grouped[i.path].append(i)
            return ValidationResult(
                valido=len(issues) == 0,
                severity_max=max((i.severity for i in issues), default=0),
                errores=sorted(set(i.problem for i in issues)),
                detalles=grouped
            )
        except Exception as e:
            raise PayloadValidatorError(e)