from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nome',
            'email',
            'telefone',
            'cpf_cnpj',
            'endereco',
            'cidade',
            'estado',
            'ativo',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'telefone': forms.TextInput(attrs={'class': 'form-input'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-input'}),
            'endereco': forms.TextInput(attrs={'class': 'form-input'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input'}),
            'estado': forms.Select(attrs={'class': 'form-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
