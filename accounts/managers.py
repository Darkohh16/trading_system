from django.contrib.auth.models import BaseUserManager
from trading_system.choices import *
from django.utils.crypto import get_random_string


class UserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, perfil=None, password=None, **extra_fields):
        if not username:
            raise ValueError('Se requiere el nombre de usuario')
        if not email:
            raise ValueError('Se requiere el email del usuario')
        if not first_name:
            raise ValueError('Se requiere el nombre del usuario')
        if not last_name:
            raise ValueError('Se requiere el apellido del usuario')

        if perfil is None:
            perfil = AccesoSistema.INVITADO

        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email),
            perfil=perfil,
            **extra_fields
        )

        """if password is None:
            password = self.make_random_password(
                length=8, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
            )
        """
        if password is None:
            password = get_random_string(
                length=8, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
            )

        user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, first_name, last_name, password=None, **extra_fields):

        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            perfil=AccesoSistema.ADMINISTRADOR,
            password=password,
            **extra_fields
        )


    def update_user(self, username, data_user):
        try:
            usern = self.get(username=username)

            if 'first_name' in data_user:
                usern.first_name = data_user.get('first_name')
            if 'last_name' in data_user:
                usern.last_name = data_user.get('last_name')
            if 'email' in data_user:
                usern.email = self.normalize_email(data_user.get('email'))
            if 'password' in data_user:
                usern.set_password(data_user.get('password'))
            if 'username' in data_user:
                usern.username = data_user.get('username')
            if 'perfil' in data_user:
                usern.perfil = data_user.get('perfil')

            usern.save()
            return usern
        except self.model.DoesNotExist:
            raise ValueError('El usuario no existe')

    def delete_user(self, username):
        try:
            usern = self.get(username=username)
            usern.delete()
            return print(f'Usuario {username} eliminado correctamente')
        except self.model.DoesNotExist:
            raise ValueError('El usuario no existe')