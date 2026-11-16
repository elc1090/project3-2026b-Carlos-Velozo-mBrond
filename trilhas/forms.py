from django import forms

from empreendimentos.models import Empreendimento

from . import regras
from .models import AtividadeTrilha, Inscricao, Trilha

CLASSES_INPUT = (
    'w-full px-3.5 py-2.5 text-slate-800 bg-slate-50 border border-slate-300 '
    'rounded-lg focus:outline-none focus:border-brand focus:ring-4 focus:ring-brand/10 '
    'placeholder:text-slate-400 transition duration-150'
)


class TrilhaForm(forms.ModelForm):
    """Título e descrição da trilha personalizada (criar e editar)."""

    class Meta:
        model = Trilha
        fields = ['titulo', 'descricao']
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': 'Ex.: Gestão financeira básica',
                'autofocus': True,
                'class': CLASSES_INPUT,
            }),
            'descricao': forms.Textarea(attrs={
                'placeholder': 'Objetivo da trilha e o que o empreendimento vai aprender',
                'rows': 5,
                'class': CLASSES_INPUT,
            }),
        }

    def clean_titulo(self):
        titulo = self.cleaned_data['titulo'].strip()
        if not titulo:
            raise forms.ValidationError('Informe um título.')
        return titulo


SIM_NAO = (('sim', 'Sim'), ('nao', 'Não'))


def _sim_nao(rotulo):
    """Sim/Não que, quando não enviado, vale Sim (A-07: padrão obrigatória e exige validação)."""
    return forms.TypedChoiceField(
        label=rotulo,
        choices=SIM_NAO,
        coerce=lambda valor: valor == 'sim',
        empty_value=True,
        required=False,
        initial='sim',
        widget=forms.Select(attrs={'class': CLASSES_INPUT}),
    )


class AtividadeForm(forms.ModelForm):
    """Atividade completa: criar, ou editar com a trilha em rascunho (TRL-04)."""

    obrigatoria = _sim_nao('Obrigatória')
    exige_validacao = _sim_nao('Exige validação')

    class Meta:
        model = AtividadeTrilha
        fields = [
            'titulo', 'descricao', 'tipo', 'endereco', 'obrigatoria',
            'exige_validacao', 'prazo_fixo', 'dias_apos_inscricao',
        ]
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
            'endereco': 'Endereço (para atividades do tipo Link)',
            'prazo_fixo': 'Prazo fixo',
            'dias_apos_inscricao': 'Ou: prazo em dias após a inscrição',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={'class': CLASSES_INPUT, 'autofocus': True}),
            'descricao': forms.Textarea(attrs={'class': CLASSES_INPUT, 'rows': 4}),
            'tipo': forms.Select(attrs={'class': CLASSES_INPUT}),
            'endereco': forms.URLInput(attrs={'class': CLASSES_INPUT, 'placeholder': 'https://'}),
            'prazo_fixo': forms.DateInput(attrs={'class': CLASSES_INPUT, 'type': 'date'}, format='%Y-%m-%d'),
            'dias_apos_inscricao': forms.NumberInput(attrs={'class': CLASSES_INPUT, 'min': 1}),
        }

    def clean_titulo(self):
        titulo = self.cleaned_data['titulo'].strip()
        if not titulo:
            raise forms.ValidationError('Informe um título.')
        return titulo

    def clean(self):
        cleaned = super().clean()
        # Erros presos a um campo: assim as restrições do banco não repetem a mensagem.
        if cleaned.get('tipo') == AtividadeTrilha.Tipo.LINK and not cleaned.get('endereco'):
            if 'endereco' not in self.errors:
                self.add_error('endereco', 'Atividade do tipo Link precisa de um endereço.')  # A-05
        if cleaned.get('prazo_fixo') and cleaned.get('dias_apos_inscricao') is not None:
            self.add_error(
                'dias_apos_inscricao',
                'Escolha só um tipo de prazo: data fixa ou dias após a inscrição.',  # A-06
            )
        dias = cleaned.get('dias_apos_inscricao')
        if dias is not None and dias < 1 and 'dias_apos_inscricao' not in self.errors:
            self.add_error('dias_apos_inscricao', 'Informe pelo menos 1 dia.')
        return cleaned


class AtividadeTextoForm(forms.ModelForm):
    """Só os textos da atividade, com a trilha publicada (A-11: o resto não muda)."""

    class Meta:
        model = AtividadeTrilha
        fields = ['titulo', 'descricao', 'endereco']
        labels = AtividadeForm.Meta.labels
        widgets = {campo: AtividadeForm.Meta.widgets[campo] for campo in fields}

    def clean_titulo(self):
        titulo = self.cleaned_data['titulo'].strip()
        if not titulo:
            raise forms.ValidationError('Informe um título.')
        return titulo

    def clean(self):
        cleaned = super().clean()
        if (
            self.instance.tipo == AtividadeTrilha.Tipo.LINK
            and not cleaned.get('endereco')
            and 'endereco' not in self.errors
        ):
            self.add_error('endereco', 'Atividade do tipo Link precisa de um endereço.')
        return cleaned


class InscricaoForm(forms.ModelForm):
    """IS inscreve um empreendimento ativo numa trilha personalizada publicada (INS-01).

    Quem salva é `regras.inscrever`. Uma trilha forjada fora da lista é recusada pelo
    próprio campo, porque o queryset já vem filtrado (A-02, A-13).
    """

    class Meta:
        model = Inscricao
        fields = ['empreendimento', 'trilha']
        widgets = {
            'empreendimento': forms.Select(attrs={'class': CLASSES_INPUT}),
            'trilha': forms.Select(attrs={'class': CLASSES_INPUT}),
        }
        error_messages = {
            'trilha': {'invalid_choice': 'Escolha uma trilha personalizada publicada.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empreendimento'].queryset = (
            Empreendimento.objects.filter(desativado_em__isnull=True).order_by('nome')
        )
        self.fields['trilha'].queryset = regras.trilhas_inscriviveis().order_by('titulo')

    def clean(self):
        cleaned = super().clean()
        empreendimento = cleaned.get('empreendimento')
        trilha = cleaned.get('trilha')
        if empreendimento and trilha:
            # A-03: só conta inscrição ativa ou pausada; concluída e cancelada liberam.
            existe = Inscricao.objects.filter(
                empreendimento=empreendimento,
                trilha=trilha,
                status__in=regras.STATUS_EM_ANDAMENTO,
            ).exists()
            if existe:
                raise forms.ValidationError(
                    'Este empreendimento já está inscrito nesta trilha.'
                )
        return cleaned
