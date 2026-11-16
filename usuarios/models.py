from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


def normalizar_email(email):
    """ACE-01: emails são guardados e comparados sempre em minúsculas."""
    return (email or '').strip().lower()


class UsuarioManager(BaseUserManager):
    """Manager que usa email em vez de username."""

    # O parâmetro se chama `password` porque é o nome que o `createsuperuser` envia (ACE-13).
    def create_user(self, email, nome, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        user = self.model(email=email, nome=nome, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('papel', Usuario.Papel.ADMIN)
        return self.create_user(email, nome, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Usuário do sistema. Login feito por email."""

    class Papel(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        IS = 'is', 'Incubadora Social'
        PROFESSOR = 'professor', 'Professor'
        EMPREENDEDOR = 'empreendedor', 'Empreendedor'

    email = models.EmailField('email', unique=True)
    nome = models.CharField('nome', max_length=150)
    papel = models.CharField('papel', max_length=20, choices=Papel.choices)
    is_active = models.BooleanField('ativo', default=True)
    is_staff = models.BooleanField('acesso ao admin', default=False)
    deve_trocar_senha = models.BooleanField('deve trocar a senha', default=False)
    criado_em = models.DateTimeField('criado em', auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        self.email = normalizar_email(self.email)  # ACE-01: venha a conta de onde vier
        super().save(*args, **kwargs)
