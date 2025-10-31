from random import choices

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario"""

    def create_user(self, username, first_name, last_name, email, celular, sucursal, perfil, password=None, **extra_fields):
        """
        Crea y guarda un usuario normal
        """
        if not username:
            raise ValueError('El usuario debe tener un username')
        if not email:
            raise ValueError('El usuario debe tener un email')
        if not first_name:
            raise ValueError('El usuario debe tener un nombre')
        if not last_name:
            raise ValueError('El usuario debe tener un apellido')
        if not celular:
            raise ValueError('El usuario debe tener un celular')
        if not sucursal:
            raise ValueError('El usuario debe estar asignado a una sucursal')
        if perfil is None:
            raise ValueError('El usuario debe tener un perfil')
        
        # Normalizar email
        email = self.normalize_email(email)
        
        # Crear usuario
        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            celular=celular,
            sucursal=sucursal,
            perfil=perfil,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, first_name, last_name, email, celular=None, perfil=1, sucursal=None, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con privilegios de administrador
        """
        # Establecer valores por defecto para superusuario
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        # Validar que sean True
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True')
        
        # Normalizar email
        email = self.normalize_email(email)
        
        # Crear superusuario directamente sin llamar a create_user
        # para evitar conflicto con **extra_fields
        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            celular=celular,
            sucursal=sucursal,
            perfil=perfil,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user