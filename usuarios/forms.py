from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from .models import Usuario

CLASSES_INPUT = (
    'w-full px-3.5 py-2.5 text-slate-800 bg-slate-50 border border-slate-300 '
    'rounded-lg focus:outline-none focus:border-brand focus:ring-4 focus:ring-brand/10 '
    'placeholder:text-slate-400 transition duration-150'
)


def normalizar_email(email):
    """Emails são guardados e comparados sempre em minúsculas."""
    return (email or '').strip().lower()


class LoginForm(forms.Form):
    """Formulário de login por email e senha."""

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'seu@email.com',
            'autofocus': True,
            'autocomplete': 'email',
            'class': CLASSES_INPUT,
        }),
    )
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Sua senha',
            'autocomplete': 'current-password',
            'class': CLASSES_INPUT,
        }),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = normalizar_email(cleaned.get('email'))
        senha = cleaned.get('senha')

        if email and senha:
            self.user_cache = authenticate(
                self.request, username=email, password=senha,
            )
            if self.user_cache is None:
                raise forms.ValidationError('Email ou senha incorretos.')
            if not self.user_cache.is_active:
                raise forms.ValidationError('Esta conta está desativada.')

        return cleaned

    def get_user(self):
        return self.user_cache


class UsuarioCadastroForm(forms.ModelForm):
    """IS cria um usuário professor ou empreendedor.

    O papel é limitado aos dois perfis que a IS pode criar; mesmo
    manipulando o POST, admin e IS não passam pela validação.
    """

    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Senha inicial do usuário',
            'autocomplete': 'new-password',
            'class': CLASSES_INPUT,
        }),
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'papel']
        labels = {
            'nome': 'Nome completo',
            'papel': 'Perfil',
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Ex.: Maria da Silva',
                'autofocus': True,
                'class': CLASSES_INPUT,
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'seu@email.com',
                'autocomplete': 'email',
                'class': CLASSES_INPUT,
            }),
            'papel': forms.Select(attrs={'class': CLASSES_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        papeis_is = (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR)
        self.fields['papel'].choices = [
            c for c in Usuario.Papel.choices if c[0] in papeis_is
        ]

    def clean_email(self):
        email = normalizar_email(self.cleaned_data['email'])
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe um usuário com este email.')
        return email

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get('senha')
        if senha:
            usuario = Usuario(
                nome=cleaned.get('nome', ''),
                email=cleaned.get('email', ''),
            )
            try:
                validate_password(senha, user=usuario)
            except forms.ValidationError as erro:
                self.add_error('senha', erro)
        return cleaned

    def save(self, commit=True):
        """Cria o usuário com a senha já criptografada."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['senha'])
        if commit:
            user.save()
        return user


class TrocarSenhaForm(forms.Form):
    """Troca da própria senha pelo usuário logado.

    Exige a senha atual (evita trocar senha de quem deixou a sessão aberta)
    e passa a nova senha pelos mesmos validadores do settings.
    """

    senha_atual = forms.CharField(
        label='Senha atual',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Sua senha atual',
            'autocomplete': 'current-password',
            'class': CLASSES_INPUT,
        }),
    )
    nova_senha = forms.CharField(
        label='Nova senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Nova senha',
            'autocomplete': 'new-password',
            'class': CLASSES_INPUT,
        }),
        help_text='Combine letras e números, com pelo menos 8 caracteres.',
    )
    confirmar_nova_senha = forms.CharField(
        label='Confirmar nova senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repita a nova senha',
            'autocomplete': 'new-password',
            'class': CLASSES_INPUT,
        }),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        senha_atual = cleaned.get('senha_atual')
        nova_senha = cleaned.get('nova_senha')
        confirmacao = cleaned.get('confirmar_nova_senha')

        if senha_atual and self.user and not self.user.check_password(senha_atual):
            self.add_error('senha_atual', 'Senha atual incorreta.')

        if nova_senha and confirmacao and nova_senha != confirmacao:
            self.add_error('confirmar_nova_senha', 'As senhas não conferem.')

        if nova_senha and self.user and self.user.check_password(nova_senha):
            self.add_error('nova_senha', 'A nova senha deve ser diferente da atual.')

        if nova_senha:
            try:
                validate_password(nova_senha, user=self.user)
            except forms.ValidationError as erro:
                self.add_error('nova_senha', erro)

        return cleaned