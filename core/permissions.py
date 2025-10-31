from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado: Solo admins pueden modificar, todos pueden leer.
    """
    def has_permission(self, request, view):
        # Permitir GET, HEAD, OPTIONS para todos los usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Permitir modificaciones solo a admins
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso: Solo el propietario o admin puede modificar.
    """
    def has_object_permission(self, request, view, obj):
        # Lectura permitida para todos los autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Admins tienen acceso total
        if request.user and request.user.is_staff:
            return True
        
        # Si el objeto tiene campo 'created_by', verificar propiedad
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user.username
        
        return False


class CanManageEmpresa(permissions.BasePermission):
    """
    Permiso personalizado para gestión de empresas.
    """
    def has_permission(self, request, view):
        # Lectura permitida para autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Creación y modificación requiere staff o permisos específicos
        if request.user and request.user.is_staff:
            return True
        
        # Puedes agregar lógica de grupos o permisos específicos
        return request.user.has_perm('core.add_empresa') or \
               request.user.has_perm('core.change_empresa')


class CanManageSucursal(permissions.BasePermission):
    """
    Permiso personalizado para gestión de sucursales.
    """
    def has_permission(self, request, view):
        # Lectura permitida para autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Creación y modificación requiere permisos
        if request.user and request.user.is_staff:
            return True
        
        return request.user.has_perm('core.add_sucursal') or \
               request.user.has_perm('core.change_sucursal')


class IsAuthenticatedAndActive(permissions.BasePermission):
    """
    Usuario debe estar autenticado Y activo.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class ReadOnly(permissions.BasePermission):
    """
    Solo permite operaciones de lectura.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS