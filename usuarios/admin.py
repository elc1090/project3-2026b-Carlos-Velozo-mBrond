from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import Usuario

# RN-16: o /admin/ só gerencia contas e papéis (F0, 3.3.1).
admin.site.unregister(Group)


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ('email', 'nome', 'papel', 'is_active')
    list_filter = ('papel', 'is_active')
    search_fields = ('email', 'nome')
    ordering = ('email',)

    # Campos exibidos ao editar um usuário existente
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Dados pessoais', {'fields': ('nome', 'papel')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    # Campos exibidos ao criar um novo usuário
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nome', 'papel', 'password1', 'password2'),
        }),
    )
