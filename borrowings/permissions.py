from rest_framework import permissions


class IsBorrowerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow borrowers of a borrowing object or admins to access it.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        return obj.user == request.user
