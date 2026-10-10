from .types import Permission


def has_permission(permissions: Permission, required: Permission) -> bool:
    return permissions & required == required
