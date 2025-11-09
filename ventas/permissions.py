from rest_framework import permissions

class CanApproveLowCostSale(permissions.BasePermission):
    def has_permission(self, request, view):

        if request.method in permissions.SAFE_METHODS:
            return True

        #puede_aprobar_bajo_costo'
        return request.user and request.user.is_authenticated and request.user.puede_aprobar_bajo_costo
