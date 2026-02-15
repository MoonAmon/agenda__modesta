from django import forms

from agenda_modesta.projects.models import Projeto

from .models import Agenda


class AgendaForm(forms.ModelForm):
    class Meta:
        model = Agenda
        fields = [
            'titulo',
            'descricao',
            'data_inicio',
            'data_fim',
            'projeto',
            'local',
            'confirmado',
            'notificar_email',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'data_inicio': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'data_fim': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'projeto': forms.Select(attrs={'class': 'form-input'}),
            'local': forms.TextInput(attrs={'class': 'form-input'}),
            'confirmado': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'notificar_email': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['projeto'].required = False
        self.fields['projeto'].empty_label = "Sem projeto (opcional)"


# ---------- Formulários HTMX em passos ----------

class StepProjetoForm(forms.Form):
    """Passo 1 – escolher projeto (agora opcional)."""
    projeto = forms.ModelChoiceField(
        queryset=Projeto.objects.none(),
        label="Projeto",
        required=False,
        empty_label="Sem projeto (opcional)",
        widget=forms.Select(attrs={"class": "form-input"}),
    )


class StepDetalhesForm(forms.Form):
    """Passo 2 – detalhes do agendamento."""
    titulo = forms.CharField(
        max_length=150,
        label="Título",
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    descricao = forms.CharField(
        required=False,
        label="Descrição",
        widget=forms.Textarea(attrs={"class": "form-input", "rows": 3}),
    )
    data_inicio = forms.DateTimeField(
        label="Data/hora início",
        widget=forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}),
    )
    data_fim = forms.DateTimeField(
        label="Data/hora fim",
        widget=forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}),
    )
    local = forms.CharField(
        required=False,
        max_length=150,
        label="Local",
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
