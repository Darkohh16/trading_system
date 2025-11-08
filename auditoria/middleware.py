from auditoria.signals import set_current_user, set_audit_motivo


class AuditoriaMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Capturar el usuario si está autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)
        
        # Capturar el motivo desde el header X-Audit-Motivo si está presente
        motivo = request.META.get('HTTP_X_AUDIT_MOTIVO', None)
        if motivo:
            set_audit_motivo(motivo)
        else:
            set_audit_motivo(None)
        
        response = self.get_response(request)
        
        # Limpiar el contexto después de la solicitud
        set_current_user(None)
        set_audit_motivo(None)
        
        return response
