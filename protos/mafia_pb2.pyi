from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class Notifications(_message.Message):
    __slots__ = ["name", "type"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: str
    def __init__(self, name: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...

class Player(_message.Message):
    __slots__ = ["name", "room_name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ROOM_NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    room_name: str
    def __init__(self, name: _Optional[str] = ..., room_name: _Optional[str] = ...) -> None: ...

class PlayersList(_message.Message):
    __slots__ = ["players"]
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    players: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, players: _Optional[_Iterable[str]] = ...) -> None: ...

class Room(_message.Message):
    __slots__ = ["room_name"]
    ROOM_NAME_FIELD_NUMBER: _ClassVar[int]
    room_name: str
    def __init__(self, room_name: _Optional[str] = ...) -> None: ...

class StartGameResponse(_message.Message):
    __slots__ = ["players", "role"]
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    players: _containers.RepeatedScalarFieldContainer[str]
    role: str
    def __init__(self, players: _Optional[_Iterable[str]] = ..., role: _Optional[str] = ...) -> None: ...

class Vote(_message.Message):
    __slots__ = ["name", "room_name", "vote"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ROOM_NAME_FIELD_NUMBER: _ClassVar[int]
    VOTE_FIELD_NUMBER: _ClassVar[int]
    name: str
    room_name: str
    vote: str
    def __init__(self, name: _Optional[str] = ..., room_name: _Optional[str] = ..., vote: _Optional[str] = ...) -> None: ...

class VoteResponse(_message.Message):
    __slots__ = ["player", "role"]
    PLAYER_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    player: str
    role: str
    def __init__(self, player: _Optional[str] = ..., role: _Optional[str] = ...) -> None: ...
