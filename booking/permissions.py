from rest_framework import permissions


class IsPlaceManager(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            user.is_authenticated and
            user.role == 'manager' and
            user in obj.managers.all()
        )
