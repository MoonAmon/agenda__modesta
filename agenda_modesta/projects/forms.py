from django import forms
from .models import Projeto


class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = [
            'nome',
            'cliente',
            'descricao',
            'status',
            'data_inicio',
            'data_prevista_conclusao',
            'data_conclusao',
            'ativo',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'cliente': forms.Select(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'data_prevista_conclusao': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'data_conclusao': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
