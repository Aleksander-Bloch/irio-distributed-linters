from typing import ClassVar as _ClassVar, Optional as _Optional

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message

DESCRIPTOR: _descriptor.FileDescriptor


class LintingRequest(_message.Message):
    __slots__ = ("code",)
    CODE_FIELD_NUMBER: _ClassVar[int]
    code: str

    def __init__(self, code: _Optional[str] = ...) -> None: ...


class LintingResult(_message.Message):
    __slots__ = ("status", "comment")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    status: int
    comment: str

    def __init__(self, status: _Optional[int] = ..., comment: _Optional[str] = ...) -> None: ...
