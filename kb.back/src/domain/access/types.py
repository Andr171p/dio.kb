from enum import IntFlag, auto


class Permission(IntFlag):
    READ = auto()
    WRITE = auto()
    PUBLISH = auto()
    ARCHIVE = auto()
