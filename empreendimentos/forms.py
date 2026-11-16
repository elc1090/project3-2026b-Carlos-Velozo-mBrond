from django import forms

from usuarios.forms import CLASSES_INPUT

from .models import Empreendimento


class EmpreendimentoCadastroForm(forms.ModelForm):
    """ACE-05: dados do empreendimento informados ao criar o empreendedor (F1, decisão 7.1)."""

    class Meta:
        model = Empreendimento
        fields = ['nome', 'tipo', 'descricao']
        labels = {
            'nome': 'Nome do empreendimento',
            'tipo': 'Tipo',
            'descricao': 'Descrição',
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Ex.: Ateliê da Praça',
                'class': CLASSES_INPUT,
            }),
            'tipo': forms.TextInput(attrs={
                'placeholder': 'Ex.: Artesanato',
                'class': CLASSES_INPUT,
            }),
            'descricao': forms.Textarea(attrs={
                'rows': 3,
                'class': CLASSES_INPUT,
            }),
        }
