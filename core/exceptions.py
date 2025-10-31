from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Handler personalizado para excepciones.
    Proporciona respuestas consistentes y detalladas.
    """
    # Llamar al handler por defecto primero
    response = exception_handler(exc, context)
    
    # Si es una excepción de Django no manejada por DRF
    if response is None:
        if isinstance(exc, DjangoValidationError):
            response = Response(
                {
                    'success': False,
                    'error': 'Validation Error',
                    'detail': exc.messages if hasattr(exc, 'messages') else str(exc),
                    'status_code': status.HTTP_400_BAD_REQUEST
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, Http404):
            response = Response(
                {
                    'success': False,
                    'error': 'Not Found',
                    'detail': 'El recurso solicitado no existe',
                    'status_code': status.HTTP_404_NOT_FOUND
                },
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            # Error no controlado
            response = Response(
                {
                    'success': False,
                    'error': 'Internal Server Error',
                    'detail': 'Ha ocurrido un error inesperado',
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Personalizar la respuesta
    if response is not None:
        # Estructura personalizada
        custom_response_data = {
            'success': False,
            'error': response.data.get('detail', 'Error'),
            'status_code': response.status_code
        }
        
        # Agregar errores de validación si existen
        if 'detail' not in response.data and isinstance(response.data, dict):
            custom_response_data['errors'] = response.data
        else:
            custom_response_data['detail'] = response.data.get('detail', str(exc))
        
        response.data = custom_response_data
    
    return response


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class EmpresaNotFoundError(APIException):
    """Excepción cuando no se encuentra una empresa"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Empresa no encontrada'
    default_code = 'empresa_not_found'


class SucursalNotFoundError(APIException):
    """Excepción cuando no se encuentra una sucursal"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Sucursal no encontrada'
    default_code = 'sucursal_not_found'


class DuplicateRUCError(APIException):
    """Excepción cuando se intenta registrar un RUC duplicado"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'El RUC ya está registrado en el sistema'
    default_code = 'duplicate_ruc'


class DuplicateCodigoSucursalError(APIException):
    """Excepción cuando se intenta registrar un código de sucursal duplicado"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'El código de sucursal ya existe'
    default_code = 'duplicate_codigo_sucursal'


class InactiveEmpresaError(APIException):
    """Excepción cuando se intenta operar con una empresa inactiva"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'No se puede operar con una empresa inactiva'
    default_code = 'inactive_empresa'


class InvalidStateTransitionError(APIException):
    """Excepción para transiciones de estado inválidas"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Transición de estado no permitida'
    default_code = 'invalid_state_transition'


class BusinessRuleViolationError(APIException):
    """Excepción genérica para violaciones de reglas de negocio"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Violación de regla de negocio'
    default_code = 'business_rule_violation'