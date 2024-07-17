from rest_framework import permissions


class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return (obj.user == request.user) and (request.user.is_verfied)

class IsOwner2(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return (obj.owner == request.user) and (request.user.is_verfied)

class IsAuthenticated(permissions.BasePermission):
    """
    Allows access only to authenticated users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_verified)